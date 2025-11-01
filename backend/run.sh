#!/bin/bash
# Start FastAPI backend server

# Activate virtual environment
source /home/psingh/medgemma/medgemma_env/bin/activate

# Run server
cd "$(dirname "$0")"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

