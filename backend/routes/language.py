"""
Language management routes for Rafiki platform.
Handles language detection, preference setting, and multilingual support.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from backend.services.language_service import language_detector
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


class LanguageDetectionRequest(BaseModel):
    text: str
    session_context: Optional[Dict[str, Any]] = None


class LanguagePreferenceRequest(BaseModel):
    language: str  # 'en' or 'sw'
    session_id: Optional[str] = None


class TranslationRequest(BaseModel):
    intent: str
    target_language: str


@router.post("/detect")
async def detect_language(request: LanguageDetectionRequest) -> Dict[str, Any]:
    """
    Detect language of input text.
    
    Returns detected language code and confidence score.
    """
    try:
        language, confidence = language_detector.detect(
            request.text,
            session_context=request.session_context
        )
        
        logger.info(f"Language detected: {language} (confidence: {confidence:.2f})")
        
        return {
            "success": True,
            "language": language,
            "confidence": confidence,
            "language_name": "English" if language == "en" else "Kiswahili",
            "supports_code_switching": language_detector.supports_code_switching()
        }
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-code-switches")
async def detect_code_switches(request: LanguageDetectionRequest) -> Dict[str, Any]:
    """
    Detect code-switching in text (mixed English and Kiswahili).
    
    Returns segments with detected language for each.
    """
    try:
        segments = language_detector.detect_code_switches(request.text)
        
        logger.info(f"Found {len(segments)} code-switch segments")
        
        return {
            "success": True,
            "segments": segments,
            "has_code_switching": len(segments) > 1,
            "primary_language": segments[0]["language"] if segments else "en"
        }
    except Exception as e:
        logger.error(f"Code-switch detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set-preference")
async def set_language_preference(request: LanguagePreferenceRequest) -> Dict[str, Any]:
    """
    Set user's preferred language for the session.
    
    Args:
        language: 'en' for English or 'sw' for Kiswahili
        session_id: Optional session identifier
    """
    try:
        if request.language not in ['en', 'sw']:
            raise HTTPException(
                status_code=400,
                detail="Language must be 'en' (English) or 'sw' (Kiswahili)"
            )
        
        # Set session language
        session_context = {"session_id": request.session_id} if request.session_id else {}
        language_detector.set_session_language(request.language, session_context)
        
        language_name = "English" if request.language == "en" else "Kiswahili"
        
        logger.info(f"Language preference set to: {language_name}")
        
        return {
            "success": True,
            "language": request.language,
            "language_name": language_name,
            "message": f"Language preference set to {language_name}",
            "message_sw": f"Lugha imewekwa kuwa {language_name}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting language preference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-languages")
async def get_supported_languages() -> Dict[str, Any]:
    """
    Get list of supported languages.
    """
    return {
        "success": True,
        "languages": [
            {
                "code": "en",
                "name": "English",
                "name_native": "English",
                "is_official": True,
                "description": "Official language of Kenya"
            },
            {
                "code": "sw",
                "name": "Kiswahili",
                "name_native": "Kiswahili",
                "is_national": True,
                "description": "National language of Kenya"
            }
        ],
        "supports_code_switching": True,
        "default_language": "en"
    }


@router.post("/translate-keywords")
async def translate_keywords(request: TranslationRequest) -> Dict[str, Any]:
    """
    Get intent keywords in target language.
    
    Useful for frontend to display localized suggestions.
    """
    try:
        keywords = language_detector.translate_intent_keywords(
            request.intent,
            request.target_language
        )
        
        if not keywords:
            return {
                "success": False,
                "error": f"No keywords found for intent: {request.intent}"
            }
        
        return {
            "success": True,
            "intent": request.intent,
            "language": request.target_language,
            "keywords": keywords
        }
    except Exception as e:
        logger.error(f"Keyword translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features")
async def get_language_features() -> Dict[str, Any]:
    """
    Get information about language features and capabilities.
    """
    return {
        "success": True,
        "features": {
            "automatic_detection": True,
            "code_switching": True,
            "multilingual_tts": True,
            "context_aware": True,
            "session_persistence": True
        },
        "capabilities": {
            "english": {
                "speech_recognition": True,
                "text_to_speech": True,
                "natural_language_understanding": True,
                "voice_options": ["Noah", "Aria", "Sage", "Rachel"]
            },
            "kiswahili": {
                "speech_recognition": True,
                "text_to_speech": True,
                "natural_language_understanding": True,
                "voice_options": ["Noah", "Aria", "Sage", "Rachel"]
            }
        },
        "notes": [
            "All voices support both English and Kiswahili",
            "Automatic language detection with 85%+ accuracy",
            "Natural code-switching between languages",
            "Warm Kenyan accent for authentic experience"
        ]
    }
