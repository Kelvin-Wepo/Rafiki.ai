# Avatar Animation Pipeline Guide

Complete guide to generate realistic avatars with Imagen and animate them with SadTalker.

## Overview

The avatar animation pipeline consists of three main components:

1. **Imagen 3** - Generates realistic portrait images
2. **ElevenLabs TTS** - Converts text to natural-sounding speech
3. **SadTalker** - Animates the image with lip-sync and facial expressions

## Quick Start

### 1. Generate Avatar Image with Imagen

The avatar image is already generated and saved at:
```
/backend/assets/avatars/rafiki_avatar.png
```

This is a beautiful Kenyan woman avatar suitable for SadTalker animation.

### 2. Run the Animation Pipeline

#### Option A: Complete Pipeline (Imagen → Audio → SadTalker)
```bash
cd /home/subchief/5TECH/backend

# Run with custom text
python3 avatar_animation_pipeline.py \
  --text "Hello! I am Rafiki, your AI assistant from Kenya." \
  --voice "Habari" \
  --output "./avatar_output"

# Output files will be saved to avatar_output/
# - avatar_variation_1.png (generated image)
# - response_audio.wav (generated audio)
# - output_video.mp4 (animated talking avatar)
```

#### Option B: Quick Demo
```bash
python3 quick_avatar_demo.py
```

This runs a simplified version for quick testing.

#### Option C: Custom Image + SadTalker
```bash
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def animate():
    from services.sadtalker_service import get_sadtalker_service
    
    sadtalker = get_sadtalker_service()
    video_path, error = await sadtalker.generate_video(
        audio_path='response_audio.wav',
        image_path='assets/avatars/rafiki_avatar.png',
        preprocess='full',
        still_mode=False,
        expression_scale=1.0
    )
    
    if video_path:
        print(f'✅ Video saved: {video_path}')
    else:
        print(f'❌ Error: {error}')

asyncio.run(animate())
"
```

## Setup & Configuration

### Prerequisites

```bash
# Install Python packages
pip install -r requirements.txt

# Additional packages for pipeline
pip install google-generativeai elevenlabs pillow opencv-python
```

### API Keys

#### Imagen 3 (Google)
```bash
# Set in .env or environment
export GEMINI_API_KEY="your-google-api-key"
```

#### ElevenLabs
```bash
# Set in .env or environment
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

#### SadTalker
SadTalker can run in multiple modes:

**Mode 1: Local Installation**
```bash
# Clone and setup SadTalker locally
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
pip install -r requirements.txt

# Set environment variable
export SADTALKER_MODE="local"
export SADTALKER_CHECKPOINT_DIR="./checkpoints"
```

**Mode 2: API Server (Gradio)**
```bash
# If you have SadTalker running via Gradio
export SADTALKER_MODE="api"
export SADTALKER_API_URL="http://localhost:7860"
```

## File Structure

```
backend/
├── assets/
│   └── avatars/
│       └── rafiki_avatar.png          # Generated avatar image
├── services/
│   ├── imagen_service.py              # Google Imagen integration
│   ├── elevenlabs_service.py          # ElevenLabs TTS integration
│   └── sadtalker_service.py           # SadTalker animation
├── avatar_animation_pipeline.py        # Complete pipeline script
├── quick_avatar_demo.py               # Quick demo script
└── test_avatar_pipeline.py            # Testing script
```

## Script Details

### avatar_animation_pipeline.py

Complete end-to-end pipeline with full control.

**Features:**
- Generates images with Imagen 3
- Creates audio with ElevenLabs TTS
- Animates with SadTalker
- Progress tracking
- Error handling with fallbacks
- Detailed logging

**Usage:**
```bash
python3 avatar_animation_pipeline.py \
  --text "Your text here" \
  --prompt "Custom image prompt" \
  --voice "VoiceName" \
  --output "./output_directory"
```

**Arguments:**
- `--text`: Text for avatar to speak (default: greeting)
- `--prompt`: Imagen prompt for avatar image (optional)
- `--voice`: ElevenLabs voice name (default: Habari)
- `--output`: Output directory (default: ./avatar_output)

### quick_avatar_demo.py

Simplified demo for testing the pipeline without heavy configuration.

**Features:**
- Minimal setup required
- Fast execution
- Clear step-by-step output
- Good for testing each component

**Usage:**
```bash
python3 quick_avatar_demo.py
```

### test_avatar_pipeline.py

Component testing and integration verification.

**Features:**
- Tests each component
- Checks API connectivity
- Verifies configuration
- Shows usage examples
- Detailed diagnostics

**Usage:**
```bash
python3 test_avatar_pipeline.py
```

## How It Works

### Step 1: Image Generation (Imagen)

```python
from services.imagen_service import ImagenService

imagen = ImagenService()
result = imagen.generate_image(
    prompt="Professional portrait of a Kenyan woman...",
    image_size="512x512",
    num_images=1
)

# Result contains PIL Image objects or base64-encoded images
image = result['images'][0]
image.save('avatar.png')
```

### Step 2: Audio Generation (ElevenLabs)

```python
from services.elevenlabs_service import ElevenLabsService

elevenlabs = ElevenLabsService()
audio_path = elevenlabs.synthesize_speech(
    text="Hello! I am Rafiki.",
    voice_name="Habari",
    output_path="response.wav"
)
```

### Step 3: Video Animation (SadTalker)

```python
import asyncio
from services.sadtalker_service import get_sadtalker_service

async def animate():
    sadtalker = get_sadtalker_service()
    
    video_path, error = await sadtalker.generate_video(
        audio_path="response.wav",
        image_path="avatar.png",
        preprocess="full",
        still_mode=False,
        expression_scale=1.0
    )
    
    return video_path

video = asyncio.run(animate())
```

## API Integration with SadTalker

Once animated, videos can be served via the backend API:

```bash
# Start the backend
python3 -m uvicorn main:app --reload

# The API endpoint for video generation
curl -X POST http://localhost:8000/api/avatar/generate-talking-video \
  -F "audio=@response.wav" \
  -F "language=en-US"
```

## Troubleshooting

### Imagen API Errors

**Error: "No valid API key"**
- Set `GEMINI_API_KEY` environment variable
- Check Google Cloud Console for valid API key
- Ensure Imagen API is enabled in project

### ElevenLabs Errors

**Error: "Invalid voice"**
- List available voices: `elevenlabs.get_available_voices()`
- Use standard voice names like "Habari", "Echo", "Bella"

**Error: "Quota exceeded"**
- Check ElevenLabs account quota
- Use shorter text or reduce number of generations

### SadTalker Errors

**Error: "API not available"**
- Check if SadTalker API is running (if using API mode)
- Verify `SADTALKER_API_URL` is correct
- Falls back to local mode if configured

**Error: "Face not detected"**
- Image must show clear frontal face
- Face should occupy 40-60% of image
- Try regenerating image with better prompt

**Error: "Video generation failed"**
- Check audio file format (WAV, MP3 supported)
- Check image file format (PNG, JPG supported)
- Verify audio duration matches video requirements
- Check GPU memory if using local mode

## Performance Optimization

### Caching

Generated videos are cached to avoid re-generation:
```
backend/assets/avatar_cache/
```

### Batch Processing

Generate multiple videos in batch:
```bash
for text in "Hello" "How are you" "Goodbye"; do
  python3 avatar_animation_pipeline.py --text "$text"
done
```

### GPU Acceleration

For local SadTalker:
```bash
# Check GPU availability
nvidia-smi

# Use GPU if available
export CUDA_VISIBLE_DEVICES=0
python3 avatar_animation_pipeline.py --text "Hello"
```

## Example Output

Running the pipeline generates:

```
🎬 RAFIKI AVATAR ANIMATION PIPELINE
====================================================================

📸 Step 1: Generating avatar image...
✅ Image saved: ./avatar_output/avatar_variation_1.png

🎤 Step 2: Generating audio...
✅ Audio saved: ./avatar_output/response_audio.wav

🎬 Step 3: Animating with SadTalker...
⏳ Processing... (this may take a while)
✅ Video saved: ./avatar_output/rafiki_video.mp4

====================================================================
✅ PIPELINE COMPLETE
====================================================================

Generated files:
  📸 Avatar image: ./avatar_output/avatar_variation_1.png
  🔊 Audio: ./avatar_output/response_audio.wav
  🎬 Video: ./avatar_output/rafiki_video.mp4
```

## Next Steps

1. **Set up API keys** for Imagen, ElevenLabs
2. **Install SadTalker** (local or API mode)
3. **Run quick demo** to test setup
4. **Integrate with frontend** to display videos in React
5. **Deploy** complete talking avatar system

## Support

For issues:
1. Run `test_avatar_pipeline.py` for diagnostics
2. Check logs in `backend/logs/`
3. Verify API keys and quotas
4. Check dependencies with `pip list`
5. Review error messages carefully

## Resources

- [Google Imagen Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)
- [ElevenLabs Documentation](https://elevenlabs.io/docs)
- [SadTalker GitHub](https://github.com/OpenTalker/SadTalker)
- [SadTalker Gradio Interface](https://huggingface.co/spaces/vumichien/SadTalker)
