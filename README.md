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
UNKNOWN_SIMILARITY_THRESHOLD = 0.55  # Embedding similarity for same person
MIN_DETECTIONS_BEFORE_ALERT = 3      # Require 3 detections before alerting
MAX_EMBEDDING_HISTORY = 5            # Keep last 5 embeddings for averaging

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
**Multi-stage detection:**
1. **Initial Detection:** Face detected but not in database
2. **Tracking:** Track same person across frames using embedding similarity (0.55 threshold)
3. **Confirmation:** Require 3 detections (2-3 seconds) before alerting
4. **Alert:** Generate alert with snapshot
5. **Cooldown:** 5-minute cooldown to prevent duplicate alerts

**Embedding Averaging:**
- Maintains last 5 embeddings per tracked person
- Uses moving average for robust matching
- Handles pose variations and lighting changes

**Similarity Threshold:** 0.55 cosine similarity to identify same unknown person

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

### False Alerts
- Increase `MIN_DETECTIONS_BEFORE_ALERT`
- Adjust `UNKNOWN_SIMILARITY_THRESHOLD`
- Increase `GRACE_PERIOD` duration

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
