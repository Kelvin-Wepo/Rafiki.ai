#!/bin/bash
# Rafiki.ai - Backend Start Script
# Starts backend server with all services (TTS, Dialogflow, ElevenLabs)
# Run from project root: ./start.sh

set -e  # Exit on error

echo "🚀 Starting Rafiki.ai Backend..."
echo "========================================"

# Navigate to project root
cd "$(dirname "$0")"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
if [ -d "sadtalker" ]; then
    source sadtalker/bin/activate
else
    echo "❌ Virtual environment not found. Run: python3 -m venv sadtalker"
    exit 1
fi

# Set Google Cloud credentials for Dialogflow
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/backend/service-account.json"
echo "🔐 Google Cloud credentials configured"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found in project root"
    echo "   Copy .env.example to .env and configure your API keys"
fi

echo ""
echo "🌐 Starting uvicorn server on http://0.0.0.0:8000"
echo "📚 API docs: http://localhost:8000/docs"
echo "🏥 Health check: http://localhost:8000/health"
echo ""
echo "✅ Services enabled:"
echo "   - Google Gemini AI"
echo "   - Dialogflow (conversation management)"
echo "   - ElevenLabs TTS (natural voice)"
echo "   - Speech Recognition"
echo "   - SadTalker Avatar Animation"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Navigate to backend and start server
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

