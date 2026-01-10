#!/bin/bash

# Rafiki AI - Docker Quick Start Script

set -e

echo "🚀 Rafiki AI - Docker Setup"
echo "============================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    echo "Please install Docker Compose"
    exit 1
fi

echo "✅ Docker and Docker Compose detected"
echo ""

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
DIALOGFLOW_PROJECT_ID=your_dialogflow_project_id

# Twilio (for SMS)
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_PHONE_NUMBER=your_twilio_phone

# SadTalker GPU Server (Google Colab)
# Leave empty to use audio-only mode
COLAB_SADTALKER_URL=
EOF
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with your API keys!"
    echo "   Run: nano .env"
    echo ""
    read -p "Press Enter after you've added your API keys..."
fi

# Check if service-account.json exists
if [ ! -f backend/service-account.json ]; then
    echo "⚠️  Warning: backend/service-account.json not found"
    echo "   Dialogflow features will not work without it"
    echo ""
fi

# Build and start
echo "🔨 Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting Rafiki AI..."
docker-compose up -d

echo ""
echo "✅ Rafiki AI is starting!"
echo ""
echo "📍 Access points:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check if backend is up
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is running!"
else
    echo "⚠️  Backend might still be starting. Check logs: docker-compose logs backend"
fi

echo ""
echo "🎉 Setup complete! Open http://localhost:5173 in your browser"
echo ""
echo "💡 To use GPU acceleration:"
echo "   1. Open SadTalker_GPU_Colab.ipynb in Google Colab"
echo "   2. Run all cells to get ngrok URL"
echo "   3. Update COLAB_SADTALKER_URL in .env"
echo "   4. Run: docker-compose restart backend"
