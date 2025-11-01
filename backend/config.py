"""
Configuration for Unknown Person Alert System
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
AIIMS_ROOT = os.path.dirname(PROJECT_ROOT)

FACE_DATABASE_PATH = os.path.join(AIIMS_ROOT, "data", "combined_face_database.pkl")
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "snapshots")
DEFAULT_VIDEO_PATH = os.path.join(AIIMS_ROOT, "recorded_videos", "extracted_2min_to_4min_trimmed.mp4")

# Face Recognition Settings
SIMILARITY_THRESHOLD = 0.42  # Cosine similarity threshold for face matching
MIN_FACE_SIZE = 30  # Minimum face size in pixels
DET_SIZE = (640, 640)  # Detection input size

# Unknown Person Tracking
UNKNOWN_COOLDOWN_SECONDS = 300  # 5 minutes cooldown for same unknown person
UNKNOWN_SIMILARITY_THRESHOLD = 0.55  # More aggressive similarity = same unknown person (Phase 1 improvement)
MIN_DETECTIONS_BEFORE_ALERT = 3  # Require 3 detections before alerting (wait 2-3 seconds)

# Known Person Tracking (prevent spam)
KNOWN_PERSON_COOLDOWN_SECONDS = 30  # Don't show same known person again for 30 seconds

# Performance Settings
GPU_DEVICE_ID = 0
FRAME_SKIP = 0  # Process every frame (0=all, 1=every 2nd, 2=every 3rd) - GPU accelerated
MAX_FACES_PER_FRAME = 10
MIN_FACE_SIZE = 30  # Minimum face size in pixels for detection

# WebSocket Settings
WS_FRAME_QUALITY = 85  # JPEG quality for streaming
WS_UPDATE_INTERVAL = 0.033  # ~30 FPS max

# Metrics Settings
METRICS_UPDATE_INTERVAL = 1.0  # Update GPU/FPS metrics every second
MAX_KNOWN_PERSONS_LOG = 50  # Keep last 50 known person detections

# Create directories
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

