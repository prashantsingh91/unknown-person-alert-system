# Unknown Person Alert System

AI-powered facial recognition system with real-time unknown person detection and alerting. Built with FastAPI, React, and InsightFace.

## 🎯 Features

- **Real-time Face Recognition**: GPU-accelerated face detection and recognition
- **Unknown Person Detection**: Intelligent tracking and alerting for unknown individuals
- **False Alert Prevention**: 10-second grace period with relaxed threshold to handle temporary occlusions
- **Smart Deduplication**: Prevents duplicate alerts for the same person
- **High Performance**: 50-60 FPS with GPU acceleration (10x faster than CPU)
- **Modern UI**: React-based dashboard with live video feed, alerts, and metrics
- **Snapshot Gallery**: Automatic capture and storage of unknown person images
- **GPU Monitoring**: Real-time GPU utilization and performance metrics

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
- Place your face database at: `data/combined_face_database.pkl`
- Update `backend/config.py` with your video path and settings

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
SIMILARITY_THRESHOLD = 0.42  # Recognition threshold
GRACE_PERIOD = 10.0  # Grace period for occlusions (seconds)
MIN_FACE_SIZE = 60  # Minimum face size (60x60 pixels)

# Unknown Person Tracking
UNKNOWN_COOLDOWN_SECONDS = 300  # 5 minutes
UNKNOWN_SIMILARITY_THRESHOLD = 0.55
MIN_DETECTIONS_BEFORE_ALERT = 3

# Known Person Tracking
KNOWN_PERSON_COOLDOWN_SECONDS = 30

# Performance
FRAME_SKIP = 0  # Process every frame (GPU mode)
GPU_DEVICE_ID = 0
```

## 📊 Performance

| Metric | CPU Mode | GPU Mode |
|--------|----------|----------|
| FPS | 5-7 FPS | 50-60 FPS |
| GPU Usage | 0% | 12-20% |
| Detection Accuracy | High | High |
| Latency | ~200ms | ~20ms |

## 🔧 Technical Details

### Grace Period System
- Caches embeddings of recognized persons for 10 seconds
- Uses relaxed threshold (0.30) vs normal (0.42) during grace period
- Prevents false unknown alerts during temporary occlusions (hand movements, turning head)

### Face Size Filter
- Only processes faces ≥ 60x60 pixels
- Improves accuracy by ignoring distant/small faces
- Reduces false detections

### Unknown Person Tracking
- Requires 3 consecutive detections before alerting
- Uses embedding similarity (0.55 threshold) for same person detection
- 5-minute cooldown between alerts for same person
- Moving average of last 5 embeddings for robust matching

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
