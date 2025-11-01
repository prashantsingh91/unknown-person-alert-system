"""
Main FastAPI Application for Unknown Person Alert System
Real-time face recognition with WebSocket streaming
"""
import asyncio
import base64
import logging
import os
import time
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque

import cv2
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.face_recognizer import FaceRecognizer
from core.unknown_tracker import UnknownPersonTracker
from core.known_tracker import KnownPersonTracker
from core.video_processor import VideoProcessor, VideoSource
from websocket.manager import ConnectionManager
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Unknown Person Alert System", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount snapshots directory
app.mount("/snapshots", StaticFiles(directory=config.SNAPSHOT_DIR), name="snapshots")

# Global instances
face_recognizer: Optional[FaceRecognizer] = None
unknown_tracker: Optional[UnknownPersonTracker] = None
known_tracker: Optional[KnownPersonTracker] = None
video_processor: Optional[VideoProcessor] = None
ws_manager = ConnectionManager()

# Known persons log (circular buffer)
known_persons_log = deque(maxlen=config.MAX_KNOWN_PERSONS_LOG)

# System state
is_processing = False
processing_task: Optional[asyncio.Task] = None


# Request/Response models
class VideoSourceRequest(BaseModel):
    source_type: str  # "file" or "camera"
    path: Optional[str] = None
    camera_id: Optional[int] = 0


class ControlRequest(BaseModel):
    action: str  # "play", "pause", "toggle"


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global face_recognizer, unknown_tracker, known_tracker, video_processor
    
    logger.info("Initializing Unknown Person Alert System...")
    
    try:
        # Initialize face recognizer
        logger.info("Loading face recognizer...")
        face_recognizer = FaceRecognizer(
            database_path=config.FACE_DATABASE_PATH,
            similarity_threshold=config.SIMILARITY_THRESHOLD,
            gpu_id=config.GPU_DEVICE_ID,
            det_size=config.DET_SIZE,
            grace_period=10.0  # 10 second grace period for temporary occlusions
        )
        
        # Initialize unknown tracker
        logger.info("Initializing unknown person tracker...")
        unknown_tracker = UnknownPersonTracker(
            cooldown_seconds=config.UNKNOWN_COOLDOWN_SECONDS,
            similarity_threshold=config.UNKNOWN_SIMILARITY_THRESHOLD,
            snapshot_dir=config.SNAPSHOT_DIR,
            min_detections_before_alert=config.MIN_DETECTIONS_BEFORE_ALERT,
            max_embedding_history=5,  # Keep last 5 embeddings for moving average
            spatial_iou_threshold=config.SPATIAL_IOU_THRESHOLD,  # Phase 2: Spatial proximity
            temporal_window_seconds=config.TEMPORAL_WINDOW_SECONDS  # Phase 2: Temporal window
        )
        
        # Initialize known person tracker
        logger.info("Initializing known person tracker...")
        known_tracker = KnownPersonTracker(
            cooldown_seconds=config.KNOWN_PERSON_COOLDOWN_SECONDS
        )
        
        # Initialize video processor with default video
        logger.info("Initializing video processor...")
        video_processor = VideoProcessor(
            video_path=config.DEFAULT_VIDEO_PATH,
            frame_skip=config.FRAME_SKIP,
            target_width=1280
        )
        
        if video_processor.open():
            logger.info("Video processor ready")
        else:
            logger.error("Failed to open default video")
        
        logger.info("System initialized successfully!")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global is_processing, processing_task, video_processor
    
    logger.info("Shutting down...")
    
    # Stop processing
    is_processing = False
    if processing_task:
        processing_task.cancel()
        try:
            await processing_task
        except asyncio.CancelledError:
            pass
    
    # Close video processor
    if video_processor:
        video_processor.close()
    
    logger.info("Shutdown complete")


async def process_video_stream():
    """Main video processing loop"""
    global is_processing, face_recognizer, unknown_tracker, video_processor
    
    logger.info("Starting video processing loop...")
    is_processing = True
    
    last_metrics_time = time.time()
    frame_number = 0
    
    try:
        while is_processing:
            # Check if we have any connected clients
            if ws_manager.get_connection_count() == 0:
                await asyncio.sleep(0.1)
                continue
            
            # Read frame
            ret, frame = video_processor.read_frame()
            if not ret or frame is None:
                await asyncio.sleep(0.01)
                continue
            
            frame_number += 1
            
            # Process frame if needed (skip frames for performance)
            detections_list = []
            if video_processor.should_process_frame():
                process_start = time.time()
                
                # Recognize faces
                results = face_recognizer.process_frame(frame)
                
                for result in results:
                    x1, y1, x2, y2 = result.bbox
                    
                    # Filter out small faces (minimum 60x60 pixels)
                    face_width = int(x2 - x1)
                    face_height = int(y2 - y1)
                    if face_width < 60 or face_height < 60:
                        logger.debug(f"Skipping small face: {face_width}x{face_height}px")
                        continue
                    
                    if result.is_known:
                        # Known person detected
                        detection_dict = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'person_id': result.person_id,
                            'person_name': result.person_name,
                            'confidence': float(result.confidence),
                            'similarity': float(result.similarity),
                            'is_known': True
                        }
                        detections_list.append(detection_dict)
                        
                        # Add to known persons log and broadcast (with deduplication)
                        if known_tracker.should_display(result.person_id):
                            known_persons_log.append({
                                'person_id': result.person_id,
                                'person_name': result.person_name,
                                'similarity': float(result.similarity),
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            # Broadcast known person detection
                            await ws_manager.broadcast_known_person({
                                'person_id': result.person_id,
                                'person_name': result.person_name,
                                'similarity': float(result.similarity),
                                'timestamp': datetime.now().isoformat()
                            })
                        
                        # Draw green box for known person
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                        
                        # Calculate face size
                        face_width = int(x2 - x1)
                        face_height = int(y2 - y1)
                        face_area = face_width * face_height
                        
                        # Display name and similarity
                        label = f"{result.person_name} ({result.similarity:.2f})"
                        cv2.putText(frame, label, (int(x1), int(y1)-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        
                        # Display face size below bbox
                        size_label = f"Size: {face_width}x{face_height} ({face_area}px)"
                        cv2.putText(frame, size_label, (int(x1), int(y2)+20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                    else:
                        # Unknown person detected
                        should_alert, uid, snapshot_path = unknown_tracker.check_unknown_person(
                            result.embedding, frame, result.bbox
                        )
                        
                        detection_dict = {
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'person_id': uid,
                            'person_name': 'Unknown',
                            'confidence': float(result.confidence),
                            'similarity': 0.0,
                            'is_known': False
                        }
                        detections_list.append(detection_dict)
                        
                        if should_alert:
                            # New unknown person - send alert
                            alert_data = {
                                'uid': uid,
                                'timestamp': datetime.now().isoformat(),
                                'snapshot_path': f"/snapshots/{os.path.basename(snapshot_path)}" if snapshot_path else None,
                                'confidence': float(result.confidence)
                            }
                            
                            await ws_manager.broadcast_alert(alert_data)
                            logger.info(f"ALERT: Unknown person {uid} detected!")
                        
                        # Draw red box for unknown person
                        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                        
                        # Calculate face size
                        face_width = int(x2 - x1)
                        face_height = int(y2 - y1)
                        face_area = face_width * face_height
                        
                        # Display "UNKNOWN" label
                        cv2.putText(frame, "UNKNOWN", (int(x1), int(y1)-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                        
                        # Display face size below bbox
                        size_label = f"Size: {face_width}x{face_height} ({face_area}px)"
                        cv2.putText(frame, size_label, (int(x1), int(y2)+20),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                
                # Mark frame as processed
                process_time = time.time() - process_start
                video_processor.mark_processed(process_time)
                
                # Cleanup expired entries periodically
                if frame_number % 100 == 0:
                    unknown_tracker.cleanup_expired()
                    known_tracker.cleanup_expired()
            
            # Encode frame as JPEG
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, config.WS_FRAME_QUALITY])
            if ret:
                frame_bytes = jpeg.tobytes()
                await ws_manager.broadcast_frame(frame_bytes, detections_list)
            
            # Send metrics update periodically
            current_time = time.time()
            if current_time - last_metrics_time >= config.METRICS_UPDATE_INTERVAL:
                metrics = get_system_metrics()
                await ws_manager.broadcast_metrics(metrics)
                last_metrics_time = current_time
                
                # Log FPS and GPU metrics
                video_stats = metrics.get('video', {})
                logger.info(f"📊 FPS: {video_stats.get('processing_fps', 0):.1f} | "
                           f"GPU: {video_stats.get('utilization', 0)}% | "
                           f"Mem: {video_stats.get('memory_used', 0)}MB | "
                           f"Frames: {video_stats.get('processed_count', 0)}")
            
            # Small delay to prevent overwhelming the system
            await asyncio.sleep(config.WS_UPDATE_INTERVAL)
    
    except Exception as e:
        logger.error(f"Error in processing loop: {e}", exc_info=True)
    finally:
        is_processing = False
        logger.info("Video processing loop stopped")


def get_system_metrics() -> Dict:
    """Get current system metrics"""
    video_stats = video_processor.get_stats() if video_processor else {}
    unknown_stats = unknown_tracker.get_stats() if unknown_tracker else {}
    model_info = face_recognizer.get_model_info() if face_recognizer else {}
    
    return {
        'video': video_stats,
        'unknown_tracker': unknown_stats,
        'model': model_info,
        'connections': ws_manager.get_connection_count(),
        'known_persons_count': len(known_persons_log)
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Unknown Person Alert System API", "status": "running"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "face_recognizer": face_recognizer is not None,
        "unknown_tracker": unknown_tracker is not None,
        "video_processor": video_processor is not None,
        "processing": is_processing
    }


@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time video streaming"""
    global processing_task, is_processing
    
    await ws_manager.connect(websocket)
    
    try:
        # Start processing if not already running
        if not is_processing and processing_task is None:
            processing_task = asyncio.create_task(process_video_stream())
        
        # Keep connection alive
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return get_system_metrics()


@app.get("/api/snapshots")
async def get_snapshots():
    """Get list of unknown person snapshots"""
    try:
        snapshot_files = []
        if os.path.exists(config.SNAPSHOT_DIR):
            files = sorted(os.listdir(config.SNAPSHOT_DIR), reverse=True)
            for filename in files:
                if filename.endswith('.jpg'):
                    filepath = os.path.join(config.SNAPSHOT_DIR, filename)
                    stat = os.stat(filepath)
                    snapshot_files.append({
                        'filename': filename,
                        'url': f"/snapshots/{filename}",
                        'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'size': stat.st_size
                    })
        
        return {"snapshots": snapshot_files}
    
    except Exception as e:
        logger.error(f"Error getting snapshots: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/known-persons")
async def get_known_persons():
    """Get recently detected known persons"""
    return {"known_persons": list(known_persons_log)}


@app.post("/api/source")
async def set_video_source(request: VideoSourceRequest):
    """Change video source"""
    global video_processor, is_processing, processing_task
    
    try:
        # Stop current processing
        if is_processing:
            is_processing = False
            if processing_task:
                processing_task.cancel()
                try:
                    await processing_task
                except asyncio.CancelledError:
                    pass
                processing_task = None
        
        # Close current video
        if video_processor:
            video_processor.close()
        
        # Create new video processor
        if request.source_type == "file":
            video_path = request.path or config.DEFAULT_VIDEO_PATH
            video_processor = VideoProcessor(
                video_path=video_path,
                frame_skip=config.FRAME_SKIP,
                target_width=1280
            )
        else:  # camera
            video_processor = VideoProcessor(
                camera_id=request.camera_id or 0,
                frame_skip=config.FRAME_SKIP,
                target_width=1280
            )
        
        # Open new source
        if video_processor.open():
            return {"status": "success", "source": request.source_type}
        else:
            raise HTTPException(status_code=500, detail="Failed to open video source")
    
    except Exception as e:
        logger.error(f"Error changing video source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/control")
async def control_playback(request: ControlRequest):
    """Control video playback"""
    if not video_processor:
        raise HTTPException(status_code=400, detail="No video processor")
    
    if request.action == "play":
        video_processor.resume()
    elif request.action == "pause":
        video_processor.pause()
    elif request.action == "toggle":
        video_processor.toggle_pause()
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return {"status": "success", "action": request.action, "is_paused": video_processor.is_paused}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

