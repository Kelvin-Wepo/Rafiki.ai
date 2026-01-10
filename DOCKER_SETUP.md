# 🚀 Rafiki AI - Docker Setup

This guide will help you run Rafiki AI using Docker for a clean, isolated environment.

## Prerequisites

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)
- Your API keys ready

## Quick Start

### 1. Clone and Setup Environment

```bash
# Create .env file from example
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Configuration

### Talking Avatar Modes

Edit `.env` to configure SadTalker:

#### Option 1: Google Colab GPU (Recommended - Fast!)
```bash
COLAB_SADTALKER_URL=https://xxxx.ngrok.io  # From your Colab notebook
```
- **Speed**: 5-15 seconds per video
- **Quality**: High
- **Requirements**: Run SadTalker_GPU_Colab.ipynb in Google Colab

#### Option 2: Audio-Only Mode (Default)
```bash
COLAB_SADTALKER_URL=
```
- **Speed**: Instant
- **Quality**: No video, just audio with static avatar
- **Requirements**: None

## Docker Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose up --build
```

### Clean Everything
```bash
docker-compose down -v
docker system prune -a
```

## Troubleshooting

### Missing Dependencies
Docker handles all dependencies automatically. If you see import errors:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Port Already in Use
Change ports in `docker-compose.yml`:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

### Service Account
Place your `service-account.json` in `backend/` directory before building.

## Using with Google Colab GPU

1. **Start Colab Notebook**:
   - Open `SadTalker_GPU_Colab.ipynb` in Google Colab
   - Run all cells
   - Copy the ngrok URL (e.g., `https://xxxx.ngrok.io`)

2. **Update Docker Environment**:
   ```bash
   # Edit .env
   COLAB_SADTALKER_URL=https://xxxx.ngrok.io
   
   # Restart backend
   docker-compose restart backend
   ```

3. **Test It**:
   ```bash
   curl http://localhost:8000/api/avatar/status
   ```

## Production Deployment

For production, consider:

1. **Use nginx** instead of dev server for frontend
2. **Add SSL/TLS** certificates
3. **Use secrets management** (AWS Secrets, Azure Key Vault)
4. **Scale with Kubernetes** or Docker Swarm

## Benefits of Docker for Rafiki AI

✅ **Isolated Environment**: No conflicts with system packages
✅ **Consistent Setup**: Works same on all machines
✅ **Easy Deployment**: Single command to start everything
✅ **Clean Uninstall**: Remove containers without affecting system
✅ **Fast Recovery**: Rebuild from scratch in minutes
✅ **Production Ready**: Same setup for dev and production

## Architecture

```
┌─────────────────┐
│   Frontend      │  (React + Vite)
│   Port 5173     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Backend       │  (FastAPI)
│   Port 8000     │
└────────┬────────┘
         │
         ├─→ ElevenLabs API (Voice)
         ├─→ Gemini API (Chat/Personality)
         ├─→ Dialogflow (Intent)
         └─→ Colab GPU (SadTalker - Optional)
```

## Next Steps

1. ✅ Start Docker containers
2. ✅ Test API: http://localhost:8000/docs
3. ✅ Open frontend: http://localhost:5173
4. 🚀 (Optional) Start Colab GPU for fast video generation
5. 🎉 Create your first talking avatar!

Need help? Check the logs: `docker-compose logs -f`
