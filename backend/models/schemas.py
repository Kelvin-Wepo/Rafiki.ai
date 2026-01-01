"""
Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import re


class ServiceType(str, Enum):
    """Available government services."""
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVING_LICENSE = "driving_license"
    GOOD_CONDUCT = "good_conduct"


class TimeSlot(str, Enum):
    """Available time slots for appointments."""
    MORNING = "08:00-12:00"
    AFTERNOON = "14:00-17:00"


class BookingStatus(str, Enum):
    """Appointment booking status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class InputMode(str, Enum):
    """User input mode."""
    VOICE = "voice"
    TEXT = "text"


# ============== Request Models ==============

class VoiceInputRequest(BaseModel):
    """Request model for voice input processing."""
    audio_data: Optional[str] = Field(None, description="Base64 encoded audio data")
    text_input: Optional[str] = Field(None, description="Text input as fallback")
    session_id: str = Field(..., description="User session identifier")
    input_mode: InputMode = Field(default=InputMode.VOICE, description="Input mode (voice/text)")
    language: str = Field(default="en-KE", description="Language code for speech recognition")
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Sanitize session ID."""
        if not re.match(r'^[a-zA-Z0-9\-_]+$', v):
            raise ValueError('Invalid session ID format')
        return v
    
    @validator('text_input')
    def sanitize_text(cls, v):
        """Sanitize text input to prevent injection."""
        if v:
            # Remove potentially harmful characters
            v = re.sub(r'[<>"\';]', '', v)
            v = v.strip()[:500]  # Limit length
        return v


class TextInputRequest(BaseModel):
    """Request model for text input processing."""
    text: str = Field(..., min_length=1, max_length=500, description="User text input")
    session_id: str = Field(..., description="User session identifier")
    
    @validator('text')
    def sanitize_text(cls, v):
        """Sanitize text input."""
        v = re.sub(r'[<>"\';]', '', v)
        return v.strip()


class BookingRequest(BaseModel):
    """Request model for service booking."""
    service_type: ServiceType = Field(..., description="Type of government service")
    user_name: str = Field(..., min_length=2, max_length=100, description="User's full name")
    phone_number: str = Field(..., description="Phone number for SMS confirmation")
    time_slot: TimeSlot = Field(..., description="Preferred time slot")
    appointment_date: datetime = Field(..., description="Preferred appointment date")
    session_id: str = Field(..., description="User session identifier")
    additional_notes: Optional[str] = Field(None, max_length=500, description="Additional notes")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate Kenyan phone number format."""
        # Clean the phone number
        v = re.sub(r'[\s\-]', '', v)
        # Check for valid Kenyan format
        if not re.match(r'^(\+254|254|0)?[17]\d{8}$', v):
            raise ValueError('Invalid Kenyan phone number format')
        # Normalize to +254 format
        if v.startswith('0'):
            v = '+254' + v[1:]
        elif v.startswith('254'):
            v = '+' + v
        elif not v.startswith('+'):
            v = '+254' + v
        return v
    
    @validator('user_name')
    def sanitize_name(cls, v):
        """Sanitize user name."""
        v = re.sub(r'[<>"\';]', '', v)
        return v.strip()


class ECitizenNavigationRequest(BaseModel):
    """Request model for eCitizen navigation."""
    action: str = Field(..., description="Navigation action (login, signup, search, service)")
    service_type: Optional[ServiceType] = Field(None, description="Service to navigate to")
    search_query: Optional[str] = Field(None, max_length=200, description="Search query")
    session_id: str = Field(..., description="User session identifier")


class SessionCreateRequest(BaseModel):
    """Request model for session creation."""
    user_agent: Optional[str] = Field(None, description="User agent string")
    accessibility_preferences: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="User accessibility preferences"
    )


# ============== Response Models ==============

class AssistantResponse(BaseModel):
    """Standard response from the assistant."""
    text: str = Field(..., description="Response text to display/speak")
    audio_url: Optional[str] = Field(None, description="URL to audio file for TTS")
    intent: Optional[str] = Field(None, description="Detected user intent")
    entities: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Extracted entities")
    session_id: str = Field(..., description="Session identifier")
    requires_input: bool = Field(default=False, description="Whether follow-up input is expected")
    suggested_actions: Optional[List[str]] = Field(default_factory=list, description="Suggested next actions")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Conversation context")
    automation: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Automation commands for eCitizen")


class BookingResponse(BaseModel):
    """Response for booking requests."""
    success: bool = Field(..., description="Whether booking was successful")
    booking_id: Optional[str] = Field(None, description="Unique booking identifier")
    message: str = Field(..., description="Response message")
    booking_details: Optional[Dict[str, Any]] = Field(None, description="Booking details")
    sms_sent: bool = Field(default=False, description="Whether SMS confirmation was sent")
    appointment_datetime: Optional[datetime] = Field(None, description="Confirmed appointment datetime")


class ServiceInfoResponse(BaseModel):
    """Response with service information."""
    service_type: ServiceType
    name: str
    description: str
    department: str
    time_slots: List[str]
    requirements: List[str]
    ecitizen_url: str


class ServicesListResponse(BaseModel):
    """Response listing all available services."""
    services: List[ServiceInfoResponse]
    total_count: int


class SessionResponse(BaseModel):
    """Response for session operations."""
    session_id: str
    created_at: datetime
    expires_at: datetime
    is_active: bool


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, bool]


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TranscriptionResponse(BaseModel):
    """Response for voice transcription."""
    text: str = Field(..., description="Transcribed text")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score")
    language: str = Field(..., description="Detected language")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")


class TTSResponse(BaseModel):
    """Response for text-to-speech conversion."""
    audio_data: str = Field(..., description="Base64 encoded audio")
    audio_format: str = Field(default="wav", description="Audio format")
    duration_seconds: Optional[float] = Field(None, description="Audio duration")
