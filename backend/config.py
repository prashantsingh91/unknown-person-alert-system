"""
Configuration for Unknown Person Alert System
"""
import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
AIIMS_ROOT = os.path.dirname(PROJECT_ROOT)

SNAPSHOT_DIR = os.path.join(PROJECT_ROOT, "snapshots")
DEFAULT_VIDEO_PATH = os.path.join(AIIMS_ROOT, "recorded_videos", "extracted_2min_to_4min_trimmed.mp4")

# Model selection (allows quick switching between buffalo_s and buffalo_l)
# Override with env var FACE_MODEL=buffalo_l to revert to previous model profile
FACE_MODEL_NAME = os.getenv("FACE_MODEL", "buffalo_l").strip()
print(f"Using FACE_MODEL_NAME: {FACE_MODEL_NAME}")

# Select database file based on model
if FACE_MODEL_NAME == "buffalo_s":
    FACE_DATABASE_PATH = os.path.join(PROJECT_ROOT, "data", "combined_face_database_buffalo_s.pkl")
else:
    FACE_DATABASE_PATH = os.path.join(PROJECT_ROOT, "data", "combined_face_database.pkl")
print(f"Using FACE_DATABASE_PATH: {FACE_DATABASE_PATH}")

# Apply model-specific tuning
if FACE_MODEL_NAME == "buffalo_s":
    # buffalo_s is faster but less precise -> tighten thresholds and filters
    SIMILARITY_THRESHOLD = 0.42
    UNKNOWN_SIMILARITY_THRESHOLD = 0.50
    TEMPORAL_WINDOW_SECONDS = 4.0
    SPATIAL_BOOST_SCORE = 0.15
    MIN_FACE_SIZE = 30  # Reduced to detect small faces
    DET_SIZE = (256, 256)  # CPU optimization: even smaller detector input for max speed
    DETECTION_CONFIDENCE_THRESHOLD = 0.80  # Higher threshold for fewer false detections

    # Hysteresis for known person continuity
    ENTER_THRESHOLD = 0.55  # Stricter threshold for initial recognition
    STAY_THRESHOLD = 0.45   # More lenient threshold to maintain recognition
    KNOWN_EMBEDDING_HISTORY = 3  # Keep last 3 embeddings for centroid smoothing
    USE_HYSTERESIS = True   # Enable hysteresis logic
else:
    # buffalo_l model defaults
    SIMILARITY_THRESHOLD = 0.42
    UNKNOWN_SIMILARITY_THRESHOLD = 0.50
    TEMPORAL_WINDOW_SECONDS = 5.0
    SPATIAL_BOOST_SCORE = 0.30
    MIN_FACE_SIZE = 40  # Reduced to detect small faces
    DET_SIZE = (640, 640)  # CPU optimization: smaller detector input for max speed
    DETECTION_CONFIDENCE_THRESHOLD = 0.60  # Higher threshold for fewer false detections

    # Hysteresis for known person continuity (buffalo_l)
    ENTER_THRESHOLD = 0.42  # Same as SIMILARITY_THRESHOLD for initial recognition
    STAY_THRESHOLD = 0.35   # More lenient threshold to maintain recognition
    KNOWN_EMBEDDING_HISTORY = 3  # Keep last 3 embeddings for centroid smoothing
    USE_HYSTERESIS = True   # Enable hysteresis logic

# Unknown Person Tracking
UNKNOWN_COOLDOWN_SECONDS = 300  # 5 minutes cooldown for same unknown person
MIN_DETECTIONS_BEFORE_ALERT = 3  # Alert immediately 
# Spatial-Temporal Tracking (Phase 2) - FIXED for actual deduplication
SPATIAL_IOU_THRESHOLD = 0.25  # Minimum IoU for spatial proximity matching

# Quick suppression and warmup settings (safe, reversible flags)
# When enabled, pre-alert suppression will merge into an existing UID if
# combined_score >= QUICK_SUPPRESSION_THRESHOLD.
QUICK_SUPPRESSION_ENABLED = True
QUICK_SUPPRESSION_THRESHOLD = 0.45

# Warmup before alerting (prevents alerts from very short/noisy appearances).
# When enabled, newly created UIDs will wait NEW_UID_WARMUP_WINDOW seconds
# before being eligible to alert even if MIN_DETECTIONS_BEFORE_ALERT is reached.
NEW_UID_WARMUP_ENABLED = True
NEW_UID_WARMUP_WINDOW = 0.6  # seconds

# Known Person Tracking (prevent spam)
KNOWN_PERSON_COOLDOWN_SECONDS = 180  # Don't show same known person again for 3 minutes

# Performance Settings
GPU_DEVICE_ID = 0  # Set to -1 for CPU mode, 0 for GPU mode
FRAME_SKIP = 1 # Base frame skip (dynamic skip will override based on faces/FPS)
TARGET_PROCESSING_FPS = 30.0  # Target FPS for dynamic frame skip (lower when FPS drops below this)
MAX_FACES_PER_FRAME = 6

# WebSocket Settings
WS_FRAME_QUALITY = 70  # JPEG quality for streaming
WS_UPDATE_INTERVAL = 0.020 # ~30 FPS max

# Metrics Settings
METRICS_UPDATE_INTERVAL = 1.0  # Update GPU/FPS metrics every second
MAX_KNOWN_PERSONS_LOG = 50  # Keep last 50 known person detections

# Authentication Settings
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")  # Login username
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")  # Login password - CHANGE THIS!
SESSION_EXPIRY_HOURS = 24  # Session expires after 24 hours

# Create directories
os.makedirs(SNAPSHOT_DIR, exist_ok=True)

