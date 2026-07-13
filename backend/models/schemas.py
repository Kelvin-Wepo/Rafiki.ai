"""
Pydantic models for request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import re


class Agency(str, Enum):
    """Supported government agencies."""
    NTSA = "ntsa"  # National Transport and Safety Authority
    KRA = "kra"  # Kenya Revenue Authority
    NRB = "nrb"  # National Registration Bureau
    DCRS = "dcrs"  # Department of Civil Registration Services
    BRS = "brs"  # Business Registration Service
    DCI = "dci"  # Directorate of Criminal Investigations
    CPB = "cpb"  # Counsellors and Psychologists Board
    MOH = "moh"  # Ministry of Health
    COUNTY = "county"  # County Services


class ServiceType(str, Enum):
    """Available government services."""
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVING_LICENSE = "driving_license"
    GOOD_CONDUCT = "good_conduct"
    # NTSA services
    VEHICLE_REGISTRATION = "vehicle_registration"
    LOGBOOK_SEARCH = "logbook_search"
    # KRA services
    KRA_PIN = "kra_pin"
    NIL_RETURNS = "nil_returns"
    TAX_COMPLIANCE = "tax_compliance"
    # NRB services
    BIRTH_CERTIFICATE = "birth_certificate"
    # BRS services
    BUSINESS_REGISTRATION = "business_registration"
    # MOH services
    HEALTH_RECORDS = "health_records"


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


# ============== KRA API Models ==============

class KRAPINVerifyRequest(BaseModel):
    """Request model for KRA PIN verification."""
    pin: str = Field(..., description="KRA PIN to verify (format: A000000000X)", min_length=11, max_length=11)
    
    @validator('pin')
    def validate_pin_format(cls, v):
        """Validate KRA PIN format."""
        if not v:
            raise ValueError("KRA PIN is required")
        
        v = v.upper().strip()
        
        # Check first character (A for individuals, P for companies)
        if v[0] not in ['A', 'P']:
            raise ValueError("KRA PIN must start with 'A' (individual) or 'P' (company)")
        
        # Check middle 9 characters are digits
        if not v[1:10].isdigit():
            raise ValueError("KRA PIN must have 9 digits after the first letter")
        
        # Check last character is a letter
        if not v[10].isalpha():
            raise ValueError("KRA PIN must end with a letter")
        
        return v


class KRAPINVerifyResponse(BaseModel):
    """Response model for KRA PIN verification."""
    success: bool = Field(..., description="Whether the request was successful")
    pin: Optional[str] = Field(None, description="Verified PIN")
    valid: Optional[bool] = Field(None, description="Whether the PIN is valid")
    taxpayer_name: Optional[str] = Field(None, description="Name of taxpayer")
    registration_date: Optional[str] = Field(None, description="PIN registration date")
    status: Optional[str] = Field(None, description="Taxpayer status")
    taxpayer_type: Optional[str] = Field(None, description="Type of taxpayer (individual/company)")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if failed")


class KRAComplianceCheckRequest(BaseModel):
    """Request model for KRA compliance check."""
    pin: str = Field(..., description="KRA PIN to check compliance for", min_length=11, max_length=11)


class KRAComplianceCheckResponse(BaseModel):
    """Response model for KRA compliance check."""
    success: bool = Field(..., description="Whether the request was successful")
    pin: Optional[str] = Field(None, description="KRA PIN checked")
    compliant: Optional[bool] = Field(None, description="Whether taxpayer is compliant")
    compliance_status: Optional[str] = Field(None, description="Compliance status description")
    outstanding_returns: Optional[List[str]] = Field(None, description="List of outstanding tax returns")
    outstanding_taxes: Optional[float] = Field(None, description="Total outstanding taxes (KES)")
    last_return_date: Optional[str] = Field(None, description="Date of last tax return filed")
    certificate_valid: Optional[bool] = Field(None, description="Whether compliance certificate is valid")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if failed")


class KRATaxpayerDetailsRequest(BaseModel):
    """Request model for taxpayer details."""
    pin: str = Field(..., description="KRA PIN", min_length=11, max_length=11)


class KRATaxpayerDetailsResponse(BaseModel):
    """Response model for taxpayer details."""
    success: bool = Field(..., description="Whether the request was successful")
    pin: Optional[str] = Field(None, description="KRA PIN")
    taxpayer_name: Optional[str] = Field(None, description="Taxpayer name")
    taxpayer_type: Optional[str] = Field(None, description="Taxpayer type")
    registration_date: Optional[str] = Field(None, description="Registration date")
    postal_address: Optional[str] = Field(None, description="Postal address")
    physical_address: Optional[str] = Field(None, description="Physical address")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    business_nature: Optional[str] = Field(None, description="Nature of business")
    status: Optional[str] = Field(None, description="Account status")
    message: Optional[str] = Field(None, description="Response message")
    error: Optional[str] = Field(None, description="Error message if failed")


class KRAComplianceCertificateRequest(BaseModel):
    """Request model for compliance certificate."""
    pin: str = Field(..., description="KRA PIN", min_length=11, max_length=11)
    email: str = Field(..., description="Email to send certificate to")
    
    @validator('email')
    def validate_email(cls, v):
        """Validate email format."""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError("Invalid email address format")
        return v.lower()


class KRAComplianceCertificateResponse(BaseModel):
    """Response model for compliance certificate request."""
    success: bool = Field(..., description="Whether the request was successful")
    message: Optional[str] = Field(None, description="Response message")
    request_id: Optional[str] = Field(None, description="Certificate request ID")
    status: Optional[str] = Field(None, description="Request status")
    estimated_time: Optional[str] = Field(None, description="Estimated processing time")
    error: Optional[str] = Field(None, description="Error message if failed")

# ============== Waitlist Models ==============

class WaitlistServiceType(str, Enum):
    """Waitlist service interest types."""
    GENERAL = "general"
    PASSPORT = "passport"
    NATIONAL_ID = "national_id"
    DRIVING_LICENSE = "driving_license"
    GOOD_CONDUCT = "good_conduct"
    KRA_SERVICES = "kra_services"
    ECITIZEN_SERVICES = "ecitizen_services"


class JoinWaitlistRequest(BaseModel):
    """Request model for joining the waitlist."""
    phone_number: str = Field(..., description="Kenyan phone number (e.g., +254712345678 or 0712345678)")
    email: Optional[str] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    service_interest: WaitlistServiceType = Field(default=WaitlistServiceType.GENERAL, description="Service of interest")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate Kenyan phone number format."""
        # Remove common formatting
        v = v.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Support +254, 254, or 0 prefix
        if v.startswith("+254"):
            v = "0" + v[4:]
        elif v.startswith("254"):
            v = "0" + v[3:]
        
        # Validate format: 0712345678 (10 digits starting with 07 or 01)
        if not re.match(r'^0[17]\d{8}$', v):
            raise ValueError("Invalid Kenyan phone number format. Use format like 0712345678")
        
        return v


class WaitlistEntryResponse(BaseModel):
    """Response model for a waitlist entry."""
    id: str = Field(..., description="Waitlist entry ID")
    phone_number: str = Field(..., description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    service_interest: str = Field(..., description="Service of interest")
    status: str = Field(..., description="Waitlist status")
    position: int = Field(..., description="Position in waitlist")
    joined_at: str = Field(..., description="Timestamp when joined")
    activated_at: Optional[str] = Field(None, description="Timestamp when activated")


class WaitlistListResponse(BaseModel):
    """Response model for listing waitlist entries."""
    total: int = Field(..., description="Total waitlist entries")
    pending: int = Field(..., description="Pending entries")
    activated: int = Field(..., description="Activated entries")
    entries: List[WaitlistEntryResponse] = Field(..., description="Waitlist entries")


class CheckWaitlistStatusResponse(BaseModel):
    """Response model for checking waitlist status."""
    phone_number: str = Field(..., description="Phone number")
    status: str = Field(..., description="Waitlist status")
    position: Optional[int] = Field(None, description="Position in waitlist (if pending)")
    joined_at: str = Field(..., description="Timestamp when joined")
    activated_at: Optional[str] = Field(None, description="Timestamp when activated")


# ================= Chat / Conversation Schemas =================


class ChatMessageCreate(BaseModel):
    session_id: str = Field(..., description="Conversation / session id")
    sender: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    audio_url: Optional[str] = Field(None, description="Optional audio URL")


class ChatMessageOut(BaseModel):
    id: str
    session_id: str
    sender: str
    content: str
    audio_url: Optional[str]
    created_at: datetime


class ChatSessionListOut(BaseModel):
    id: str
    title: Optional[str]
    last_message_preview: Optional[str]
    updated_at: datetime


class ChatSessionDetailOut(BaseModel):
    id: str
    title: Optional[str]
    status: Optional[str]
    last_message_preview: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageOut]


class TranscriptOut(BaseModel):
    transcript_id: str
    conversation_id: str
    filename: str
    file_path: str
    content_type: str
    is_read: bool
    generated_at: datetime


class UnreadCountOut(BaseModel):
    count: int

    message: str = Field(..., description="Status message")