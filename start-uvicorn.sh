#!/bin/bash
# Start Rafiki.ai Backend with uvicorn

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"

echo "🚀 Starting Rafiki.ai Backend..."
echo "📍 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo ""

/home/subchief/Rafiki.ai/venv/bin/uvicorn backend.main:app \
  --reload \
  --host 0.0.0.0 \
  --port 8000 \
  --log-level info
