# Unknown Person Alert System

AI-powered facial recognition system with real-time unknown person detection and alerting. Built with FastAPI, React, and InsightFace.

## 🎯 Features

### Core Functionality
- **Real-time Face Recognition**: GPU-accelerated face detection and recognition using InsightFace
- **Unknown Person Detection**: Intelligent tracking and alerting for unknown individuals
- **Smart Face Filtering**: Minimum 60x60 pixel face size filter for accuracy
- **False Alert Prevention**: 10-second grace period with relaxed threshold (0.30) to handle temporary occlusions
- **Smart Deduplication**: Prevents duplicate alerts for both known and unknown persons
- **High Performance**: 50-60 FPS with GPU acceleration (10x faster than CPU)

### User Interface
- **Modern Dashboard**: React-based UI with TailwindCSS styling
- **Live Video Feed**: Real-time video streaming with face detection overlays
- **Alert Panel**: Instant unknown person alerts with snapshots
- **Snapshot Gallery**: Searchable gallery with image preview and download
- **Metrics Dashboard**: FPS, GPU usage, memory, and system statistics
- **Known Persons Log**: Detection history with 30-second deduplication

### Performance & Monitoring
- **GPU Monitoring**: Real-time NVIDIA GPU utilization and memory tracking
- **Performance Metrics**: Live FPS counter and frame processing statistics
- **WebSocket Streaming**: Low-latency bi-directional communication

## 🏗️ Architecture

### Backend (FastAPI + Python)
- **Face Recognition**: InsightFace with GPU acceleration
- **Video Processing**: OpenCV with frame skipping
- **WebSocket**: Real-time streaming and bi-directional communication
- **Tracking Systems**:
  - Unknown Person Tracker (5-minute cooldown, embedding similarity)
  - Known Person Tracker (30-second cooldown)
  - Grace Period System (10-second tolerance for occlusions)

### Frontend (React + TailwindCSS)
- **Video Player**: Live video feed with face detection overlays
- **Alert Panel**: Real-time unknown person alerts with snapshots
- **Snapshot Gallery**: Searchable gallery with image preview
- **Metrics Dashboard**: FPS, GPU usage, and system statistics
- **Known Persons Log**: Detection history for known individuals

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 16+
- NVIDIA GPU (optional but recommended)
- CUDA 11+ (for GPU acceleration)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/prashantsingh91/unknown-person-alert-system.git
cd unknown-person-alert-system
```

2. **Setup Backend**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Setup Frontend**
```bash
cd ../frontend
npm install
```

4. **Configure**

**Face Database:**
- A sample face database is included: `data/combined_face_database.pkl`
- Contains face embeddings registered using InsightFace
- **For production**: Replace with your own face database
- **Format**: Pickle file with structure: `{person_id: {'name': str, 'embeddings': [np.ndarray]}}`

**Settings:**
- Update `backend/config.py` with your video path and settings
- Configure GPU device, thresholds, cooldown periods, etc.

### Running with GPU

**Backend:**
```bash
cd backend
source venv/bin/activate
python start_uvicorn_gpu.py
```

**Frontend:**
```bash
cd frontend
npm start
```

Access at: `http://localhost:3000`

## ⚙️ Configuration

### Key Settings (backend/config.py)

```python
# Face Recognition
SIMILARITY_THRESHOLD = 0.42          # Normal recognition threshold
GRACE_PERIOD = 10.0                  # Grace period for occlusions (10 seconds)
GRACE_PERIOD_THRESHOLD = 0.30        # Relaxed threshold during grace period
MIN_FACE_SIZE = 60                   # Minimum face size (60x60 pixels)

# Unknown Person Tracking
UNKNOWN_COOLDOWN_SECONDS = 300       # 5 minutes cooldown between alerts
UNKNOWN_SIMILARITY_THRESHOLD = 0.50  # Embedding similarity threshold (Phase 3 optimized)
MIN_DETECTIONS_BEFORE_ALERT = 1      # Alert immediately (Phase 2 prevents duplicates)
MAX_EMBEDDING_HISTORY = 5            # Keep last 5 embeddings for averaging

# Spatial-Temporal Tracking (Phase 2 & 3 - Anti-Duplicate)
SPATIAL_IOU_THRESHOLD = 0.3          # Minimum IoU for spatial proximity matching
TEMPORAL_WINDOW_SECONDS = 2.0        # Time window for spatial-temporal matching
SPATIAL_BOOST_SCORE = 0.20           # Score boost when spatial-temporal criteria met

# Known Person Tracking
KNOWN_PERSON_COOLDOWN_SECONDS = 30   # 30 seconds cooldown for display

# Performance
FRAME_SKIP = 0                       # Process every frame (0=all, GPU mode)
GPU_DEVICE_ID = 0                    # NVIDIA GPU device ID
DET_SIZE = (640, 640)                # Face detection input size
```

## 📊 Performance

| Metric | CPU Mode | GPU Mode |
|--------|----------|----------|
| FPS | 5-7 FPS | 50-60 FPS |
| GPU Usage | 0% | 12-20% |
| Detection Accuracy | High | High |
| Latency | ~200ms | ~20ms |

## 🔧 Technical Details

### Grace Period System (Anti-False Alert)
**Problem Solved:** Known persons being marked as unknown during temporary occlusions (hand on mouth, turning head, poor lighting)

**Solution:**
- Maintains a cache of recently recognized persons (10 seconds)
- Two-tier recognition threshold:
  - **Normal:** 0.42 similarity for initial recognition
  - **Grace Period:** 0.30 similarity for cached persons
- If a face matches a cached person with 0.30+ similarity within 10 seconds, it's recognized
- Prevents false "unknown" alerts while maintaining security

**Example Flow:**
1. Person recognized with 0.45 similarity → Added to cache
2. Person covers mouth, similarity drops to 0.35
3. System checks cache, finds match at 0.35 (above 0.30 threshold)
4. Person still recognized (no false unknown alert)
5. After 10 seconds, cache expires and normal threshold applies

### Face Size Filter (Quality Control)
- **Minimum size:** 60x60 pixels (width × height)
- **Benefits:**
  - Improves recognition accuracy
  - Reduces false positives from distant/small faces
  - Better embedding quality from larger faces
  - Lower computational overhead
- Faces smaller than threshold are detected but not processed

### Unknown Person Tracking (Smart Deduplication)

**Phase 3 Optimized System** - Advanced spatial-temporal deduplication with immediate alerts

**How It Works:**
1. **Initial Detection:** Face detected but not in database → Create tracking entry
2. **Immediate Alert:** Alert triggered on first detection (MIN_DETECTIONS = 1)
3. **Spatial-Temporal Matching:** Track same person using multi-factor approach:
   - **Embedding Similarity:** Base threshold 0.50
   - **Spatial Proximity:** IoU (Intersection over Union) ≥ 0.3
   - **Temporal Window:** Within 2 seconds
   - **Smart Boost:** +0.20 score bonus when spatial-temporal criteria met
4. **Snapshot:** One snapshot per unique unknown person
5. **Cooldown:** 5-minute cooldown to prevent re-alerts

**Embedding Averaging:**
- Maintains last 5 embeddings per tracked person
- Uses moving average for robust matching
- Handles pose variations and lighting changes

**Spatial-Temporal Deduplication (Phase 2 & 3):**

**Problem Solved:**
Face embeddings from the same person naturally vary by 0.05-0.15 across consecutive frames due to:
- Slight head movements and pose changes
- Lighting variations
- Expression changes
- InsightFace embedding extraction variance

Pure embedding-based matching would create duplicate unknown IDs for the same person.

**Algorithm Overview:**

The spatial-temporal algorithm combines three factors to identify if a detection matches an existing tracked person:

```
1. Embedding Similarity (S): Cosine similarity between face embeddings
2. Spatial Proximity (IoU): Intersection over Union of bounding boxes
3. Temporal Proximity (T): Time difference between detections

Final Score = S + Boost (if spatial-temporal criteria met)
Match if: Final Score >= UNKNOWN_SIMILARITY_THRESHOLD (0.50)
```

**Detailed Algorithm Steps:**

**Step 1: Embedding Similarity Calculation**
```python
# Cosine similarity between current face and tracked person
similarity = dot(embedding_current, embedding_tracked) / 
             (norm(embedding_current) * norm(embedding_tracked))
# Range: [-1.0, 1.0], typically [0.3, 0.95] for same person
```

**Step 2: Spatial Proximity (IoU Calculation)**
```python
# Intersection over Union for bounding boxes
# bbox format: [x1, y1, x2, y2]

def compute_iou(bbox1, bbox2):
    # Find intersection rectangle
    x1_inter = max(bbox1[0], bbox2[0])
    y1_inter = max(bbox1[1], bbox2[1])
    x2_inter = min(bbox1[2], bbox2[2])
    y2_inter = min(bbox1[3], bbox2[3])
    
    # Calculate areas
    intersection = (x2_inter - x1_inter) * (y2_inter - y1_inter)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection
    
    return intersection / union

# Range: [0.0, 1.0]
# 0.0 = no overlap, 1.0 = perfect overlap
```

**Step 3: Temporal Proximity Check**
```python
time_diff = current_time - person.last_seen
# Check if within temporal window (2 seconds by default)
```

**Step 4: Spatial-Temporal Boost Application**
```python
spatial_temporal_boost = 0.0

if person.bbox is not None:
    time_diff = current_time - person.last_seen
    
    # Only apply boost if within temporal window
    if time_diff <= TEMPORAL_WINDOW_SECONDS (2.0s):
        iou = compute_iou(bbox_current, person.bbox)
        
        # Only apply boost if spatially close
        if iou >= SPATIAL_IOU_THRESHOLD (0.3):
            spatial_temporal_boost = SPATIAL_BOOST_SCORE (0.20)

final_score = similarity + spatial_temporal_boost
```

**Step 5: Matching Decision**
```python
if final_score >= UNKNOWN_SIMILARITY_THRESHOLD (0.50):
    # Match found! Same person
    # Update tracking, NO new alert
else:
    # No match, create new unknown person
    # Trigger alert + snapshot
```

**Visual Example:**

```
Frame t=0.00s:
┌─────────────────────────────────┐
│  Person appears                 │
│  ┌──────┐                       │
│  │Face 1│  (200, 150, 280, 230) │
│  └──────┘                       │
│  Similarity: N/A (new)          │
│  → Alert + Snapshot             │
│  → Track as UNKNOWN_0001        │
└─────────────────────────────────┘

Frame t=0.10s:
┌─────────────────────────────────┐
│  Person moved slightly          │
│     ┌──────┐                    │
│     │Face 1│ (205, 152, 285, 232)│
│     └──────┘                    │
│  Similarity: 0.38 (low!)        │
│  IoU: 0.93 (high overlap!)      │
│  Time: 0.10s (within 2s)        │
│  → Boost: +0.20                 │
│  → Final: 0.38 + 0.20 = 0.58 ✓  │
│  → Matched to UNKNOWN_0001      │
│  → NO new alert                 │
└─────────────────────────────────┘

Frame t=3.50s:
┌─────────────────────────────────┐
│  Person moved far               │
│                    ┌──────┐     │
│                    │Face 1│     │
│                    └──────┘     │
│  Similarity: 0.42               │
│  IoU: 0.05 (low overlap)        │
│  Time: 3.40s (outside 2s)       │
│  → Boost: 0.0 (no boost)        │
│  → Final: 0.42 (< 0.50) ✗       │
│  → Would create new unknown     │
│  BUT: Cooldown active (5 min)   │
└─────────────────────────────────┘
```

**Why It Works:**

1. **Handles Embedding Variance:** Even if similarity drops to 0.35-0.45, spatial context confirms it's the same person
2. **Position Continuity:** Same person can't teleport; must be near previous position
3. **Temporal Locality:** Recent detections more likely to be same person
4. **Adaptive Threshold:** Effectively lowers threshold to 0.30 (0.50 - 0.20) for nearby detections

**Performance Impact:**
- **Before Phase 3:** 13 duplicate snapshots, 0 spatial-temporal matches
- **After Phase 3:** 4-6 snapshots, 130+ spatial-temporal matches
- **Reduction:** 69% fewer duplicates

**Key Parameters:**
- `UNKNOWN_SIMILARITY_THRESHOLD = 0.50`: Base threshold (balanced for boost)
- `SPATIAL_BOOST_SCORE = 0.20`: Bonus score for nearby detections
- `SPATIAL_IOU_THRESHOLD = 0.3`: Minimum overlap (30% box overlap)
- `TEMPORAL_WINDOW_SECONDS = 2.0`: Time window for spatial matching

## 🛠️ Development

### Project Structure
```
.
├── backend/
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Configuration
│   ├── start_uvicorn_gpu.py         # GPU-enabled startup script
│   ├── core/
│   │   ├── face_recognizer.py       # Face recognition engine
│   │   ├── unknown_tracker.py       # Unknown person tracking
│   │   ├── known_tracker.py         # Known person deduplication
│   │   └── video_processor.py       # Video processing
│   └── websocket/
│       └── manager.py               # WebSocket manager
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Main app component
│   │   ├── components/              # React components
│   │   └── services/
│   │       └── api.js               # API service
│   └── public/
└── snapshots/                       # Unknown person snapshots
```

## 🗄️ Face Database

### Included Sample Database
The repository includes a sample face database (`data/combined_face_database.pkl`) for testing purposes.

**⚠️ IMPORTANT:** This database contains biometric data. For production use:
- Replace with your own database
- Keep it private and secure
- Comply with privacy regulations (GDPR, etc.)
- Never commit real personal data to public repositories

### Creating Your Own Database
```python
import pickle
import numpy as np
from insightface.app import FaceAnalysis

# Initialize InsightFace
app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider'])
app.prepare(ctx_id=0, det_size=(640, 640))

# Create database
face_database = {}

# Register a person
person_id = "person_001"
person_name = "John Doe"
image_path = "path/to/person_photo.jpg"

# Extract embedding
img = cv2.imread(image_path)
faces = app.get(img)
if faces:
    embedding = faces[0].embedding
    face_database[person_id] = {
        'name': person_name,
        'embeddings': [embedding]
    }

# Save database
with open('data/combined_face_database.pkl', 'wb') as f:
    pickle.dump(face_database, f)
```

### Database Structure
```python
{
    'person_001': {
        'name': 'John Doe',
        'embeddings': [np.ndarray(512,), np.ndarray(512,), ...]  # Multiple embeddings per person
    },
    'person_002': {
        'name': 'Jane Smith',
        'embeddings': [np.ndarray(512,), ...]
    }
}
```

**Tips:**
- Register multiple photos per person (different angles, lighting)
- Use high-quality, well-lit photos
- Face should be clearly visible and at least 112x112 pixels
- More embeddings = better recognition accuracy

## 📝 API Endpoints

- `GET /api/health` - Health check
- `GET /api/stats` - System metrics
- `GET /api/snapshots` - List snapshots
- `GET /api/known-persons` - Known persons log
- `WS /api/stream` - WebSocket video stream

## 🐛 Troubleshooting

### GPU Not Working
- Ensure CUDA libraries are installed
- Check `nvidia-smi` output
- Verify ONNX Runtime GPU version: `pip list | grep onnxruntime`
- Start with `python start_uvicorn_gpu.py` (sets LD_LIBRARY_PATH)

### Low FPS
- Enable GPU acceleration
- Increase `FRAME_SKIP` in config
- Reduce video resolution
- Check GPU memory usage

### False Alerts (Known Persons Marked as Unknown)
- **Solution:** Increase `GRACE_PERIOD` duration (default: 10 seconds)
- **Solution:** Lower `GRACE_PERIOD_THRESHOLD` (default: 0.30)
- **Solution:** Increase `MIN_FACE_SIZE` to ignore poor quality detections

### Duplicate Unknown Alerts (Same Person, Multiple Snapshots)
**Phase 3 Configuration (Optimized):**
- `UNKNOWN_SIMILARITY_THRESHOLD = 0.50` - Balanced threshold
- `SPATIAL_BOOST_SCORE = 0.20` - Strong spatial-temporal boost
- `SPATIAL_IOU_THRESHOLD = 0.3` - Spatial proximity sensitivity
- `TEMPORAL_WINDOW_SECONDS = 2.0` - Time window for matching

**If still getting duplicates:**
1. **Increase spatial boost:** `SPATIAL_BOOST_SCORE = 0.25`
2. **Lower similarity threshold:** `UNKNOWN_SIMILARITY_THRESHOLD = 0.45`
3. **Widen temporal window:** `TEMPORAL_WINDOW_SECONDS = 3.0`
4. **Lower IoU threshold:** `SPATIAL_IOU_THRESHOLD = 0.25`

**If merging different people:**
1. **Raise similarity threshold:** `UNKNOWN_SIMILARITY_THRESHOLD = 0.55`
2. **Lower spatial boost:** `SPATIAL_BOOST_SCORE = 0.15`
3. **Increase IoU threshold:** `SPATIAL_IOU_THRESHOLD = 0.4`

**Monitor effectiveness:**
```bash
# Watch spatial-temporal matching in action
tail -f backend/backend.log | grep -E '(🎯|✅ Matched)'

# Count unique unknowns vs snapshots (should be equal)
grep "New unknown person tracking started" backend/backend.log | wc -l
ls snapshots/ | wc -l
```

## 📄 License

MIT License

## 👤 Author

**Prashant Singh**
- GitHub: [@prashantsingh91](https://github.com/prashantsingh91)

## 🙏 Acknowledgments

- InsightFace for face recognition models
- FastAPI for the backend framework
- React and TailwindCSS for the frontend

---

**Note**: This system is for educational and research purposes. Ensure compliance with privacy laws and regulations when deploying in production.
