#!/bin/bash
# Wrapper script to start backend with GPU support

echo "=================================================="
echo "🚀 Starting Backend with GPU Support"
echo "=================================================="
echo ""

# Activate virtual environment
source /home/psingh/medgemma/medgemma_env/bin/activate

# Find all NVIDIA CUDA library directories
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
export LD_LIBRARY_PATH=$(find $SITE_PACKAGES/nvidia* -type d -name "lib" 2>/dev/null | tr '\n' ':')$LD_LIBRARY_PATH

echo "🔧 CUDA libraries configured"
echo "   Site packages: $SITE_PACKAGES"
echo "   Found $(find $SITE_PACKAGES/nvidia* -type d -name "lib" 2>/dev/null | wc -l) CUDA library directories"
echo ""
echo "✅ GPU support enabled"
echo "🌐 Starting Uvicorn on port 8001..."
echo ""

# Start uvicorn
cd "$(dirname "$0")"
python -m uvicorn main:app --host 0.0.0.0 --port 8001

