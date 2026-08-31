"""
Cross-agency identity continuity models.

These tables did not exist in the codebase. They are the durable store for
WhatsApp (and later web/voice) sessions so verified status, consent, and
handoffs survive process restarts. Hot-path session state still lives in
Redis with SESSION_EXPIRE_MINUTES TTL — see services/whatsapp_session.py.
"""

from datetime import datetime
from typing import Optional, List
import enum
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class ChannelType(str, enum.Enum):
    WHATSAPP = "whatsapp"
    WEB = "web"
    VOICE = "voice"


class AgentSessionStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"


class AgentSession(Base):
    """
    One conversational agent session.

    WhatsApp: keyed by hashed phone. `workflow_session_id` is the id used by
    agency_workflows.SessionState (the in-memory Decision Graph stand-in).
    `voice_id` is pinned at create time and must not be reassigned mid-session.
    """
    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    channel: Mapped[str] = mapped_column(String(20), default=ChannelType.WHATSAPP.value)
    status: Mapped[str] = mapped_column(String(20), default=AgentSessionStatus.ACTIVE.value)

    workflow_session_id: Mapped[str] = mapped_column(String(128), index=True)
    whatsapp_phone_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    whatsapp_phone_masked: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    current_agency: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    voice_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    entropy_score: Mapped[float] = mapped_column(Float, default=1.0)

    last_inbound_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    last_outbound_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime)

    user_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=False), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )

    verified_attributes: Mapped[List["VerifiedAttribute"]] = relationship(
        back_populates="agent_session", cascade="all, delete-orphan"
    )
    consent_grants: Mapped[List["ConsentGrant"]] = relationship(
        back_populates="agent_session", cascade="all, delete-orphan"
    )
    handoffs: Mapped[List["HandoffLog"]] = relationship(
        back_populates="agent_session", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_agent_sessions_phone_status", "whatsapp_phone_hash", "status"),
        Index("ix_agent_sessions_expires", "expires_at"),
    )


class VerifiedAttribute(Base):
    """A fact verified once and reusable across agencies (hashed at rest)."""
    __tablename__ = "verified_attributes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_session_id: Mapped[str] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    value_hash: Mapped[str] = mapped_column(String(64))
    source_agency: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    agent_session: Mapped["AgentSession"] = relationship(back_populates="verified_attributes")

    __table_args__ = (
        Index("ix_verified_attributes_session_name", "agent_session_id", "name"),
    )


class ConsentGrant(Base):
    """Per-agency consent required before referencing agency-specific data."""
    __tablename__ = "consent_grants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_session_id: Mapped[str] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"), index=True
    )
    agency: Mapped[str] = mapped_column(String(80))
    purpose: Mapped[str] = mapped_column(String(80), default="session_guidance")
    granted: Mapped[bool] = mapped_column(Boolean, default=True)
    scope_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    agent_session: Mapped["AgentSession"] = relationship(back_populates="consent_grants")

    __table_args__ = (
        Index("ix_consent_grants_session_agency", "agent_session_id", "agency"),
    )


class HandoffLog(Base):
    """Recorded when conversation context moves from one agency to another."""
    __tablename__ = "handoff_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    agent_session_id: Mapped[str] = mapped_column(
        ForeignKey("agent_sessions.id", ondelete="CASCADE"), index=True
    )
    from_agency: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    to_agency: Mapped[str] = mapped_column(String(80))
    trigger: Mapped[str] = mapped_column(String(40), default="user_message")
    user_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    message_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extra_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    agent_session: Mapped["AgentSession"] = relationship(back_populates="handoffs")
