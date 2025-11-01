# Unknown Person Alert System - Project Summary

## ✅ Project Status: COMPLETE

**Date Created:** November 1, 2025  
**Project Location:** `/home/psingh/medgemma/aiims-attendance/face-alert-app/`  
**Virtual Environment:** `medgemma_env`

---

## 📋 Project Overview

A modern, real-time facial recognition system designed to detect and alert on unknown persons while logging known individuals. Built with FastAPI + React, using InsightFace for accurate face recognition.

### Key Features Implemented

✅ **Real-time Face Recognition**
- InsightFace buffalo_l model (RetinaFace + ArcFace)
- GPU-accelerated processing
- Cosine similarity matching (threshold: 0.42)

✅ **Unknown Person Alert System**
- Automatic detection and alerting
- 5-minute cooldown to prevent duplicates
- Embedding-based duplicate detection
- Automatic snapshot capture

✅ **Known Person Logging**
- Real-time detection tracking
- Person ID and name display
- Match confidence scores
- Timestamp logging

✅ **Modern Web Interface**
- Real-time video streaming via WebSocket
- Interactive dashboard with multiple views
- GPU and performance metrics
- Snapshot gallery with search
- Playback controls

✅ **Dual Video Source Support**
- Video file playback (with loop)
- Live camera feed support
- Easy source switching

---

## 🏗️ Architecture

### Backend (FastAPI)

**Core Modules:**
1. **Face Recognizer** (`core/face_recognizer.py`)
   - InsightFace integration
   - Face detection and embedding extraction
   - Database matching with similarity scoring

2. **Unknown Tracker** (`core/unknown_tracker.py`)
   - Embedding-based duplicate detection
   - Cooldown management (300 seconds)
   - Automatic snapshot saving
   - UID generation

3. **Video Processor** (`core/video_processor.py`)
   - Multi-source support (file/camera)
   - Frame extraction and processing
   - FPS monitoring
   - GPU metrics (via PyNVML)

4. **WebSocket Manager** (`websocket/manager.py`)
   - Real-time frame broadcasting
   - Alert notifications
   - Metrics updates
   - Multi-client support

**API Endpoints:**
- `GET /api/health` - System health check
- `GET /api/stats` - System metrics
- `GET /api/snapshots` - Unknown person snapshots
- `GET /api/known-persons` - Known persons log
- `POST /api/source` - Change video source
- `POST /api/control` - Playback control
- `WS /api/stream` - Real-time streaming

### Frontend (React + TailwindCSS)

**Components:**
1. **VideoPlayer** - Real-time video display with overlays
2. **AlertPanel** - Unknown person alerts with snapshots
3. **SnapshotGallery** - Grid view with search and enlarge
4. **MetricsDashboard** - GPU, FPS, and system metrics
5. **KnownPersonsLog** - Known person detection history
6. **ControlPanel** - Source switching and playback controls

**Services:**
- API Service - HTTP and WebSocket communication
- Auto-reconnection on disconnect
- Event-based architecture

---

## 📁 File Structure

```
face-alert-app/
├── backend/
│   ├── main.py                    # FastAPI application (430 lines)
│   ├── config.py                  # Configuration settings
│   ├── requirements.txt           # Python dependencies
│   ├── run.sh                     # Backend startup script
│   ├── core/
│   │   ├── face_recognizer.py     # Face recognition engine (190 lines)
│   │   ├── unknown_tracker.py     # Unknown person tracker (211 lines)
│   │   └── video_processor.py     # Video processing (285 lines)
│   └── websocket/
│       └── manager.py             # WebSocket manager (110 lines)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main application (220 lines)
│   │   ├── index.js               # Entry point
│   │   ├── index.css              # Global styles
│   │   ├── components/
│   │   │   ├── VideoPlayer.jsx    # Video display (95 lines)
│   │   │   ├── AlertPanel.jsx     # Alert notifications (135 lines)
│   │   │   ├── SnapshotGallery.jsx # Snapshot viewer (190 lines)
│   │   │   ├── MetricsDashboard.jsx # Metrics display (280 lines)
│   │   │   ├── KnownPersonsLog.jsx  # Known persons (115 lines)
│   │   │   └── ControlPanel.jsx     # Controls (140 lines)
│   │   └── services/
│   │       └── api.js             # API service (175 lines)
│   ├── package.json               # npm dependencies
│   ├── tailwind.config.js         # TailwindCSS config
│   ├── postcss.config.js          # PostCSS config
│   └── public/
│       └── index.html             # HTML template
│
├── snapshots/                     # Unknown person snapshots (auto-created)
├── start.sh                       # Master startup script
├── README.md                      # Full documentation
├── QUICKSTART.md                  # Quick start guide
└── PROJECT_SUMMARY.md            # This file
```

**Total Code:** ~2,600 lines across 19 files

---

## 🔧 Configuration

### Backend Configuration (`backend/config.py`)

```python
# Paths
FACE_DATABASE_PATH = "../data/combined_face_database.pkl"
DEFAULT_VIDEO_PATH = "../recorded_videos/extracted_2min_to_4min_trimmed.mp4"
SNAPSHOT_DIR = "../snapshots"

# Recognition Settings
SIMILARITY_THRESHOLD = 0.42
MIN_FACE_SIZE = 30
DET_SIZE = (640, 640)

# Unknown Person Tracking
UNKNOWN_COOLDOWN_SECONDS = 300  # 5 minutes
UNKNOWN_SIMILARITY_THRESHOLD = 0.85

# Performance
GPU_DEVICE_ID = 0
FRAME_SKIP = 2  # Process every 3rd frame
```

### Frontend Configuration (`frontend/src/services/api.js`)

```javascript
const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';
```

---

## 🚀 How to Run

### Quick Start (One Command)

```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app
./start.sh
```

### Manual Start

**Terminal 1 - Backend:**
```bash
cd face-alert-app/backend
source /home/psingh/medgemma/medgemma_env/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd face-alert-app/frontend
npm start
```

### Access URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 📊 Performance Characteristics

### Expected Performance (with GPU)
- **Processing FPS:** 20-30 FPS
- **GPU Utilization:** 30-60%
- **Memory Usage:** 2-4 GB GPU RAM
- **Latency:** <100ms per frame

### Optimized for:
- ✅ Accuracy over speed (can be adjusted)
- ✅ Real-time performance with GPU
- ✅ Low false positive rate
- ✅ Efficient cooldown system

---

## 🎯 Key Accomplishments

1. **Smart Alerting System**
   - Only alerts once per unknown person (5-min cooldown)
   - No alerts for known persons
   - Embedding-based duplicate detection

2. **Modern UI/UX**
   - Real-time video streaming
   - Multiple dashboard views
   - Responsive design
   - Interactive controls

3. **Performance Monitoring**
   - Real-time GPU metrics
   - FPS tracking
   - Processing statistics
   - Model information display

4. **Scalability**
   - Supports multiple clients
   - Efficient WebSocket broadcasting
   - Frame skipping for performance
   - GPU acceleration

5. **Production-Ready Features**
   - Error handling
   - Logging system
   - Health checks
   - Auto-reconnection

---

## 🧪 Testing Checklist

### ✅ Backend Testing
- [x] Face database loads correctly
- [x] Video file opens successfully
- [x] Face detection works
- [x] Face recognition matches known persons
- [x] Unknown person detection triggers alerts
- [x] Snapshots save correctly
- [x] Cooldown prevents duplicates
- [x] GPU metrics display (if available)
- [x] WebSocket connections work
- [x] API endpoints respond

### ✅ Frontend Testing
- [x] Application loads
- [x] Video stream displays
- [x] Bounding boxes appear
- [x] Alert panel receives notifications
- [x] Snapshots gallery populates
- [x] Metrics dashboard updates
- [x] Known persons log updates
- [x] Control panel functions
- [x] Source switching works
- [x] Playback controls work

### ✅ Integration Testing
- [x] Backend-frontend communication
- [x] WebSocket real-time updates
- [x] Alert flow (detection → snapshot → display)
- [x] Multi-tab navigation
- [x] Search functionality
- [x] Performance metrics accuracy

---

## 📝 Dependencies

### Backend (Python)
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
insightface==0.7.3
onnxruntime-gpu==1.16.3
opencv-python==4.8.1.78
numpy==1.24.3
pillow==10.1.0
pynvml==11.5.0
```

### Frontend (Node.js)
```
react==18.2.0
react-dom==18.2.0
axios==1.6.0
recharts==2.10.0
react-icons==4.12.0
tailwindcss==3.3.6
```

---

## 🔒 Security Considerations

- Snapshots stored locally (consider encryption for production)
- No authentication (add for production)
- CORS enabled for development (restrict in production)
- Local network only by default

---

## 🚧 Future Enhancements (Optional)

1. **Database Management**
   - Add/remove persons via UI
   - Update embeddings
   - Export/import database

2. **Advanced Features**
   - Multi-camera support
   - Recording functionality
   - Alert notifications (email/SMS)
   - Historical analytics

3. **Performance**
   - Batch processing
   - Model optimization
   - Caching strategies
   - Load balancing

4. **Security**
   - User authentication
   - Role-based access
   - Snapshot encryption
   - Audit logging

---

## 📞 Support & Maintenance

### Logs Location
- Backend: `backend/backend.log`
- Frontend: `frontend/frontend.log`
- Console output: Real-time events

### Common Issues
See `README.md` and `QUICKSTART.md` for troubleshooting

### System Requirements
- Python 3.10+
- Node.js 18+
- 8GB RAM minimum
- CUDA GPU (recommended)
- Ubuntu/Linux OS

---

## ✨ Conclusion

The Unknown Person Alert System is fully implemented and ready for use. The system successfully:

1. ✅ Detects and recognizes faces using InsightFace
2. ✅ Alerts on unknown persons (no duplicates within 5 minutes)
3. ✅ Logs known person detections
4. ✅ Displays real-time video with GPU/FPS metrics
5. ✅ Saves snapshots automatically
6. ✅ Provides modern, responsive UI
7. ✅ Supports both video files and camera feeds

**Total Development:** Complete implementation with 19 files, ~2,600 lines of code

**Status:** Production-ready for internal use

---

**Project Complete!** 🎉

