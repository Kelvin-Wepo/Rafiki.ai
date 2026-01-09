"""
Google Colab GPU Backend for SadTalker
Connects to a SadTalker instance running on Google Colab with GPU
"""

import os
import httpx
import base64
import logging
from pathlib import Path
from typing import Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)

class ColabSadTalkerService:
    """Service to connect to SadTalker running on Google Colab GPU"""
    
    def __init__(self, colab_url: Optional[str] = None):
        """
        Initialize Colab SadTalker service
        
        Args:
            colab_url: The ngrok URL from your Colab notebook
        """
        self.colab_url = colab_url or os.getenv("COLAB_SADTALKER_URL")
        self.timeout = 120.0  # 2 minutes timeout (fast with GPU)
        
        if not self.colab_url:
            logger.warning("No Colab URL configured. Set COLAB_SADTALKER_URL environment variable.")
    
    def is_available(self) -> bool:
        """Check if Colab server is configured and reachable"""
        if not self.colab_url:
            return False
        
        try:
            import requests
            response = requests.get(self.colab_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def generate_video(
        self,
        source_image_path: str,
        driven_audio_path: str,
        preprocess: str = 'crop',
        still_mode: bool = False,
        expression_scale: float = 1.0,
        size: int = 256,
        enhancer: bool = False
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate video using Colab GPU backend
        
        Args:
            source_image_path: Path to avatar image
            driven_audio_path: Path to audio file
            preprocess: Preprocessing mode ('crop', 'resize', 'full')
            still_mode: Minimize head movement
            expression_scale: Scale of facial expressions (0.0-2.0)
            size: Video resolution (256 or 512)
            enhancer: Use face enhancer (slower)
        
        Returns:
            Tuple of (video_path, error_message)
        """
        if not self.colab_url:
            return None, "Colab URL not configured"
        
        try:
            logger.info(f"🌐 Sending request to Colab GPU server: {self.colab_url}")
            logger.info(f"   Settings: size={size}, preprocess={preprocess}, scale={expression_scale}")
            
            # Read and encode files
            with open(source_image_path, 'rb') as f:
                image_b64 = base64.b64encode(f.read()).decode()
            
            with open(driven_audio_path, 'rb') as f:
                audio_b64 = base64.b64encode(f.read()).decode()
            
            # Prepare request data for Gradio API
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Gradio API format
                data = {
                    "data": [
                        f"data:image/png;base64,{image_b64}",  # source image
                        f"data:audio/wav;base64,{audio_b64}",   # driven audio
                        preprocess,                              # preprocess mode
                        still_mode,                              # still mode
                        expression_scale,                        # expression scale
                        size,                                    # video size
                        enhancer                                 # face enhancer
                    ]
                }
                
                # Call Gradio API endpoint
                api_endpoint = f"{self.colab_url}/api/predict"
                logger.info(f"   Calling: {api_endpoint}")
                
                response = await client.post(api_endpoint, json=data)
                
                if response.status_code != 200:
                    error_msg = f"Colab API error: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return None, error_msg
                
                result = response.json()
                
                # Extract video from response
                if "data" in result and len(result["data"]) > 0:
                    video_data = result["data"][0]
                    
                    # If it's a file path on Colab, need to download it
                    if isinstance(video_data, str) and video_data.startswith("http"):
                        # Download video file
                        video_response = await client.get(video_data)
                        if video_response.status_code == 200:
                            # Save to temp file
                            import tempfile
                            temp_file = tempfile.mktemp(suffix=".mp4")
                            with open(temp_file, 'wb') as f:
                                f.write(video_response.content)
                            
                            logger.info(f"✅ Video generated successfully via Colab GPU")
                            logger.info(f"   Saved to: {temp_file}")
                            return temp_file, None
                    
                    # If it's base64 encoded video
                    elif isinstance(video_data, str) and "base64," in video_data:
                        video_b64 = video_data.split("base64,")[1]
                        video_bytes = base64.b64decode(video_b64)
                        
                        import tempfile
                        temp_file = tempfile.mktemp(suffix=".mp4")
                        with open(temp_file, 'wb') as f:
                            f.write(video_bytes)
                        
                        logger.info(f"✅ Video generated successfully via Colab GPU")
                        logger.info(f"   Saved to: {temp_file}")
                        return temp_file, None
                    
                    # If it's a local file path from Gradio
                    elif isinstance(video_data, dict) and "name" in video_data:
                        file_url = f"{self.colab_url}/file={video_data['name']}"
                        video_response = await client.get(file_url)
                        
                        if video_response.status_code == 200:
                            import tempfile
                            temp_file = tempfile.mktemp(suffix=".mp4")
                            with open(temp_file, 'wb') as f:
                                f.write(video_response.content)
                            
                            logger.info(f"✅ Video generated successfully via Colab GPU")
                            logger.info(f"   Saved to: {temp_file}")
                            return temp_file, None
                
                error_msg = "Could not extract video from Colab response"
                logger.error(f"{error_msg}: {result}")
                return None, error_msg
        
        except httpx.TimeoutException:
            error_msg = "Colab API request timed out"
            logger.error(error_msg)
            return None, error_msg
        
        except Exception as e:
            error_msg = f"Colab API error: {str(e)}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            return None, error_msg
    
    def get_status(self) -> dict:
        """Get status of Colab server"""
        return {
            "configured": bool(self.colab_url),
            "url": self.colab_url,
            "available": self.is_available(),
            "timeout": self.timeout
        }


# Singleton instance
_colab_service = None

def get_colab_service() -> ColabSadTalkerService:
    """Get or create Colab service singleton"""
    global _colab_service
    if _colab_service is None:
        _colab_service = ColabSadTalkerService()
    return _colab_service
