# Render Deployment Guide for Rafiki.ai

This guide will help you deploy Rafiki.ai to Render.com with both backend and frontend services.

## Prerequisites

- GitHub account with your Rafiki.ai repository
- Render.com account (free tier works)
- API keys for:
  - Google Gemini
  - ElevenLabs (optional)
  - Africa's Talking (optional)
  - Google Colab ngrok URL (optional, for GPU acceleration)

## Deployment Options

### Option 1: Blueprint Deployment (Recommended)

This method uses the `render.yaml` file for automated setup.

1. **Push your code to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

2. **Go to Render Dashboard**
   - Visit https://dashboard.render.com
   - Click "New +" → "Blueprint"

3. **Connect Repository**
   - Connect your GitHub account
   - Select the `Rafiki.ai` repository
   - Render will detect `render.yaml` automatically

4. **Configure Environment Variables**
   
   For **rafiki-backend**:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `ELEVENLABS_API_KEY`: Your ElevenLabs API key (optional)
   - `ELEVENLABS_AGENT_ID`: Your ElevenLabs agent ID (optional)
   - `ELEVENLABS_BRANCH_ID`: Your ElevenLabs branch ID (optional)
   - `AFRICASTALKING_API_KEY`: Your Africa's Talking API key (optional)
   - `COLAB_SADTALKER_URL`: Your Google Colab ngrok URL (optional)

5. **Deploy**
   - Click "Apply" to deploy both services
   - Wait for build to complete (~5-10 minutes)

### Option 2: Manual Deployment

#### Backend Service

1. **Create New Web Service**
   - Go to Render Dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Backend**
   ```
   Name: rafiki-backend
   Region: Oregon (US West)
   Branch: main
   Runtime: Python 3
   Build Command: pip install --upgrade pip && pip install -r backend/requirements.txt
   Start Command: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
   Plan: Free
   ```

3. **Add Environment Variables**
   - Go to "Environment" tab
   - Add all variables from the Blueprint section above
   - Set `CORS_ORIGINS` to include your frontend URL

4. **Set Health Check**
   - Path: `/health`
   - This ensures the service stays alive

#### Frontend Service

1. **Create New Static Site or Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Frontend**
   ```
   Name: rafiki-frontend
   Region: Oregon (US West)
   Branch: main
   Runtime: Node
   Build Command: cd frontend && npm install && npm run build
   Start Command: cd frontend && npm run preview -- --host 0.0.0.0 --port $PORT
   Plan: Free
   ```

3. **Add Environment Variables**
   ```
   NODE_VERSION=18.19.0
   VITE_API_URL=https://rafiki-backend.onrender.com
   ```

## Post-Deployment Configuration

### 1. Update CORS Settings

After deployment, update your backend's CORS origins:

```bash
# In Render Dashboard → rafiki-backend → Environment
CORS_ORIGINS=https://your-frontend-url.onrender.com,https://rafiki-backend.onrender.com
```

### 2. Configure Google Colab (Optional)

If using GPU acceleration:

1. Run your Colab notebook
2. Get the ngrok URL
3. Update `COLAB_SADTALKER_URL` in Render environment variables
4. Manually deploy to apply changes

### 3. Test Your Deployment

Visit your frontend URL (e.g., `https://rafiki-frontend.onrender.com`)

Test endpoints:
```bash
# Health check
curl https://rafiki-backend.onrender.com/health

# API docs
open https://rafiki-backend.onrender.com/docs
```

## Render Free Tier Limitations

- **Services spin down after 15 minutes of inactivity**
  - First request after inactivity takes ~30 seconds to wake up
  - Consider using a service like UptimeRobot to ping your app

- **750 hours/month of free compute**
  - Enough for 1 service running 24/7
  - Multiple services share this quota

- **Build minutes are limited**
  - ~400 build minutes per month on free tier

## Troubleshooting

### Backend won't start

**Check logs:**
```
Render Dashboard → rafiki-backend → Logs
```

**Common issues:**
- Missing environment variables
- Python version mismatch
- Dependencies not installing

**Solutions:**
1. Verify all required env vars are set
2. Check `requirements.txt` is valid
3. Try specifying `PYTHON_VERSION=3.10.0`

### Frontend build fails

**Common issues:**
- Node version mismatch
- Build command errors
- Missing dependencies

**Solutions:**
1. Set `NODE_VERSION=18.19.0`
2. Check `package.json` scripts
3. Test build locally: `cd frontend && npm run build`

### CORS errors

**Solution:**
Update `CORS_ORIGINS` in backend environment to include frontend URL:
```
CORS_ORIGINS=https://your-frontend.onrender.com,https://rafiki-backend.onrender.com
```

### Video generation is slow

**Solutions:**
1. Use Google Colab GPU (recommended)
   - Set up Colab notebook
   - Add ngrok URL to `COLAB_SADTALKER_URL`
   
2. Disable video generation
   - System will fall back to audio-only mode
   - Much faster, but no lip-sync video

### Service keeps sleeping

**Solution:**
Use a ping service to keep it awake:
- UptimeRobot (free)
- Cron-job.org
- Or upgrade to paid Render plan

## Monitoring

### Health Checks

Backend health endpoint:
```
GET https://rafiki-backend.onrender.com/health
```

Returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "gemini": true,
    "elevenlabs": true
  }
}
```

### Logs

Access logs in Render Dashboard:
- Click on service name
- Go to "Logs" tab
- View real-time logs

## Scaling & Performance

### Upgrade Options

**Starter Plan ($7/month per service):**
- No sleeping
- Faster CPU
- More build minutes

**Standard Plan ($25/month per service):**
- Dedicated CPU
- More RAM
- Priority support

### Performance Tips

1. **Enable caching**
   - Avatar videos are cached automatically
   - Reduces generation time for repeated content

2. **Use Colab GPU**
   - Free T4 GPU acceleration
   - 50-100x faster than Render CPU

3. **Optimize images**
   - Compress avatar images
   - Use WebP format when possible

4. **CDN for static assets**
   - Consider Cloudflare for frontend
   - Faster global delivery

## Continuous Deployment

Render automatically deploys on git push:

1. Make changes locally
2. Commit and push:
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin main
   ```
3. Render detects push and rebuilds
4. New version goes live after build

### Auto-Deploy Settings

In Render Dashboard:
- Service → Settings → Auto-Deploy
- Toggle to enable/disable
- Choose branch to deploy from

## Environment Management

### Production vs Staging

Create separate branches:

```bash
# Staging
git checkout -b staging
git push origin staging

# In Render, create new services pointing to staging branch
```

### Secret Management

**Never commit secrets!**

Use Render's environment variables for:
- API keys
- Database passwords
- OAuth secrets

## Backup & Recovery

### Database (if using)

Render PostgreSQL includes:
- Daily backups (retained 7 days on free tier)
- Point-in-time recovery (paid plans)

### Code

- GitHub repository is your source of truth
- Tag releases: `git tag v1.0.0 && git push --tags`

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- GitHub Issues: https://github.com/Kelvin-Wepo/Rafiki.ai/issues

## Next Steps

After successful deployment:

1. Test all features thoroughly
2. Set up monitoring (UptimeRobot, etc.)
3. Configure custom domain (optional)
4. Enable HTTPS (automatic on Render)
5. Share your app!

Your Rafiki.ai assistant is now live and accessible globally!
