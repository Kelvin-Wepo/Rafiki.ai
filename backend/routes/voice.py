"""
Voice processing API endpoints.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from models.schemas import (
    VoiceInputRequest,
    TextInputRequest,
    AssistantResponse,
    TranscriptionResponse,
    TTSResponse,
    ErrorResponse
)
from services.voice_service import voice_service
from services.gemini_service import gemini_service
from services.dialogflow_service import dialogflow_service
from services.booking_service import booking_service
from utils.session_manager import session_manager
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger, RequestLogger
from config import ASSISTANT_RESPONSES

logger = get_logger(__name__)
router = APIRouter(prefix="/voice", tags=["Voice Processing"])


async def check_rate_limit(request: Request):
    """Dependency to check rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    result = await rate_limiter.check_rate_limit(client_ip)
    
    if not result.allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": result.retry_after_seconds,
                "reset_time": result.reset_time.isoformat()
            }
        )
    
    return result


@router.post(
    "/process",
    response_model=AssistantResponse,
    summary="Process voice or text input",
    description="Process user input (voice or text) and return assistant response"
)
async def process_input(
    request: VoiceInputRequest,
    rate_limit: dict = Depends(check_rate_limit)
):
    """
    Process voice or text input from the user.
    
    - **audio_data**: Base64 encoded audio (optional)
    - **text_input**: Text input as fallback (optional)
    - **session_id**: Session identifier for conversation tracking
    - **input_mode**: 'voice' or 'text'
    - **language**: Language code (default: en-KE)
    """
    with RequestLogger(logger, "process_input", session_id=request.session_id):
        try:
            # Get or validate session
            session = await session_manager.get_session(request.session_id)
            if not session:
                # Create new session if doesn't exist
                session = await session_manager.create_session()
            
            # Get user text (from voice or direct text)
            user_text = None
            
            if request.input_mode.value == "voice" and request.audio_data:
                # Transcribe audio
                transcription = await voice_service.transcribe_audio(
                    request.audio_data,
                    language=request.language
                )
                
                if transcription.get("success"):
                    user_text = transcription.get("text", "")
                else:
                    return AssistantResponse(
                        text="I couldn't understand the audio. Please try again or type your message.",
                        session_id=session.session_id,
                        requires_input=True,
                        suggested_actions=["Try again", "Switch to text input"]
                    )
            
            elif request.text_input:
                user_text = request.text_input
            
            if not user_text:
                return AssistantResponse(
                    text="I didn't receive any input. Please speak or type your message.",
                    session_id=session.session_id,
                    requires_input=True,
                    suggested_actions=["Speak", "Type a message"]
                )
            
            # Process with Dialogflow for conversation management
            dialogflow_result = await dialogflow_service.detect_intent(
                user_text,
                session.session_id,
                {
                    "conversation_context": session.conversation_context.get("context", "welcome"),
                    "entities": session.booking_state
                }
            )
            
            # Check if we need to complete a booking
            if dialogflow_result.get("action") == "complete_booking":
                booking_result = await _complete_booking(session)
                if booking_result:
                    dialogflow_result["response"] = booking_result["message"]
            
            # Determine the response language (sw for Kiswahili, en for English)
            response_language = "sw" if request.language.startswith("sw") else "en"
            
            # Use Gemini for enhanced responses if needed
            gemini_response = None
            if dialogflow_result.get("intent") in ["unknown", "fallback"]:
                gemini_response = await gemini_service.process_message(
                    user_text,
                    conversation_history=session.conversation_context.get("history", []),
                    context={
                        "booking_state": session.booking_state,
                        "last_intent": session.conversation_context.get("last_intent")
                    },
                    language=response_language
                )
            
            # Determine final response
            response_text = dialogflow_result.get("response") or \
                          (gemini_response.get("text") if gemini_response else None) or \
                          "I'm not sure how to help with that. Please say 'help' for available options."
            
            intent = dialogflow_result.get("intent", "unknown")
            entities = dialogflow_result.get("entities", {})
            
            # Update session
            await session_manager.update_session(
                session.session_id,
                conversation_context={
                    "context": dialogflow_result.get("context", "welcome"),
                    "last_intent": intent,
                    "history": session.conversation_context.get("history", [])[-10:] + [
                        {"role": "user", "content": user_text},
                        {"role": "assistant", "content": response_text}
                    ]
                },
                booking_state=entities if entities else session.booking_state
            )
            
            # Get conversation state for UI
            conv_state = dialogflow_service.get_conversation_state({
                "conversation_context": dialogflow_result.get("context", "welcome"),
                "entities": entities or session.booking_state
            })
            
            return AssistantResponse(
                text=response_text,
                session_id=session.session_id,
                intent=intent,
                entities=entities,
                requires_input=dialogflow_result.get("requires_input", True),
                suggested_actions=dialogflow_result.get("suggested_actions", []),
                context={
                    "conversation_state": conv_state,
                    "transcribed_text": user_text
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            raise HTTPException(status_code=500, detail=str(e))


async def _complete_booking(session) -> Optional[dict]:
    """Complete a booking with collected information."""
    from models.schemas import ServiceType, TimeSlot
    from datetime import date, timedelta
    
    booking_state = session.booking_state
    
    service_type = booking_state.get("service_type")
    user_name = booking_state.get("user_name")
    phone_number = booking_state.get("phone_number")
    time_slot = booking_state.get("time_slot")
    
    if not all([service_type, user_name, phone_number, time_slot]):
        return None
    
    try:
        # Map service type
        service_map = {
            "passport": ServiceType.PASSPORT,
            "national_id": ServiceType.NATIONAL_ID,
            "driving_license": ServiceType.DRIVING_LICENSE,
            "good_conduct": ServiceType.GOOD_CONDUCT
        }
        
        # Map time slot
        slot_map = {
            "08:00-12:00": TimeSlot.MORNING,
            "14:00-17:00": TimeSlot.AFTERNOON,
            "morning": TimeSlot.MORNING,
            "afternoon": TimeSlot.AFTERNOON
        }
        
        service = service_map.get(service_type)
        slot = slot_map.get(time_slot)
        
        if not service or not slot:
            return None
        
        # Default to next business day
        appointment_date = date.today() + timedelta(days=1)
        while appointment_date.weekday() >= 5:  # Skip weekends
            appointment_date += timedelta(days=1)
        
        result = await booking_service.create_booking(
            service_type=service,
            user_name=user_name,
            phone_number=phone_number,
            time_slot=slot,
            appointment_date=appointment_date,
            send_sms=True
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error completing booking: {e}")
        return None


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe audio to text",
    description="Convert audio input to text using speech recognition"
)
async def transcribe_audio(
    request: VoiceInputRequest,
    rate_limit: dict = Depends(check_rate_limit)
):
    """
    Transcribe audio data to text.
    
    - **audio_data**: Base64 encoded audio data
    - **language**: Language code for recognition (default: en-KE)
    """
    if not request.audio_data:
        raise HTTPException(status_code=400, detail="No audio data provided")
    
    result = await voice_service.transcribe_audio(
        request.audio_data,
        language=request.language
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=422,
            detail=result.get("error", "Transcription failed")
        )
    
    return TranscriptionResponse(
        text=result["text"],
        confidence=result.get("confidence", 0.0),
        language=result.get("language", request.language)
    )


@router.post(
    "/speak",
    response_model=TTSResponse,
    summary="Convert text to speech",
    description="Convert text to audio using text-to-speech"
)
async def text_to_speech(
    text: str,
    rate_limit: dict = Depends(check_rate_limit)
):
    """
    Convert text to speech audio.
    
    - **text**: Text to convert to speech
    """
    if not text or len(text) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Text must be between 1 and 1000 characters"
        )
    
    result = await voice_service.text_to_speech(text)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "TTS conversion failed")
        )
    
    return TTSResponse(
        audio_data=result["audio_data"],
        audio_format=result.get("audio_format", "wav")
    )


@router.get(
    "/voices",
    summary="Get available TTS voices",
    description="Get list of available text-to-speech voices"
)
async def get_voices():
    """Get available TTS voices."""
    voices = voice_service.get_available_voices()
    return {"voices": voices}


@router.post(
    "/settings",
    summary="Update voice settings",
    description="Update text-to-speech settings"
)
async def update_voice_settings(
    rate: Optional[int] = 160,  # Default to normal conversational speed
    volume: Optional[float] = None,
    voice_id: Optional[int] = None
):
    """
    Update TTS settings.
    
    - **rate**: Speech rate (words per minute, 100-300, default: 160)
    - **volume**: Volume level (0.0 to 1.0)
    - **voice_id**: Voice index from available voices
    """
    if rate is not None and not (100 <= rate <= 300):
        raise HTTPException(status_code=400, detail="Rate must be between 100 and 300")
    
    if volume is not None and not (0.0 <= volume <= 1.0):
        raise HTTPException(status_code=400, detail="Volume must be between 0.0 and 1.0")
    
    success = voice_service.set_voice_properties(
        rate=rate,
        volume=volume,
        voice_id=voice_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update settings")
    
    return {"success": True, "message": "Voice settings updated"}


@router.post(
    "/chat",
    response_model=AssistantResponse,
    summary="Chat with Gemini AI",
    description="Send a text message to Gemini and get response with automation commands"
)
async def chat_with_gemini(
    request: dict,
    rate_limit: dict = Depends(check_rate_limit)
):
    """
    Chat endpoint for direct Gemini interaction with automation support.
    
    - **message**: User's text message
    - **language**: Language code ('en' or 'sw')
    - **session_id**: Optional session identifier
    """
    message = request.get("message", "")
    language = request.get("language", "en")
    session_id = request.get("session_id")
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        # Get or create session
        session = None
        if session_id:
            session = await session_manager.get_session(session_id)
        if not session:
            session = await session_manager.create_session()
        
        # Process with Gemini
        gemini_response = await gemini_service.process_message(
            message,
            conversation_history=session.conversation_context.get("history", []),
            context={
                "booking_state": session.booking_state,
                "last_intent": session.conversation_context.get("last_intent")
            },
            language=language
        )
        
        # Update session history
        await session_manager.update_session(
            session.session_id,
            conversation_context={
                "context": gemini_response.get("intent", "chat"),
                "last_intent": gemini_response.get("intent"),
                "history": session.conversation_context.get("history", [])[-10:] + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": gemini_response.get("text", "")}
                ]
            },
            booking_state=gemini_response.get("entities", session.booking_state)
        )
        
        return AssistantResponse(
            text=gemini_response.get("text", "I'm not sure how to help with that."),
            session_id=session.session_id,
            intent=gemini_response.get("intent", "unknown"),
            entities=gemini_response.get("entities", {}),
            requires_input=gemini_response.get("requires_input", True),
            suggested_actions=gemini_response.get("suggested_actions", []),
            automation=gemini_response.get("automation", {"action": "none"}),
            context={}
        )
        
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/analyze-automation",
    summary="Analyze text for automation",
    description="Analyze text to extract automation commands without full conversation"
)
async def analyze_for_automation(request: dict):
    """
    Analyze text for automation commands.
    Used to extract navigation/autofill commands from ElevenLabs responses.
    
    - **text**: Text to analyze (usually AI response)
    - **language**: Language code
    """
    text = request.get("text", "")
    language = request.get("language", "en")
    
    if not text:
        return {"automation": {"action": "none"}, "entities": {}}
    
    try:
        # Quick analysis prompt
        analysis_prompt = f"""Analyze this assistant response and extract any automation commands.
        
Response to analyze: "{text}"

Return JSON with:
{{
    "automation": {{
        "action": "navigate/autofill/click/none",
        "target_url": "eCitizen URL if navigating",
        "form_data": {{}},
        "element_to_click": null
    }},
    "entities": {{
        "service_type": "passport/national_id/driving_license/good_conduct or null",
        "user_name": null,
        "phone_number": null,
        "id_number": null
    }}
}}

eCitizen URLs:
- Passport: https://accounts.ecitizen.go.ke/en/services/passport
- National ID: https://accounts.ecitizen.go.ke/en/services/id
- Driving License: https://accounts.ecitizen.go.ke/en/services/dl
- Good Conduct: https://accounts.ecitizen.go.ke/en/services/goodconduct"""

        import json
        response = gemini_service._model.generate_content(analysis_prompt)
        
        # Parse JSON from response
        response_text = response.text
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            result = json.loads(response_text[json_start:json_end])
            return result
        
        return {"automation": {"action": "none"}, "entities": {}}
        
    except Exception as e:
        logger.error(f"Error analyzing automation: {e}")
        return {"automation": {"action": "none"}, "entities": {}}
