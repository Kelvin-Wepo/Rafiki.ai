# SadTalker Avatar System Setup Guide

Complete guide for setting up and using the talking avatar system with SadTalker and Imagen for the Rafiki AI assistant.

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Image Preprocessing](#image-preprocessing)
6. [SadTalker Setup](#sadtalker-setup)
7. [API Usage](#api-usage)
8. [Frontend Integration](#frontend-integration)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

## Overview

The avatar animation system creates realistic, lip-synced talking head videos from static images and audio. It uses:

- **Imagen 3**: AI image generation for creating high-quality avatar portraits
- **SadTalker**: Deep learning model for audio-driven animation
- **FastAPI**: Backend service for processing and caching
- **React**: Frontend video player and UI

### Key Features

- ✨ Realistic avatar animations from audio
- 🎯 Automatic face detection and alignment
- 🔄 Response caching for faster generation
- 📱 Responsive design for all devices
- ♿ Full accessibility support
- 🎬 Video download capabilities
- 🚀 GPU acceleration support

## System Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                 │
│  - RafikiAvatar Component               │
│  - Video Player with Controls           │
│  - Audio Upload                         │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│      Backend (FastAPI)                  │
│  ┌─────────────────────────────────┐    │
│  │ Avatar Animation Routes         │    │
│  │  - /animate                     │    │
│  │  - /text-to-video               │    │
│  │  - /preprocess-image            │    │
│  │  - /settings                    │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ SadTalker Service               │    │
│  │  - Model Management             │    │
│  │  - Animation Generation         │    │
│  │  - Caching                      │    │
│  └─────────────────────────────────┘    │
│  ┌─────────────────────────────────┐    │
│  │ Image Preprocessing Service     │    │
│  │  - Face Detection               │    │
│  │  - Image Optimization           │    │
│  │  - Format Conversion            │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│       External Services                  │
│  - ElevenLabs (Text-to-Speech)          │
│  - Imagen 3 (Image Generation)          │
│  - SadTalker Models (Local/Cloud)       │
└─────────────────────────────────────────┘
```

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **CUDA**: 11.8+ (for GPU acceleration, optional but recommended)
- **Memory**: 8GB RAM minimum (16GB+ recommended for GPU)
- **Storage**: 5GB for models and cache
- **FFmpeg**: For video processing

### Python Dependencies

See `backend/requirements.txt` for complete list:

```bash
# Core
fastapi uvicorn python-multipart

# Image/Video Processing
pillow opencv-python opencv-contrib-python

# Face Detection
dlib face-alignment mediapipe

# Deep Learning
torch torchvision torchaudio

# Video
ffmpeg-python

# Services
httpx aiohttp
```

### GPU Setup (Recommended)

For NVIDIA GPUs (significantly faster inference):

```bash
# CUDA 11.8 + cuDNN
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
```

## Installation

### 1. Clone SadTalker Repository

```bash
cd /home/subchief/5TECH

# Clone official SadTalker repo
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Pre-trained Models

SadTalker requires pre-trained model checkpoints:

```bash
cd /home/subchief/5TECH/SadTalker

# Download models (automatically handled by the repo)
python scripts/download_checkpoint.py

# Models will be in: ./checkpoints/
# Expected files:
# - checkpoints/face_detection.pth
# - checkpoints/expression_scale.pth
# - checkpoints/gaze.pth
# - checkpoints/head_pose_estimation.pth
# - checkpoints/lip_sync_expert.pth
# - checkpoints/mapping_0.pth
# - checkpoints/mapping_1.pth
# - checkpoints/first_frame_model.pth
# - checkpoints/sadtalker.pth
```

### 3. Install Backend Dependencies

```bash
cd /home/subchief/5TECH

# Install all requirements
pip install -r backend/requirements.txt

# Or install specific components
pip install torch torchvision torchaudio
pip install opencv-python dlib face-alignment mediapipe
pip install ffmpeg-python
```

### 4. Set Environment Variables

```bash
# .env file
SADTALKER_MODE=local              # 'local', 'api', or 'cloud'
SADTALKER_PATH=/home/subchief/5TECH/SadTalker
SADTALKER_CHECKPOINT_DIR=/home/subchief/5TECH/SadTalker/checkpoints
SADTALKER_DEVICE=cuda             # 'cuda' or 'cpu'
```

## Image Preprocessing

### Overview

Before animating, images must be preprocessed to ensure optimal results:

1. **Face Detection**: Verify a face is present and clearly visible
2. **Alignment Check**: Ensure face is roughly centered and forward-facing
3. **Optimization**: Resize to 512x512, convert to RGB, adjust quality
4. **Validation**: Check technical requirements for animation

### Using ImagePreprocessingService

```python
from backend.services.image_preprocessing_service import ImagePreprocessingService

# Initialize service
preprocess = ImagePreprocessingService()

# Validate image
validation = preprocess.validate_image_for_sadtalker('avatar.png')
print(f"Valid: {validation['valid']}")
print(f"Errors: {validation['errors']}")
print(f"Warnings: {validation['warnings']}")
print(f"Face ratio: {validation['details']['face_ratio']}")

# Preprocess image
result = preprocess.preprocess_image(
    input_path='avatar.png',
    output_path='avatar_ready.jpg',
    target_size=(512, 512),
    quality=95
)

if result['success']:
    print(f"Image preprocessed: {result['output_path']}")
else:
    print(f"Preprocessing failed: {result['errors']}")

# Batch process multiple images
batch_result = preprocess.batch_preprocess(
    input_dir='./avatars/',
    output_dir='./avatars_processed/'
)
print(f"Processed {batch_result['successful']}/{batch_result['total']} images")
```

### Technical Requirements

**Image Specifications**:
- **Dimensions**: 256x256 minimum (512x512 optimal)
- **Format**: JPEG, PNG (no transparency after preprocessing)
- **Face Size**: 25-75% of image area
- **Alignment**: Face should be centered, forward-facing
- **Lighting**: Even, soft lighting (no harsh shadows)
- **Background**: Solid, uniform background preferred

**Face Requirements**:
- Eyes clearly visible and open
- Mouth in neutral or slightly smiling position
- No obstructions (glasses, hands, hair covering face)
- Head not tilted (neutral pose)
- High contrast between face and background

### Generating Avatar with Imagen 3

```
Prompt for Imagen 3:

"Professional portrait photo of a Kenyan AI assistant, mid-30s, warm 
genuine smile, head and shoulders framing, neutral beige background, 
soft even lighting, photorealistic, approachable demeanor, smart casual 
attire, facing camera directly, 512x512 resolution, high detail on 
facial features"

Generate 3-5 variations and select the best one for animation.
```

## SadTalker Setup

### Configuration

The `SadTalkerService` manages animation generation with these settings:

```python
from backend.services.sadtalker_service import SadTalkerService

# Initialize service
service = SadTalkerService(
    checkpoint_dir="./checkpoints",
    sadtalker_repo_dir="./SadTalker",
    device="cuda",              # 'cuda' or 'cpu'
    still_mode=False,           # Head movement
    preprocess="full",          # Face detection level
    expression_scale=1.0,       # Facial expression intensity
    pose_style=0                # Head pose style
)

# Update settings
service.update_settings(
    still_mode=False,
    expression_scale=1.2,
    pose_style=2
)

# Get current settings
settings = service.get_settings()
```

### Animation Settings Reference

| Setting | Type | Range | Description |
|---------|------|-------|-------------|
| `still_mode` | bool | - | If True, only animate mouth (no head movement) |
| `preprocess` | str | 'full', 'trim', 'crop' | Face detection/preprocessing level |
| `expression_scale` | float | 0.0-2.0 | Facial expression intensity (1.0 = natural) |
| `pose_style` | int | 0-6 | Head movement style (0=neutral, 1-6=variations) |

### Caching

Animations are automatically cached to improve performance:

```python
# Get cache stats
stats = service.get_cache_stats()
print(f"Cached animations: {stats['cached_animations']}")
print(f"Cache size: {stats['total_size_mb']}MB")

# Clear cache
service.clear_cache()
```

## API Usage

### Endpoints

#### 1. Generate Animation from Audio

```
POST /api/avatar/animate

Content-Type: multipart/form-data

Parameters:
- audio_file: Audio file (WAV, MP3, OGG)
- avatar_id: Avatar ID (default: 'habari')
- preprocess: 'crop', 'resize', 'full'
- still_mode: true/false
- expression_scale: 0.0-2.0
```

**Example - Python**:
```python
import requests

with open('audio.wav', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/avatar/animate',
        files={'audio_file': f},
        data={
            'avatar_id': 'habari',
            'preprocess': 'crop',
            'still_mode': False,
            'expression_scale': 1.0
        }
    )

if response.status_code == 200:
    with open('output.mp4', 'wb') as video:
        video.write(response.content)
else:
    print(f"Error: {response.json()}")
```

**Example - cURL**:
```bash
curl -X POST http://localhost:8000/api/avatar/animate \
  -F "audio_file=@audio.wav" \
  -F "avatar_id=habari" \
  -F "preprocess=crop" \
  -F "still_mode=false" \
  -F "expression_scale=1.0" \
  -o output.mp4
```

#### 2. Generate Animation from Text

```
POST /api/avatar/text-to-video

Parameters:
- text: Text to synthesize and animate
- avatar_id: Avatar ID (default: 'habari')
- language: Language code (default: 'en')
- use_elevenlabs: Use ElevenLabs TTS (default: true)
```

**Example**:
```python
response = requests.post(
    'http://localhost:8000/api/avatar/text-to-video',
    data={
        'text': 'Hello! I am Rafiki, your AI assistant.',
        'avatar_id': 'habari',
        'language': 'en'
    }
)
```

#### 3. Preprocess Image

```
POST /api/avatar/preprocess-image

Parameters:
- image_file: Avatar image
- output_format: 'jpeg' or 'png'
- quality: 1-100 (for JPEG)
```

#### 4. Get/Update Settings

```
GET /api/avatar/settings              # Get current settings
POST /api/avatar/settings             # Update settings

Parameters:
- still_mode: boolean
- preprocess: string
- expression_scale: float
- pose_style: integer
```

#### 5. Avatar Management

```
GET /api/avatar/avatars               # List available avatars
GET /api/avatar/cache/stats           # Cache statistics
POST /api/avatar/cache/clear          # Clear cache
GET /api/avatar/health                # Health check
```

## Frontend Integration

### Using RafikiAvatar Component

```jsx
import RafikiAvatar from './components/RafikiAvatar';

function ChatBot() {
  const [audioFile, setAudioFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAudioUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setAudioFile(file);
    }
  };

  return (
    <div className="chatbot">
      <div className="avatar-section">
        <RafikiAvatar
          audioStream={audioFile}
          avatarId="habari"
          onLoadingChange={setIsLoading}
          onError={(error) => console.error('Avatar error:', error)}
          autoPlay={true}
          showControls={true}
        />
      </div>

      <div className="controls">
        <input
          type="file"
          accept="audio/*"
          onChange={handleAudioUpload}
          disabled={isLoading}
        />
      </div>
    </div>
  );
}
```

### Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `audioStream` | File | null | Audio file to animate |
| `fallbackImage` | string | '👩' | Emoji when no video available |
| `avatarId` | string | 'habari' | Avatar to use |
| `onLoadingChange` | func | null | Callback when loading state changes |
| `onError` | func | null | Callback for errors |
| `autoPlay` | bool | true | Auto-play video when ready |
| `showControls` | bool | true | Show playback controls |

## Performance Optimization

### GPU Acceleration

Using GPU dramatically improves performance:

```
CPU: ~30-60 seconds for 10 second video
GPU: ~5-15 seconds for 10 second video
```

Enable GPU:
```bash
export SADTALKER_DEVICE=cuda
export CUDA_VISIBLE_DEVICES=0  # For multi-GPU systems
```

### Caching Strategy

Pre-generate common responses:

```python
common_phrases = [
    "How can I help you?",
    "Please wait a moment...",
    "I didn't understand that.",
    "Could you please repeat?",
]

# Pre-generate animations
for phrase in common_phrases:
    service.text_to_video(phrase, avatar_id='habari')
```

### Chunked Processing

For real-time applications, process audio in chunks:

```python
async def stream_avatar_animation(audio_chunks):
    for chunk in audio_chunks:
        # Process small chunks (1-2 seconds)
        video_path, error = await service.generate_video(
            audio_path=chunk,
            avatar_id='habari'
        )
        
        if error:
            # Show static avatar with audio
            yield static_avatar_frame()
        else:
            # Stream video frames
            yield from stream_video_frames(video_path)
```

### Memory Management

```python
# Monitor GPU memory
import torch
print(f"GPU Memory: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
print(f"GPU Reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

# Clear cache
torch.cuda.empty_cache()

# Enable memory efficient mode
service.update_settings(expression_scale=0.8)
```

## Troubleshooting

### Face Not Detected

**Symptoms**: "No face detected in image" error

**Solutions**:
1. Ensure face is clearly visible and forward-facing
2. Increase image resolution (minimum 256x256)
3. Improve lighting - even, soft lighting works best
4. Ensure high contrast between face and background
5. Regenerate image if it's too small or obscured

**Debug**:
```python
validation = preprocess.validate_image_for_sadtalker('image.png')
if validation['details']['face_ratio'] < 0.25:
    print("Face too small - regenerate with larger face")
```

### Poor Lip Sync

**Symptoms**: Audio and mouth movement don't match

**Solutions**:
1. Check audio quality (good quality needed for lip sync)
2. Ensure audio length matches talking duration
3. Adjust `expression_scale` parameter:
   - Lower (0.5-0.8): More subtle movements
   - Higher (1.2-1.5): More pronounced movements
4. Try different `preprocess` modes

**Debug**:
```python
service.update_settings(expression_scale=1.0)  # Reset to default
```

### Unnatural Head Movements

**Symptoms**: Head movements look jerky or unnatural

**Solutions**:
1. Try different `pose_style` values (0-6)
2. Enable `still_mode=True` to reduce head movement
3. Lower `expression_scale` for smoother movements
4. Ensure audio quality is good

### GPU Out of Memory

**Symptoms**: CUDA out of memory error

**Solutions**:
1. Process smaller videos (shorter audio clips)
2. Enable CPU mode:
   ```bash
   export SADTALKER_DEVICE=cpu
   ```
3. Clear GPU cache:
   ```python
   import torch
   torch.cuda.empty_cache()
   ```
4. Close other GPU-using applications

### Slow Generation

**Symptoms**: Avatar generation takes >1 minute for 10 seconds audio

**Solutions**:
1. Ensure GPU is being used:
   ```python
   import torch
   print(torch.cuda.is_available())  # Should be True
   ```
2. Check system resource usage (CPU, RAM, GPU)
3. Pre-cache common responses
4. Use smaller images (512x512)
5. Try `still_mode=True` for faster processing

### Audio File Issues

**Symptoms**: "Invalid audio format" or generation fails

**Solutions**:
1. Supported formats: WAV, MP3, OGG, MP4
2. Check sample rate: 16kHz or 44.1kHz recommended
3. Ensure mono or stereo (not multi-channel)
4. Verify file is not corrupted:
   ```bash
   ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1:precision=3 audio.wav
   ```

### Connection Issues

**Symptoms**: "Cannot connect to API" or timeout errors

**Solutions**:
1. Verify backend is running:
   ```bash
   curl http://localhost:8000/api/avatar/health
   ```
2. Check SADTALKER_API_URL environment variable
3. Increase timeout for large files:
   ```python
   response = requests.post(..., timeout=300)
   ```

## Testing

See `test_avatar_animation.py` for comprehensive test suite:

```bash
# Run all tests
python test_avatar_animation.py

# Run specific test
python test_avatar_animation.py TestAvatarAnimation.test_animation_generation

# With coverage
pytest test_avatar_animation.py --cov=backend.services
```

## Next Steps

1. ✅ Generate avatar image using Imagen 3
2. ✅ Preprocess image for SadTalker
3. ✅ Initialize SadTalker service
4. ✅ Integrate with FastAPI backend
5. ✅ Build React frontend component
6. ✅ Test with sample audio
7. ⏭️ Deploy to production
8. ⏭️ Monitor performance and cache stats

## References

- [SadTalker GitHub](https://github.com/OpenTalker/SadTalker)
- [Google Imagen 3](https://deepmind.google/technologies/imagen/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [PyTorch Documentation](https://pytorch.org/docs/)

## Support

For issues or questions:
1. Check the Troubleshooting section
2. Review SadTalker GitHub issues
3. Check backend logs: `backend/logs/`
4. Enable debug mode: `DEBUG=True` in environment
