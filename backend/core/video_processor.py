"""
Video Processor with support for video files and camera feeds
Handles frame extraction, processing, and metrics tracking
"""
import cv2
import time
import numpy as np
from typing import Optional, Tuple, Dict
from enum import Enum
import logging
import threading
from collections import deque

try:
    import pynvml
    HAVE_PYNVML = True
except ImportError:
    HAVE_PYNVML = False
    logging.warning("pynvml not available, GPU metrics disabled")

logger = logging.getLogger(__name__)


class VideoSource(Enum):
    """Video source types"""
    FILE = "file"
    CAMERA = "camera"


class VideoProcessor:
    """Video processor with FPS and GPU monitoring"""
    
    def __init__(self, video_path: str = None, camera_id: int = 0, 
                 frame_skip: int = 2, target_width: int = 1280):
        """
        Initialize video processor
        
        Args:
            video_path: Path to video file (for FILE source)
            camera_id: Camera device ID (for CAMERA source)
            frame_skip: Process every Nth frame (0=all, 1=every 2nd, 2=every 3rd)
            target_width: Target frame width for processing
        """
        self.video_path = video_path
        self.camera_id = camera_id
        self.frame_skip = frame_skip
        self.target_width = target_width
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.source_type = VideoSource.FILE if video_path else VideoSource.CAMERA
        self.is_playing = False
        self.is_paused = False
        
        # FPS tracking
        self.frame_times = deque(maxlen=30)
        self.processing_times = deque(maxlen=30)
        self.current_fps = 0.0
        self.processing_fps = 0.0
        
        # Frame counting
        self.frame_count = 0
        self.processed_count = 0
        
        # GPU monitoring
        self.gpu_handle = None
        if HAVE_PYNVML:
            try:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                logger.info("GPU monitoring initialized")
            except Exception as e:
                logger.warning(f"Could not initialize GPU monitoring: {e}")
        
        # Video properties
        self.video_fps = 0
        self.total_frames = 0
        self.frame_width = 0
        self.frame_height = 0
        
    def open(self) -> bool:
        """Open video source"""
        try:
            if self.source_type == VideoSource.FILE:
                if not self.video_path:
                    logger.error("No video path specified")
                    return False
                self.cap = cv2.VideoCapture(self.video_path)
                logger.info(f"Opened video file: {self.video_path}")
            else:
                self.cap = cv2.VideoCapture(self.camera_id)
                logger.info(f"Opened camera: {self.camera_id}")
            
            if not self.cap.isOpened():
                logger.error("Failed to open video source")
                return False
            
            # Get video properties
            self.video_fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Video properties: {self.frame_width}x{self.frame_height} @ {self.video_fps} FPS")
            if self.source_type == VideoSource.FILE:
                logger.info(f"Total frames: {self.total_frames}")
            
            self.is_playing = True
            return True
            
        except Exception as e:
            logger.error(f"Error opening video source: {e}")
            return False
    
    def close(self):
        """Close video source"""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_playing = False
        logger.info("Video source closed")
    
    def read_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read next frame from video source
        
        Returns:
            Tuple of (success, frame)
        """
        if not self.cap or not self.is_playing or self.is_paused:
            return False, None
        
        frame_time_start = time.time()
        
        ret, frame = self.cap.read()
        
        if not ret:
            # End of video or error
            if self.source_type == VideoSource.FILE:
                logger.info("End of video reached (will be reset to True when seek(0) is called)")
                # Don't loop automatically - return False to signal end
                # Note: is_playing is set to False here, but will be reset to True
                # when seek(0) is called in control_playback (play action)
                self.is_playing = False
                return False, None
            else:
                logger.error("Failed to read camera frame")
                return False, None
        
        self.frame_count += 1
        
        # Resize if needed
        if frame is not None and frame.shape[1] != self.target_width:
            aspect_ratio = frame.shape[0] / frame.shape[1]
            target_height = int(self.target_width * aspect_ratio)
            frame = cv2.resize(frame, (self.target_width, target_height))
        
        # Update FPS
        frame_time_end = time.time()
        self.frame_times.append(frame_time_end - frame_time_start)
        
        if len(self.frame_times) > 1:
            self.current_fps = len(self.frame_times) / sum(self.frame_times)
        
        return ret, frame
    
    def set_dynamic_skip(self, faces_present: bool, target_fps: float = 12.0):
        """Dynamic frame skip: lower skip when faces present or FPS too low"""
        if faces_present or self.processing_fps < target_fps:
            # When faces present or FPS low, process more frames (skip 0-1)
            self.dynamic_skip = min(1, self.frame_skip)  # Don't skip more than 1 frame
        else:
            # When scene empty and FPS good, skip more (3-4 frames)
            self.dynamic_skip = max(3, self.frame_skip)  # Skip at least 3 frames
            self.dynamic_skip = min(4, self.dynamic_skip)  # Don't skip more than 4 frames

    def should_process_frame(self) -> bool:
        """Check if current frame should be processed (based on dynamic frame skip)"""
        # Use dynamic_skip if set, otherwise fall back to static frame_skip
        skip_count = getattr(self, 'dynamic_skip', self.frame_skip)
        return self.frame_count % (skip_count + 1) == 0
    
    def mark_processed(self, processing_time: float):
        """Mark frame as processed and update metrics"""
        self.processed_count += 1
        self.processing_times.append(processing_time)
        
        if len(self.processing_times) > 1:
            self.processing_fps = len(self.processing_times) / sum(self.processing_times)
    
    def get_gpu_metrics(self) -> Dict:
        """Get GPU utilization metrics"""
        metrics = {
            'gpu_available': False,
            'utilization': 0,
            'memory_used': 0,
            'memory_total': 0,
            'memory_percent': 0,
            'temperature': 0
        }
        
        if not self.gpu_handle:
            return metrics
        
        try:
            # GPU utilization
            util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            metrics['utilization'] = util.gpu
            
            # Memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            metrics['memory_used'] = mem_info.used // (1024 * 1024)  # MB
            metrics['memory_total'] = mem_info.total // (1024 * 1024)  # MB
            metrics['memory_percent'] = (mem_info.used / mem_info.total) * 100
            
            # Temperature
            temp = pynvml.nvmlDeviceGetTemperature(self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU)
            metrics['temperature'] = temp
            
            metrics['gpu_available'] = True
            
        except Exception as e:
            logger.debug(f"Error reading GPU metrics: {e}")
        
        return metrics
    
    def get_stats(self) -> Dict:
        """Get processor statistics"""
        gpu_metrics = self.get_gpu_metrics()
        
        progress = 0.0
        if self.source_type == VideoSource.FILE and self.total_frames > 0:
            progress = (self.frame_count / self.total_frames) * 100
        
        return {
            'source_type': self.source_type.value,
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'frame_count': self.frame_count,
            'processed_count': self.processed_count,
            'current_fps': round(self.current_fps, 1),
            'processing_fps': round(self.processing_fps, 1),
            'video_fps': round(self.video_fps, 1),
            'progress': round(progress, 1),
            'resolution': f"{self.frame_width}x{self.frame_height}",
            **gpu_metrics
        }
    
    def pause(self):
        """Pause video playback"""
        self.is_paused = True
        logger.info("Video paused")
    
    def resume(self):
        """Resume video playback"""
        if not self.cap:
            logger.warning("Cannot resume: video source not opened")
            return
        
        self.is_paused = False
        self.is_playing = True  # Ensure video is marked as playing
        logger.info(f"Video resumed (is_playing={self.is_playing}, is_paused={self.is_paused})")
    
    def toggle_pause(self):
        """Toggle pause state"""
        self.is_paused = not self.is_paused
        logger.info(f"Video {'paused' if self.is_paused else 'resumed'}")
    
    def seek(self, frame_number: int) -> bool:
        """Seek to specific frame (file only)"""
        if self.source_type != VideoSource.FILE or not self.cap:
            return False
        
        try:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.frame_count = frame_number
            # Ensure video is marked as playing after seek (important for restarting after video ends)
            self.is_playing = True
            self.is_paused = False
            logger.info(f"Seeked to frame {frame_number}, is_playing set to True")
            return True
        except Exception as e:
            logger.error(f"Error seeking: {e}")
            return False
    
    def __del__(self):
        """Cleanup"""
        self.close()
        if HAVE_PYNVML and self.gpu_handle:
            try:
                pynvml.nvmlShutdown()
            except:
                pass

