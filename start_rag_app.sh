#!/bin/bash

# RAG App Launcher Script
# This script starts both backend and frontend servers

echo "🚀 Starting RAG Application..."
echo "================================"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down RAG Application..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ Application stopped"
    exit 0
}

# Set up trap to catch Ctrl+C
trap cleanup INT TERM

# Start Backend
echo "📦 Starting Backend (FastAPI)..."
cd "$SCRIPT_DIR/backend"
"$SCRIPT_DIR/backend/venv/bin/python" -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 > /tmp/rag_backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Backend URL: http://127.0.0.1:8000"

# Wait a moment for backend to start
sleep 2

# Start Frontend
echo ""
echo "🎨 Starting Frontend (Next.js)..."
cd "$SCRIPT_DIR/frontend"
npm run dev > /tmp/rag_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
echo "   Frontend URL: http://localhost:3000"

# Wait for frontend to be ready
sleep 3

echo ""
echo "✅ RAG Application is running!"
echo "================================"
echo "📊 Backend:  http://127.0.0.1:8000"
echo "🌐 Frontend: http://localhost:3000"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f /tmp/rag_backend.log"
echo "   Frontend: tail -f /tmp/rag_frontend.log"
echo ""
echo "Press Ctrl+C to stop all servers"
echo "================================"

# Open browser (optional - uncomment if you want auto-open)
sleep 2
open http://localhost:3000

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID
