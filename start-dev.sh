#!/bin/bash

echo "Starting RegDoc Development Environment..."
echo

echo "[1/2] Starting Backend Server..."
cd backend
python main.py &
BACKEND_PID=$!

echo "[2/2] Starting Frontend Development Server..."
cd ../frontend
npm run dev &
FRONTEND_PID=$!

echo
echo "Both servers are starting..."
echo "Backend: http://10.21.22.107:8443"
echo "Frontend: http://localhost:5173"
echo
echo "Press Ctrl+C to stop both servers"

# Function to clean up processes
cleanup() {
    echo "Stopping servers..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait
