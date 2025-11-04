# GPU Setup & Troubleshooting Guide

## 🎯 Purpose
This document provides step-by-step instructions to ensure the Face Alert App runs with GPU acceleration after server restarts. Follow this guide whenever GPU issues occur.

---

## 📋 Prerequisites

### 1. System Requirements
- **NVIDIA GPU** with CUDA support
- **CUDA Driver** installed on host system
- **Python 3.10** (recommended)

### 2. Verify System GPU
```bash
# Check if NVIDIA driver is installed
nvidia-smi

# Expected output: GPU info, driver version, CUDA version
```

---

## 🔧 Required Package Versions

### Critical Version Compatibility

The app requires **CUDA 11.x** libraries. Using CUDA 12 will cause errors.

| Package | Version | CUDA Support | Notes |
|---------|---------|--------------|-------|
| **PyTorch** | `2.0.1+cu118` | CUDA 11.8 | ⚠️ **CRITICAL**: Must be CUDA 11 version |
| **torchvision** | `0.15.2+cu118` | CUDA 11.8 | Must match PyTorch version |
| **onnxruntime-gpu** | `1.16.3` | CUDA 11.x | For InsightFace acceleration |
| **insightface** | Latest | - | Face recognition library |
| **NVIDIA CUDA 11 Libraries** | See below | CUDA 11.x | Runtime libraries |

### Required NVIDIA CUDA 11 Libraries
```
nvidia-cublas-cu11
nvidia-cuda-cupti-cu11
nvidia-cuda-nvrtc-cu11
nvidia-cuda-runtime-cu11
nvidia-cudnn-cu11
nvidia-cufft-cu11
nvidia-curand-cu11
nvidia-cusolver-cu11
nvidia-cusparse-cu11
nvidia-nccl-cu11
nvidia-nvtx-cu11
```

---

## 🚀 Setup Steps

### Step 1: Activate Python Environment

```bash
# Navigate to project root
cd /home/psingh/medgemma/aiims-attendance/face-alert-app

# Activate the correct environment
source ~/medgemma_env/bin/activate
```

### Step 2: Verify Current Package Versions

```bash
# Check PyTorch version (MUST be 2.0.1+cu118 or 2.0.1+cu117)
python -c "import torch; print('PyTorch:', torch.__version__)"

# Expected output: PyTorch: 2.0.1+cu118
```

**❌ If you see `2.6.0+cu124` or any CUDA 12 version:**
```bash
# Uninstall CUDA 12 versions
pip uninstall -y torch torchaudio torchvision

# Install CUDA 11 compatible versions
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118
```

### Step 3: Verify NVIDIA CUDA 11 Libraries

```bash
# Check for NVIDIA CUDA 11 libraries
pip list | grep nvidia-cublas-cu11

# If NOT installed, install all CUDA 11 libraries:
pip install nvidia-cublas-cu11 nvidia-cuda-cupti-cu11 nvidia-cuda-nvrtc-cu11 \
    nvidia-cuda-runtime-cu11 nvidia-cudnn-cu11 nvidia-cufft-cu11 \
    nvidia-curand-cu11 nvidia-cusolver-cu11 nvidia-cusparse-cu11 \
    nvidia-nccl-cu11 nvidia-nvtx-cu11
```

### Step 4: Verify onnxruntime-gpu

```bash
# Check onnxruntime-gpu version
pip show onnxruntime-gpu

# Expected: Version 1.16.3 (or similar 1.16.x)
# If not installed:
pip install onnxruntime-gpu==1.16.3
```

---

## 🎬 Starting the Application

### Backend Startup (GPU-Enabled)

The app includes a special startup script that configures CUDA libraries:

```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend

# Method 1: Using the GPU startup script (RECOMMENDED)
bash start_backend_gpu.sh

# Method 2: Background mode
nohup bash start_backend_gpu.sh > backend.log 2>&1 &
```

**What the script does:**
1. Activates `medgemma_env` environment
2. Finds all NVIDIA CUDA library directories in site-packages
3. Sets `LD_LIBRARY_PATH` to include these directories
4. Starts Uvicorn on port 8001

### Frontend Startup

```bash
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/frontend

# Start frontend
npm start
```

---

## ✅ Verification Steps

### 1. Check Backend is Running
```bash
# Check if port 8001 is listening
lsof -i :8001 | grep LISTEN

# Expected output:
# python  41022 psingh   70u  IPv4 294564      0t0  TCP *:8001 (LISTEN)
```

### 2. Verify GPU Initialization
```bash
# Check backend logs for GPU messages
head -80 backend/backend.log | grep -E "🚀|🔧|✅|GPU|CUDA|provider|FPS"

# Expected output:
# 🚀 Starting Backend with GPU Support
# 🔧 CUDA libraries configured
#    Found 14 CUDA library directories
# ✅ GPU support enabled
# InsightFace initialized with providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
```

### 3. Monitor GPU Usage
```bash
# Watch GPU utilization in real-time
watch -n 1 nvidia-smi

# Expected during video processing:
# GPU Memory: ~3800-4000 MB
# GPU Utilization: 6-15%
```

### 4. Check FPS Performance
```bash
# Monitor backend logs for FPS
tail -f backend/backend.log | grep FPS

# Expected output:
# 📊 FPS: 60-65 | GPU: 6% | Mem: 3867MB | Frames: 854
```

---

## ⚠️ Common Issues & Solutions

### Issue 1: `libcudart.so.12: cannot open shared object file`

**Problem:** PyTorch is CUDA 12 version, but app needs CUDA 11.

**Solution:**
```bash
source ~/medgemma_env/bin/activate
pip uninstall -y torch torchaudio torchvision
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118
```

### Issue 2: `libonnxruntime_providers_cuda.so: libcublasLt.so.11: cannot open shared object file`

**Problem:** NVIDIA CUDA 11 libraries not installed.

**Solution:**
```bash
source ~/medgemma_env/bin/activate
pip install nvidia-cublas-cu11 nvidia-cudnn-cu11 nvidia-cufft-cu11 \
    nvidia-curand-cu11 nvidia-cusolver-cu11 nvidia-cusparse-cu11
```

### Issue 3: GPU Not Used (0% GPU in nvidia-smi)

**Problem:** Backend started without GPU script or LD_LIBRARY_PATH not set.

**Solution:**
```bash
# Stop backend
pkill -9 -f uvicorn

# Restart with GPU script
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
bash start_backend_gpu.sh
```

### Issue 4: `CPUExecutionProvider` Only (No CUDA Provider)

**Problem:** onnxruntime-gpu not installed or incompatible version.

**Solution:**
```bash
source ~/medgemma_env/bin/activate
pip uninstall -y onnxruntime onnxruntime-gpu
pip install onnxruntime-gpu==1.16.3

# Verify CUDA libraries
pip list | grep nvidia-cu
```

### Issue 5: Port 8001 Already in Use

**Problem:** Old backend process still running.

**Solution:**
```bash
# Kill all uvicorn processes
pkill -9 -f uvicorn

# Wait 2 seconds
sleep 2

# Restart backend
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
bash start_backend_gpu.sh
```

---

## 🔍 Diagnostic Commands

### Quick Health Check
```bash
# Run this complete diagnostic
cd /home/psingh/medgemma/aiims-attendance/face-alert-app
source ~/medgemma_env/bin/activate

echo "=== System GPU ==="
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

echo ""
echo "=== PyTorch Version ==="
python -c "import torch; print('Version:', torch.__version__); print('CUDA Available:', torch.cuda.is_available()); print('CUDA Version:', torch.version.cuda)"

echo ""
echo "=== ONNX Runtime ==="
pip show onnxruntime-gpu | grep Version

echo ""
echo "=== NVIDIA CUDA 11 Libraries ==="
pip list | grep nvidia-cu11 | wc -l
echo "libraries installed"

echo ""
echo "=== Backend Status ==="
lsof -i :8001 | grep LISTEN || echo "Backend NOT running"

echo ""
echo "=== Frontend Status ==="
lsof -i :3000 | grep LISTEN || echo "Frontend NOT running"
```

---

## 📂 Important File Locations

### Python Environment
```
Environment: ~/medgemma_env
Activation: source ~/medgemma_env/bin/activate
Site Packages: ~/medgemma_env/lib/python3.10/site-packages
CUDA Libraries: ~/medgemma_env/lib/python3.10/site-packages/nvidia/*/lib
```

### Application Files
```
App Root: /home/psingh/medgemma/aiims-attendance/face-alert-app
Backend: /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
Frontend: /home/psingh/medgemma/aiims-attendance/face-alert-app/frontend
Startup Script: backend/start_backend_gpu.sh
Backend Log: backend/backend.log
Face Database: data/combined_face_database.pkl
```

---

## 🔄 Clean Restart Procedure

**Use this procedure after server restart or when GPU issues occur:**

```bash
# 1. Stop all processes
pkill -9 -f uvicorn
pkill -9 -f "npm start"
sleep 2

# 2. Activate environment
source ~/medgemma_env/bin/activate

# 3. Verify versions
python -c "import torch; print(torch.__version__)"
# Must show: 2.0.1+cu118 (not 2.6.0+cu124)

# 4. If wrong PyTorch version, fix it:
# pip uninstall -y torch torchaudio torchvision
# pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cu118

# 5. Delete old log
rm -f /home/psingh/medgemma/aiims-attendance/face-alert-app/backend/backend.log

# 6. Start backend with GPU
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
nohup bash start_backend_gpu.sh > backend.log 2>&1 &

# 7. Wait and verify
sleep 8
head -80 backend.log | grep -E "🚀|✅|provider"

# 8. Start frontend
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/frontend
npm start > /dev/null 2>&1 &

# 9. Verify both running
sleep 5
lsof -i :8001 | grep LISTEN  # Backend
lsof -i :3000 | grep LISTEN  # Frontend
```

---

## 📊 Expected Performance Benchmarks

With GPU acceleration properly configured:

| Metric | Value | Notes |
|--------|-------|-------|
| **FPS** | 50-65 | Varies with scene complexity |
| **GPU Utilization** | 6-15% | Efficient usage |
| **GPU Memory** | ~3800-4000 MB | Stable |
| **Detection Latency** | <20ms | Per frame |
| **Providers** | `CUDAExecutionProvider` | First in list |

**Without GPU (CPU-only mode):**
- FPS: 8-12 (very slow)
- CPU Usage: 80-100%
- No GPU memory usage

---

## 🛠️ Advanced Troubleshooting

### Check LD_LIBRARY_PATH
```bash
source ~/medgemma_env/bin/activate

# Find NVIDIA library directories
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
find $SITE_PACKAGES/nvidia* -type d -name "lib" 2>/dev/null

# Should show ~14 directories like:
# /home/psingh/medgemma/medgemma_env/lib/python3.10/site-packages/nvidia/cublas/lib
# /home/psingh/medgemma/medgemma_env/lib/python3.10/site-packages/nvidia/cudnn/lib
# etc.
```

### Test ONNX Runtime GPU
```bash
source ~/medgemma_env/bin/activate
python -c "import onnxruntime as ort; print('Available providers:', ort.get_available_providers())"

# Expected output:
# Available providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']

# If only CPUExecutionProvider, reinstall:
# pip uninstall -y onnxruntime-gpu
# pip install onnxruntime-gpu==1.16.3
```

### Manual CUDA Library Check
```bash
# Check if CUDA libraries are accessible
source ~/medgemma_env/bin/activate
python -c "import ctypes; ctypes.CDLL('libcublas.so.11')"

# If error, CUDA 11 libraries not in LD_LIBRARY_PATH
```

---

## 📞 Support

If issues persist after following this guide:

1. **Check logs**: `tail -100 backend/backend.log`
2. **Run diagnostic**: Copy-paste the "Quick Health Check" command above
3. **Compare versions**: Ensure all versions match this guide
4. **Check system GPU**: Run `nvidia-smi` to verify driver

---

## 📝 Version History

- **v1.0** (Nov 3, 2025): Initial GPU setup guide
- Issue resolved: Mixed CUDA 11/12 library conflicts
- Working configuration documented: PyTorch 2.0.1 + CUDA 11.8

---

## ⚡ Quick Reference Card

```bash
# 1. Environment
source ~/medgemma_env/bin/activate

# 2. Verify PyTorch (must be 2.0.1+cu118)
python -c "import torch; print(torch.__version__)"

# 3. Start backend with GPU
cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend
bash start_backend_gpu.sh

# 4. Verify GPU active
head -80 backend.log | grep provider
# Should show: ['CUDAExecutionProvider', 'CPUExecutionProvider']

# 5. Monitor GPU
nvidia-smi
```

---

**Last Updated**: November 3, 2025  
**Environment**: medgemma_env  
**App Location**: /home/psingh/medgemma/aiims-attendance/face-alert-app

