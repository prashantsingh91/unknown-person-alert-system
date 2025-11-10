#!/bin/bash
# Wrapper script to start backend with CPU-only processing

echo "=================================================="
echo "🚀 Starting Backend (CPU Mode)"
echo "=================================================="
echo ""

# Activate virtual environment
source /home/psingh/medgemma/medgemma_env/bin/activate

echo "💻 CPU Mode Selected"
echo "✅ CPU-only processing enabled"
echo "🌐 Starting Uvicorn on port 8001..."
echo ""

# Start uvicorn
cd "$(dirname "$0")"
python -m uvicorn main:app --host 0.0.0.0 --port 8001
