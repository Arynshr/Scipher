#!/bin/bash

# ==========================================
# 🚀 Scipher Development Startup Script
# Starts both FastAPI (backend) and Next.js (Web)
# ==========================================

set -e  # Exit immediately on error

echo "🚀 Starting Scipher Development Environment"
echo "=========================================="

# Ensure we're in the project root
if [ ! -d "backend" ] || [ ! -d "Web" ]; then
    echo "❌ Error: Please run this script from the scipher project root directory."
    exit 1
fi

# --- Cache Cleanup Function ---
clean_caches() {
    echo "🧹 Cleaning caches for a fresh start..."
    
    # Backend: Python caches
    echo "  📦 Clearing Python caches..."
    find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    find backend -name "*.pyc" -delete 2>/dev/null || true
    find backend -name "*.pyo" -delete 2>/dev/null || true
    
    # Backend: App-specific caches (e.g., processed data dir if exists)
    if [ -d "backend/src/processed_data" ]; then  # Adjust path based on settings.PROCESSED_DATA_DIR
        echo "  📁 Clearing processed data cache..."
        rm -rf backend/processed/*.json 2>/dev/null || true
    fi
    
    # Frontend: Next.js and npm caches
    echo "  🖥️  Clearing Next.js and npm caches..."
    cd Web
    rm -rf .next 2>/dev/null || true
    rm -rf node_modules/.cache 2>/dev/null || true
    npm cache clean --force 2>/dev/null || true
    cd ..
    
    # General: Any temp dirs (optional: add more as needed)
    rm -rf /tmp/scipher_* 2>/dev/null || true  # Temp files if used
    
    echo "✅ Caches cleared!"
}

# --- Backend startup ---
start_backend() {
    echo "📡 Starting FastAPI Backend..."
    cd backend

    # Activate venv if it exists (uv-compatible)
    if [ -d ".venv" ]; then
        echo "📦 Activating virtual environment..."
        source .venv/bin/activate
    fi

    # Install dependencies (prefer uv if available)
    if command -v uv &> /dev/null; then
        echo "📥 Installing Python dependencies via uv..."
        uv sync
    elif [ -f "requirements.txt" ]; then
        echo "📥 Installing Python dependencies via pip..."
        pip install -r requirements.txt
    fi

    echo "🚀 Starting backend server at http://localhost:8080"
    PYTHONPATH=src uvicorn main:app --reload --host 0.0.0.0 --port 8080 &
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend started (PID: $BACKEND_PID)"
}

# --- Web (Next.js) startup ---
start_web() {
    echo "🖥️  Starting Next.js Web Frontend..."
    cd Web

    if [ ! -d "node_modules" ]; then
        echo "📦 Installing Node.js dependencies..."
        npm install
    fi

    echo "🚀 Starting frontend server at http://localhost:3000"
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Web frontend started (PID: $FRONTEND_PID)"
}

# --- Cleanup handler ---
cleanup() {
    echo ""
    echo "🧹 Shutting down servers..."
    [ ! -z "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null && echo "✅ Backend stopped"
    [ ! -z "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null && echo "✅ Web frontend stopped"
    exit 0
}

# Catch termination signals
trap cleanup SIGINT SIGTERM

# --- Run startup sequence ---
clean_caches  # NEW: Clean caches before each startup/restart
start_backend
sleep 3  # small delay for backend to initialize
start_web

echo ""
echo "✨ Scipher is now running!"
echo "=========================="
echo "🔹 Backend API: http://localhost:8080"
echo "🔹 Docs:        http://localhost:8080/docs"
echo "🔹 Web UI:      http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers."
echo ""

wait
