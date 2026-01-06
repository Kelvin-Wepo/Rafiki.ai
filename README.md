# Rafiki.ai - eCitizen Voice Assistant

A voice-powered AI assistant for Kenya's eCitizen government services platform. Features natural language understanding, talking avatar animation, and accessible design for all users.

## Features

- Voice-based interaction with speech recognition and text-to-speech
- AI-powered natural language understanding using Google Gemini
- Talking avatar with lip-sync animation (SadTalker integration)
- SMS notifications via Africa's Talking
- Accessible UI with WCAG 2.1 AA compliance
- Support for multiple government services (Passport, ID, Driving License, etc.)

## Architecture

```
Frontend (React/TypeScript)     Backend (FastAPI)           External Services
-------------------------       -----------------           -----------------
- Vite dev server               - REST API                  - Google Gemini AI
- Avatar components             - Session management        - ElevenLabs TTS
- useSadTalker hook             - TTS with fallback         - Africa's Talking SMS
- Audio visualization           - SadTalker integration     - SadTalker API
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- espeak (for TTS fallback on Linux)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/Kelvin-Wepo/Rafiki.ai.git
cd Rafiki.ai
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp ../.env.example ../.env
# Edit .env with your API keys
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# ElevenLabs TTS (optional - falls back to espeak)
ELEVENLABS_API_KEY=your-elevenlabs-api-key

# Africa's Talking SMS
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your-api-key
```

### 4. Start Backend Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
Rafiki.ai/
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Configuration management
│   ├── requirements.txt        # Python dependencies
│   ├── assets/
│   │   └── avatars/            # Avatar images
│   ├── routes/
│   │   ├── avatar_animation.py # Avatar video generation
│   │   ├── booking.py          # Appointment booking
│   │   ├── elevenlabs.py       # ElevenLabs TTS routes
│   │   ├── services.py         # Government services
│   │   ├── session.py          # Session management
│   │   └── voice.py            # Voice processing
│   ├── services/
│   │   ├── elevenlabs_service.py   # TTS with espeak fallback
│   │   ├── gemini_service.py       # Google Gemini AI
│   │   ├── sadtalker_service.py    # Avatar animation
│   │   ├── sms_service.py          # Africa's Talking SMS
│   │   └── voice_service.py        # Speech recognition
│   └── utils/
│       ├── logger.py           # Logging configuration
│       ├── rate_limiter.py     # API rate limiting
│       └── session_manager.py  # Session handling
│
├── frontend/
│   ├── package.json            # Node.js dependencies
│   ├── vite.config.ts          # Vite configuration
│   └── src/
│       ├── App.tsx             # Main React component
│       ├── components/
│       │   ├── RafikiIntegrationDemo.tsx  # Demo page
│       │   └── avatar/
│       │       ├── RafikiSadTalkerAvatar.tsx  # SadTalker video player
│       │       ├── RafikiImageAvatar.tsx      # SVG animated fallback
│       │       └── index.ts                   # Component exports
│       ├── hooks/
│       │   ├── useSadTalker.ts    # Backend communication
│       │   ├── useBlinking.ts     # Natural blinking
│       │   ├── useEmotions.ts     # Emotion management
│       │   └── index.ts           # Hook exports
│       └── types/
│           └── avatar.types.ts    # TypeScript definitions
│
├── .env.example                # Environment template
└── README.md                   # This file
```

## Avatar System

The Rafiki avatar supports two modes:

### Video Mode (SadTalker)
When SadTalker API is available, generates lip-synced video from text or audio.

### Fallback Mode (SVG Animation)
When SadTalker is unavailable, displays an animated SVG avatar with:
- Natural blinking
- Eye tracking (follows cursor)
- Emotion expressions
- Audio-synced waveform visualization

### API Endpoints

#### Generate Video from Text
```
POST /api/avatar/text-to-video
Content-Type: multipart/form-data

Parameters:
  text: string           # Text to speak
  avatar_id: string      # Avatar ID (default: rafiki_avatar)
  language: string       # Language code (default: en)
  use_elevenlabs: bool   # Use ElevenLabs TTS (default: true)

Response: MP4 video or MP3 audio (fallback)
```

#### Generate Video from Audio
```
POST /api/avatar/animate
Content-Type: multipart/form-data

Parameters:
  audio_file: File       # WAV, MP3, or OGG
  avatar_id: string      # Avatar ID
  preprocess: string     # crop, resize, or full
  still_mode: boolean    # Only animate mouth
  expression_scale: float # 0.0-2.0

Response: MP4 video
```

#### List Avatars
```
GET /api/avatar/avatars

Response:
{
  "success": true,
  "avatars": [
    {"id": "rafiki_avatar", "name": "Rafiki Avatar", "path": "..."}
  ]
}
```

#### Health Check
```
GET /api/avatar/health

Response:
{
  "status": "healthy",
  "sadtalker_available": false,
  "avatars": [...]
}
```

## Frontend Usage

```tsx
import { RafikiSadTalkerAvatar } from './components/avatar';
import { useSadTalker } from './hooks';

function App() {
  const {
    generateFromText,
    currentVideoUrl,
    currentAudioUrl,
    isFallbackMode,
    isGenerating
  } = useSadTalker({
    backendUrl: 'http://localhost:8000',
    avatarId: 'rafiki_avatar'
  });

  return (
    <RafikiSadTalkerAvatar
      videoUrl={currentVideoUrl}
      audioUrl={currentAudioUrl}
      isFallbackMode={isFallbackMode}
      isGenerating={isGenerating}
      status="idle"
    />
  );
}
```

## TTS Fallback

The backend automatically falls back to espeak when ElevenLabs is unavailable:

1. Tries ElevenLabs API first
2. On 401/404 errors, falls back to local espeak
3. Returns WAV audio that works with the frontend

Install espeak on Ubuntu/Debian:
```bash
sudo apt install espeak
```

## Accessibility

- Voice control for navigation
- Screen reader support with ARIA labels
- High contrast mode
- Keyboard navigation
- Adjustable text sizes

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Tab | Navigate forward |
| Shift + Tab | Navigate backward |
| Enter / Space | Activate button |
| Escape | Close dialog |

## Development

### Running Tests

```bash
# Backend tests
cd backend
python test_integration.py

# Frontend type checking
cd frontend
npm run lint
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GEMINI_API_KEY | Google Gemini API key | Yes |
| ELEVENLABS_API_KEY | ElevenLabs TTS key | No (fallback to espeak) |
| AFRICASTALKING_USERNAME | SMS username | For SMS features |
| AFRICASTALKING_API_KEY | SMS API key | For SMS features |
| SADTALKER_API_URL | SadTalker API URL | No (default: localhost:7860) |

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
