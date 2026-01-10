#!/bin/bash
# Render.com start script for Rafiki.ai backend

echo "Starting Rafiki.ai backend on Render..."

# Change to backend directory
cd backend || exit 1

# Start uvicorn server
# PORT is provided by Render automatically
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
