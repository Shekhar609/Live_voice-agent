#!/usr/bin/env bash
set -e

echo "Starting Multilingual Real-Time Speech-to-Text Application..."

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

export PORT=${PORT:-8000}
export HOST=${HOST:-0.0.0.0}

echo "Server starting at http://localhost:${PORT}"
./venv/bin/uvicorn app.main:app --host $HOST --port $PORT --reload
