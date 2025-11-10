#!/bin/bash
# Wrapper script to start backend with GPU/CPU support

echo "=================================================="
echo "🚀 Starting Backend"
echo "=================================================="
echo ""

# Activate virtual environment
source /home/psingh/medgemma/medgemma_env/bin/activate

# Set buffalo_s model
export FACE_MODEL=buffalo_s

# Check if GPU is enabled in config (suppress print statements from config.py)
GPU_DEVICE_ID=$(python << 'PYTHON_SCRIPT'
import sys
import os
# Redirect stdout/stderr to suppress print statements
old_stdout = sys.stdout
old_stderr = sys.stderr
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# Import config (print statements will be suppressed)
import config

# Restore stdout to print only the value we want
sys.stdout = old_stdout
sys.stderr = old_stderr
print(config.GPU_DEVICE_ID)
PYTHON_SCRIPT
)

if [ "$GPU_DEVICE_ID" -ge 0 ]; then
    echo "🎮 GPU Mode Detected (GPU_DEVICE_ID=$GPU_DEVICE_ID)"

    # Find all NVIDIA CUDA library directories
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
    CUDA_LIB_DIRS=$(find $SITE_PACKAGES/nvidia* -type d -name "lib" 2>/dev/null | tr '\n' ':')
    export LD_LIBRARY_PATH="${CUDA_LIB_DIRS}${LD_LIBRARY_PATH}"

    echo "🔧 CUDA libraries configured"
    echo "   Site packages: $SITE_PACKAGES"
    LIB_COUNT=$(find $SITE_PACKAGES/nvidia* -type d -name "lib" 2>/dev/null | wc -l)
    echo "   Found $LIB_COUNT CUDA library directories"
    echo "   LD_LIBRARY_PATH includes: $(echo $LD_LIBRARY_PATH | tr ':' '\n' | grep nvidia | head -3 | tr '\n' ' ')"
    echo ""
    echo "✅ GPU support enabled"
else
    echo "💻 CPU Mode Detected (GPU_DEVICE_ID=$GPU_DEVICE_ID)"
    echo "✅ CPU-only processing enabled"
fi

echo "🌐 Starting Uvicorn on port 8000..."
echo ""

# Start uvicorn
cd "$(dirname "$0")"
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Note: To switch between GPU and CPU modes:
# - GPU: Set GPU_DEVICE_ID = 0 in config.py
# - CPU: Set GPU_DEVICE_ID = -1 in config.py

