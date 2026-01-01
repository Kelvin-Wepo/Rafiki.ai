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
│   │   └── session.py       # Session management endpoints
│   ├── services/
│   │   ├── gemini_service.py    # Google Gemini AI integration
│   │   ├── dialogflow_service.py # Dialogflow integration
│   │   ├── sms_service.py       # Africa's Talking SMS
│   │   ├── booking_service.py   # Booking logic
│   │   └── voice_service.py     # Speech recognition/TTS
│   └── utils/
│       ├── logger.py        # Logging configuration
│       ├── session_manager.py # Session handling
│       └── rate_limiter.py  # API rate limiting
│
├── frontend/
│   ├── package.json         # Node.js dependencies
│   ├── public/
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
