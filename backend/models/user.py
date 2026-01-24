"""
User and authentication models with security-first design.
Implements encryption for sensitive data and audit logging.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from enum import Enum
import re
import hashlib
import secrets


class AuthProvider(str, Enum):
    """Authentication provider types."""
    PHONE = "phone"
    ECITIZEN = "ecitizen"  # Future implementation


class UserStatus(str, Enum):
    """User account status."""
    PENDING = "pending"  # Awaiting OTP verification
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"  # Too many failed attempts


class OTPStatus(str, Enum):
    """OTP verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


# ============== Database Models ==============

class User(BaseModel):
    """User account model with encrypted sensitive data."""
    id: str = Field(..., description="Unique user identifier")
    phone_number_hash: str = Field(..., description="SHA-256 hash of phone number")
    phone_number_masked: str = Field(..., description="Masked phone number for display")
    auth_provider: AuthProvider = Field(default=AuthProvider.PHONE)
    status: UserStatus = Field(default=UserStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    failed_attempts: int = Field(default=0)
    locked_until: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class OTPRecord(BaseModel):
    """OTP record for verification."""
    id: str = Field(..., description="Unique OTP record ID")
    user_id: str = Field(..., description="Associated user ID")
    phone_number_hash: str = Field(..., description="SHA-256 hash of phone number")
    otp_hash: str = Field(..., description="SHA-256 hash of OTP")
    status: OTPStatus = Field(default=OTPStatus.PENDING)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(...)
    attempts: int = Field(default=0)
    max_attempts: int = Field(default=5)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        use_enum_values = True
    
    def is_expired(self) -> bool:
        """Check if OTP has expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_max_attempts(self) -> bool:
        """Check if max verification attempts reached."""
        return self.attempts >= self.max_attempts


class Session(BaseModel):
    """User session model with JWT token reference."""
    id: str = Field(..., description="Session ID")
    user_id: str = Field(..., description="Associated user ID")
    token_hash: str = Field(..., description="SHA-256 hash of JWT token")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(...)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = Field(default=True)
    
    class Config:
        use_enum_values = True
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at


class Conversation(BaseModel):
    """Conversation history model."""
    id: str = Field(..., description="Conversation ID")
    user_id: str = Field(..., description="User who owns this conversation")
    title: str = Field(default="New Conversation")
    messages: List[dict] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_archived: bool = Field(default=False)
    
    class Config:
        use_enum_values = True


class AuthAuditLog(BaseModel):
    """Audit log for authentication events (National Security Compliance)."""
    id: str = Field(..., description="Audit log ID")
    event_type: str = Field(..., description="Type of auth event")
    user_id: Optional[str] = None
    phone_number_hash: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = Field(...)
    failure_reason: Optional[str] = None
    metadata: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# ============== Request/Response Models ==============

class PhoneAuthRequest(BaseModel):
    """Request to initiate phone authentication."""
    phone_number: str = Field(..., description="Phone number in Kenyan format")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate and normalize Kenyan phone number."""
        # Remove spaces, dashes
        v = re.sub(r'[\s\-]', '', v)
        
        # Check for valid Kenyan format
        if not re.match(r'^(\+254|254|0)?[17]\d{8}$', v):
            raise ValueError('Invalid Kenyan phone number format. Use +254XXXXXXXXX or 0XXXXXXXXX')
        
        # Normalize to +254 format
        if v.startswith('0'):
            v = '+254' + v[1:]
        elif v.startswith('254'):
            v = '+' + v
        elif not v.startswith('+'):
            v = '+254' + v
        
        return v


class OTPVerifyRequest(BaseModel):
    """Request to verify OTP."""
    phone_number: str = Field(..., description="Phone number used for OTP request")
    otp: str = Field(..., min_length=6, max_length=6, description="6-digit OTP code")
    
    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate and normalize phone number."""
        v = re.sub(r'[\s\-]', '', v)
        if v.startswith('0'):
            v = '+254' + v[1:]
        elif v.startswith('254'):
            v = '+' + v
        elif not v.startswith('+'):
            v = '+254' + v
        return v
    
    @validator('otp')
    def validate_otp(cls, v):
        """Validate OTP format."""
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be exactly 6 digits')
        return v


class AuthResponse(BaseModel):
    """Authentication response."""
    success: bool
    message: str
    user_id: Optional[str] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # seconds
    requires_otp: bool = False


class UserProfile(BaseModel):
    """User profile for frontend display."""
    user_id: str
    phone_masked: str
    status: str
    created_at: datetime
    last_login: Optional[datetime]


class ConversationSummary(BaseModel):
    """Conversation summary for history list."""
    id: str
    title: str
    preview: str  # First message preview
    message_count: int
    created_at: datetime
    updated_at: datetime


class TranscriptExport(BaseModel):
    """Transcript export request."""
    conversation_id: str
    format: str = Field(default="txt", description="Export format: txt, json, pdf")


# ============== Utility Functions ==============

def hash_value(value: str) -> str:
    """Create SHA-256 hash of a value."""
    return hashlib.sha256(value.encode()).hexdigest()


def mask_phone_number(phone: str) -> str:
    """Mask phone number for display (e.g., +254***XXX123)."""
    if len(phone) < 10:
        return "***"
    return f"{phone[:4]}***{phone[-3:]}"


def generate_user_id() -> str:
    """Generate unique user ID."""
    return f"usr_{secrets.token_hex(16)}"


def generate_session_id() -> str:
    """Generate unique session ID."""
    return f"ses_{secrets.token_hex(16)}"


def generate_otp_id() -> str:
    """Generate unique OTP record ID."""
    return f"otp_{secrets.token_hex(16)}"


def generate_conversation_id() -> str:
    """Generate unique conversation ID."""
    return f"conv_{secrets.token_hex(16)}"


def generate_audit_id() -> str:
    """Generate unique audit log ID."""
    return f"aud_{secrets.token_hex(16)}"
