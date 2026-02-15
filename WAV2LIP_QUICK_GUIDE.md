# Quick Implementation: Wav2Lip for Talking Head Avatar

## Why Wav2Lip is Better Than SadTalker for Most Use Cases

| Aspect | Wav2Lip | SadTalker |
|--------|---------|-----------|
| **Speed** | 10-15s per minute | 40-60s per minute |
| **GPU Memory** | 2-3GB | 8-10GB |
| **Setup Complexity** | Simple | Complex |
| **Quality** | 9/10 | 10/10 |
| **Worth It?** | ✅ YES | Overkill for most |

---

## 🚀 Step-by-Step Implementation (2-3 hours)

### Phase 1: Backend Setup (30 minutes)

#### 1. Install Wav2Lip
```bash
cd backend
pip install -q https://github.com/Rudrabha/Wav2Lip/archive/master.zip
pip install librosa scipy imageio imageio-ffmpeg
```

#### 2. Download Pre-trained Model
```bash
# Create models directory
mkdir -p models

# Download model (about 600MB)
wget -O models/wav2lip.pth \
  https://github.com/Rudrabha/Wav2Lip/releases/download/Weights/wav2lip.pth
```

#### 3. Create Service File
Create `backend/services/wav2lip_service.py`:

```python
import os
import cv2
import numpy as np
from pathlib import Path
import torch
import librosa
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class Wav2LipService:
    def __init__(self):
        self.model = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.cache_dir = Path('cache/videos')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Wav2Lip service initialized on {self.device}")
    
    def load_model(self):
        """Load Wav2Lip model"""
        if self.model is not None:
            return
        
        try:
            from wav2lip import Wav2Lip
            model_path = 'models/wav2lip.pth'
            
            if not os.path.exists(model_path):
                raise FileNotFoundError(f"Model not found: {model_path}")
            
            self.model = Wav2Lip(checkpoint_path=model_path)
            self.model.to(self.device)
            logger.info("Wav2Lip model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Wav2Lip model: {e}")
            raise
    
    def generate_video(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = None
    ) -> str:
        """Generate lip-synced video"""
        self.load_model()
        
        # Check cache first
        cache_key = f"{Path(image_path).stem}_{Path(audio_path).stem}"
        cache_file = self.cache_dir / f"{cache_key}.mp4"
        
        if cache_file.exists():
            logger.info(f"Using cached video: {cache_file}")
            return str(cache_file)
        
        try:
            logger.info(f"Generating video from {image_path} and {audio_path}")
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Failed to load image: {image_path}")
            
            # Convert BGR to RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Load audio
            audio, sr = librosa.load(audio_path, sr=16000)
            
            # Generate frames
            frames = self.model.infer_batch(
                first_frame=image_rgb,
                mels=self._get_mels(audio),
                fps=25,
                pads=(0, 10, 0, 0)
            )
            
            # Save video
            output_path = output_path or str(cache_file)
            self._save_video(frames, output_path, fps=25)
            
            logger.info(f"Video generated successfully: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            raise
    
    @staticmethod
    def _get_mels(audio: np.ndarray, sr: int = 16000) -> np.ndarray:
        """Convert audio to mel-spectrogram"""
        import librosa
        
        mel = librosa.feature.melspectrogram(y=audio, sr=sr)
        return mel
    
    @staticmethod
    def _save_video(frames, output_path: str, fps: int = 25):
        """Save frames to MP4 video"""
        from imageio import get_writer
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with get_writer(output_path, fps=fps, codec='libx264', quality=8) as writer:
            for frame in frames:
                # Ensure frame is in correct format
                if frame.max() <= 1.0:
                    frame = (frame * 255).astype(np.uint8)
                elif frame.dtype != np.uint8:
                    frame = frame.astype(np.uint8)
                
                writer.append_data(frame)

# Singleton
_service = None

def get_wav2lip_service():
    global _service
    if _service is None:
        _service = Wav2LipService()
    return _service
```

### Phase 2: API Endpoint (30 minutes)

Add to `backend/routes/avatar.py`:

```python
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import aiofiles
import os
from services.wav2lip_service import get_wav2lip_service

router = APIRouter(prefix="/api/avatar", tags=["avatar"])

@router.post("/generate-lip-sync")
async def generate_lip_sync_video(
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    user: dict = Depends(get_current_user)
):
    """
    Generate lip-synced talking head video.
    
    Input:
    - image: Avatar image (PNG, JPG)
    - audio: Audio file (WAV, MP3)
    
    Output: MP4 video file with lip-sync
    """
    try:
        # Create temp directory
        os.makedirs('/tmp/avatar', exist_ok=True)
        
        # Save uploaded files
        image_path = f"/tmp/avatar/{image.filename}"
        audio_path = f"/tmp/avatar/{audio.filename}"
        
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(await image.read())
        
        async with aiofiles.open(audio_path, 'wb') as f:
            await f.write(await audio.read())
        
        # Generate video
        wav2lip = get_wav2lip_service()
        video_path = await wav2lip.generate_video(image_path, audio_path)
        
        # Schedule cleanup
        if background_tasks:
            background_tasks.add_task(os.remove, image_path)
            background_tasks.add_task(os.remove, audio_path)
        
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename="talking_head.mp4"
        )
    
    except Exception as e:
        logger.error(f"Error generating lip-sync video: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/lip-sync/status")
async def get_lip_sync_status():
    """Check if Wav2Lip service is ready"""
    try:
        service = get_wav2lip_service()
        service.load_model()
        return {"status": "ready", "device": service.device}
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### Phase 3: Frontend Integration (1 hour)

Create `frontend/src/services/wav2lipService.ts`:

```typescript
import { getStoredToken } from './authService';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface GenerateVideoParams {
  imageFile: File;
  audioFile: File;
}

export async function generateLipSyncVideo(
  params: GenerateVideoParams
): Promise<Blob> {
  const formData = new FormData();
  formData.append('image', params.imageFile);
  formData.append('audio', params.audioFile);

  const token = getStoredToken();
  
  const response = await fetch(
    `${API_BASE_URL}/api/avatar/generate-lip-sync`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    }
  );

  if (!response.ok) {
    throw new Error('Failed to generate lip-sync video');
  }

  return response.blob();
}

export async function downloadLipSyncVideo(
  imageFile: File,
  audioFile: File,
  filename: string = 'talking_head.mp4'
) {
  const blob = await generateLipSyncVideo({
    imageFile,
    audioFile
  });

  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}
```

Create React component `frontend/src/components/avatar/Wav2LipGenerator.tsx`:

```tsx
import { useState } from 'react';
import { generateLipSyncVideo } from '../../services/wav2lipService';

interface Wav2LipGeneratorProps {
  imageSrc: string;
  onVideoGenerated?: (videoUrl: string) => void;
}

export function Wav2LipGenerator({ 
  imageSrc, 
  onVideoGenerated 
}: Wav2LipGeneratorProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerateVideo = async (audioBlob: Blob) => {
    setIsGenerating(true);
    setError(null);

    try {
      // Get image
      const imageResponse = await fetch(imageSrc);
      const imageBlob = await imageResponse.blob();
      const imageFile = new File([imageBlob], 'avatar.png', { type: 'image/png' });
      const audioFile = new File([audioBlob], 'speech.wav', { type: 'audio/wav' });

      // Generate video
      const videoBlob = await generateLipSyncVideo({
        imageFile,
        audioFile
      });

      const url = URL.createObjectURL(videoBlob);
      setVideoUrl(url);
      onVideoGenerated?.(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate video');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="wav2lip-generator">
      {videoUrl ? (
        <video
          src={videoUrl}
          autoPlay
          loop
          muted
          controls
          style={{ maxWidth: '100%', borderRadius: '12px' }}
        />
      ) : (
        <img src={imageSrc} alt="Avatar" style={{ maxWidth: '100%' }} />
      )}

      {isGenerating && (
        <div className="generating">
          <span className="spinner" />
          <p>Generating lip-sync video...</p>
        </div>
      )}

      {error && (
        <div className="error">
          <p>Error: {error}</p>
        </div>
      )}

      <button
        onClick={() => handleGenerateVideo(new Blob())}
        disabled={isGenerating}
        className="btn btn-primary"
      >
        {isGenerating ? 'Generating...' : 'Generate Talking Head'}
      </button>
    </div>
  );
}
```

---

## ✅ Verification Checklist

- [ ] Installed Wav2Lip and dependencies
- [ ] Downloaded pre-trained model (600MB)
- [ ] Created `wav2lip_service.py`
- [ ] Added API endpoint to `routes/avatar.py`
- [ ] Created `wav2lipService.ts` for frontend
- [ ] Created `Wav2LipGenerator.tsx` component
- [ ] Backend starts without errors
- [ ] Frontend can access the API
- [ ] Test with sample image and audio

---

## 🧪 Testing

```bash
# Backend test
curl -X POST http://localhost:8000/api/avatar/lip-sync/status

# Check status
# Expected: {"status": "ready", "device": "cuda"}
```

---

## 📊 Performance Metrics

After implementation, measure:
- Generation time for 1-minute video
- GPU memory usage
- Video quality (visual inspection)
- Lip-sync accuracy

---

## 🔄 Fallback Strategy

If Wav2Lip fails, fallback to existing animated avatar:

```typescript
try {
  const video = await generateLipSyncVideo(...);
  setVideoUrl(URL.createObjectURL(video));
} catch (err) {
  // Fallback to animated avatar with audio
  console.warn('Wav2Lip generation failed, using animated avatar');
  showAnimatedAvatar(audioUrl);
}
```

---

## 🚀 Next Steps

1. **Today**: Install and download model
2. **Tomorrow**: Implement backend service
3. **Day 3**: Add API endpoint and test
4. **Day 4**: Integrate frontend component
5. **Day 5**: Performance testing and optimization

**Estimated time: 2-3 days of work (or 8-12 hours of focused coding)**

Want me to implement this for you?
