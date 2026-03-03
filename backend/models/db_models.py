"""
SQLAlchemy Database Models for Rafiki.ai
Proper ORM models with PostgreSQL support.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, Text, 
    ForeignKey, Enum as SQLEnum, JSON, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from database import Base


class AuthProvider(str, enum.Enum):
    """Authentication provider types."""
    PHONE = "phone"
    ECITIZEN = "ecitizen"


class UserStatus(str, enum.Enum):
    """User account status."""
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"


class OTPStatus(str, enum.Enum):
    """OTP verification status."""
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"


class User(Base):
    """User account model."""
    __tablename__ = "users"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    # Core authentication fields
    phone_number_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    phone_number_masked: Mapped[str] = mapped_column(String(20))
    email_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    email_masked: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # bcrypt hash
    
    # Profile fields
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    id_number_hash: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    has_disability: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Account status
    auth_provider: Mapped[str] = mapped_column(
        SQLEnum(AuthProvider, name="auth_provider_enum"),
        default=AuthProvider.PHONE
    )
    status: Mapped[str] = mapped_column(
        SQLEnum(UserStatus, name="user_status_enum"),
        default=UserStatus.PENDING
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred_language: Mapped[str] = mapped_column(String(10), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    otp_records: Mapped[List["OTPRecord"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[List["Session"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.phone_number_masked}>"


class OTPRecord(Base):
    """OTP record for phone verification."""
    __tablename__ = "otp_records"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    phone_number_hash: Mapped[str] = mapped_column(String(64), index=True)
    otp_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(
        SQLEnum(OTPStatus, name="otp_status_enum"),
        default=OTPStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=5)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Relationship
    user: Mapped["User"] = relationship(back_populates="otp_records")
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def is_max_attempts(self) -> bool:
        return self.attempts >= self.max_attempts


class Session(Base):
    """User session for authentication."""
    __tablename__ = "sessions"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationship
    user: Mapped["User"] = relationship(back_populates="sessions")
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class Conversation(Base):
    """Conversation history for a user session."""
    __tablename__ = "conversations"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en")
    service_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # 'metadata' is reserved in SQLAlchemy, use 'conversation_metadata' instead
    conversation_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
    
    # Index for quick lookup
    __table_args__ = (
        Index("ix_conversations_user_active", "user_id", "is_active"),
    )


class Message(Base):
    """Individual message in a conversation."""
    __tablename__ = "messages"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20))  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    language: Mapped[str] = mapped_column(String(10), default="en")
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    # 'metadata' is reserved in SQLAlchemy, use 'message_metadata' instead
    message_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    # Relationship
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    
    # Index for chronological ordering
    __table_args__ = (
        Index("ix_messages_conversation_timestamp", "conversation_id", "timestamp"),
    )


class AuditLog(Base):
    """Security audit log for tracking authentication events."""
    __tablename__ = "audit_logs"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True
    )
    action: Mapped[str] = mapped_column(String(50), index=True)  # login, logout, otp_request, etc.
    status: Mapped[str] = mapped_column(String(20))  # success, failed
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")


class ServiceBooking(Base):
    """Government service booking/appointment."""
    __tablename__ = "service_bookings"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    service_type: Mapped[str] = mapped_column(String(100), index=True)
    service_name: Mapped[str] = mapped_column(String(200))
    booking_reference: Mapped[str] = mapped_column(String(50), unique=True)
    scheduled_date: Mapped[datetime] = mapped_column(DateTime)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, confirmed, cancelled, completed
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    # 'metadata' is reserved in SQLAlchemy, use 'booking_metadata' instead
    booking_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    
    # Index for user lookups
    __table_args__ = (
        Index("ix_bookings_user_status", "user_id", "status"),
    )


class WaitlistStatus(str, enum.Enum):
    """Waitlist entry status."""
    PENDING = "pending"
    ACTIVATED = "activated"
    CANCELLED = "cancelled"


class Waitlist(Base):
    """Waitlist entry model for feature/service access."""
    __tablename__ = "waitlist"
    
    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    service_interest: Mapped[str] = mapped_column(String(100), default="general")  # passport, id, license, general, etc.
    status: Mapped[WaitlistStatus] = mapped_column(SQLEnum(WaitlistStatus), default=WaitlistStatus.PENDING)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # Higher priority = higher in queue
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Index for lookups
    __table_args__ = (
        Index("ix_waitlist_phone", "phone_number"),
        Index("ix_waitlist_status", "status"),
        Index("ix_waitlist_service", "service_interest"),
    )
