# 🎬 African Avatar Studio - Imagen + SadTalker

Create professional talking avatars for African presenters using Google's Imagen for image generation and SadTalker for lip-synced video creation.

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY=your_key_here
python -m uvicorn main:app --reload
```

Visit: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm start
```

Visit: http://localhost:3000

## 📋 Features

✨ **Avatar Customization**
- Skin tone selection (light, medium, dark)
- Hair style options (natural, braids, twists, straight)
- Clothing styles (professional suit, traditional, casual, formal)
- Personality types (warm & friendly, professional, patient, encouraging)
- Background settings (office, traditional, neutral, government)
- Language/accent support (Kenyan, US, UK, Swahili)

🎬 **Video Generation**
- Lip-synced talking head videos
- Multiple pose styles (still, natural, expressive)
- Expression intensity control
- High-quality MP4 output

## 🏗️ Architecture

```
Frontend (React)
   ↓
Avatar Studio Component
   ├─ Avatar Customization
   ├─ Audio Upload
   └─ Video Preview
   ↓
   ↓ API Calls
   ↓
Backend (FastAPI)
   ├─ Imagen Service (Avatar Generation)
   └─ SadTalker Service (Video Synthesis)
   ↓
External APIs
   ├─ Google Gemini (Imagen)
   └─ SadTalker (Lip-sync)
```

## 📡 API Endpoints

### Avatar Generation
```bash
POST /avatar/generate
Content-Type: application/json

{
  "name": "Amara",
  "skin_tone": "medium",
  "hair_style": "braids",
  "clothing": "professional_suit",
  "personality": "warm_friendly",
  "background": "office",
  "language": "en-KE"
}
```

### Video Generation
```bash
POST /avatar/generate-talking-video
Content-Type: multipart/form-data

image: [File]
audio: [File]
pose_style: 1
exp_scale: 1.0
```

### Get Configurations
```bash
GET /avatar/configurations
```

## 🔧 Configuration

Create `.env` in backend:
```
GEMINI_API_KEY=your_gemini_api_key
```

Create `.env.local` in frontend:
```
REACT_APP_API_URL=http://localhost:8000
```

## 📁 Project Structure

```
5TECH/
├── backend/
│   ├── services/
│   │   ├── imagen_service.py      (Avatar generation)
│   │   └── sadtalker_service.py   (Video synthesis)
│   ├── routes/
│   │   └── avatar_generation.py   (API endpoints)
│   └── main.py
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── AfricanAvatarGenerator.js
    │   ├── App.js
    │   └── index.js
    ├── public/
    │   └── index.html
    └── package.json
```

## 🎯 Workflow

1. **Customize Avatar**
   - Select skin tone, hair style, clothing, personality, background, language
   - Click "Generate Avatar"

2. **Upload Audio**
   - Upload MP3/WAV/OGG file
   - Audio will be used for lip-sync

3. **Generate Video**
   - Click "Generate Video"
   - System creates talking head video
   - Video is displayed in browser

4. **Download**
   - Download MP4 file
   - Use in presentations, training, etc.

## 🔑 Environment Variables

### Backend
- `GEMINI_API_KEY` - Google Gemini API key for Imagen

### Frontend
- `REACT_APP_API_URL` - Backend API URL (default: http://localhost:8000)

## 🐛 Troubleshooting

**Avatar generation fails:**
- Check GEMINI_API_KEY is set
- Verify API key has Imagen access
- Check network connectivity

**Video generation fails:**
- Ensure audio file is valid (MP3/WAV/OGG)
- Check image file is PNG/JPG
- Verify SadTalker service is running

**Frontend won't start:**
```bash
rm -rf node_modules
npm install
npm start
```

**Backend port in use:**
```bash
# Find process on port 8000
lsof -i :8000
# Kill it
kill -9 <PID>
```

## 📚 Technologies

- **Frontend:** React 18, Fetch API
- **Backend:** FastAPI, Python 3.10+
- **AI:** Google Gemini (Imagen), SadTalker
- **Video:** MP4 encoding

## 📝 License

MIT License

## 🤝 Contributing

Contributions welcome! Please submit pull requests or issues.

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review API documentation
3. Check browser console for errors
4. Check backend logs

---

**Version:** 1.0.0  
**Last Updated:** 2024-01-15  
**Status:** Production Ready ✅
