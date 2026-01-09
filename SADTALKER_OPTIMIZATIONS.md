# SadTalker Performance Optimizations

## Summary of Changes

All three major optimizations have been implemented to make SadTalker **2-3x faster**:

### 1. ✅ Lower Resolution Model (256x256)
- **Changed from:** 512x512 model
- **Changed to:** 256x256 model (default)
- **Speed improvement:** 2-3x faster generation
- **File modified:** `backend/services/sadtalker_service.py`
- **Configuration:**
  ```python
  USE_256_MODEL = True
  DEFAULT_SETTINGS['size'] = 256
  ```

### 2. ✅ Video Length Reduction
- **Max audio length:** 10 seconds (configurable)
- **Auto-truncation:** Long audio files are automatically truncated
- **Benefits:** 
  - Faster generation (less frames to render)
  - Lower memory usage
  - Better user experience (quick responses)
- **File modified:** `backend/services/sadtalker_service.py`
- **Configuration:**
  ```python
  MAX_AUDIO_LENGTH = 10.0  # seconds
  ```
- **Implementation:** `_truncate_audio_if_needed()` method

### 3. ✅ Video Caching System
- **Cache common phrases:** Instant playback for frequent responses
- **Smart caching:** MD5 hash-based key generation
- **Cache expiry:** 24 hours (configurable)
- **Disk + memory cache:** Fast retrieval
- **Pre-generation script:** `backend/pregenerate_videos.py`
- **Configuration:**
  ```python
  ENABLE_CACHING = True
  CACHE_EXPIRY_HOURS = 24
  CACHE_DIR = backend/assets/avatar_cache/
  ```

## Additional Speed Optimizations

### Preprocessing Mode
- **Changed from:** `'full'` (slow, comprehensive)
- **Changed to:** `'crop'` (fast, face-focused)
- **Effect:** Skips unnecessary background processing

### Face Enhancement
- **Changed from:** GFPGAN enabled
- **Changed to:** Disabled by default
- **Effect:** Eliminates post-processing overhead

### Reference Videos
- **Changed from:** Eye blink reference videos
- **Changed to:** Disabled
- **Effect:** Removes additional processing steps

## Expected Performance

| Scenario | Before | After | Improvement |
|----------|--------|-------|-------------|
| First-time generation (10s audio) | ~6-8 minutes | ~2-3 minutes | **3x faster** |
| Cached phrase | ~6-8 minutes | **<100ms** | **Instant** |
| Short greeting (3s) | ~2-3 minutes | ~40-60 seconds | **3x faster** |

## Usage

### Automatic (Default)
All optimizations are enabled by default. Just use the service normally:
```python
from services.sadtalker_service import get_sadtalker_service

service = get_sadtalker_service()
video_path, error = await service.text_to_video(
    "Hello! How can I help you?",
    avatar_id="rafiki_avatar"
)
```

### Pre-generate Common Phrases
Run this script to pre-generate and cache common phrases:
```bash
cd backend
python pregenerate_videos.py
```

This will:
1. Show current cache stats
2. List all common phrases
3. Generate videos for each phrase
4. Cache them for instant retrieval

### Common Phrases Included
1. "Hello! I'm Rafiki, your government AI assistant. How can I help you today?"
2. "Habari! Mimi ni Rafiki, msaidizi wako wa serikali. Ninaweza kukusaidiaje leo?"
3. "Thank you for contacting us. How may I assist you?"
4. "I'm here to help with government services."
5. "Would you like me to help you book an appointment?"
6. "Let me check that information for you."
7. "Is there anything else I can help you with?"
8. "Thank you! Have a great day!"
9. "Asante! Kuwa na siku njema!"

### Cache Management
```python
# Get cache statistics
stats = service.get_cache_stats()
print(f"Cached videos: {stats['cached_videos']}")
print(f"Total size: {stats['total_size_mb']} MB")

# Clear cache if needed
service.clear_cache()
```

## Configuration Variables

You can adjust these in `backend/services/sadtalker_service.py`:

```python
# Performance settings
MAX_AUDIO_LENGTH = 10.0        # Maximum audio length (seconds)
USE_256_MODEL = True           # Use 256 model (faster) vs 512 (quality)
ENABLE_CACHING = True          # Enable video caching
CACHE_EXPIRY_HOURS = 24        # Cache videos for 24 hours

# Model settings
DEFAULT_SETTINGS = {
    'still_mode': False,       # Allow head movement
    'preprocess': 'crop',      # Fast face-focused preprocessing
    'expression_scale': 1.0,   # Normal expressions
    'pose_style': 0,           # Default pose
    'enhancer': None,          # Disable face enhancement (faster)
    'size': 256                # Use 256x256 model
}
```

## Files Modified

1. **backend/services/sadtalker_service.py**
   - Added caching system
   - Added audio truncation
   - Changed default to 256 model
   - Optimized preprocessing settings
   - Added pre-generation method

2. **backend/services/sadtalker_direct.py**
   - Changed default enhancer to False
   - Kept size parameter at 256

3. **backend/pregenerate_videos.py** (NEW)
   - Script to pre-generate common phrases
   - Interactive cache management

## Next Steps

### To Use GPU (Future Enhancement)
If you get a GPU, the generation will be **50-100x faster** (seconds instead of minutes):

```bash
# Check GPU availability
nvidia-smi

# Install CUDA-enabled PyTorch in SadTalker venv
cd /home/subchief/SadTalker
source venv/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### To Increase Quality (When Needed)
For important videos where quality matters more than speed:

```python
# Use 512 model temporarily
service.settings['size'] = 512
service.settings['preprocess'] = 'full'
service.settings['enhancer'] = 'gfpgan'

video_path, error = await service.generate_video(...)

# Reset to fast settings
service.settings['size'] = 256
service.settings['preprocess'] = 'crop'
service.settings['enhancer'] = None
```

## Testing

Test the optimizations:

```bash
# Start backend
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Test generation (in another terminal)
curl -X POST http://localhost:8000/api/avatar/text-to-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! How can I help you?",
    "personality": "friendly",
    "use_elevenlabs": true
  }' \
  --output test_video.mp4

# Check cache
cd backend
python -c "from services.sadtalker_service import get_sadtalker_service; s = get_sadtalker_service(); print(s.get_cache_stats())"
```

## Benefits Summary

✅ **2-3x faster generation** with 256 model  
✅ **Instant responses** for common phrases (cached)  
✅ **Lower resource usage** (less memory, faster CPU)  
✅ **Better user experience** (quick responses)  
✅ **Automatic optimization** (no manual intervention)  
✅ **Smart caching** (frequently used phrases cached automatically)  
✅ **Configurable** (easy to adjust settings)

The system now intelligently balances **speed vs quality**, defaulting to fast generation while maintaining acceptable video quality.
