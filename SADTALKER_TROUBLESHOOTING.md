# SadTalker Troubleshooting Guide

## Common Errors and Solutions

### Error: KeyboardInterrupt during model initialization

**Problem:** SadTalker is taking too long to initialize model layers, causing timeout.

**Symptoms:**
```
File ".../torch/nn/init.py", line 412, in kaiming_uniform_
    return tensor.uniform_(-bound, bound)
KeyboardInterrupt
```

**Solutions:**

#### 1. **Increase Timeout** (Applied ✅)
```python
# In sadtalker_direct.py
timeout=600  # Changed from 300 to 600 seconds (10 minutes)
```

#### 2. **Reduce Batch Size** (Applied ✅)
```python
# Changed from batch_size=2 to batch_size=1
batch_size=1  # More stable on CPU
```

#### 3. **Use 256 Model** (Applied ✅)
```python
size=256  # Instead of 512 - 2-3x faster
```

#### 4. **Disable Enhancer** (Applied ✅)
```python
enhancer=False  # Saves significant time
```

#### 5. **Use Crop Preprocessing** (Applied ✅)
```python
preprocess='crop'  # Faster than 'full'
```

---

## Testing SadTalker

### Quick Test
```bash
cd /home/subchief/5TECH
python3 test_sadtalker_quick.py
```

This will:
- Check if SadTalker is installed
- Verify avatar image exists
- Create 3-second test audio
- Generate a test video
- Report success/failure

Expected output:
```
✅ SUCCESS! Video generated!
   Path: /tmp/tmp123.mp4
   Size: 1.23 MB
```

---

## Alternative: Use Audio-Only Mode

**Recommended for production until GPU is available.**

Audio-only mode is:
- ✅ **Instant** (2-3 seconds)
- ✅ **Reliable** (no timeouts)
- ✅ **Same voice quality**
- ❌ No lip-sync video

The backend automatically falls back to audio-only if SadTalker fails or times out.

---

## Performance Expectations

### With Current Setup (CPU Only)

| Audio Length | Generation Time | Notes |
|--------------|----------------|-------|
| 3 seconds | 1-3 minutes | Minimum test case |
| 5 seconds | 2-5 minutes | Reasonable for short phrases |
| 10 seconds | 4-10 minutes | Maximum recommended |
| 30 seconds | 12-30 minutes | **Too slow for production** |

### With GPU (Future)

| Audio Length | Generation Time | Notes |
|--------------|----------------|-------|
| 3 seconds | 3-5 seconds | 50x faster |
| 5 seconds | 5-8 seconds | Practical for real-time |
| 10 seconds | 10-15 seconds | Good user experience |
| 30 seconds | 30-45 seconds | Acceptable |

---

## Current Optimizations Applied

All of these have been implemented:

1. ✅ **256x256 Model** - 2-3x faster than 512x512
2. ✅ **Crop Preprocessing** - Faster face detection
3. ✅ **No Enhancer** - Skips post-processing
4. ✅ **Batch Size = 1** - More stable on CPU
5. ✅ **10 Min Timeout** - Enough time for CPU generation
6. ✅ **Audio Truncation** - Max 10 seconds
7. ✅ **Video Caching** - Instant for common phrases
8. ✅ **Auto Fallback** - Falls back to audio if slow

---

## Recommended Workflow

### For Development/Testing
```bash
# Option 1: Test SadTalker directly
python3 test_sadtalker_quick.py

# Option 2: Test via API with short text
curl -X POST http://localhost:8000/api/avatar/text-to-video \
  -H "Content-Type: application/json" \
  -d '{"text": "Hi", "personality": "friendly", "use_elevenlabs": false}' \
  --output test.mp4
```

### For Production
1. **Pre-generate common phrases:**
   ```bash
   cd backend
   python3 pregenerate_videos.py
   ```

2. **Use audio-only as default:**
   - Fast, reliable, same voice quality
   - Videos only for special cases

3. **Consider cloud GPU:**
   - Google Colab (free tier)
   - Replicate.com ($0.0004/second)
   - RunPod/Vast.ai ($0.20/hour)

---

## Debugging Steps

### 1. Check SadTalker Installation
```bash
cd /home/subchief/SadTalker
source venv/bin/activate
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "from src.gradio_demo import SadTalker; print('SadTalker imported successfully')"
```

### 2. Check Checkpoints
```bash
ls -lh /home/subchief/5TECH/SadTalker/checkpoints/
```

Should see:
- `SadTalker_V0.0.2_256.safetensors` (for speed)
- `SadTalker_V0.0.2_512.safetensors` (for quality)

### 3. Check Avatar Image
```bash
ls -lh /home/subchief/5TECH/backend/assets/avatars/rafiki_avatar.png
```

Should be 1-3 MB (high quality image).

### 4. Test Model Loading
```bash
cd /home/subchief/5TECH/SadTalker
source venv/bin/activate
python -c "
import torch
from src.gradio_demo import SadTalker

print('Initializing SadTalker...')
sad_talker = SadTalker(
    checkpoint_path='checkpoints',
    config_path='src/config',
    lazy_load=True
)
print('✅ SadTalker initialized successfully!')
"
```

### 5. Monitor Backend Logs
```bash
# In one terminal
cd /home/subchief/5TECH/backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Watch logs for SadTalker messages
# Look for: "🎬 Generating video with SadTalker..."
```

---

## When to Use What

### Use Audio-Only When:
- ✅ Need fast responses (< 5 seconds)
- ✅ Production environment
- ✅ High traffic expected
- ✅ CPU-only system
- ✅ Testing/development

### Use SadTalker Video When:
- 🎥 Special announcements
- 🎥 Marketing/demos
- 🎥 Low traffic periods
- 🎥 Have GPU available
- 🎥 Pre-generated content

---

## Getting Help

If SadTalker still doesn't work:

1. **Check logs:** Backend terminal shows detailed errors
2. **Run test:** `python3 test_sadtalker_quick.py`
3. **Verify setup:**
   ```bash
   cd /home/subchief/5TECH
   python3 -c "from backend.services.sadtalker_direct import check_sadtalker_available; check_sadtalker_available()"
   ```
4. **Use audio-only:** It works perfectly and is much faster

---

## Summary

**Current Status:** SadTalker configured and optimized for CPU

**Reality Check:** Video generation on CPU is **slow** (2-10 minutes per video)

**Best Practice:** 
- Use audio-only mode for real-time responses
- Pre-generate videos for common phrases
- Consider GPU for video generation in the future

**Bottom Line:** Audio-only mode works great and is the practical solution until you get a GPU.
