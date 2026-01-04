#!/bin/bash

# Avatar Studio - Quick Start Script
# Starts both backend and frontend servers

echo "🎬 African Avatar Studio - Quick Start"
echo "========================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node
if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found. Please install Node.js 16+"
    exit 1
fi

# Set API Key
read -p "Enter your GEMINI_API_KEY (press Enter to skip): " GEMINI_KEY
if [ -n "$GEMINI_KEY" ]; then
    export GEMINI_API_KEY=$GEMINI_KEY
fi

echo ""
echo "Starting Backend Server..."
echo "cd backend && python3 -m uvicorn main:app --reload"
cd backend &
BACKEND_PID=$!
sleep 3

echo ""
echo "Starting Frontend Server..."
echo "cd frontend && npm install && npm start"
cd ../frontend &
FRONTEND_PID=$!

echo ""
echo "✅ Servers starting..."
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Keep script running
wait
