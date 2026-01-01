"""
Session management API endpoints.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request

from models.schemas import SessionCreateRequest, SessionResponse
from utils.session_manager import session_manager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/session", tags=["Session"])


@router.post(
    "/create",
    response_model=SessionResponse,
    summary="Create a new session",
    description="Create a new conversation session"
)
async def create_session(
    request: Optional[SessionCreateRequest] = None
):
    """
    Create a new session for conversation tracking.
    
    - **user_agent**: Optional user agent string
    - **accessibility_preferences**: Optional accessibility settings
    
    Returns session details including session_id and expiration time.
    """
    preferences = {}
    if request:
        preferences = request.accessibility_preferences or {}
    
    session = await session_manager.create_session(user_preferences=preferences)
    
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        expires_at=session.expires_at,
        is_active=session.is_active
    )


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    summary="Get session details",
    description="Get details of an existing session"
)
async def get_session(session_id: str):
    """
    Get session details by ID.
    
    - **session_id**: Session identifier
    
    Returns session details or 404 if not found/expired.
    """
    session = await session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        expires_at=session.expires_at,
        is_active=session.is_active
    )


@router.get(
    "/{session_id}/state",
    summary="Get session conversation state",
    description="Get the current conversation state and booking progress"
)
async def get_session_state(session_id: str):
    """
    Get the conversation state for a session.
    
    - **session_id**: Session identifier
    
    Returns conversation context, booking state, and progress information.
    """
    session = await session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    # Calculate booking progress
    booking_state = session.booking_state
    required_fields = ["service_type", "user_name", "phone_number", "time_slot"]
    completed_fields = [f for f in required_fields if booking_state.get(f)]
    progress = len(completed_fields) / len(required_fields) * 100
    
    return {
        "session_id": session.session_id,
        "conversation_context": session.conversation_context,
        "booking_state": booking_state,
        "booking_progress": {
            "percentage": progress,
            "completed_fields": completed_fields,
            "remaining_fields": [f for f in required_fields if f not in completed_fields]
        },
        "user_preferences": session.user_preferences,
        "last_activity": session.last_activity.isoformat()
    }


@router.patch(
    "/{session_id}/preferences",
    summary="Update session preferences",
    description="Update accessibility and user preferences for a session"
)
async def update_preferences(
    session_id: str,
    preferences: Dict[str, Any]
):
    """
    Update user preferences for a session.
    
    - **session_id**: Session identifier
    - **preferences**: Dictionary of preference settings
    
    Supported preferences:
    - **high_contrast**: Enable high contrast mode (boolean)
    - **large_text**: Enable large text mode (boolean)
    - **speech_rate**: TTS speech rate (100-300)
    - **voice_id**: Preferred TTS voice ID
    - **language**: Preferred language code
    """
    session = await session_manager.update_session(
        session_id,
        user_preferences=preferences
    )
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    return {
        "success": True,
        "message": "Preferences updated successfully",
        "preferences": session.user_preferences
    }


@router.delete(
    "/{session_id}",
    summary="Delete a session",
    description="End and delete a conversation session"
)
async def delete_session(session_id: str):
    """
    Delete a session.
    
    - **session_id**: Session identifier
    
    This will clear all conversation history and booking state.
    """
    deleted = await session_manager.delete_session(session_id)
    
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    return {
        "success": True,
        "message": "Session deleted successfully"
    }


@router.post(
    "/{session_id}/reset",
    summary="Reset session state",
    description="Reset conversation and booking state while keeping the session"
)
async def reset_session(session_id: str):
    """
    Reset session state without deleting the session.
    
    - **session_id**: Session identifier
    
    This clears conversation history and booking state but keeps preferences.
    """
    session = await session_manager.update_session(
        session_id,
        conversation_context={},
        booking_state={}
    )
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    return {
        "success": True,
        "message": "Session state reset successfully",
        "session_id": session.session_id
    }


@router.get(
    "/stats/active",
    summary="Get active session count",
    description="Get the number of currently active sessions"
)
async def get_active_sessions():
    """
    Get count of active sessions.
    
    Returns the number of sessions that haven't expired.
    """
    count = await session_manager.get_active_session_count()
    
    return {
        "active_sessions": count,
        "timestamp": datetime.utcnow().isoformat()
    }
