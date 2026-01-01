"""
SadTalker Service
Generates lip-synced talking head videos from audio
Supports both local SadTalker installation and cloud API
"""

import os
import uuid
import base64
import asyncio
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

# Configuration
SADTALKER_API_URL = os.getenv("SADTALKER_API_URL", "http://localhost:7860")  # Gradio default port
SADTALKER_MODE = os.getenv("SADTALKER_MODE", "api")  # "api" or "local"
AVATAR_DIR = Path(__file__).parent.parent / "assets" / "avatars"

# Default African woman avatar image (base64 placeholder - should be replaced with actual image)
DEFAULT_AVATAR = "african_woman.png"


class SadTalkerService:
    """Service for generating talking head videos using SadTalker"""
    
    def __init__(self):
        self.api_url = SADTALKER_API_URL
        self.mode = SADTALKER_MODE
        self.avatar_dir = AVATAR_DIR
        self._ensure_avatar_dir()
    
    def _ensure_avatar_dir(self):
        """Ensure avatar directory exists"""
        self.avatar_dir.mkdir(parents=True, exist_ok=True)
    
    def get_available_avatars(self) -> list:
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
        preprocess: str = "crop",
        still_mode: bool = False,
        expression_scale: float = 1.0
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a lip-synced video from audio
        
        Args:
            audio_path: Path to the audio file
            avatar_id: ID of the avatar to use
            preprocess: Preprocessing mode ('crop', 'resize', 'full')
            still_mode: If True, only animate mouth (no head movement)
            expression_scale: Scale of facial expressions (0.0-2.0)
        
        Returns:
            Tuple of (video_path, error_message)
        """
        try:
            # Get avatar image path
            avatar_path = self._get_avatar_path(avatar_id)
            if not avatar_path:
                return None, f"Avatar '{avatar_id}' not found"
            
            if self.mode == "api":
                return await self._generate_via_api(
                    audio_path, avatar_path, preprocess, still_mode, expression_scale
                )
            else:
                return await self._generate_locally(
                    audio_path, avatar_path, preprocess, still_mode, expression_scale
                )
                
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
    
    async def _generate_via_api(
        self,
        audio_path: str,
        avatar_path: str,
        preprocess: str,
        still_mode: bool,
        expression_scale: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate video using SadTalker API (Gradio interface)"""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                # Read files as base64
                with open(avatar_path, "rb") as f:
                    avatar_b64 = base64.b64encode(f.read()).decode()
                
                with open(audio_path, "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode()
                
                # Call SadTalker API
                response = await client.post(
                    f"{self.api_url}/api/predict",
                    json={
                        "data": [
                            f"data:image/png;base64,{avatar_b64}",  # Source image
                            f"data:audio/wav;base64,{audio_b64}",   # Driven audio
                            preprocess,
                            still_mode,
                            True,  # Use GFPGAN for face enhancement
                            "crop",  # batch size
                            0,  # size of image
                            0,  # yaw (pose)
                            0,  # pitch
                            0,  # roll
                            expression_scale
                        ]
                    }
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
        expression_scale: float
    ) -> Tuple[Optional[str], Optional[str]]:
        """Generate video using local SadTalker installation"""
        try:
            # Check if SadTalker is installed
            sadtalker_path = os.getenv("SADTALKER_PATH", "/opt/SadTalker")
            if not os.path.exists(sadtalker_path):
                return None, "SadTalker not installed locally"
            
            output_dir = tempfile.mkdtemp()
            output_path = os.path.join(output_dir, "result.mp4")
            
            # Build command
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
            
            # Run SadTalker
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
        
        Args:
            text: Text to speak
            avatar_id: Avatar to use
            voice_service: Voice service for TTS (optional)
            language: Language for TTS
        
        Returns:
            Tuple of (video_path, error_message)
        """
        try:
            # Generate audio from text
            if voice_service:
                audio_path = await voice_service.text_to_speech_file(text, language)
            else:
                # Use system TTS as fallback
                audio_path = await self._generate_tts_audio(text, language)
            
            if not audio_path:
                return None, "Failed to generate audio"
            
            # Generate video from audio
            return await self.generate_video(audio_path, avatar_id)
            
        except Exception as e:
            logger.error(f"Text to video error: {e}")
            return None, str(e)
    
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
