# Quick Start Guide

## Prerequisites Check

1. **Virtual Environment**: `medgemma_env` should exist
2. **Face Database**: `aiims-attendance/data/combined_face_database.pkl` should exist
3. **Test Video**: `aiims-attendance/recorded_videos/extracted_2min_to_4min_trimmed.mp4` should exist
4. **GPU**: CUDA-capable GPU (optional but recommended)

## Installation

### Step 1: Install Backend Dependencies

```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
source /home/psingh/medgemma/medgemma_env/bin/activate
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies

```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/frontend
npm install
```

## Running the System

### Option 1: One Command (Recommended)

```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app
./start.sh
```

This will:
- Start the backend server on port 8000
- Start the frontend server on port 3000
- Open logs in the background

### Option 2: Start Separately

**Terminal 1 - Backend:**
```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
./run.sh
```

**Terminal 2 - Frontend:**
```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/frontend
./run.sh
```

## Access the Application

Once both servers are running:

1. Open your browser: **http://localhost:3000**
2. You should see the Unknown Person Alert System interface
3. Video feed will start automatically with the test video
4. Known persons will have **green** bounding boxes
5. Unknown persons will have **red** bounding boxes and trigger alerts

## What to Expect

### On Known Person Detection:
- Green bounding box with person name
- Entry appears in "Known Persons" log
- No alert triggered

### On Unknown Person Detection:
- Red bounding box labeled "UNKNOWN"
- **Alert notification** appears
- **Snapshot saved** automatically
- 5-minute cooldown prevents duplicate alerts

### Real-time Metrics:
- GPU utilization (if available)
- Processing FPS
- Video FPS
- Detection counts

## Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:3000
- [ ] Video feed displays
- [ ] Known persons detected with green boxes
- [ ] Unknown persons trigger red alerts
- [ ] Snapshots saved in `/snapshots` directory
- [ ] Metrics dashboard shows GPU/FPS info
- [ ] No duplicate alerts for same unknown person

## Troubleshooting

### Backend Issues

**"Face database not found"**
```bash
# Check if database exists
ls -lh /home/psingh/medgemma/aiims-attendance/data/combined_face_database.pkl
```

**"Failed to open video"**
```bash
# Check if test video exists
ls -lh /home/psingh/medgemma/aiims-attendance/recorded_videos/extracted_2min_to_4min_trimmed.mp4
```

**"CUDA error"**
- Check GPU availability: `nvidia-smi`
- If no GPU, system will use CPU (slower)

### Frontend Issues

**"Cannot connect to backend"**
- Ensure backend is running on port 8000
- Check: `curl http://localhost:8000/api/health`

**"npm install fails"**
- Check Node.js version: `node --version` (should be 18+)
- Try: `rm -rf node_modules package-lock.json && npm install`

### Performance Issues

**Low FPS (<10 FPS)**
1. Check GPU utilization in Metrics tab
2. Increase FRAME_SKIP in `backend/config.py`
3. Reduce video resolution

**High GPU memory usage**
- Normal for deep learning models
- Check temperature in Metrics tab
- Reduce DET_SIZE if needed

## API Testing

Test backend independently:

```bash
# Health check
curl http://localhost:8000/api/health

# Get system stats
curl http://localhost:8000/api/stats

# Get snapshots
curl http://localhost:8000/api/snapshots

# Get known persons
curl http://localhost:8000/api/known-persons
```

## Stopping the System

If using `start.sh`: Press **Ctrl+C**

If running separately:
- Press **Ctrl+C** in each terminal

## Logs

- Backend: `backend/backend.log`
- Frontend: `frontend/frontend.log`
- Console output shows real-time events

## Next Steps

1. **Switch to camera feed**: Use Control Panel in UI
2. **Adjust sensitivity**: Modify `SIMILARITY_THRESHOLD` in config
3. **Change cooldown**: Modify `UNKNOWN_COOLDOWN_SECONDS`
4. **View API docs**: http://localhost:8000/docs

## Features to Try

1. **View Different Tabs**: Explore Alerts, Snapshots, Metrics, Known Persons
2. **Search Snapshots**: Use search bar in Snapshots tab
3. **Monitor Performance**: Watch GPU and FPS in Metrics tab
4. **Control Playback**: Use Play/Pause in Control Panel
5. **Check Alert History**: See all unknown person detections

## Support

For issues, check:
1. Backend logs for errors
2. Browser console for frontend errors
3. GPU status with `nvidia-smi`
4. System resources with `htop`

---

**Enjoy using the Unknown Person Alert System!** 🎥🔍

