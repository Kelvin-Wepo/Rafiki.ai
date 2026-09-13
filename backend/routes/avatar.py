"""
Avatar Routes
API endpoints for talking avatar functionality
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Depends
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os
import logging
import aiofiles
import base64
import struct

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


@router.get("/image")
async def get_avatar_image():
    """
    Serve the Rafiki avatar image
    
    Returns:
        PNG image file of the Rafiki avatar
    """
    try:
        avatar_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "assets",
            "avatars",
            "rafiki_avatar.png"
        )
        
        if not os.path.exists(avatar_path):
            logger.warning(f"Avatar image not found at {avatar_path}")
            raise HTTPException(status_code=404, detail="Avatar image not found")
        
        return FileResponse(
            avatar_path,
            media_type="image/png",
            filename="rafiki_avatar.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving avatar image: {e}")
        raise HTTPException(status_code=500, detail=f"Error serving avatar: {str(e)}")


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


@router.post("/generate-lip-sync")
async def generate_lip_sync_video(
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Generate lip-synced talking head video using Wav2Lip
    
    This endpoint creates a high-quality lip-synced video by:
    1. Taking an avatar image
    2. Processing audio to extract mel-spectrogram
    3. Using Wav2Lip model to animate lips
    4. Returning MP4 video with perfect audio-video sync
    
    Args:
        image: Avatar image file (PNG, JPG, etc.)
        audio: Audio file (WAV, MP3, etc.)
        background_tasks: For cleanup operations
    
    Returns:
        MP4 video file with lip-synced talking head
        or error response with fallback indicators
    
    Performance:
        - 1-minute video: ~15-30 seconds generation time
        - GPU memory: ~2-3GB (vs 8-10GB for SadTalker)
        - Quality: 9/10 lip-sync accuracy
    """
    temp_files = []
    
    try:
        # Create temp directory
        temp_dir = tempfile.mkdtemp(prefix="wav2lip_")
        
        # Save uploaded image
        image_ext = os.path.splitext(image.filename)[1]
        image_path = os.path.join(temp_dir, f"avatar{image_ext}")
        
        async with aiofiles.open(image_path, 'wb') as f:
            await f.write(await image.read())
        temp_files.append(image_path)
        
        logger.info(f"Image saved: {image_path}")
        
        # Save uploaded audio
        audio_ext = os.path.splitext(audio.filename)[1]
        audio_path = os.path.join(temp_dir, f"audio{audio_ext}")
        
        async with aiofiles.open(audio_path, 'wb') as f:
            await f.write(await audio.read())
        temp_files.append(audio_path)
        
        logger.info(f"Audio saved: {audio_path}")
        
        # Validate files
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            raise ValueError("Invalid image file")
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise ValueError("Invalid audio file")
        
        # Generate video using Wav2Lip
        logger.info("Starting Wav2Lip video generation...")
        from services.wav2lip_service import get_wav2lip_service
        wav2lip = get_wav2lip_service()
        
        video_path = await wav2lip.generate_video(
            image_path=image_path,
            audio_path=audio_path,
            fps=25
        )
        
        logger.info(f"Video generated successfully: {video_path}")
        
        # Schedule cleanup of temp files
        if background_tasks:
            background_tasks.add_task(cleanup_files, temp_files)
        
        # Return video file
        return FileResponse(
            video_path,
            media_type="video/mp4",
            filename="talking_head.mp4",
            headers={
                "Content-Disposition": "attachment; filename=talking_head.mp4"
            }
        )
    
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        cleanup_files(temp_files)
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e),
                "fallback": True,
                "message": "Invalid input files. Using animated avatar fallback."
            }
        )
    
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        cleanup_files(temp_files)
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "Wav2Lip model not available",
                "fallback": True,
                "message": "Using animated avatar instead. Install Wav2Lip to enable lip-sync video."
            }
        )
    
    except Exception as e:
        logger.error(f"Unexpected error in lip-sync generation: {e}", exc_info=True)
        cleanup_files(temp_files)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "fallback": True,
                "message": "Video generation failed. Using animated avatar fallback."
            }
        )


@router.get("/lip-sync/status")
async def get_lip_sync_status():
    """
    Check if Wav2Lip service is ready and get status
    
    Returns:
        Service status, available device (CPU/GPU), cached videos count
    """
    try:
        from services.wav2lip_service import get_wav2lip_service
        service = get_wav2lip_service()
        status = service.get_status()
        
        return {
            "success": True,
            "service": "wav2lip",
            **status
        }
    except Exception as e:
        logger.error(f"Error checking Wav2Lip status: {e}")
        return {
            "success": False,
            "service": "wav2lip",
            "available": False,
            "error": str(e)
        }


def cleanup_files(file_paths: list):
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {file_path}: {e}")


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


class LipsyncPreviewRequest(BaseModel):
    text: str = "Habari! Mimi ni Rafiki."
    language: str = "en"


@router.get("/lipsync/config")
async def lipsync_config():
    """Mouth-region coordinates and viseme extraction status for the canvas avatar."""
    from services.viseme_service import mouth_region_config, rhubarb_bin

    return {
        "success": True,
        "mouth_region": mouth_region_config(),
        "rhubarb_available": bool(rhubarb_bin()),
        "source_order": ["elevenlabs_timestamps", "rhubarb", "pcm_energy"],
    }


@router.post("/lipsync/preview")
async def lipsync_preview(request: LipsyncPreviewRequest):
    """TTS + viseme timeline for the /lipsync-demo tuner. Never raises on viseme failure."""
    from services.elevenlabs_service import elevenlabs_service
    from services.viseme_service import get_viseme_timeline, mouth_region_config

    text = (request.text or "").strip()[:500]
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    result = await elevenlabs_service.text_to_speech(
        text=text,
        language=request.language,
        include_visemes=True,
    )
    if result.get("success") and result.get("audio_data"):
        visemes = result.get("viseme_timeline") or []
        if not visemes:
            audio_bytes = base64.b64decode(result["audio_data"])
            visemes = get_viseme_timeline(audio_bytes, text=text)
        return {
            "success": True,
            "audio_base64": result["audio_data"],
            "audio_mime": result.get("content_type") or "audio/mpeg",
            "viseme_timeline": visemes,
            "mouth_region": mouth_region_config(),
            "fallback": not bool(result.get("viseme_timeline")),
        }

    # Tiny amplitude-modulated tone so the demo still exercises the canvas.
    import io
    import math
    import wave as wave_mod

    sample_rate = 22050
    duration_s = 1.2
    frames = bytearray()
    for i in range(int(sample_rate * duration_s)):
        t = i / sample_rate
        envelope = 0.15 + 0.85 * abs(math.sin(t * 9.0))
        sample = int(12000 * envelope * math.sin(2 * math.pi * 220 * t))
        frames += struct.pack("<h", max(-32767, min(32767, sample)))

    buf = io.BytesIO()
    with wave_mod.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(bytes(frames))
    wav_bytes = buf.getvalue()
    timeline = get_viseme_timeline(wav_bytes, text=text)
    return {
        "success": True,
        "audio_base64": base64.b64encode(wav_bytes).decode("utf-8"),
        "audio_mime": "audio/wav",
        "viseme_timeline": timeline,
        "mouth_region": mouth_region_config(),
        "fallback": True,
        "note": result.get("error") or "TTS unavailable; playing a tone so you can still check mouth motion.",
    }
