"""
Avatar Routes
API endpoints for talking avatar functionality
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import logging

from services.sadtalker_service import get_sadtalker_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/avatar", tags=["avatar"])


class TextToVideoRequest(BaseModel):
    """Request model for text-to-video generation"""
    text: str
    avatar_id: str = "habari"
    language: str = "en"


class VideoGenerationResponse(BaseModel):
    """Response model for video generation"""
    success: bool
    video_url: Optional[str] = None
    error: Optional[str] = None


@router.get("/list")
async def list_avatars():
    """
    Get list of available avatars
    
    Returns:
        List of avatar objects with id, name, and preview URL
    """
    try:
        service = get_sadtalker_service()
        avatars = service.get_available_avatars()
        
        return {
            "success": True,
            "avatars": avatars,
            "default": "habari"
        }
        
    except Exception as e:
        logger.error(f"Error listing avatars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_video(
    audio: UploadFile = File(...),
    avatar_id: str = Form(default="habari"),
    preprocess: str = Form(default="crop"),
    still_mode: bool = Form(default=False),
    expression_scale: float = Form(default=1.0)
):
    """
    Generate a lip-synced video from audio file
    
    Args:
        audio: Audio file (WAV, MP3, etc.)
        avatar_id: ID of the avatar to use
        preprocess: Preprocessing mode ('crop', 'resize', 'full')
        still_mode: If True, only animate mouth
        expression_scale: Scale of expressions (0.0-2.0)
    
    Returns:
        Generated video file or error message
    """
    try:
        # Save uploaded audio to temp file
        audio_path = tempfile.mktemp(suffix=os.path.splitext(audio.filename)[1])
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # Generate video
        service = get_sadtalker_service()
        video_path, error = await service.generate_video(
            audio_path=audio_path,
            avatar_id=avatar_id,
            preprocess=preprocess,
            still_mode=still_mode,
            expression_scale=expression_scale
        )
        
        # Cleanup audio temp file
        os.unlink(audio_path)
        
        if video_path:
            return FileResponse(
                video_path,
                media_type="video/mp4",
                filename="habari_response.mp4"
            )
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": error or "Video generation failed",
                    "fallback": True,
                    "message": "Using animated avatar fallback"
                }
            )
            
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "fallback": True
            }
        )


@router.post("/text-to-video")
async def text_to_video(request: TextToVideoRequest, background_tasks: BackgroundTasks):
    """
    Generate a talking head video from text
    
    Args:
        text: Text to speak
        avatar_id: Avatar to use
        language: Language for TTS (en/sw)
    
    Returns:
        Video file or error with fallback indication
    """
    try:
        service = get_sadtalker_service()
        video_path, error = await service.text_to_video(
            text=request.text,
            avatar_id=request.avatar_id,
            language=request.language
        )
        
        if video_path:
            return FileResponse(
                video_path,
                media_type="video/mp4",
                filename="habari_response.mp4"
            )
        else:
            # Return fallback indicator for client to use animated avatar
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": error or "Video generation not available",
                    "fallback": True,
                    "message": "SadTalker not available. Using animated avatar."
                }
            )
            
    except Exception as e:
        logger.error(f"Text to video error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "fallback": True
            }
        )


@router.get("/status")
async def get_service_status():
    """
    Check if SadTalker service is available
    
    Returns:
        Service status and capabilities
    """
    try:
        service = get_sadtalker_service()
        avatars = service.get_available_avatars()
        
        # Check if API is reachable
        import httpx
        api_available = False
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{service.api_url}/api/predict")
                api_available = response.status_code in [200, 405]  # 405 = method not allowed but reachable
        except:
            pass
        
        return {
            "success": True,
            "api_available": api_available,
            "mode": service.mode,
            "avatars_count": len(avatars),
            "capabilities": {
                "video_generation": api_available,
                "animated_fallback": True,
                "supported_formats": ["wav", "mp3", "ogg"],
                "max_duration_seconds": 60
            }
        }
        
    except Exception as e:
        logger.error(f"Status check error: {e}")
        return {
            "success": False,
            "api_available": False,
            "error": str(e),
            "capabilities": {
                "animated_fallback": True
            }
        }
