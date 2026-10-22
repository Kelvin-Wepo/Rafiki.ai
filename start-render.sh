#!/bin/bash
# Render.com start script for Rafiki.ai backend

echo "Starting Rafiki.ai backend on Render..."

# Change to backend directory
cd backend || exit 1

# Start uvicorn server
# PORT is provided by Render automatically.
# Render terminates TLS in its own proxy, so trust X-Forwarded-For; otherwise
# every visitor looks like the proxy IP and per-IP rate limits are shared by all.
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 \
  --proxy-headers --forwarded-allow-ips="*"
