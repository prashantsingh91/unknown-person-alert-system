#!/bin/bash
# GPU-enabled backend startup script
# Based on proven Flask GPU approach

set -e

cd /home/psingh/medgemma/aiims-attendance/face-alert-app

# Activate virtual environment
source /home/psingh/medgemma_env/bin/activate

# Find ALL NVIDIA CUDA library directories (same as Flask)
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
export LD_LIBRARY_PATH=$(find $SITE_PACKAGES/nvidia* -type d -name "lib" 2>/dev/null | tr '\n' ':')$LD_LIBRARY_PATH

echo "==========================================="
echo "🚀 Starting Backend with GPU Support"
echo "==========================================="
echo "📁 Auto-detected CUDA libraries:"
echo "$LD_LIBRARY_PATH" | tr ':' '\n' | grep nvidia | grep -E "(cudnn|cublas)" | head -3
echo ""

# Kill any existing backend
echo "🔄 Stopping any existing backend..."
pkill -9 -f "python.*uvicorn main:app" 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 2

# Clear old log
> backend.log
echo "✅ Log cleared"

# Start backend (run in foreground to preserve environment, use screen/tmux for background)
echo "🎬 Starting uvicorn..."
echo ""
cd backend

# Use exec to replace shell with python process (preserves environment)
exec python -m uvicorn main:app --host 0.0.0.0 --port 8001 2>&1 | tee ../backend.log

