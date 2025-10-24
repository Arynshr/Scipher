#!/bin/bash

# Scipher Development Startup Script
# This script starts both the FastAPI backend and Next.js frontend

echo "🚀 Starting Scipher Development Environment"
echo "=========================================="

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the scipher project root directory"
    exit 1
fi

# Function to start backend
start_backend() {
    echo "📡 Starting FastAPI Backend..."
    cd backend
    if [ -f "requirements.txt" ]; then
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
    fi
    echo "Starting backend server on http://localhost:8080"
    PYTHONPATH=src uvicorn main:app --reload --host 0.0.0.0 --port 8080 &
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend started with PID: $BACKEND_PID"
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting Next.js Frontend..."
    cd frontend
    echo "Installing Node.js dependencies..."
    npm install
    echo "Starting frontend server on http://localhost:3000"
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend started with PID: $FRONTEND_PID"
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "✅ Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "✅ Frontend stopped"
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start services
start_backend
sleep 3  # Give backend time to start
start_frontend

echo ""
echo "🎉 Scipher is now running!"
echo "========================="
echo "📡 Backend API: http://localhost:8080"
echo "📚 API Docs: http://localhost:8080/docs"
echo "🎨 Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user to stop
wait
