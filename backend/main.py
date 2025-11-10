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
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
import secrets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from core.face_recognizer import FaceRecognizer

# Phase 1: Display/Compute Decoupling
@dataclass
class FrameSnapshot:
    """Snapshot of processed frame data for streaming"""
    frame_bytes: bytes
    detections: List[dict]
    timestamp: float
    frame_number: int
    metrics: Dict
    detections_changed: bool = False  # Phase 4: Track if detections changed

from core.unknown_tracker import UnknownPersonTracker
from core.known_tracker import KnownPersonTracker
from core.video_processor import VideoProcessor, VideoSource
from websocket.manager import ConnectionManager
import config

# Latest-frame fan-out optimization (replaces bounded queue)
class FrameStore:
    def __init__(self):
        self.frame: Optional[FrameSnapshot] = None

    def set_frame(self, snapshot: FrameSnapshot):
        self.frame = snapshot

    def get_frame(self) -> Optional[FrameSnapshot]:
        return self.frame

latest_frame_store = FrameStore()  # Single latest frame slot - atomic updates
processing_task: Optional[asyncio.Task] = None  # Single processing task (producer)
streaming_tasks: Dict[str, asyncio.Task] = {}  # Per-client streaming tasks (consumers)

# Phase 3: JPEG encoding ThreadPool
jpeg_executor: Optional[ThreadPoolExecutor] = None  # Thread pool for CPU-bound JPEG encoding

# Phase 4: Detection delta tracking
last_sent_detections: List[dict] = []  # Track last sent detections for delta comparison

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='backend.log',
    filemode='a'
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

# Authentication: Session storage (in-memory)
sessions: Dict[str, dict] = {}  # {session_id: {username, created_at}}


# Request/Response models
class VideoSourceRequest(BaseModel):
    source_type: str  # "file" or "camera"
    path: Optional[str] = None
    camera_id: Optional[int] = 0


class ControlRequest(BaseModel):
    action: str  # "play", "pause", "toggle"


class LoginRequest(BaseModel):
    username: str
    password: str


# Authentication helper functions
def create_session(username: str) -> str:
    """Create a new session and return session ID"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "username": username,
        "created_at": time.time()
    }
    logger.info(f"Created session for user: {username}")
    return session_id


def validate_session(session_id: Optional[str]) -> bool:
    """Validate if session ID is valid and not expired"""
    if not session_id:
        return False
    
    if session_id not in sessions:
        return False
    
    # Check if session expired
    session = sessions[session_id]
    elapsed_hours = (time.time() - session["created_at"]) / 3600
    if elapsed_hours > config.SESSION_EXPIRY_HOURS:
        # Session expired, remove it
        del sessions[session_id]
        logger.info(f"Session expired: {session_id}")
        return False
    
    return True


def delete_session(session_id: Optional[str]):
    """Delete a session"""
    if session_id and session_id in sessions:
        username = sessions[session_id]["username"]
        del sessions[session_id]
        logger.info(f"Deleted session for user: {username}")


async def require_auth(session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """Dependency to require authentication for protected endpoints"""
    if not validate_session(session_id):
        raise HTTPException(status_code=401, detail="Authentication required")
    return session_id


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup"""
    global face_recognizer, unknown_tracker, known_tracker, video_processor, latest_frame, processing_task, jpeg_executor

    logger.info("Initializing Unknown Person Alert System...")

    try:
        # Phase 3: Initialize JPEG encoding ThreadPool
        logger.info("Initializing JPEG encoding thread pool...")
        jpeg_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="jpeg-encoder")
        logger.info("JPEG encoding thread pool initialized")

        # Initialize face recognizer
        logger.info("Loading face recognizer...")
        face_recognizer = FaceRecognizer(
            database_path=config.FACE_DATABASE_PATH,
            similarity_threshold=config.SIMILARITY_THRESHOLD,
            gpu_id=config.GPU_DEVICE_ID,
            det_size=config.DET_SIZE,
            grace_period=10.0,  # 10 second grace period for temporary occlusions
            model_name=config.FACE_MODEL_NAME,
            enter_threshold=config.ENTER_THRESHOLD,
            stay_threshold=config.STAY_THRESHOLD,
            known_embedding_history=config.KNOWN_EMBEDDING_HISTORY,
            use_hysteresis=config.USE_HYSTERESIS
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
            temporal_window_seconds=config.TEMPORAL_WINDOW_SECONDS,  # Phase 2: Temporal window
            spatial_boost_score=config.SPATIAL_BOOST_SCORE  # Phase 2: Spatial boost
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

        # Note: Processing task will be started manually via play button
        # Do not start processing automatically on startup
        logger.info("System initialized successfully! Waiting for play button to start processing...")

    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global is_processing, processing_task, streaming_tasks, video_processor, jpeg_executor

    logger.info("Shutting down...")

    # Stop processing
    is_processing = False

    # Cancel processing task
    if processing_task:
        processing_task.cancel()
        try:
            await processing_task
        except asyncio.CancelledError:
            pass

    # Cancel all streaming tasks
    for client_id, task in streaming_tasks.items():
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    streaming_tasks.clear()

    # Shutdown JPEG encoding thread pool
    if jpeg_executor:
        jpeg_executor.shutdown(wait=True)
        logger.info("JPEG encoding thread pool shut down")

    # Close video processor
    if video_processor:
        video_processor.close()

    logger.info("Shutdown complete")


def generate_client_id(websocket: WebSocket) -> str:
    """Generate unique client ID for streaming task"""
    return f"client_{id(websocket)}_{time.time()}"


def detections_changed(current_detections: List[dict], last_detections: List[dict]) -> bool:
    """Phase 4: Check if detections changed significantly"""
    if len(current_detections) != len(last_detections):
        return True

    # Check if bounding boxes or person IDs changed significantly
    for curr, last in zip(current_detections, last_detections):
        # Check person ID
        if curr.get('person_id') != last.get('person_id'):
            return True

        # Check bounding box (allow small tolerance for movement)
        curr_bbox = curr.get('bbox', [])
        last_bbox = last.get('bbox', [])
        if len(curr_bbox) == 4 and len(last_bbox) == 4:
            # Check if any coordinate changed by more than 10 pixels
            for c, l in zip(curr_bbox, last_bbox):
                if abs(c - l) > 10:
                    return True

    return False


async def process_frames_task():
    """Single processing task that updates frame snapshots (Writer)"""
    global is_processing, face_recognizer, unknown_tracker, video_processor, latest_frame_store

    logger.info("🚀 PROCESSING TASK STARTED")
    logger.info("Starting video processing loop...")
    is_processing = True
    logger.info("✅ Set is_processing = True")
    
    last_metrics_time = time.time()
    frame_number = 0
    
    # Cache for last detected faces (prevents flickering with frame skip)
    cached_results = []
    cached_detections = []  # Cache for detection info panel

    # Phase 4: Detection delta tracking
    detection_frame_counter = 0  # Counter for periodic detection updates
    
    # Video timing control - match video's native FPS for smooth playback
    video_fps = video_processor.video_fps if video_processor else 25.0
    target_frame_interval = 1.0 / video_fps if video_fps > 0 else 0.04  # Default to 25 FPS if unknown
    last_frame_time = time.time()
    
    try:
        while is_processing:
            # Check if we have any connected clients
            if ws_manager.get_connection_count() == 0:
                await asyncio.sleep(0.1)
                continue
            
            # Timing control: wait to match video's native FPS (for smooth playback)
            current_time = time.time()
            time_since_last_frame = current_time - last_frame_time
            if time_since_last_frame < target_frame_interval:
                await asyncio.sleep(target_frame_interval - time_since_last_frame)
            last_frame_time = time.time()
            
            # Read frame
            ret, frame = video_processor.read_frame()
            if not ret or frame is None:
                # Check if video ended (for file sources)
                if video_processor.source_type.value == "file" and not video_processor.is_playing:
                    # Video ended, stop processing
                    logger.info("📹 Video ended, stopping processing")
                    is_processing = False
                    break
                await asyncio.sleep(0.01)
                continue
            
            frame_number += 1

            # Dynamic frame skip: lower skip when faces present or FPS too low
            faces_present = len(cached_results) > 0  # Check if faces were detected in last processed frame
            video_processor.set_dynamic_skip(faces_present, config.TARGET_PROCESSING_FPS)

            # Process frame if needed (skip frames for performance, but draw boxes on all frames)
            if video_processor.should_process_frame():
                process_start = time.time()

                # Recognize faces (using original method for stability)
                results = face_recognizer.process_frame(frame)
                cached_results = results  # Update cache for drawing on next frames

                # Build detections list for this frame
                detections_list = []

                for result in results:
                    x1, y1, x2, y2 = result.bbox
                    
                    # Filter out small faces and low-confidence detections
                    face_width = int(x2 - x1)
                    face_height = int(y2 - y1)
                    if face_width < config.MIN_FACE_SIZE or face_height < config.MIN_FACE_SIZE:
                        logger.debug(f"Skipping small face: {face_width}x{face_height}px")
                        continue
                    
                    if float(result.confidence) < float(config.DETECTION_CONFIDENCE_THRESHOLD):
                        logger.debug(f"Skipping low-confidence detection: {result.confidence:.2f}")
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
                            # Check if person already exists in log within last 3 minutes
                            current_time = datetime.now()
                            should_add = True
                            
                            # Check existing entries in reverse order (most recent first)
                            for entry in reversed(known_persons_log):
                                if entry['person_id'] == result.person_id:
                                    entry_time = datetime.fromisoformat(entry['timestamp'])
                                    time_diff = (current_time - entry_time).total_seconds()
                                    if time_diff < 180:  # 3 minutes = 180 seconds
                                        should_add = False
                                        logger.debug(f"Known person {result.person_id} already in log ({time_diff:.1f}s ago), skipping")
                                        break
                            
                            if should_add:
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
                
                # Update cached detections for next frames
                cached_detections = detections_list
                
                # Mark frame as processed
                process_time = time.time() - process_start
                video_processor.mark_processed(process_time)
                
                # Cleanup expired entries periodically
                if frame_number % 100 == 0:
                    unknown_tracker.cleanup_expired()
                    known_tracker.cleanup_expired()
            else:
                # Non-processing frame: use cached detections for drawing only
                detections_list = cached_detections

            # Draw bounding boxes on EVERY frame (from cache) to prevent flickering
            for result in cached_results:
                x1, y1, x2, y2 = result.bbox
                
                # Filter out small faces (same as above)
                face_width = int(x2 - x1)
                face_height = int(y2 - y1)
                if face_width < config.MIN_FACE_SIZE or face_height < config.MIN_FACE_SIZE:
                    continue
                
                face_area = face_width * face_height
                
                if result.is_known:
                    # Draw green box for known person
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                    
                    # Display name and similarity
                    label = f"{result.person_name} ({result.similarity:.2f})"
                    cv2.putText(frame, label, (int(x1), int(y1)-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Display face size below bbox
                    size_label = f"Size: {face_width}x{face_height} ({face_area}px)"
                    cv2.putText(frame, size_label, (int(x1), int(y2)+20),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                else:
                    # Draw red box for unknown person
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 2)
                    
                    # Display "UNKNOWN" label
                    cv2.putText(frame, "UNKNOWN", (int(x1), int(y1)-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # Display face size below bbox
                    size_label = f"Size: {face_width}x{face_height} ({face_area}px)"
                    cv2.putText(frame, size_label, (int(x1), int(y2)+20),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            
            # Phase 3: Offload JPEG encoding to ThreadPool (CPU-bound)
            def encode_jpeg(frame_data):
                """CPU-bound JPEG encoding function"""
                ret, jpeg = cv2.imencode('.jpg', frame_data, [cv2.IMWRITE_JPEG_QUALITY, config.WS_FRAME_QUALITY])
                if ret:
                    return jpeg.tobytes()
                return None

            # Submit JPEG encoding to thread pool
            jpeg_future = asyncio.get_event_loop().run_in_executor(jpeg_executor, encode_jpeg, frame.copy())

            # Wait for encoding to complete (non-blocking for GPU work since it's in thread pool)
            frame_bytes = await jpeg_future

            if frame_bytes and len(frame_bytes) > 100:  # Validate JPEG data is reasonable size
                current_time = time.time()  # Get current timestamp for frame

                # Phase 4: Check if detections changed or send periodically (every 15 frames ~500ms at 30fps)
                detection_frame_counter += 1
                has_changed = detections_changed(cached_detections, last_sent_detections)
                should_send_detections = has_changed or (detection_frame_counter % 15 == 0)

                if should_send_detections:
                    last_sent_detections[:] = cached_detections.copy()  # Update last sent
                    detection_frame_counter = 0  # Reset counter

                # Create frame snapshot
                snapshot = FrameSnapshot(
                    frame_bytes=frame_bytes,
                    detections=cached_detections if should_send_detections else [],
                    timestamp=current_time,
                    frame_number=frame_number,
                    metrics={},  # Will be filled by metrics update
                    detections_changed=should_send_detections
                )

                # Update latest frame slot (atomic replacement - no async overhead!)
                latest_frame_store.set_frame(snapshot)
                logger.info(f"📤 Frame {frame_number} set as latest ({len(frame_bytes)} bytes, detections: {len(snapshot.detections)}), active clients: {len(streaming_tasks)}")
            else:
                logger.warning(f"⚠️ Invalid frame data for frame {frame_number}: {len(frame_bytes) if frame_bytes else 0} bytes")
            
            # Send metrics update periodically (now handled by streaming tasks)
            current_time = time.time()
            if current_time - last_metrics_time >= config.METRICS_UPDATE_INTERVAL:
                # Get current metrics for logging
                metrics = get_system_metrics()
                video_stats = metrics.get('video', {})
                logger.info(f"📊 FPS: {video_stats.get('processing_fps', 0):.1f} | "
                           f"GPU: {video_stats.get('utilization', 0)}% | "
                           f"Mem: {video_stats.get('memory_used', 0)}MB | "
                           f"Frames: {video_stats.get('processed_count', 0)}")
                last_metrics_time = current_time
            
            # Note: Frame timing is now controlled at the start of the loop to match video FPS
            # No additional sleep needed here
    
    except Exception as e:
        logger.error(f"Error in processing loop: {e}", exc_info=True)
    finally:
        is_processing = False
        logger.info("Video processing loop stopped")


async def stream_frames_task(websocket: WebSocket, client_id: str):
    """Per-client streaming task that reads latest frame and sends to client"""
    global latest_frame_store, streaming_tasks

    logger.info(f"🎬 Starting streaming task for client {client_id}")

    last_metrics_time = time.time()
    last_frame_number = -1  # Track last sent frame to avoid duplicates

    try:
        # Send initial test message to verify WebSocket connection
        test_message = {"type": "test", "message": f"Hello from server to client {client_id}"}
        await ws_manager.send_personal_message(test_message, websocket)
        logger.info(f"✅ Sent test message to client {client_id}")

        frame_check_count = 0
        while True:
            current_time = time.time()
            frame_check_count += 1

            # Debug log every 50 iterations
            if frame_check_count % 50 == 0:
                logger.info(f"🔄 Client {client_id} loop #{frame_check_count}, latest_frame is {'None' if latest_frame is None else f'Frame {latest_frame.frame_number}'}")

            # Send metrics update periodically (independent of frames)
            if current_time - last_metrics_time >= config.METRICS_UPDATE_INTERVAL:
                metrics = get_system_metrics()
                await ws_manager.send_metrics_to_client(websocket, metrics)
                last_metrics_time = current_time
                logger.info(f"📊 Sent metrics to client {client_id}")

            # Send latest frame if available and new
            latest_frame = latest_frame_store.get_frame()
            if latest_frame is not None and latest_frame.frame_number != last_frame_number:
                logger.info(f"🎥 Sending frame {latest_frame.frame_number} to client {client_id} ({len(latest_frame.frame_bytes)} bytes)")
                await ws_manager.send_frame_to_client(websocket, latest_frame.frame_bytes, latest_frame.detections)
                last_frame_number = latest_frame.frame_number
                logger.info(f"📤 Successfully sent frame {last_frame_number} to client {client_id} (detections: {len(latest_frame.detections)})")
            elif latest_frame is None:
                # Debug: Check if latest_frame becomes None after being set
                if frame_check_count % 50 == 0:  # Log less frequently
                    logger.info(f"⏳ Waiting for first frame for client {client_id} (check #{frame_check_count})")
            else:
                # Debug: Check if frame number is the same
                if frame_check_count % 100 == 0:  # Log less frequently
                    logger.debug(f"⏸️ Same frame {latest_frame.frame_number} for client {client_id} (check #{frame_check_count})")

            # Small delay to prevent busy waiting
            await asyncio.sleep(0.01)  # 10ms - still responsive but less CPU intensive

    except asyncio.CancelledError:
        logger.info(f"🛑 Streaming task cancelled for client {client_id}")
        raise
    except Exception as e:
        logger.error(f"Error in streaming task for client {client_id}: {e}")
    finally:
        # Clean up this client's streaming task
        streaming_tasks.pop(client_id, None)
        logger.info(f"🧹 Streaming task cleaned up for client {client_id}")


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
    """Health check endpoint (public)"""
    return {
        "status": "healthy",
        "face_recognizer": face_recognizer is not None,
        "unknown_tracker": unknown_tracker is not None,
        "video_processor": video_processor is not None,
        "processing": is_processing
    }


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login endpoint - authenticate user"""
    if request.username == config.ADMIN_USERNAME and request.password == config.ADMIN_PASSWORD:
        session_id = create_session(request.username)
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Login successful"
        }
    else:
        logger.warning(f"Failed login attempt for username: {request.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")


@app.post("/api/auth/logout")
async def logout(session_id: str = Depends(require_auth)):
    """Logout endpoint - invalidate session"""
    delete_session(session_id)
    return {"status": "success", "message": "Logged out successfully"}


@app.get("/api/auth/check")
async def check_auth(session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """Check if session is valid"""
    if validate_session(session_id):
        return {"authenticated": True, "username": sessions[session_id]["username"]}
    else:
        return {"authenticated": False}


@app.websocket("/api/stream")
async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
    """WebSocket endpoint for real-time video streaming"""
    global processing_task, streaming_tasks, is_processing

    # Authenticate WebSocket connection
    # Try to get session_id from query params first, then headers
    if not session_id:
        # Check query params
        query_params = dict(websocket.query_params)
        session_id = query_params.get("session_id")
    
    if not validate_session(session_id):
        logger.warning(f"WebSocket connection rejected: invalid or missing session")
        await websocket.close(code=1008, reason="Authentication required")
        return

    await ws_manager.connect(websocket)
    client_id = generate_client_id(websocket)

    try:
        # Note: Processing task will be started manually via play button
        # Do not start processing automatically on WebSocket connection
        
        # Start streaming task for this client (reader)
        # This will wait for frames once processing starts
        logger.info(f"🎬 Starting streaming task for client {client_id}")
        streaming_task = asyncio.create_task(stream_frames_task(websocket, client_id))
        streaming_tasks[client_id] = streaming_task

        # Keep connection alive (this will block until client disconnects)
        while True:
            data = await websocket.receive_text()
            # Handle any client messages if needed

    except WebSocketDisconnect:
        logger.info(f"👋 WebSocket disconnected for client {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
    finally:
        # Clean up this client's streaming task
        ws_manager.disconnect(websocket)
        if client_id in streaming_tasks:
            task = streaming_tasks[client_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            streaming_tasks.pop(client_id, None)


@app.get("/api/stats")
async def get_stats(session_id: str = Depends(require_auth)):
    """Get system statistics"""
    return get_system_metrics()


@app.get("/api/snapshots")
async def get_snapshots(session_id: str = Depends(require_auth)):
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
async def get_known_persons(session_id: str = Depends(require_auth)):
    """Get recently detected known persons"""
    return {"known_persons": list(known_persons_log)}


@app.post("/api/source")
async def set_video_source(request: VideoSourceRequest, session_id: str = Depends(require_auth)):
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
            # Restart processing task with new video source
            logger.info("🔄 Restarting processing task with new video source")
            latest_frame_store.frame = None  # Clear latest frame for new source
            logger.info("🟢 Creating new processing task...")
            processing_task = asyncio.create_task(process_frames_task())
            logger.info(f"✅ Processing task created: {processing_task}")
            return {"status": "success", "source": request.source_type}
        else:
            raise HTTPException(status_code=500, detail="Failed to open video source")
    
    except Exception as e:
        logger.error(f"Error changing video source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/control")
async def control_playback(request: ControlRequest, session_id: str = Depends(require_auth)):
    """Control video playback"""
    global is_processing, processing_task, video_processor, unknown_tracker, known_tracker, known_persons_log
    
    if not video_processor:
        raise HTTPException(status_code=400, detail="No video processor")
    
    if request.action == "play":
        # Reset system for fresh start
        logger.info("🔄 Resetting system for fresh detection...")
        
        # Clear snapshots folder
        try:
            import glob
            snapshot_files = glob.glob(os.path.join(config.SNAPSHOT_DIR, "*.jpg"))
            for file in snapshot_files:
                try:
                    os.remove(file)
                    logger.debug(f"Deleted snapshot: {os.path.basename(file)}")
                except Exception as e:
                    logger.warning(f"Failed to delete snapshot {file}: {e}")
            logger.info(f"✅ Cleared {len(snapshot_files)} snapshots")
        except Exception as e:
            logger.error(f"Error clearing snapshots: {e}")
        
        # Reset trackers
        if unknown_tracker:
            unknown_tracker.reset()
        if known_tracker:
            known_tracker.reset()
        
        # Clear known persons log
        known_persons_log.clear()
        logger.info("✅ Cleared known persons log")
        
        # Reset video to beginning
        if video_processor.source_type.value == "file":
            video_processor.seek(0)
        
        video_processor.resume()
        
        # Start processing if not already running
        if not is_processing and processing_task is None:
            logger.info("🚀 Starting processing task from play button")
            processing_task = asyncio.create_task(process_frames_task())
        elif processing_task and processing_task.done():
            # Restart if previous task completed
            logger.info("🔄 Restarting processing task")
            processing_task = asyncio.create_task(process_frames_task())
    elif request.action == "stop":
        # Stop processing completely
        logger.info("🛑 Stopping processing from stop button")
        is_processing = False
        if processing_task:
            processing_task.cancel()
            try:
                await processing_task
            except asyncio.CancelledError:
                pass
            processing_task = None
        # Reset video to beginning if file source
        if video_processor.source_type.value == "file":
            video_processor.seek(0)
    elif request.action == "pause":
        video_processor.pause()
    elif request.action == "toggle":
        video_processor.toggle_pause()
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return {
        "status": "success", 
        "action": request.action, 
        "is_paused": video_processor.is_paused,
        "is_processing": is_processing
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

