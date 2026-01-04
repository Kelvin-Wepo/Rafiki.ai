# eCitizen Voice Assistant 🇰🇪

 

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-green.svg)
![React](https://img.shields.io/badge/react-18.0+-blue.svg)

## 🎯 Features

- **Voice Interaction**: Full voice-based navigation using speech recognition and text-to-speech
- **AI-Powered**: Natural language understanding with Google Gemini API
- **Conversation Management**: Contextual conversations using Dialogflow
- **SMS Notifications**: Appointment confirmations via Africa's Talking
- **Accessible UI**: High-contrast mode, large buttons, ARIA labels, keyboard navigation
- **Multi-Service Support**: Passport, ID, Driving License, Good Conduct certificates
- **🎬 Talking Avatar**: AI-powered animated avatar using SadTalker & Imagen for realistic conversations
- **😊 Avatar Customization**: Personalized avatar with skin tone, hair, clothing, and expression options
- **🎤 Real-time Audio-to-Video**: Convert audio to lip-synced talking head videos

## 🏗️ Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React App     │────▶│   FastAPI       │────▶│   Google        │
│   (Frontend)    │     │   (Backend)     │     │   Gemini AI     │
│                 │     │                 │     │                 │
│ • Voice Input   │     │ • Voice Process │     │ • NLU           │
│ • Accessible UI │     │ • Session Mgmt  │     │ • Intent        │
│ • Chat Interface│     │ • Booking Logic │     │ • Response Gen  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Africa's       │
                        │  Talking SMS    │
                        │                 │
                        │ • Confirmations │
                        │ • Reminders     │
                        └─────────────────┘
```

## 📋 Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn
- Google Cloud account (for Gemini API and Dialogflow)
- Africa's Talking account (for SMS)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ecitizen-voice-assistant.git
cd ecitizen-voice-assistant
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp ../.env.example ../.env

# Edit .env with your API keys
nano ../.env
```

### 3. Configure Environment Variables

Edit the `.env` file with your actual credentials:

```env
# Google Gemini API
GEMINI_API_KEY=your-gemini-api-key

# Dialogflow
DIALOGFLOW_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json

# Africa's Talking
AFRICASTALKING_USERNAME=sandbox
AFRICASTALKING_API_KEY=your-api-key
```

### 4. Start Backend Server

```bash
# From the backend directory
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Start development server
npm start
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🎬 Avatar System (Rafiki)

The Rafiki AI assistant features a realistic talking avatar system using SadTalker and Imagen:

### Features

- **Realistic Animation**: AI-powered lip-sync from audio using SadTalker
- **Image Generation**: Create avatars using Imagen 3 with customization
- **Real-time Processing**: Generate talking videos from audio or text
- **Caching**: Automatic caching of animations for faster response
- **GPU Acceleration**: CUDA support for 4-6x faster generation
- **Web Integration**: React component with full video player controls
- **Customization**: Configurable expression scale, head movement, preprocessing

### Avatar Generation Workflow

```
┌──────────────────┐
│ Generate Avatar  │
│ with Imagen 3    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Preprocess Image │
│ • Face Detection │
│ • Alignment      │
│ • Optimization   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Get Audio Input  │
│ • ElevenLabs TTS │
│ • User recording │
│ • Pre-recorded   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Generate Video   │
│ SadTalker        │
│ Animation        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Display on Web   │
│ RafikiAvatar     │
│ Component        │
└──────────────────┘
```

### Quick Start - Avatar System

```bash
# 1. Clone SadTalker repository
git clone https://github.com/OpenTalker/SadTalker.git

# 2. Download pre-trained models
cd SadTalker
python scripts/download_checkpoint.py

# 3. Install avatar dependencies
cd ../backend
pip install -r requirements.txt

# 4. Set environment variables
export SADTALKER_MODE=local
export SADTALKER_DEVICE=cuda  # or 'cpu'

# 5. Start backend
python -m uvicorn main:app --reload

# 6. Use API to generate videos
curl -X POST http://localhost:8000/api/avatar/animate \
  -F "audio_file=@audio.wav" \
  -F "avatar_id=habari"
```

### API Endpoints

#### Generate Avatar from Audio
```
POST /api/avatar/animate
Content-Type: multipart/form-data

Parameters:
  audio_file: File       # WAV, MP3, OGG
  avatar_id: string      # Avatar ID (default: 'habari')
  preprocess: string     # 'crop', 'resize', 'full'
  still_mode: boolean    # Only animate mouth
  expression_scale: float # 0.0-2.0 (default: 1.0)

Response: MP4 video file
```

#### Generate from Text
```
POST /api/avatar/text-to-video
Content-Type: application/x-www-form-urlencoded

Parameters:
  text: string           # Text to speak
  avatar_id: string      # Avatar ID
  language: string       # Language code (default: 'en')
  use_elevenlabs: boolean # Use ElevenLabs TTS

Response: MP4 video file
```

#### Get Available Avatars
```
GET /api/avatar/avatars

Response:
{
  "success": true,
  "avatars": [
    {
      "id": "habari",
      "name": "Habari",
      "path": "/assets/avatars/habari.png"
    }
  ]
}
```

#### Preprocess Image
```
POST /api/avatar/preprocess-image
Content-Type: multipart/form-data

Parameters:
  image_file: File      # Avatar image
  output_format: string # 'jpeg' or 'png'
  quality: integer      # 1-100 (for JPEG)

Response: Processed image file
```

#### Manage Settings
```
GET /api/avatar/settings           # Get current settings
POST /api/avatar/settings          # Update settings
GET /api/avatar/cache/stats        # Cache statistics
POST /api/avatar/cache/clear       # Clear cache
GET /api/avatar/health             # Health check
```

### React Component Usage

```jsx
import RafikiAvatar from './components/RafikiAvatar';

function ChatBot() {
  const [audioFile, setAudioFile] = useState(null);

  return (
    <div className="chatbot">
      <RafikiAvatar
        audioStream={audioFile}
        avatarId="habari"
        onLoadingChange={(isLoading) => console.log(isLoading)}
        onError={(error) => console.error(error)}
        autoPlay={true}
        showControls={true}
      />

      <input
        type="file"
        accept="audio/*"
        onChange={(e) => setAudioFile(e.target.files[0])}
      />
    </div>
  );
}
```

### Avatar Customization

The avatar supports the following customizations:

```javascript
const avatarConfig = {
  name: 'Rafiki',
  skin_tone: 'dark',              // light, medium, dark
  hair_style: 'natural',          // natural, braids, twists, straight
  clothing: 'professional_suit',  // professional_suit, traditional, casual, formal
  personality: 'warm_friendly',   // warm_friendly, professional, patient, encouraging
  background: 'office',           // office, traditional, neutral, government
  language: 'en-KE'               // en-KE, en-US, en-GB, sw-KE
};
```

### Performance Settings

Configure animation quality and speed:

```python
# Fast (CPU-friendly)
service.update_settings(
    still_mode=True,           # No head movement
    preprocess='crop',         # Minimal processing
    expression_scale=0.8,      # Subtle expressions
    pose_style=0               # Neutral pose
)

# Balanced
service.update_settings(
    still_mode=False,
    preprocess='full',
    expression_scale=1.0,
    pose_style=2
)

# High-quality (GPU recommended)
service.update_settings(
    still_mode=False,
    preprocess='full',
    expression_scale=1.2,
    pose_style=4
)
```

### Troubleshooting Avatar Issues

**Common Issues and Solutions**:

| Issue | Cause | Solution |
|-------|-------|----------|
| "No face detected" | Image quality or face too small | Regenerate with centered, clear face |
| Poor lip sync | Low audio quality | Use high-quality audio (16kHz+) |
| Slow generation | Using CPU | Use GPU: `SADTALKER_DEVICE=cuda` |
| Unnatural movements | Poor settings | Adjust `expression_scale` or `pose_style` |
| CUDA out of memory | Large video | Process shorter audio clips |

For detailed troubleshooting, see [SADTALKER_SETUP.md](./SADTALKER_SETUP.md).

## 📁 Project Structure

```
5TECH/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── requirements.txt     # Python dependencies
│   ├── models/
│   │   └── schemas.py       # Pydantic data models
│   ├── routes/
│   │   ├── voice.py         # Voice processing endpoints
│   │   ├── booking.py       # Appointment booking endpoints
│   │   ├── services.py      # Government services endpoints
│   │   ├── session.py       # Session management endpoints
│   │   ├── avatar_animation.py  # Avatar animation endpoints
│   │   └── avatar.py        # Avatar customization endpoints
│   ├── services/
│   │   ├── gemini_service.py        # Google Gemini AI integration
│   │   ├── dialogflow_service.py    # Dialogflow integration
│   │   ├── sms_service.py           # Africa's Talking SMS
│   │   ├── booking_service.py       # Booking logic
│   │   ├── voice_service.py         # Speech recognition/TTS
│   │   ├── sadtalker_service.py     # SadTalker avatar animation
│   │   ├── image_preprocessing_service.py # Image preprocessing
│   │   └── elevenlabs_service.py    # ElevenLabs TTS
│   └── utils/
│       ├── logger.py        # Logging configuration
│       ├── session_manager.py # Session handling
│       └── rate_limiter.py  # API rate limiting
│
├── frontend/
│   ├── package.json         # Node.js dependencies
│   ├── public/
│   └── src/
│       ├── components/
│       │   ├── RafikiAvatar.js       # Avatar video player
│       │   ├── RafikiAvatar.css      # Avatar styling
│       │   ├── AfricanAvatarGenerator.js
│       │   ├── AvatarStudioShowcase.js
│       │   └── chatbot/
│       │       └── talking-avatar.tsx
│       ├── App.js
│       └── index.js
│
├── SADTALKER_SETUP.md              # Detailed avatar setup guide
├── FRONTEND_UI_GUIDE.md            # Frontend UI documentation
├── API_DOCS.md                     # API documentation
└── README.md                        # This file
```
│   │   └── index.html       # HTML template
│   └── src/
│       ├── App.js           # Main React component
│       ├── components/      # UI components
│       │   ├── Header.js
│       │   ├── VoiceButton.js
│       │   ├── ChatInterface.js
│       │   └── ...
│       ├── context/         # React context providers
│       │   ├── AccessibilityContext.js
│       │   └── SessionContext.js
│       ├── hooks/           # Custom React hooks
│       │   ├── useSpeechRecognition.js
│       │   └── useTextToSpeech.js
│       ├── services/        # API services
│       │   └── api.js
│       └── styles/          # CSS files
│
├── .env.example             # Environment template
├── API_DOCS.md              # API documentation
└── README.md                # This file
```

## ♿ Accessibility Features

This application is designed with WCAG 2.1 AA compliance in mind:

- **Voice Control**: Full voice-based navigation
- **Screen Reader Support**: Comprehensive ARIA labels
- **High Contrast Mode**: Toggle high-contrast colors
- **Text Sizing**: Adjustable font sizes
- **Keyboard Navigation**: Full keyboard accessibility
- **Reduced Motion**: Option to minimize animations
- **Focus Management**: Clear focus indicators
- **Skip Links**: Skip to main content

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Navigate forward |
| `Shift + Tab` | Navigate backward |
| `Enter` / `Space` | Activate button |
| `Escape` | Close dialog |
| `Alt + V` | Toggle voice input |
| `Alt + H` | Toggle high contrast |
| `Alt + +` | Increase text size |
| `Alt + -` | Decrease text size |

## 🔌 API Documentation

See [API_DOCS.md](./API_DOCS.md) for complete API documentation.

### Quick API Examples

```bash
# Create a session
curl -X POST http://localhost:8000/api/v1/session/create

# Send a chat message
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"session_id": "your-session-id", "message": "I want to apply for a passport"}'

# Get available services
curl http://localhost:8000/api/v1/services
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

## 🚢 Deployment

### Docker

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Manual Deployment

1. Set up a production database (PostgreSQL recommended)
2. Configure production environment variables
3. Use gunicorn for the backend:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
4. Build and serve the frontend:
   ```bash
   npm run build
   # Serve with nginx or similar
   ```

## 📱 Supported Services

- 🛂 **Passport**: Application and renewal
- 🪪 **National ID**: New application and replacement
- 🚗 **Driving License**: Application, renewal, and duplicates
- 📜 **Good Conduct Certificate**: Police clearance
- 🏢 **Business Registration**: Company and business names
- 🗺️ **Land Search**: Title deed verification

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Kenya ICT Authority for eCitizen services
- Google Cloud for Gemini AI and Dialogflow
- Africa's Talking for SMS infrastructure
- The accessibility community for guidance on inclusive design

## 📞 Support

- **Email**: support@ecitizen-assistant.co.ke
- **Documentation**: https://docs.ecitizen-assistant.co.ke
- **Issues**: https://github.com/yourusername/ecitizen-voice-assistant/issues

---

# Rafiki.ai
