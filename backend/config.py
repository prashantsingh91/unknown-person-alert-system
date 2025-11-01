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
DET_SIZE = (480, 480)  # Detection input size (Phase 1 optimization: 640→480 for +20-30% FPS)

# Unknown Person Tracking
UNKNOWN_COOLDOWN_SECONDS = 300  # 5 minutes cooldown for same unknown person
UNKNOWN_SIMILARITY_THRESHOLD = 0.50  # Optimal: Balanced threshold for spatial-temporal to work
MIN_DETECTIONS_BEFORE_ALERT = 1  # Alert immediately (Phase 2 spatial-temporal prevents duplicates)

# Spatial-Temporal Tracking (Phase 2) - FIXED for actual deduplication
SPATIAL_IOU_THRESHOLD = 0.3  # Minimum IoU for spatial proximity matching
TEMPORAL_WINDOW_SECONDS = 3.0  # Time window for spatial-temporal matching (Phase 1: 2.0→3.0 for frame skip)
SPATIAL_BOOST_SCORE = 0.20  # Boost applied when spatial-temporal criteria met (increased from 0.15)

# Known Person Tracking (prevent spam)
KNOWN_PERSON_COOLDOWN_SECONDS = 30  # Don't show same known person again for 30 seconds

# Performance Settings
GPU_DEVICE_ID = 0
FRAME_SKIP = 1  # Phase 1 optimization: Process every 2nd frame for 2x throughput (0=all, 1=every 2nd, 2=every 3rd)
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

