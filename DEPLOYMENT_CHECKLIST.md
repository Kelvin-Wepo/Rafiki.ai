# Quick Deployment Checklist for Render.com

## Pre-Deployment

- [ ] All code committed and pushed to GitHub
- [ ] API keys ready:
  - [ ] Google Gemini API key
  - [ ] ElevenLabs API key (optional)
  - [ ] Africa's Talking API key (optional)
  - [ ] Google Colab ngrok URL (optional)
- [ ] Test locally one more time
- [ ] Update README if needed

## Render Setup

### Backend Service
- [ ] Create Web Service on Render
- [ ] Connect GitHub repository
- [ ] Configure build command: `./build.sh`
- [ ] Configure start command: `./start-render.sh`
- [ ] Set Python version: 3.10.0
- [ ] Add all environment variables
- [ ] Set health check path: `/health`
- [ ] Deploy and wait for build

### Frontend Service
- [ ] Create Static Site or Web Service
- [ ] Connect GitHub repository
- [ ] Configure build command: `cd frontend && npm install && npm run build`
- [ ] Configure start command: `cd frontend && npm run preview -- --host 0.0.0.0 --port $PORT`
- [ ] Set Node version: 18.19.0
- [ ] Add VITE_API_URL environment variable
- [ ] Deploy and wait for build

## Post-Deployment

- [ ] Update CORS_ORIGINS in backend with frontend URL
- [ ] Test health endpoint: `https://your-backend.onrender.com/health`
- [ ] Test API docs: `https://your-backend.onrender.com/docs`
- [ ] Test frontend: `https://your-frontend.onrender.com`
- [ ] Test avatar generation
- [ ] Test voice features
- [ ] Check logs for any errors

## Optional Enhancements

- [ ] Set up UptimeRobot to keep service awake
- [ ] Configure custom domain
- [ ] Set up monitoring/alerts
- [ ] Configure Google Colab for GPU acceleration
- [ ] Add SSL certificate (automatic on Render)

## Troubleshooting Checklist

If deployment fails:
- [ ] Check build logs in Render dashboard
- [ ] Verify all environment variables are set
- [ ] Check Python/Node version compatibility
- [ ] Test build commands locally
- [ ] Review requirements.txt for any issues
- [ ] Check CORS settings

## URLs After Deployment

Backend: https://rafiki-backend.onrender.com
Frontend: https://rafiki-frontend.onrender.com
API Docs: https://rafiki-backend.onrender.com/docs
Health: https://rafiki-backend.onrender.com/health
