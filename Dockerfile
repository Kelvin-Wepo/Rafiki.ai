# Rafiki AI - Production Backend for Render
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (minimal for production)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy production requirements
COPY backend/requirements-prod.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy backend code
COPY backend/ ./backend/
COPY app.py .

# Create necessary directories
RUN mkdir -p backend/assets/avatars backend/assets/avatar_cache

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
ENV PORT=8000

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application from backend directory
WORKDIR /app/backend
CMD uvicorn main:app --host 0.0.0.0 --port $PORT
