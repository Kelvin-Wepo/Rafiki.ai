"""
ElevenLabs API endpoints.
Provides signed URL generation and TTS functionality.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional
from pydantic import BaseModel

from services.elevenlabs_service import elevenlabs_service
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/elevenlabs", tags=["ElevenLabs"])


class TTSRequest(BaseModel):
    """Text-to-speech request model."""
    text: str
    voice_id: Optional[str] = None
    model_id: str = "eleven_multilingual_v2"


class SignedUrlResponse(BaseModel):
    """Signed URL response model."""
    success: bool
    signed_url: Optional[str] = None
    agent_id: Optional[str] = None
    error: Optional[str] = None


class TTSResponse(BaseModel):
    """TTS response model."""
    success: bool
    audio_data: Optional[str] = None
    content_type: Optional[str] = None
    error: Optional[str] = None


class VoicesResponse(BaseModel):
    """Voices response model."""
    success: bool
    voices: Optional[list] = None
    error: Optional[str] = None


@router.get(
    "/signed-url",
    response_model=SignedUrlResponse,
    summary="Get signed URL for ElevenLabs agent",
    description="Generate a signed WebSocket URL for connecting to ElevenLabs Conversational AI agent"
)
async def get_signed_url(
    agent_id: Optional[str] = Query(None, description="Optional agent ID override")
):
    """
    Get a signed URL for secure WebSocket connection to ElevenLabs agent.
    This allows the frontend to connect without exposing the API key.
    """
    try:
        result = await elevenlabs_service.get_signed_url(agent_id)
        
        if result.get("success"):
            return SignedUrlResponse(
                success=True,
                signed_url=result["signed_url"],
                agent_id=result["agent_id"]
            )
        else:
            return SignedUrlResponse(
                success=False,
                error=result.get("error", "Unknown error")
            )
            
    except Exception as e:
        logger.error(f"Error getting signed URL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tts",
    response_model=TTSResponse,
    summary="Text-to-speech conversion",
    description="Convert text to speech using ElevenLabs TTS API"
)
async def text_to_speech(request: TTSRequest):
    """
    Convert text to speech using ElevenLabs.
    Returns base64-encoded audio data.
    """
    try:
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text is required")
        
        if len(request.text) > 5000:
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        result = await elevenlabs_service.text_to_speech(
            text=request.text,
            voice_id=request.voice_id,
            model_id=request.model_id
        )
        
        if result.get("success"):
            return TTSResponse(
                success=True,
                audio_data=result["audio_data"],
                content_type=result["content_type"]
            )
        else:
            return TTSResponse(
                success=False,
                error=result.get("error", "TTS failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/voices",
    response_model=VoicesResponse,
    summary="Get available voices",
    description="Get list of available ElevenLabs voices"
)
async def get_voices():
    """Get all available ElevenLabs voices."""
    try:
        result = await elevenlabs_service.get_voices()
        
        if result.get("success"):
            return VoicesResponse(
                success=True,
                voices=result["voices"]
            )
        else:
            return VoicesResponse(
                success=False,
                error=result.get("error", "Failed to get voices")
            )
            
    except Exception as e:
        logger.error(f"Error getting voices: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/agent",
    summary="Get agent information",
    description="Get information about the configured ElevenLabs agent"
)
async def get_agent_info(
    agent_id: Optional[str] = Query(None, description="Optional agent ID override")
):
    """Get information about an ElevenLabs conversational agent."""
    try:
        result = await elevenlabs_service.get_agent_info(agent_id)
        return result
    except Exception as e:
        logger.error(f"Error getting agent info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    summary="Health check",
    description="Check if ElevenLabs service is configured and accessible"
)
async def health_check():
    """Check ElevenLabs service health."""
    from config import get_settings
    settings = get_settings()
    
    return {
        "status": "ok",
        "configured": bool(settings.ELEVENLABS_API_KEY),
        "agent_id": settings.ELEVENLABS_AGENT_ID,
        "voice_id": settings.ELEVENLABS_VOICE_ID
    }
