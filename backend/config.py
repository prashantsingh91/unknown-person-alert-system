"""
Configuration for Unknown Person Alert System
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
AIIMS_ROOT = os.path.dirname(PROJECT_ROOT)

FACE_DATABASE_PATH = os.path.join(AIIMS_ROOT, "data", "face_database_buffalo_s.pkl")
SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "snapshots")
DEFAULT_VIDEO_PATH = os.path.join(AIIMS_ROOT, "recorded_videos", "extracted_2min_to_4min_trimmed.mp4")

# Model selection (allows quick switching between buffalo_s and buffalo_l)
# Override with env var FACE_MODEL=buffalo_l to revert to previous model profile
FACE_MODEL_NAME = os.getenv("FACE_MODEL", "buffalo_s").strip()

# Base defaults (will be overridden per model profile below)
SIMILARITY_THRESHOLD = 0.42
UNKNOWN_SIMILARITY_THRESHOLD = 0.50
TEMPORAL_WINDOW_SECONDS = 3.0
SPATIAL_BOOST_SCORE = 0.20
MIN_FACE_SIZE = 60
DET_SIZE = (640, 640)
DETECTION_CONFIDENCE_THRESHOLD = 0.60  # Filter low-confidence detections from detector

# Known person recognition tuning (new hysteresis + centroid features)
ENTER_THRESHOLD = SIMILARITY_THRESHOLD  # Default: same as single threshold
STAY_THRESHOLD = SIMILARITY_THRESHOLD   # Default: same as single threshold
KNOWN_EMBEDDING_HISTORY = 1            # Default: no centroid (single embedding)
USE_HYSTERESIS = False                 # Default: single threshold mode

# Apply model-specific tuning
if FACE_MODEL_NAME == "buffalo_s":
    # buffalo_s is faster but less precise -> tighten thresholds and filters
    SIMILARITY_THRESHOLD = 0.50
    UNKNOWN_SIMILARITY_THRESHOLD = 0.50
    TEMPORAL_WINDOW_SECONDS = 4.0
    SPATIAL_BOOST_SCORE = 0.15
    MIN_FACE_SIZE = 70
    DET_SIZE = (480, 480)
    DETECTION_CONFIDENCE_THRESHOLD = 0.70

    # NEW: Hysteresis for known person continuity
    ENTER_THRESHOLD = 0.55  # Stricter threshold for initial recognition
    STAY_THRESHOLD = 0.45   # More lenient threshold to maintain recognition
    KNOWN_EMBEDDING_HISTORY = 3  # Keep last 3 embeddings for centroid smoothing
    USE_HYSTERESIS = True   # Enable hysteresis logic
else:
    # buffalo_l (previous model) defaults - keep original single threshold behavior
    SIMILARITY_THRESHOLD = 0.42
    UNKNOWN_SIMILARITY_THRESHOLD = 0.50
    TEMPORAL_WINDOW_SECONDS = 3.0
    SPATIAL_BOOST_SCORE = 0.20
    MIN_FACE_SIZE = 60
    DET_SIZE = (640, 640)
    DETECTION_CONFIDENCE_THRESHOLD = 0.60

    # Keep single threshold behavior for buffalo_l
    ENTER_THRESHOLD = SIMILARITY_THRESHOLD
    STAY_THRESHOLD = SIMILARITY_THRESHOLD
    KNOWN_EMBEDDING_HISTORY = 1  # Single embedding (no centroid)
    USE_HYSTERESIS = False  # Disable hysteresis

# Unknown Person Tracking
UNKNOWN_COOLDOWN_SECONDS = 300  # 5 minutes cooldown for same unknown person
MIN_DETECTIONS_BEFORE_ALERT = 1  # Alert immediately (Phase 2 spatial-temporal prevents duplicates)

# Spatial-Temporal Tracking (Phase 2) - FIXED for actual deduplication
SPATIAL_IOU_THRESHOLD = 0.3  # Minimum IoU for spatial proximity matching

# Known Person Tracking (prevent spam)
KNOWN_PERSON_COOLDOWN_SECONDS = 30  # Don't show same known person again for 30 seconds

# Performance Settings
GPU_DEVICE_ID = 0
FRAME_SKIP = 1  # Phase 1 optimization: Process every 2nd frame for 2x throughput (0=all, 1=every 2nd, 2=every 3rd)
MAX_FACES_PER_FRAME = 10

# WebSocket Settings
WS_FRAME_QUALITY = 85  # JPEG quality for streaming
WS_UPDATE_INTERVAL = 0.020 # ~30 FPS max

# Metrics Settings
METRICS_UPDATE_INTERVAL = 1.0  # Update GPU/FPS metrics every second
MAX_KNOWN_PERSONS_LOG = 50  # Keep last 50 known person detections

# Create directories
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

