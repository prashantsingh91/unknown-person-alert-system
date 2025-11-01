# Face Alert System - Status Report
**Date:** November 1, 2025, 17:37 UTC
**Backend:** Running on port 8001
**Frontend:** Running on port 3000

## ✅ What's Working

### 1. FPS Logging
- **Status:** ✅ WORKING
- **Current FPS:** 5.1-5.2 FPS
- **Logs:** Now displaying in backend logs every second
- **Example:** `📊 FPS: 5.1 | GPU: 0% | Mem: 2578MB | Frames: 228`

### 2. Face Detection & Recognition
- **Status:** ✅ WORKING
- **Mode:** CPU-based processing
- **Known Persons:** 19 people in database
- **Deduplication:** Working (30s cooldown for known persons, 5min for unknown)

### 3. Snapshot Creation
- **Status:** ✅ WORKING
- **Location:** `/home/psingh/medgemma/aiims-attendance/face-alert-app/snapshots/`
- **Format:** `UNKNOWN_XXXX_YYYYMMDD_HHMMSS.jpg`
- **Snapshots Created:** Multiple (UNKNOWN_0025, 0026, 0030, etc.)

### 4. Backend/Frontend Communication
- **Status:** ✅ WORKING
- **WebSocket:** Active
- **Port 8001:** Backend API
- **Port 3000:** Frontend UI

## ⚠️ Issues Identified

### 1. GPU Not Utilized (Critical)
- **Current:** GPU utilization at 0%
- **Cause:** Missing CUDA library: `libcudnn.so.8` (cuDNN)
- **Impact:** Processing running on CPU only, resulting in low FPS (5 FPS instead of potential 15-25 FPS)
- **InsightFace Status:** Initialized with CUDAExecutionProvider but falling back to CPUExecutionProvider

**Error Message:**
```
Failed to load library libonnxruntime_providers_cuda.so with error: 
libcudnn.so.8: cannot open shared object file: No such file or directory
```

**What's Installed:**
- ✅ NVIDIA Driver (A10-24Q GPU detected)
- ✅ onnxruntime-gpu (1.18.1)
- ✅ nvidia-cublas-cu11 (installed)
- ✅ nvidia-cuda-runtime-cu11 (installed)  
- ❌ nvidia-cudnn-cu11 (needs installation or system cuDNN)

### 2. Snapshots Not Visible in UI
- **Backend:** Snapshots are being created and saved ✅
- **API Endpoint:** `/snapshots/` is mounted ✅
- **Possible Causes:**
  - Frontend image loading issue (port mismatch - already fixed to 8001)
  - CORS configuration
  - SSH tunnel issue (if accessing remotely)
  
**Need to verify:** Check browser console for image loading errors

## 📊 Current Performance Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Processing FPS | 5.1-5.2 | 15-25 | ❌ Low |
| GPU Utilization | 0% | 50-80% | ❌ Not Used |
| System Memory | 2578 MB | N/A | ✅ OK |
| Known Persons | 19 | N/A | ✅ Loaded |
| Detection Accuracy | Good | N/A | ✅ Working |

## 🔧 Fixes Applied

1. **Added FPS Logging** ✅
   - Modified `backend/main.py` to log FPS, GPU%, Memory, and Frame count every second
   
2. **Fixed Snapshot Port** ✅  
   - Updated `frontend/src/components/SnapshotGallery.jsx` to use port 8001
   
3. **Fixed Face Size Display** ✅
   - Added face size calculation (width x height) in video processing
   
4. **Installed CUDA Libraries** ⚠️
   - Installed cublas and cuda-runtime
   - Still missing: cuDNN (libcudnn.so.8)

5. **Fixed numpy Version** ✅
   - Resolved incompatibility issue (now using numpy 1.26.4)

## 🚀 Next Steps to Enable GPU

### Option 1: Install cuDNN via pip (Recommended)
```bash
source /home/psingh/medgemma_env/bin/activate
pip install nvidia-cudnn-cu11
```

Then restart backend with CUDA paths:
```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app
./start_backend_gpu.sh
```

### Option 2: Install System cuDNN (Requires sudo)
```bash
# Ubuntu/Debian
sudo apt-get install libcudnn8 libcudnn8-dev

# Then restart backend
pkill -f "uvicorn main:app"
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### Option 3: Accept CPU Mode and Optimize
If GPU access is not possible, optimize CPU performance:
- Increase `FRAME_SKIP` in `config.py` (currently 0)
- Reduce video resolution
- Optimize detection threshold

## 📝 To Check Snapshots in UI

1. **Open browser:** `http://localhost:3000` (or via SSH tunnel)
2. **Check browser console (F12):** Look for image loading errors
3. **Verify API endpoint:** Open `http://localhost:8001/snapshots/` in browser
4. **Test direct image:** Try `http://localhost:8001/snapshots/UNKNOWN_0025_20251101_172335_048013.jpg`

## 💡 Current Workaround

The system is functional but running at reduced performance:
- ✅ Face detection working
- ✅ Recognition working  
- ✅ Snapshots being saved
- ✅ Alerts triggered correctly
- ⚠️ Running at 5 FPS (slow due to CPU processing)

**User can use the system now, but GPU acceleration would improve FPS by 3-5x.**

## 🔍 Monitoring Commands

```bash
# Check backend logs
tail -f /home/psingh/medgemma/aiims-attendance/face-alert-app/backend.log | grep "📊 FPS"

# Check GPU status
watch -n 1 nvidia-smi

# Check snapshots
ls -lh /home/psingh/medgemma/aiims-attendance/face-alert-app/snapshots/

# Check if backend running
lsof -i:8001

# Check if frontend running
lsof -i:3000
```

## 📞 Support

If GPU is required, you'll need to install cuDNN. The system administrator can install it system-wide, or you can try installing it via pip in the virtual environment.

