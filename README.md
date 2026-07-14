# Rafiki.ai - Kenya Government Voice Assistant

A production-grade, accessible voice assistant helping citizens navigate Kenya government services via voice in **English**, **Kiswahili**, and **Mixed/Code-Switching**.

## 🎯 Features

### Core Voice Assistant
- 🎤 **Voice-based interaction** with speech recognition and text-to-speech
- 🤖 **AI-powered NLU** using Google Gemini with RAG (citations included)
- 🇰🇪 **Bilingual support** - English, Kiswahili, and code-switching
- 🗣️ **Talking avatar** with realistic lip-sync (SadTalker + Google Colab GPU)
- ⚡ **50-100x faster** video generation with T4 GPU acceleration

### Government Services Workflow Engine
- 📋 **7 Pre-built Workflows** for common government services:
  - NTSA Driving License appointment booking
  - KRA Nil Returns filing guidance
  - DCI Good Conduct Certificate application
  - Huduma Centre location finder
  - Constitutional knowledge Q&A
  - Feedback submission
  - Emergency reporting
- ✅ **Built-in validators** for Kenya-specific data:
  - Phone numbers (07xx, +254xx)
  - National ID (7-8 digits)
  - KRA PIN (A###########B format)
- 🔄 **State machine** with pause/resume/cancel support

### Security & Compliance
- 🔐 **Immutable audit logging** with SHA-256 hash chaining
- 🕵️ **PII auto-redaction** in logs
- 🚨 **Fraud detection** with rate limiting
- 📱 **SMS confirmations** via Africa's Talking

### Accessibility
- ♿ **WCAG 2.1 AA compliant** UI
- 📜 **Conversation history** with transcript downloads
- 🗺️ **Huduma Centre locator** with directions

## Architecture

```
Frontend (React/TypeScript)     Backend (FastAPI)           External Services
-------------------------       -----------------           -----------------
- Vite dev server               - REST API                  - Google Gemini AI
- Avatar components             - Workflow Engine           - ElevenLabs TTS
- useSadTalker hook             - RAG with ChromaDB         - Africa's Talking SMS
- Audio visualization           - Session management        - Google Colab GPU
- Emotion system                - Audit logging             - SadTalker API
                                - Maps service
```

## Prerequisites

- Python 3.10+ (for backend and SadTalker)
- Node.js 18+ (for frontend)
- espeak (for TTS fallback on Linux)
- Docker & Docker Compose (optional, for containerized deployment)
- Google Colab account (optional, for GPU acceleration)

## Quick Start

### Option 1: Docker Setup (Recommended)

```bash
# Clone repository
git clone https://github.com/Kelvin-Wepo/Rafiki.ai.git
cd Rafiki.ai

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
./start-docker.sh

# Stop all services
./stop-docker.sh
```

Services will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed Docker documentation.

### Option 2: Manual Setup

### Option 2: Manual Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/Kelvin-Wepo/Rafiki.ai.git
cd Rafiki.ai
```

#### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

#### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash-exp

# ElevenLabs TTS (optional - falls back to espeak)
ELEVENLABS_API_KEY=your-elevenlabs-api-key
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM

# Africa's Talking SMS (optional)
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your-api-key

# Google Colab GPU (optional - for fast video generation)
COLAB_SADTALKER_URL=https://your-ngrok-url.ngrok-free.app

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Optional: Redis for fraud detection
# If you want to use Redis to back the rate-limiting/blocklist store for
# OTP/fraud checks set:
# FRAUD_REDIS_URL=redis://localhost:6379/0
#
# Then, in your app startup (backend), create a redis client and wire the
# service example:
#
# from redis import Redis
# from services.fraud_service_redis import create_redis_fraud_service
# from services.fraud_service import set_fraud_service
#
# r = Redis.from_url(os.environ.get("FRAUD_REDIS_URL"))
# set_fraud_service(create_redis_fraud_service(r))
```

#### 4. Start Backend Server

```bash
cd backend
source ../.venv/bin/activate
python -m deactivate
```

> If you run from the repository root, use:
>
> ```bash
> source .venv/bin/activate
> python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
> ```
>
> If you still see `ModuleNotFoundError: No module named 'jose'`, reinstall the backend dependencies inside the same venv:
>
> ```bash
> .venv/bin/python -m pip install -r backend/requirements.txt
> ```

#### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 3: Google Colab GPU Setup (Fastest)

For 50-100x faster video generation, set up a free GPU backend:

1. **Open the Colab notebook**: [SadTalker_GPU_Colab.ipynb](./SadTalker_GPU_Colab.ipynb)
2. **Run all cells** (Setup → Install ngrok → Start Server)
3. **Copy the ngrok URL** from the output (e.g., `https://abc123.ngrok-free.app`)
4. **Update your `.env`**:
   ```env
   COLAB_SADTALKER_URL=https://your-ngrok-url.ngrok-free.app
   ```
5. **Restart your backend** to use the GPU

See [COLAB_SETUP_GUIDE.md](COLAB_SETUP_GUIDE.md) for detailed instructions.

**Performance Comparison:**
- CPU (local): 2-10 minutes per video
- GPU (Colab): 5-15 seconds per video (50-100x faster!)

## Project Structure

```
Rafiki.ai/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration with Colab support
│   ├── requirements.txt        # Python dependencies
│   ├── assets/
│   │   ├── avatars/            # Avatar images
│   │   └── avatar_cache/       # Cached generated videos
│   ├── routes/
│   │   ├── avatar_animation.py # Avatar video generation
│   │   ├── avatar.py           # Avatar management
│   │   ├── booking.py          # Appointment booking
│   │   ├── elevenlabs.py       # ElevenLabs TTS routes
│   │   ├── language.py         # Language detection
│   │   ├── services.py         # Government services
│   │   ├── session.py          # Session management
│   │   └── voice.py            # Voice processing
│   ├── services/
│   │   ├── colab_sadtalker_service.py  # Google Colab GPU client
│   │   ├── sadtalker_service.py        # Multi-backend orchestration
│   │   ├── sadtalker_direct.py         # Local CPU generation
│   │   ├── elevenlabs_service.py       # TTS with espeak fallback
│   │   ├── gemini_service.py           # Google Gemini AI
│   │   ├── intent_service.py           # Intent detection
│   │   ├── language_service.py         # Language processing
│   │   ├── sms_service.py              # Africa's Talking SMS
│   │   └── voice_service.py            # Speech recognition
│   └── utils/
│       ├── logger.py           # Logging configuration
│       ├── rate_limiter.py     # API rate limiting
│       └── session_manager.py  # Session handling
│
├── frontend/
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.ts          # Vite configuration
│   ├── Dockerfile              # Frontend container
│   └── src/
│       ├── App.tsx             # Main React component
│       ├── components/
│       │   ├── RafikiIntegrationDemo.tsx  # Demo page
│       │   └── avatar/
│       │       ├── RafikiTalkingAvatar.tsx    # Video + image hybrid
│       │       ├── RafikiImageAvatar.tsx      # Pure image with effects
│       │       └── index.ts                   # Component exports
│       ├── hooks/
│       │   ├── useSadTalker.ts    # Backend communication
│       │   ├── useBlinking.ts     # Natural blinking
│       │   ├── useEmotions.ts     # Emotion management
│       │   ├── useBreathing.ts    # Breathing animation
│       │   └── index.ts           # Hook exports
│       ├── assets/
│       │   └── rafiki_avatar.png  # Base avatar image
│       └── types/
│           └── avatar.types.ts    # TypeScript definitions
│
├── SadTalker/                  # SadTalker submodule (for local CPU)
│   ├── checkpoints/            # Model weights
│   ├── src/                    # SadTalker source code
│   └── inference.py            # Video generation script
│
├── docker-compose.yml          # Multi-container orchestration
├── Dockerfile                  # Backend container
├── start-docker.sh             # Docker startup script
├── stop-docker.sh              # Docker shutdown script
├── SadTalker_GPU_Colab.ipynb   # Google Colab GPU notebook
├── .env.example                # Environment template
├── README.md                   # This file
├── DOCKER_SETUP.md             # Docker documentation
├── COLAB_SETUP_GUIDE.md        # Colab GPU setup guide
├── SADTALKER_TROUBLESHOOTING.md # Troubleshooting guide
└── API_DOCS.md                 # API documentation
```

## Avatar System

The Rafiki avatar uses a **multi-backend architecture** for optimal performance:

### 1. Google Colab GPU (Fastest - Recommended)
- **Speed**: 5-15 seconds per video
- **Quality**: High-quality lip-sync
- **Cost**: Free (Google Colab)
- **Setup**: See [COLAB_SETUP_GUIDE.md](COLAB_SETUP_GUIDE.md)

### 2. Local CPU (Slow but Reliable)
- **Speed**: 2-10 minutes per video
- **Quality**: Same as GPU
- **Cost**: Free (local compute)
- **Setup**: Automatic (requires SadTalker models)

### 3. Audio-Only Fallback
- **Speed**: Instant
- **Quality**: Audio-only (no video)
- **Cost**: Free
- **Setup**: Automatic

The system automatically tries backends in this order:
1. Colab GPU (if `COLAB_SADTALKER_URL` is set)
2. Local CPU (if models are available)
3. Audio-only (always works)

### Frontend Avatar Components

#### RafikiTalkingAvatar
Hybrid component that shows:
- **Idle/Listening**: Animated image with effects (particles, waveform, breathing)
- **Speaking with video**: SadTalker lip-synced video
- **Speaking without video**: Animated image with mouth animation

#### RafikiImageAvatar
Pure image-based avatar with:
- Natural blinking animation
- Eye tracking (follows cursor)
- Breathing effect
- Emotion system (happy, sad, surprised, neutral)
- Particle effects
- Voice waveform visualization

### API Endpoints

#### Generate Video from Text
```http
POST /api/avatar/text-to-video
Content-Type: multipart/form-data

Parameters:
  text: string           # Text to speak (max 2000 chars)
  avatar_id: string      # Avatar ID (default: rafiki_avatar)
  language: string       # Language code (default: en)
  use_elevenlabs: bool   # Use ElevenLabs TTS (default: true)
  personality: string    # friendly, professional, excited, calm

Response: 
  - MP4 video (if SadTalker available)
  - MP3 audio (fallback mode)
  
Headers:
  X-Generation-Method: colab-gpu | cpu | audio-only
  X-Generation-Time: <seconds>
```

#### Generate Video from Audio
```http
POST /api/avatar/animate
Content-Type: multipart/form-data

Parameters:
  audio_file: File       # WAV, MP3, or OGG (max 50MB)
  avatar_id: string      # Avatar ID
  preprocess: string     # crop, resize, or full
  still_mode: boolean    # Only animate mouth
  expression_scale: float # 0.0-2.0

Response: MP4 video or error
```

#### List Avatars
```http
GET /api/avatar/avatars

Response:
{
  "success": true,
  "avatars": [
    {
      "id": "rafiki_avatar",
      "name": "Rafiki Avatar",
      "path": "/assets/avatars/rafiki_avatar.png"
    }
  ]
}
```

#### Avatar Health Check
```http
GET /api/avatar/health

Response:
{
  "status": "healthy",
  "service": "avatar-animation",
  "mode": "multi-backend",
  "sadtalker_available": false,
  "colab_available": true,
  "avatars": [...],
  "cache_stats": {
    "cached_videos": 5,
    "total_size_mb": 12.3
  }
}
```

#### Clear Cache
```http
POST /api/avatar/cache/clear

Response:
{
  "success": true,
  "message": "Cache cleared",
  "freed_mb": 12.3
}
```

## Frontend Usage

### Basic Usage

```tsx
import { RafikiTalkingAvatar } from './components/avatar';
import { useSadTalker } from './hooks';

function App() {
  const {
    generateFromText,
    currentVideoUrl,
    currentAudioUrl,
    isFallbackMode,
    isGenerating,
    error
  } = useSadTalker({
    backendUrl: 'http://localhost:8000',
    avatarId: 'rafiki_avatar'
  });

  const handleSpeak = () => {
    generateFromText('Hello! Welcome to Rafiki AI assistant.');
  };

  return (
    <div>
      <RafikiTalkingAvatar
        state={isGenerating ? 'thinking' : 'idle'}
        videoUrl={currentVideoUrl}
        audioUrl={currentAudioUrl}
        size={400}
        showParticles={true}
        showWaveform={true}
      />
      <button onClick={handleSpeak}>Speak</button>
      {error && <p>Error: {error}</p>}
    </div>
  );
}
```

### Avatar States

- `idle` - Default state with subtle animations
- `listening` - Pulsing effect, active waveform
- `thinking` - Orbiting particles
- `speaking` - Video playback or animated mouth
- `error` - Red glow, shaking effect

## TTS System

The backend uses a **fallback chain** for text-to-speech:

1. **ElevenLabs API** (preferred)
   - High-quality voices
   - Kenyan accents available (Noah, Aria)
   - Requires API key

2. **espeak** (fallback)
   - Free, local TTS
   - Robotic voice
   - Works offline

Install espeak on Ubuntu/Debian:
```bash
sudo apt install espeak
```

The system automatically falls back to espeak on:
- 401 errors (quota exceeded)
- 404 errors (voice not found)
- Connection failures

## Accessibility

- Voice control for navigation
- Screen reader support with ARIA labels
- High contrast mode
- Full keyboard navigation
- Adjustable text sizes
- Multi-language support (English, Swahili)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Tab | Navigate forward |
| Shift + Tab | Navigate backward |
| Enter / Space | Activate button |
| Escape | Close dialog |
| Arrow keys | Navigate menus |

## Development

### Running Tests

```bash
# Backend integration tests
cd backend
python test_integration.py

# Test avatar generation
python test_sadtalker_quick.py

# Test Colab GPU connection
python test_colab_avatar.py

# Frontend type checking
cd frontend
npm run lint
npm run type-check
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes | - |
| `GEMINI_MODEL` | Gemini model name | No | `gemini-2.0-flash-exp` |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS key | No | Falls back to espeak |
| `ELEVENLABS_VOICE_ID` | Voice ID | No | `21m00Tcm4TlvDq8ikWAM` |
| `AFRICASTALKING_USERNAME` | SMS username | For SMS | `sandbox` |
| `AFRICASTALKING_API_KEY` | SMS API key | For SMS | - |
| `COLAB_SADTALKER_URL` | Colab ngrok URL | For GPU | - |
| `HOST` | Server host | No | `0.0.0.0` |
| `PORT` | Server port | No | `8000` |
| `DEBUG` | Debug mode | No | `false` |

## Docker Deployment

### Quick Start

```bash
# Start all services
./start-docker.sh

# View logs
docker-compose logs -f

# Stop services
./stop-docker.sh
```

### Manual Docker Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

See [DOCKER_SETUP.md](DOCKER_SETUP.md) for detailed documentation.

## Render.com Deployment

Deploy Rafiki.ai to Render.com for production hosting:

**Quick Deploy:**
1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New +" → "Blueprint"
4. Connect your repository
5. Add environment variables
6. Deploy!

See [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for complete deployment guide.

**What you get:**
- Free hosting (with limitations)
- Automatic HTTPS
- Auto-deploy on git push
- Built-in monitoring
- Global CDN

## Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.10+ required)
- Verify all dependencies installed: `pip install -r requirements.txt`
- Check logs: `tail -f /tmp/backend.log`

**Video generation is slow:**
- Use Google Colab GPU (50-100x faster)
- See [COLAB_SETUP_GUIDE.md](COLAB_SETUP_GUIDE.md)

**SadTalker errors:**
- Check [SADTALKER_TROUBLESHOOTING.md](SADTALKER_TROUBLESHOOTING.md)
- Verify models are downloaded
- Check CUDA/GPU availability

**Frontend can't connect to backend:**
- Verify backend is running: `curl http://localhost:8000/health`
- Check CORS settings in backend/config.py
- Verify ports are not blocked

## Workflow Engine API

The workflow engine provides step-by-step guidance for government services.

### Available Workflows

| Workflow ID | Service | Agency |
|-------------|---------|--------|
| `ntsa_driving_license` | Driving License Appointment | NTSA |
| `kra_nil_returns` | Nil Returns Filing | KRA |
| `dci_good_conduct` | Good Conduct Certificate | DCI |
| `huduma_centre_lookup` | Find Nearest Huduma Centre | Huduma Kenya |
| `constitution_query` | Constitutional Knowledge Q&A | - |
| `feedback_submission` | Submit Feedback | - |
| `emergency_report` | Report Emergency | - |

### Workflow API Endpoints

```bash
# List all workflows
GET /api/workflows/

# Start a workflow
POST /api/workflows/start
{
  "workflow_id": "ntsa_driving_license",
  "session_id": "user-session-123",
  "language": "en"  # or "sw" for Kiswahili
}

# Process user input
POST /api/workflows/input
{
  "execution_id": "exec-uuid",
  "input": "John Doe",
  "session_id": "user-session-123"
}

# Pause/Resume/Cancel
POST /api/workflows/execution/{execution_id}/pause
POST /api/workflows/execution/{execution_id}/resume
DELETE /api/workflows/execution/{execution_id}
```

### Example Conversation

```
User: I want to book a driving license appointment
Bot: Welcome to NTSA driving license appointment booking. 
     Please tell me your full name as it appears on your National ID.
User: John Kamau Mwangi
Bot: Thank you John. Please provide your 7 or 8 digit National ID number.
User: 12345678
Bot: Got it. Please provide your phone number for SMS confirmation.
User: 0712345678
Bot: Great! I have the following details:
     Name: John Kamau Mwangi
     ID: 12345678
     Phone: 0712345678
     Please confirm (Yes/No)
User: Yes
Bot: ✅ Appointment booked! You'll receive SMS confirmation shortly.
     Reference: NTSA-2024-0001
```

## Running Tests

```bash
cd backend
source ../.venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_workflows.py -v  # Workflow engine tests (23 tests)
python -m pytest tests/test_audit.py -v       # Audit service tests (18 tests)
python -m pytest tests/test_maps.py -v        # Maps service tests (19 tests)

# Run with coverage (requires pytest-cov)
pip install pytest-cov
python -m pytest tests/ --cov=. --cov-report=html
```

## Documentation

- [API_DOCS.md](API_DOCS.md) - Complete API documentation
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Docker deployment guide
- [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) - Render.com deployment guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Pre-deployment checklist
- [COLAB_SETUP_GUIDE.md](COLAB_SETUP_GUIDE.md) - GPU acceleration setup
- [SADTALKER_TROUBLESHOOTING.md](SADTALKER_TROUBLESHOOTING.md) - Troubleshooting guide
- [HISTORY_TRANSCRIPTS_FEATURE.md](HISTORY_TRANSCRIPTS_FEATURE.md) - Conversation history & transcript download feature documentation
- [USER_GUIDE_HISTORY_TRANSCRIPTS.md](USER_GUIDE_HISTORY_TRANSCRIPTS.md) - User guide for history and transcript features
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Summary of implementation details

## Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Add tests for new features
- Update documentation
- Keep commits atomic and descriptive

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- [SadTalker](https://github.com/OpenTalker/SadTalker) - Talking head animation
- [Google Gemini](https://ai.google.dev/) - AI language model
- [ElevenLabs](https://elevenlabs.io/) - Text-to-speech
- [FastAPI](https://fastapi.tiangolo.com/) - Backend framework
- [React](https://react.dev/) - Frontend framework

## Support

- Email: support@rafiki.ai
- Issues: [GitHub Issues](https://github.com/Kelvin-Wepo/Rafiki.ai/issues)
- Discussions: [GitHub Discussions](https://github.com/Kelvin-Wepo/Rafiki.ai/discussions)

---

Made with love in Kenya
