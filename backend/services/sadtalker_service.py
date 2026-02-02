"""
SadTalker Service for Avatar Animation

Comprehensive service for animating avatars using SadTalker:
- Multiple backend support (local inference, API, cloud)
- Caching of common animations
- Batch processing capabilities
- Real-time streaming support
- Performance optimization with GPU acceleration
"""

import os
import uuid
import base64
import asyncio
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import httpx
import shutil
from functools import lru_cache
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
SADTALKER_API_URL = os.getenv("SADTALKER_API_URL", "http://localhost:7860")  # Gradio default port
SADTALKER_MODE = os.getenv("SADTALKER_MODE", "direct")  # "direct", "api", "local", "cloud", or "colab"
COLAB_URL = os.getenv("COLAB_SADTALKER_URL")  # Google Colab ngrok URL
AVATAR_DIR = Path(__file__).parent.parent / "assets" / "avatars"
CACHE_DIR = Path(__file__).parent.parent / "assets" / "avatar_cache"
CHECKPOINT_DIR = os.getenv("SADTALKER_CHECKPOINT_DIR", "./checkpoints")
SADTALKER_PATH = Path(__file__).parent.parent.parent / "SadTalker"

# Performance optimization settings - CPU OPTIMIZED for AMD Ryzen
MAX_AUDIO_LENGTH = 10.0  # Maximum audio length in seconds (reduced for CPU)
USE_256_MODEL = True  # Use 256x256 model for 2-3x speed improvement
ENABLE_CACHING = True  # Enable video caching for common phrases
CACHE_EXPIRY_HOURS = 24  # Cache videos for 24 hours
USE_COLAB_IF_AVAILABLE = True  # Automatically use Colab GPU if configured

# CPU-specific optimizations
CPU_BATCH_SIZE = 1  # Batch size 1 is optimal for CPU memory management
CPU_DISABLE_ENHANCER = True  # Disable enhancers on CPU (too slow)
CPU_STILL_MODE_DEFAULT = True  # Still mode is faster
CPU_FRAME_SKIP = 5  # Process every 5th frame, interpolate the rest (4x speedup)

# Default African woman avatar image
DEFAULT_AVATAR = "rafiki_avatar.png"

# Reference video paths for natural animations
REF_VIDEO_DIR = SADTALKER_PATH / "examples" / "ref_video"
DEFAULT_REF_EYEBLINK = str(REF_VIDEO_DIR / "WDA_AlexandriaOcasioCortez_000.mp4") if REF_VIDEO_DIR.exists() else None

# Animation settings optimized for speed
DEFAULT_SETTINGS = {
    'still_mode': True,  # Still mode is faster
    'preprocess': 'crop',  # 'crop' is faster than 'full'
    'expression_scale': 1.0,
    'pose_style': 0,
    'enhancer': None,  # Disable enhancer for faster generation
    'background_enhancer': None,  # 'realesrgan' for full video enhancement
    'ref_eyeblink': None,  # Disable for speed
    'ref_pose': None,  # Reference video for pose
    'size': 256  # Use 256x256 model for 2-3x speed improvement
}

# Personality presets for different moods and interaction styles
# Optimized for speed: crop preprocessing, no enhancer, no ref videos
PERSONALITY_PRESETS = {
    'friendly': {
        'expression_scale': 1.2,
        'still_mode': False,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Warm and welcoming with moderate expressions'
    },
    'professional': {
        'expression_scale': 0.8,
        'still_mode': True,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Composed and formal with minimal head movement'
    },
    'excited': {
        'expression_scale': 1.5,
        'still_mode': False,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Energetic and enthusiastic with vivid expressions'
    },
    'calm': {
        'expression_scale': 0.6,
        'still_mode': True,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Peaceful and soothing with gentle movements'
    },
    'energetic': {
        'expression_scale': 1.8,
        'still_mode': False,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Highly animated with dynamic expressions and movement'
    },
    'empathetic': {
        'expression_scale': 1.1,
        'still_mode': False,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Compassionate and understanding with soft expressions'
    },
    'humorous': {
        'expression_scale': 1.4,
        'still_mode': False,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Playful and lighthearted with expressive animations'
    },
    'serious': {
        'expression_scale': 0.7,
        'still_mode': True,
        'preprocess': 'crop',
        'enhancer': None,
        'ref_eyeblink': None,
        'size': 256,
        'description': 'Focused and businesslike with controlled movements'
    }
}


class SadTalkerService:
    """Service for generating talking head videos using SadTalker with personality features"""
    
    # Expose personality presets as class attribute
    PERSONALITY_PRESETS = PERSONALITY_PRESETS
    
    def __init__(self):
        self.api_url = SADTALKER_API_URL
        self.mode = SADTALKER_MODE
        self.avatar_dir = AVATAR_DIR
        self.cache_dir = CACHE_DIR
        self.checkpoint_dir = CHECKPOINT_DIR
        self.settings = DEFAULT_SETTINGS.copy()
        self.current_personality = 'friendly'  # Default personality
        self._ensure_directories()
        self._client = None
        self._video_cache = {}  # In-memory cache for video paths
        self._init_common_phrases()
        self._colab_service = None  # Lazy load Colab service
        
        # Check if Colab is available and preferred
        if USE_COLAB_IF_AVAILABLE and COLAB_URL:
            logger.info(f"🌐 Colab GPU server configured: {COLAB_URL}")
            self.mode = "colab"
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        self.avatar_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_common_phrases(self):
        """Initialize common phrases for pre-generation"""
        self.common_phrases = [
            "Hello! I'm Rafiki, your government AI assistant. How can I help you today?",
            "Habari! Mimi ni Rafiki, msaidizi wako wa serikali. Ninaweza kukusaidiaje leo?",
            "Thank you for contacting us. How may I assist you?",
            "I'm here to help with government services.",
            "Would you like me to help you book an appointment?",
            "Let me check that information for you.",
            "Is there anything else I can help you with?",
            "Thank you! Have a great day!",
            "Asante! Kuwa na siku njema!"
        ]
    
    def _get_cache_key(self, text: str, avatar_id: str, personality: str) -> str:
        """Generate cache key for video"""
        import hashlib
        key_str = f"{text}_{avatar_id}_{personality}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached_video(self, cache_key: str) -> Optional[str]:
        """Get cached video path if exists and not expired"""
        if not ENABLE_CACHING:
            return None
        
        # Check in-memory cache first
        if cache_key in self._video_cache:
            video_path = self._video_cache[cache_key]
            if Path(video_path).exists():
                # Check if file is not too old
                file_age_hours = (datetime.now().timestamp() - Path(video_path).stat().st_mtime) / 3600
                if file_age_hours < CACHE_EXPIRY_HOURS:
                    logger.info(f"Using cached video: {video_path}")
                    return video_path
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key}.mp4"
        if cache_file.exists():
            file_age_hours = (datetime.now().timestamp() - cache_file.stat().st_mtime) / 3600
            if file_age_hours < CACHE_EXPIRY_HOURS:
                self._video_cache[cache_key] = str(cache_file)
                logger.info(f"Using cached video from disk: {cache_file}")
                return str(cache_file)
        
        return None
    
    def _cache_video(self, cache_key: str, video_path: str) -> str:
        """Cache video for future use"""
        if not ENABLE_CACHING:
            return video_path
        
        try:
            cache_file = self.cache_dir / f"{cache_key}.mp4"
            if not cache_file.exists():
                shutil.copy2(video_path, cache_file)
                logger.info(f"Cached video: {cache_file}")
            self._video_cache[cache_key] = str(cache_file)
            return str(cache_file)
        except Exception as e:
            logger.warning(f"Failed to cache video: {e}")
            return video_path
    
    async def _ensure_audio_in_video(self, video_path: str, audio_path: str) -> str:
        """
        Ensure audio is properly embedded in the video file.
        If video has no audio track, merge the original audio into the video.
        
        Args:
            video_path: Path to the generated video
            audio_path: Path to the original audio file
            
        Returns:
            Path to video with audio (may be same file or new merged file)
        """
        try:
            import subprocess
            
            # Check if video has audio track
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                 '-show_entries', 'stream=codec_type', '-of', 'csv=p=0', video_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            has_audio = result.returncode == 0 and result.stdout.strip() == 'audio'
            
            if not has_audio and os.path.exists(audio_path):
                logger.info(f"Video has no audio track, merging audio from: {audio_path}")
                
                # Create output path for merged video
                merged_path = video_path.replace('.mp4', '_with_audio.mp4')
                
                # Merge audio into video using ffmpeg
                merge_result = subprocess.run(
                    ['ffmpeg', '-i', video_path, '-i', audio_path,
                     '-c:v', 'copy', '-c:a', 'aac', '-map', '0:v:0', '-map', '1:a:0',
                     '-shortest', '-y', merged_path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if merge_result.returncode == 0 and os.path.exists(merged_path):
                    logger.info(f"✅ Audio merged into video: {merged_path}")
                    # Replace original video with merged version
                    try:
                        os.remove(video_path)
                        os.rename(merged_path, video_path)
                    except Exception as rename_err:
                        logger.warning(f"Could not replace video file: {rename_err}")
                        # Use merged file if rename fails
                        return merged_path
                    return video_path
                else:
                    logger.warning(f"Failed to merge audio: {merge_result.stderr}")
                    return video_path  # Return original even if merge failed
            else:
                logger.info("Video already has audio track")
                return video_path
                
        except Exception as e:
            logger.warning(f"Could not verify/merge audio in video: {e}")
            return video_path  # Return original video even if check failed
    
    def _truncate_audio_if_needed(self, audio_path: str) -> str:
        """Truncate audio to MAX_AUDIO_LENGTH if too long"""
        try:
            # Try to get audio duration
            import subprocess
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', audio_path],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                
                if duration > MAX_AUDIO_LENGTH:
                    logger.info(f"Audio too long ({duration:.1f}s), truncating to {MAX_AUDIO_LENGTH}s")
                    truncated_path = audio_path.replace('.wav', '_truncated.wav').replace('.mp3', '_truncated.mp3')
                    
                    subprocess.run(
                        ['ffmpeg', '-i', audio_path, '-t', str(MAX_AUDIO_LENGTH),
                         '-c', 'copy', truncated_path, '-y'],
                        capture_output=True, timeout=30
                    )
                    
                    if Path(truncated_path).exists():
                        return truncated_path
        except Exception as e:
            logger.warning(f"Could not check/truncate audio length: {e}")
        
        return audio_path
    
    @property
    def client(self):
        """Get or create HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=300.0)
        return self._client
    
    def set_personality(self, personality: str) -> bool:
        """
        Set avatar personality/mood
        
        Args:
            personality: One of 'friendly', 'professional', 'excited', 'calm'
        
        Returns:
            True if successful, False otherwise
        """
        if personality in PERSONALITY_PRESETS:
            self.current_personality = personality
            self.settings.update(PERSONALITY_PRESETS[personality])
            logger.info(f"Avatar personality set to: {personality}")
            return True
        return False
    
    def get_personality(self) -> str:
        """Get current personality setting"""
        return self.current_personality
    
    def get_all_personalities(self) -> Dict[str, Dict[str, Any]]:
        """Get all available personalities with their descriptions"""
        return {
            name: {
                'name': name,
                'description': preset.get('description', ''),
                'expression_scale': preset['expression_scale'],
                'still_mode': preset['still_mode']
            }
            for name, preset in PERSONALITY_PRESETS.items()
        }
    
    def get_personality_info(self, personality: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific personality"""
        if personality in PERSONALITY_PRESETS:
            preset = PERSONALITY_PRESETS[personality]
            return {
                'name': personality,
                'description': preset.get('description', ''),
                'settings': {
                    'expression_scale': preset['expression_scale'],
                    'still_mode': preset['still_mode'],
                    'preprocess': preset['preprocess'],
                    'enhancer': preset.get('enhancer')
                }
            }
        return None
    
    def get_available_avatars(self) -> List[Dict[str, str]]:
        """Get list of available avatar images"""
        avatars = []
        if self.avatar_dir.exists():
            for file in self.avatar_dir.glob("*.png"):
                avatars.append({
                    "id": file.stem,
                    "name": file.stem.replace("_", " ").title(),
                    "path": str(file)
                })
            for file in self.avatar_dir.glob("*.jpg"):
                avatars.append({
                    "id": file.stem,
                    "name": file.stem.replace("_", " ").title(),
                    "path": str(file)
                })
        
        # Add default avatar if no custom ones exist
        if not avatars:
            avatars.append({
                "id": "habari",
                "name": "Habari (Default)",
                "path": None  # Will use SVG fallback
            })
        
        return avatars
    
    async def generate_video(
        self,
        audio_path: str,
        avatar_id: str = "habari",
        image_path: Optional[str] = None,
        preprocess: Optional[str] = None,
        still_mode: Optional[bool] = None,
        expression_scale: Optional[float] = None,
        enhancer: Optional[str] = None,
        background_enhancer: Optional[str] = None,
        ref_eyeblink: Optional[str] = None,
        ref_pose: Optional[str] = None,
        cache_key: Optional[str] = None,
        ensure_audio: bool = True
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a lip-synced video from audio with personality and enhancements
        
        Args:
            audio_path: Path to the audio file
            avatar_id: ID of the avatar to use
            image_path: Optional custom image path (overrides avatar_id)
            preprocess: Preprocessing mode ('crop', 'resize', 'full') - uses current personality if None
            still_mode: If True, only animate mouth (no head movement) - uses current personality if None
            expression_scale: Scale of facial expressions (0.0-2.0) - uses current personality if None
            enhancer: Face enhancer ('gfpgan', 'RestoreFormer', None)
            background_enhancer: Background enhancer ('realesrgan', None)
            ref_eyeblink: Path to reference video for natural eye blinking
            ref_pose: Path to reference video for natural head pose
            cache_key: Optional cache key for video caching
        
        Returns:
            Tuple of (video_path, error_message)
        """
        try:
            # Check cache first if key provided
            if cache_key:
                cached_video = self._get_cached_video(cache_key)
                if cached_video:
                    return cached_video, None
            
            # Truncate audio if too long (for speed)
            audio_path = self._truncate_audio_if_needed(audio_path)
            
            # Apply personality settings if parameters not explicitly provided
            if preprocess is None:
                preprocess = self.settings.get('preprocess', 'crop')
            if still_mode is None:
                still_mode = self.settings.get('still_mode', False)
            if expression_scale is None:
                expression_scale = self.settings.get('expression_scale', 1.0)
            if enhancer is None:
                enhancer = self.settings.get('enhancer')
            if background_enhancer is None:
                background_enhancer = self.settings.get('background_enhancer')
            if ref_eyeblink is None:
                ref_eyeblink = self.settings.get('ref_eyeblink')
            if ref_pose is None:
                ref_pose = self.settings.get('ref_pose')
            
            # Get avatar image path - use custom image if provided
            if image_path:
                avatar_path = image_path
            else:
                avatar_path = self._get_avatar_path(avatar_id)
                if not avatar_path:
                    return None, f"Avatar '{avatar_id}' not found"
            
            # Try Colab GPU first if available (fastest with GPU)
            if self.mode == "colab":
                video_path, error = await self._generate_via_colab(
                    audio_path, avatar_path, preprocess, still_mode, expression_scale
                )
            # Try direct integration (CPU)
            elif self.mode == "direct":
                video_path, error = await self._generate_direct(
                    audio_path, avatar_path, preprocess, still_mode, expression_scale,
                    enhancer, ref_eyeblink, ref_pose
                )
            elif self.mode == "api":
                video_path, error = await self._generate_via_api(
                    audio_path, avatar_path, preprocess, still_mode, expression_scale,
                    enhancer, background_enhancer, ref_eyeblink, ref_pose
                )
            else:
                video_path, error = await self._generate_locally(
                    audio_path, avatar_path, preprocess, still_mode, expression_scale,
                    enhancer, background_enhancer, ref_eyeblink, ref_pose
                )
            
            # Verify and ensure audio is embedded in video
            if video_path and os.path.exists(video_path) and ensure_audio:
                video_path = await self._ensure_audio_in_video(video_path, audio_path)
            
            # Cache the video if generation was successful
            if video_path and cache_key:
                video_path = self._cache_video(cache_key, video_path)
            
            return video_path, error
                
        except Exception as e:
            logger.error(f"SadTalker generation error: {e}")
            return None, str(e)
    
    def _get_avatar_path(self, avatar_id: str) -> Optional[str]:
        """Get the file path for an avatar"""
        # Check for PNG
        png_path = self.avatar_dir / f"{avatar_id}.png"
        if png_path.exists():
            return str(png_path)
        
        # Check for JPG
        jpg_path = self.avatar_dir / f"{avatar_id}.jpg"
        if jpg_path.exists():
            return str(jpg_path)
        
        # Use default if available
        default_path = self.avatar_dir / DEFAULT_AVATAR
        if default_path.exists():
            return str(default_path)
        
        return None
    
    async def _generate_via_colab(
        self,
        audio_path: str,
        avatar_path: str,
        preprocess: str,
        still_mode: bool,
        expression_scale: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate video using Google Colab GPU backend (fastest with GPU)"""
        try:
            # Lazy load Colab service
            if self._colab_service is None:
                from .colab_sadtalker_service import get_colab_service
                self._colab_service = get_colab_service()
            
            if not self._colab_service.is_available():
                logger.warning("Colab service not available, falling back to local")
                return None, "Colab service not reachable"
            
            logger.info(f"🌐 Using Google Colab GPU for video generation")
            
            # Get size from settings
            size = self.settings.get('size', 256)
            
            # Generate via Colab
            video_path, error = await self._colab_service.generate_video(
                source_image_path=avatar_path,
                driven_audio_path=audio_path,
                preprocess=preprocess,
                still_mode=still_mode,
                expression_scale=expression_scale,
                size=size,
                enhancer=False  # Disable for speed
            )
            
            if video_path:
                logger.info(f"✅ Video generated via Colab GPU: {video_path}")
                return video_path, None
            else:
                return None, error or "Colab generation failed"
                
        except Exception as e:
            logger.error(f"Colab generation error: {e}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    async def _generate_direct(
        self,
        audio_path: str,
        avatar_path: str,
        preprocess: str,
        still_mode: bool,
        expression_scale: float,
        enhancer: Optional[str] = None,
        ref_eyeblink: Optional[str] = None,
        ref_pose: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate video using direct SadTalker integration (CPU method)"""
        try:
            # Check if SadTalker is available
            if not SADTALKER_PATH.exists():
                logger.warning(f"SadTalker not found at {SADTALKER_PATH}")
                return None, "SadTalker not installed"
            
            # Import direct integration
            try:
                from .sadtalker_direct import generate_video_direct, check_sadtalker_available
            except ImportError as e:
                logger.error(f"Failed to import sadtalker_direct: {e}")
                return None, "SadTalker direct integration not available"
            
            # Check if SadTalker is properly configured
            if not check_sadtalker_available():
                logger.warning("SadTalker is not properly configured")
                return None, "SadTalker checkpoints missing. Run: cd SadTalker && bash scripts/download_models.sh"
            
            # Prepare output path
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, "result.mp4")
            
            # Get size from settings (256 for speed)
            size = self.settings.get('size', 256)
            
            # Run generation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result_path, error = await loop.run_in_executor(
                None,
                generate_video_direct,
                avatar_path,
                audio_path,
                output_path,
                preprocess,
                still_mode,
                expression_scale,
                enhancer == 'gfpgan' if enhancer else False,
                1,  # batch_size - reduced to 1 for CPU stability
                size,  # size (256 for speed, 512 for quality)
                0  # pose_style
            )
            
            if result_path and os.path.exists(result_path):
                logger.info(f"Generated video with direct SadTalker: {result_path}")
                return result_path, None
            else:
                return None, error or "Failed to generate video"
                
        except Exception as e:
            logger.error(f"Direct SadTalker generation error: {e}")
            import traceback
            traceback.print_exc()
            return None, str(e)
    
    async def _generate_via_api(
        self,
        audio_path: str,
        avatar_path: str,
        preprocess: str,
        still_mode: bool,
        expression_scale: float,
        enhancer: Optional[str] = None,
        background_enhancer: Optional[str] = None,
        ref_eyeblink: Optional[str] = None,
        ref_pose: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate video using SadTalker API (Gradio interface) with enhancements"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Read files as base64
                with open(avatar_path, "rb") as f:
                    avatar_b64 = base64.b64encode(f.read()).decode()
                
                with open(audio_path, "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode()
                
                # Prepare reference video data if provided
                ref_eyeblink_b64 = None
                if ref_eyeblink and Path(ref_eyeblink).exists():
                    with open(ref_eyeblink, "rb") as f:
                        ref_eyeblink_b64 = base64.b64encode(f.read()).decode()
                
                ref_pose_b64 = None
                if ref_pose and Path(ref_pose).exists():
                    with open(ref_pose, "rb") as f:
                        ref_pose_b64 = base64.b64encode(f.read()).decode()
                
                # Call SadTalker API with full parameters
                api_data = [
                    f"data:image/png;base64,{avatar_b64}",  # Source image
                    f"data:audio/wav;base64,{audio_b64}",   # Driven audio
                    preprocess,
                    still_mode,
                    enhancer is not None,  # Use enhancer flag
                    "crop",  # batch size
                    0,  # size of image
                    0,  # yaw (pose)
                    0,  # pitch
                    0,  # roll
                    expression_scale
                ]
                
                # Add optional reference videos if provided
                if ref_eyeblink_b64:
                    api_data.append(f"data:video/mp4;base64,{ref_eyeblink_b64}")
                if ref_pose_b64:
                    api_data.append(f"data:video/mp4;base64,{ref_pose_b64}")
                
                response = await client.post(
                    f"{self.api_url}/api/predict",
                    json={"data": api_data}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if "data" in result and len(result["data"]) > 0:
                        # Result is base64 encoded video
                        video_b64 = result["data"][0]
                        
                        # Save to temp file
                        output_path = tempfile.mktemp(suffix=".mp4")
                        if video_b64.startswith("data:"):
                            video_b64 = video_b64.split(",")[1]
                        
                        with open(output_path, "wb") as f:
                            f.write(base64.b64decode(video_b64))
                        
                        logger.info(f"Generated video with {self.current_personality} personality")
                        return output_path, None
                    else:
                        return None, "No video generated"
                else:
                    return None, f"API error: {response.status_code}"
                    
        except httpx.ConnectError:
            logger.warning("SadTalker API not available, using fallback")
            return None, "SadTalker API not available"
        except Exception as e:
            logger.error(f"SadTalker API error: {e}")
            return None, str(e)
    
    async def _generate_locally(
        self,
        audio_path: str,
        avatar_path: str,
        preprocess: str,
        still_mode: bool,
        expression_scale: float,
        enhancer: Optional[str] = None,
        background_enhancer: Optional[str] = None,
        ref_eyeblink: Optional[str] = None,
        ref_pose: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate video using local SadTalker installation with enhancements"""
        try:
            # Check if SadTalker is installed
            sadtalker_path = os.getenv("SADTALKER_PATH", "/opt/SadTalker")
            if not os.path.exists(sadtalker_path):
                return None, "SadTalker not installed locally"
            
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, "result.mp4")
            
            # Build command with full parameters
            cmd = [
                "python",
                os.path.join(sadtalker_path, "inference.py"),
                "--driven_audio", audio_path,
                "--source_image", avatar_path,
                "--result_dir", output_dir,
                "--preprocess", preprocess,
                "--expression_scale", str(expression_scale),
            ]
            
            if still_mode:
                cmd.append("--still")
            
            # Add enhancers
            if enhancer:
                cmd.extend(["--enhancer", enhancer])
            if background_enhancer:
                cmd.extend(["--background_enhancer", background_enhancer])
            
            # Add reference videos for natural animations
            if ref_eyeblink and Path(ref_eyeblink).exists():
                cmd.extend(["--ref_eyeblink", ref_eyeblink])
            if ref_pose and Path(ref_pose).exists():
                cmd.extend(["--ref_pose", ref_pose])
            
            # Run SadTalker
            logger.info(f"Running SadTalker with {self.current_personality} personality")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=sadtalker_path
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Find the generated video
                for file in os.listdir(output_dir):
                    if file.endswith(".mp4"):
                        logger.info(f"Successfully generated video with {self.current_personality} personality")
                        return os.path.join(output_dir, file), None
                return None, "Video generation completed but file not found"
            else:
                return None, f"SadTalker error: {stderr.decode()}"
                
        except Exception as e:
            logger.error(f"Local SadTalker error: {e}")
            return None, str(e)
    
    async def text_to_video(
        self,
        text: str,
        avatar_id: str = "habari",
        voice_service = None,
        language: str = "en"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a talking head video from text
        First converts text to speech, then generates video
        Uses caching for common phrases for faster responses
        
        Args:
            text: Text to speak
            avatar_id: Avatar to use
            voice_service: Voice service for TTS (optional)
            language: Language for TTS
        
        Returns:
            Tuple of (video_path, error_message)
        """
        try:
            # Generate cache key
            cache_key = self._get_cache_key(text, avatar_id, self.current_personality)
            
            # Check cache first
            cached_video = self._get_cached_video(cache_key)
            if cached_video:
                return cached_video, None
            
            # Generate audio from text
            if voice_service:
                audio_path = await voice_service.text_to_speech_file(text, language)
            else:
                # Use system TTS as fallback
                audio_path = await self._generate_tts_audio(text, language)
            
            if not audio_path:
                return None, "Failed to generate audio"
            
            # Generate video from audio with caching
            return await self.generate_video(audio_path, avatar_id, cache_key=cache_key)
            
        except Exception as e:
            logger.error(f"Text to video error: {e}")
            return None, str(e)
    
    async def generate_with_personality(
        self,
        text: str,
        personality: str,
        avatar_id: str = "habari",
        voice_service = None,
        language: str = "en"
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate video with specific personality
        Uses caching for faster responses on common phrases
        
        Args:
            text: Text to speak
            personality: One of 'friendly', 'professional', 'excited', 'calm'
            avatar_id: Avatar to use
            voice_service: Voice service for TTS
            language: Language for TTS
        
        Returns:
            Tuple of (video_path, error_message)
        """
        # Set personality temporarily
        original_personality = self.current_personality
        if not self.set_personality(personality):
            logger.warning(f"Invalid personality '{personality}', using '{original_personality}'")
        
        try:
            # Generate cache key with personality
            cache_key = self._get_cache_key(text, avatar_id, personality)
            
            # Check cache first
            cached_video = self._get_cached_video(cache_key)
            if cached_video:
                return cached_video, None
            
            result = await self.text_to_video(text, avatar_id, voice_service, language)
            return result
        finally:
            # Restore original personality
            self.set_personality(original_personality)
    
    async def _generate_tts_audio(self, text: str, language: str = "en") -> Optional[str]:
        """Generate audio using system TTS"""
        try:
            # This is a placeholder - implement with pyttsx3 or espeak
            import tempfile
            audio_path = tempfile.mktemp(suffix=".wav")
            
            try:
                import pyttsx3
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)
                engine.setProperty('volume', 0.9)
                engine.save_to_file(text, audio_path)
                engine.runAndWait()
                return audio_path
            except ImportError:
                logger.warning("pyttsx3 not available for TTS")
                return None
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    def update_settings(self, **kwargs):
        """Update animation settings"""
        valid_keys = {'still_mode', 'preprocess', 'expression_scale', 'pose_style'}
        for key, value in kwargs.items():
            if key in valid_keys:
                self.settings[key] = value
                logger.info(f"Updated setting {key}={value}")
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current animation settings"""
        return self.settings.copy()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            cache_files = list(self.cache_dir.glob('*.mp4'))
            total_size = sum(f.stat().st_size for f in cache_files)
            return {
                'cached_videos': len(cache_files),
                'cache_dir': str(self.cache_dir),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'in_memory_entries': len(self._video_cache)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    async def pregenerate_common_phrases(self, voice_service=None, avatar_id: str = "habari") -> Dict[str, Any]:
        """
        Pre-generate videos for common phrases to speed up responses
        This should be run during startup or low-traffic periods
        
        Args:
            voice_service: Voice service for TTS
            avatar_id: Avatar to use
        
        Returns:
            Dict with generation results
        """
        results = {
            'generated': [],
            'failed': [],
            'cached': [],
            'total': len(self.common_phrases)
        }
        
        logger.info(f"Pre-generating {len(self.common_phrases)} common phrases...")
        
        for phrase in self.common_phrases:
            try:
                cache_key = self._get_cache_key(phrase, avatar_id, 'friendly')
                
                # Check if already cached
                if self._get_cached_video(cache_key):
                    results['cached'].append(phrase[:50] + '...' if len(phrase) > 50 else phrase)
                    logger.info(f"Already cached: {phrase[:50]}...")
                    continue
                
                # Generate video
                video_path, error = await self.text_to_video(
                    phrase, avatar_id, voice_service, language="en"
                )
                
                if video_path:
                    results['generated'].append(phrase[:50] + '...' if len(phrase) > 50 else phrase)
                    logger.info(f"Generated: {phrase[:50]}...")
                else:
                    results['failed'].append({
                        'phrase': phrase[:50] + '...' if len(phrase) > 50 else phrase,
                        'error': error
                    })
                    logger.warning(f"Failed to generate: {phrase[:50]}... - {error}")
                
            except Exception as e:
                results['failed'].append({
                    'phrase': phrase[:50] + '...' if len(phrase) > 50 else phrase,
                    'error': str(e)
                })
                logger.error(f"Error pre-generating phrase: {e}")
        
        logger.info(f"Pre-generation complete: {len(results['generated'])} generated, "
                   f"{len(results['cached'])} cached, {len(results['failed'])} failed")
        
        return results
    
    def clear_cache(self) -> bool:
        """Clear animation cache"""
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self._client:
            await self._client.aclose()
            self._client = None


def create_sadtalker_service() -> SadTalkerService:
    """Factory function to create SadTalker service"""
    return SadTalkerService()
    
    async def _generate_tts_audio(self, text: str, language: str) -> Optional[str]:
        """Generate TTS audio using system voice"""
        try:
            import pyttsx3
            
            output_path = tempfile.mktemp(suffix=".wav")
            
            engine = pyttsx3.init()
            engine.setProperty('rate', 130)  # Slower for lip sync
            engine.save_to_file(text, output_path)
            engine.runAndWait()
            
            return output_path
            
        except Exception as e:
            logger.error(f"TTS audio generation error: {e}")
            return None


# Singleton instance
_sadtalker_service = None

def get_sadtalker_service() -> SadTalkerService:
    """Get or create SadTalker service singleton"""
    global _sadtalker_service
    if _sadtalker_service is None:
        _sadtalker_service = SadTalkerService()
    return _sadtalker_service
