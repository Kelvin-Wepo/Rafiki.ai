"""
Avatar Routes - Imagen + SadTalker Integration
Generate African avatars and create talking head videos
"""

from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import tempfile
import logging
from typing import Optional
from pydantic import BaseModel
from services.imagen_service import imagen_service
from services.sadtalker_service import get_sadtalker_service
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/avatar", tags=["Avatar Generation"])


class AvatarRequest(BaseModel):
    """Request model for avatar generation"""
    name: str
    skin_tone: str  # light, medium, dark
    hair_style: str  # natural, braids, twists, straight
    clothing: str  # professional_suit, traditional, casual, formal
    personality: str  # warm_friendly, professional, patient, encouraging
    background: str  # office, traditional, neutral, government
    language: str = "en-KE"


@router.post("/generate")
async def generate_avatar(request: AvatarRequest):
    """
    Generate an African avatar using Imagen.
    
    Args:
        request: Avatar configuration
    
    Returns:
        Avatar data with image prompt and configuration
    """
    try:
        logger.info(f"Generating avatar: {request.name}")
        
        result = imagen_service.generate_african_avatar(
            name=request.name,
            skin_tone=request.skin_tone,
            hair_style=request.hair_style,
            clothing=request.clothing,
            personality=request.personality,
            background=request.background,
            language=request.language
        )
        
        if result:
            return {
                "success": True,
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate avatar")
    
    except Exception as e:
        logger.error(f"Error generating avatar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-talking-video")
async def generate_talking_video(
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    still: bool = Form(False),
    preprocess: str = Form("crop"),
    pose_style: int = Form(0),
    exp_scale: float = Form(1.0)
):
    """
    Generate a talking head video from image and audio using SadTalker.
    
    Args:
        image: Avatar image file
        audio: Audio file for speech
        still: Keep face still (no head movement)
        preprocess: Preprocessing mode (crop, resize, full)
        pose_style: Head movement style (0=still, 1=natural, 2=expressive)
        exp_scale: Expression intensity (0.5-1.5)
    
    Returns:
        Generated video file
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded files
        image_path = os.path.join(temp_dir, f"image.{image.filename.split('.')[-1]}")
        audio_path = os.path.join(temp_dir, f"audio.{audio.filename.split('.')[-1]}")
        
        with open(image_path, "wb") as f:
            f.write(await image.read())
        
        with open(audio_path, "wb") as f:
            f.write(await audio.read())
        
        logger.info(f"Processing: image={image.filename}, audio={audio.filename}")
        
        # Get SadTalker service
        sadtalker_service = get_sadtalker_service()
        
        # Generate talking video
        output_path, error = await sadtalker_service.generate_video(
            audio_path=audio_path,
            avatar_id="custom",
            preprocess=preprocess,
            still_mode=still,
            expression_scale=exp_scale
        )
        
        if error or not output_path:
            logger.error(f"Video generation failed: {error}")
            raise HTTPException(status_code=500, detail=error or "Video generation failed")
        
        if not os.path.exists(output_path):
            logger.error(f"Output video not found: {output_path}")
            raise HTTPException(status_code=500, detail="Video file not created")
        
        logger.info(f"Video generated successfully: {output_path}")
        
        return FileResponse(
            output_path,
            media_type="video/mp4",
            filename=f"talking_avatar_{image.filename.split('.')[0]}.mp4"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating talking video: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/configurations")
async def get_configurations():
    """Get available avatar configurations"""
    return {
        "skin_tones": ["light", "medium", "dark"],
        "hair_styles": ["natural", "braids", "twists", "straight"],
        "clothing": [
            "professional_suit",
            "traditional",
            "casual",
            "formal"
        ],
        "personalities": [
            "warm_friendly",
            "professional",
            "patient",
            "encouraging"
        ],
        "backgrounds": [
            "office",
            "traditional",
            "neutral",
            "government"
        ],
        "languages": ["en-KE", "en-US", "en-GB", "sw-KE"],
        "pose_styles": [
            {"id": 0, "name": "Still", "description": "No head movement"},
            {"id": 1, "name": "Natural", "description": "Natural head motion"},
            {"id": 2, "name": "Expressive", "description": "More expressive movement"}
        ]
    }


@router.get("/health")
async def health_check():
    """Check avatar generation service health"""
    return {
        "status": "healthy",
        "services": {
            "imagen": imagen_service._initialized,
            "sadtalker": True
        }
    }
