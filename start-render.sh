#!/bin/bash
# Render.com start script for Rafiki.ai backend

echo "Starting Rafiki.ai backend on Render..."

# Change to backend directory
cd backend || exit 1

# Start uvicorn server
# PORT is provided by Render automatically.
# Do NOT pass --forwarded-allow-ips="*": uvicorn would then believe any client-sent
# X-Forwarded-For and per-IP rate limits could be dodged by spoofing it. The real
# client IP is read in utils/rate_limit_dep.client_ip from Cloudflare's header.
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
