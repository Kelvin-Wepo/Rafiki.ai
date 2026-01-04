"""
Avatar Animation API Routes

Endpoints for generating talking head videos with SadTalker:
- /api/avatar/animate - Generate video from audio
- /api/avatar/text-to-video - Generate video from text
- /api/avatar/preprocess-image - Preprocess image for animation
- /api/avatar/settings - Get/update animation settings
- /api/avatar/cache - Manage animation cache
"""

import os
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import tempfile
from typing import Optional

from backend.services.sadtalker_service import SadTalkerService
from backend.services.image_preprocessing_service import ImagePreprocessingService
from backend.services.elevenlabs_service import ElevenLabsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/avatar", tags=["avatar-animation"])

# Initialize services
sadtalker_service = SadTalkerService()
preprocess_service = ImagePreprocessingService()
elevenlabs_service = ElevenLabsService()


@router.post("/animate")
async def animate_avatar(
    audio_file: UploadFile = File(...),
    avatar_id: str = Form(default="habari"),
    preprocess: str = Form(default="crop"),
    still_mode: bool = Form(default=False),
    expression_scale: float = Form(default=1.0),
    background_tasks: BackgroundTasks = None
):
    """
    Generate talking avatar video from audio file

    Args:
        audio_file: Audio file (WAV, MP3, OGG)
        avatar_id: ID of avatar to animate
        preprocess: Preprocessing mode ('crop', 'resize', 'full')
        still_mode: If True, only animate mouth
        expression_scale: Scale of facial expressions (0.0-2.0)

    Returns:
        Video file or error message
    """
    try:
        # Validate audio file
        if audio_file.size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=400, detail="Audio file too large (max 50MB)")

        allowed_types = {'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/mp4'}
        if audio_file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid audio format: {audio_file.content_type}")

        # Save audio temporarily
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        contents = await audio_file.read()
        temp_audio.write(contents)
        temp_audio.close()

        try:
            # Generate video
            logger.info(f"Generating video for avatar '{avatar_id}' from audio")
            video_path, error = await sadtalker_service.generate_video(
                audio_path=temp_audio.name,
                avatar_id=avatar_id,
                preprocess=preprocess,
                still_mode=still_mode,
                expression_scale=expression_scale
            )

            if error:
                raise HTTPException(status_code=500, detail=f"Video generation failed: {error}")

            # Schedule cleanup
            if background_tasks:
                background_tasks.add_task(os.unlink, temp_audio.name)

            # Return video file
            return FileResponse(
                path=video_path,
                media_type="video/mp4",
                filename=f"avatar_{avatar_id}_talking.mp4"
            )

        finally:
            # Cleanup temp audio
            if os.path.exists(temp_audio.name):
                try:
                    os.unlink(temp_audio.name)
                except:
                    pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Avatar animation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text-to-video")
async def text_to_video(
    text: str = Form(...),
    avatar_id: str = Form(default="habari"),
    language: str = Form(default="en"),
    use_elevenlabs: bool = Form(default=True),
    background_tasks: BackgroundTasks = None
):
    """
    Generate talking avatar video from text

    Args:
        text: Text to speak
        avatar_id: ID of avatar to animate
        language: Language for TTS
        use_elevenlabs: Use ElevenLabs for TTS (better quality)
        background_tasks: FastAPI background tasks

    Returns:
        Video file or error message
    """
    try:
        # Validate text
        if not text or len(text) > 2000:
            raise HTTPException(
                status_code=400,
                detail="Text must be between 1 and 2000 characters"
            )

        logger.info(f"Generating video for text: {text[:50]}...")

        # Generate audio using appropriate service
        voice_service = elevenlabs_service if use_elevenlabs else None

        video_path, error = await sadtalker_service.text_to_video(
            text=text,
            avatar_id=avatar_id,
            voice_service=voice_service,
            language=language
        )

        if error:
            raise HTTPException(status_code=500, detail=f"Video generation failed: {error}")

        return FileResponse(
            path=video_path,
            media_type="video/mp4",
            filename=f"avatar_{avatar_id}_response.mp4"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text to video error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preprocess-image")
async def preprocess_image(
    image_file: UploadFile = File(...),
    output_format: str = Form(default="jpeg"),
    quality: int = Form(default=95)
):
    """
    Preprocess image for SadTalker animation

    Args:
        image_file: Avatar image file
        output_format: Output format ('jpeg' or 'png')
        quality: JPEG quality (1-100)

    Returns:
        Preprocessed image or error message
    """
    try:
        # Validate image file
        if image_file.size > 20 * 1024 * 1024:  # 20MB limit
            raise HTTPException(status_code=400, detail="Image file too large (max 20MB)")

        allowed_types = {'image/jpeg', 'image/png', 'image/webp'}
        if image_file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"Invalid image format: {image_file.content_type}")

        # Save image temporarily
        temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        contents = await image_file.read()
        temp_image.write(contents)
        temp_image.close()

        try:
            # Preprocess image
            logger.info(f"Preprocessing image: {image_file.filename}")
            output_path = tempfile.mktemp(suffix=f".{output_format}")

            result = preprocess_service.preprocess_image(
                input_path=temp_image.name,
                output_path=output_path,
                target_size=(512, 512),
                quality=quality
            )

            if not result['success']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Preprocessing failed: {', '.join(result['errors'])}"
                )

            return FileResponse(
                path=output_path,
                media_type=f"image/{output_format}",
                filename=f"avatar_processed.{output_format}"
            )

        finally:
            if os.path.exists(temp_image.name):
                try:
                    os.unlink(temp_image.name)
                except:
                    pass

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image preprocessing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_settings():
    """Get current animation settings"""
    try:
        settings = sadtalker_service.get_settings()
        return {
            'success': True,
            'settings': settings
        }
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/settings")
async def update_settings(
    still_mode: Optional[bool] = None,
    preprocess: Optional[str] = None,
    expression_scale: Optional[float] = None,
    pose_style: Optional[int] = None
):
    """Update animation settings"""
    try:
        kwargs = {}
        if still_mode is not None:
            kwargs['still_mode'] = still_mode
        if preprocess is not None:
            kwargs['preprocess'] = preprocess
        if expression_scale is not None:
            kwargs['expression_scale'] = expression_scale
        if pose_style is not None:
            kwargs['pose_style'] = pose_style

        sadtalker_service.update_settings(**kwargs)

        return {
            'success': True,
            'settings': sadtalker_service.get_settings()
        }
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/avatars")
async def get_available_avatars():
    """Get list of available avatars"""
    try:
        avatars = sadtalker_service.get_available_avatars()
        return {
            'success': True,
            'avatars': avatars
        }
    except Exception as e:
        logger.error(f"Error getting avatars: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = sadtalker_service.get_cache_stats()
        return {
            'success': True,
            'stats': stats
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cache/clear")
async def clear_cache():
    """Clear animation cache"""
    try:
        success = sadtalker_service.clear_cache()
        return {
            'success': success,
            'message': 'Cache cleared' if success else 'Failed to clear cache'
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for avatar animation service"""
    return {
        'status': 'healthy',
        'service': 'avatar-animation',
        'mode': sadtalker_service.mode,
        'cache_stats': sadtalker_service.get_cache_stats()
    }
