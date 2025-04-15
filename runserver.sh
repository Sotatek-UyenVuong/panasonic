#!/bin/bash

APP_MODULE="app:app"
HOST="0.0.0.0"
PORT=${1:-1117}
WORKERS=1

# Activate virtual environment
source venv/bin/activate

kill_processes() {
    echo "Finding and stopping processes running on port ${PORT}..."
    
    # Kiểm tra OS và sử dụng lệnh phù hợp
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        PIDS=$(lsof -ti tcp:${PORT})
        if [ ! -z "$PIDS" ]; then
            echo "Killing processes: $PIDS"
            kill -9 $PIDS
            echo "Stopped processes running on port ${PORT}"
        else
            echo "No processes found running on port ${PORT}"
        fi
    else
        # Linux
        if fuser -k ${PORT}/tcp 2>/dev/null; then
            echo "Stopped processes running on port ${PORT}"
        else 
            echo "No processes found running on port ${PORT}"
        fi
    fi
    
    sleep 2 
}

cleanup() {
    echo "Cleaning up..."
    [ ! -z "$UVICORN_PID" ] && kill $UVICORN_PID
    deactivate
    exit 0
}

trap cleanup SIGINT SIGTERM

kill_processes

# Use the virtual environment's uvicorn
./venv/bin/uvicorn $APP_MODULE \
    --host $HOST \
    --port $PORT \
    --workers $WORKERS \
    --log-level info &

UVICORN_PID=$!

wait $UVICORN_PID