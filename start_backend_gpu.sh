#!/bin/bash
# Startup script for backend with GPU support
# Based on successful Flask GPU approach from aiims_attendance/run_with_gpu.sh

cd /home/psingh/medgemma/aiims-attendance/face-alert-app/backend

# Activate virtual environment
source /home/psingh/medgemma_env/bin/activate

# Find ALL PyTorch/NVIDIA CUDA library directories (like Flask script does)
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
export LD_LIBRARY_PATH=$(find $SITE_PACKAGES/nvidia* -type d -name "lib" 2>/dev/null | tr '\n' ':')$LD_LIBRARY_PATH

echo "========================================="
echo "🚀 Starting Backend with GPU Support"
echo "========================================="
echo "🔧 Auto-detected CUDA libraries from nvidia packages"
echo "Port: 8001"
echo "Logs: ../backend.log"
echo ""

# Kill any existing backend
pkill -9 -f "uvicorn main:app" 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
nohup uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info > ../backend.log 2>&1 &

sleep 3

# Check if started
if lsof -ti:8001 >/dev/null 2>&1; then
    echo "✅ Backend started successfully!"
    echo ""
    echo "Checking GPU initialization..."
    sleep 2
    grep -E "(InsightFace initialized|Failed to load)" ../backend.log | tail -5
else
    echo "❌ Backend failed to start. Check logs:"
    tail -20 ../backend.log
fi

