#!/bin/bash
# Master script to start both backend and frontend

echo "=========================================="
echo "Unknown Person Alert System"
echo "=========================================="
echo ""

# Function to handle cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start backend
echo "[1/2] Starting Backend (FastAPI)..."
cd "$SCRIPT_DIR/backend"
source /home/psingh/medgemma/medgemma_env/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!

echo "  ✓ Backend started (PID: $BACKEND_PID)"
echo "  → Backend logs: $SCRIPT_DIR/backend/backend.log"
echo ""

# Wait for backend to start
echo "Waiting for backend to initialize..."
sleep 5

# Start frontend
echo "[2/2] Starting Frontend (React)..."
cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "  → Installing npm dependencies..."
    npm install
fi

BROWSER=none npm start > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "  ✓ Frontend started (PID: $FRONTEND_PID)"
echo "  → Frontend logs: $SCRIPT_DIR/frontend/frontend.log"
echo ""

echo "=========================================="
echo "System is ready!"
echo "=========================================="
echo ""
echo "Access the application:"
echo "  • Frontend: http://localhost:3000"
echo "  • Backend API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID

