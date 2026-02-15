"""
Session management for conversation state.

Features:
- Secure session tokens
- AES-256-GCM encryption for sensitive data
- PII detection and masking
- Automatic expiration and cleanup
"""

import uuid
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

from utils.logger import get_logger
from utils.encryption import (
    get_encryption_service, 
    get_pii_detector,
    EncryptionService,
    PIIDetector
)
from rafiki_settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class Session:
    """Represents a user session with encrypted sensitive data."""
    session_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    booking_state: Dict[str, Any] = field(default_factory=dict)
    
    # Encrypted storage for sensitive data
    _encrypted_context: Optional[str] = field(default=None, repr=False)
    _encrypted_booking: Optional[str] = field(default=None, repr=False)
    _pii_summary: Dict[str, int] = field(default_factory=dict)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert session to dictionary.
        
        Args:
            include_sensitive: Whether to include encrypted sensitive data
        
        Returns:
            Dictionary representation of session
        """
        result = {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active,
            "conversation_context": self.conversation_context,
            "user_preferences": self.user_preferences,
            "booking_state": self.booking_state,
            "pii_detected": self._pii_summary
        }
        
        if include_sensitive and self._encrypted_context:
            result["_encrypted_context"] = self._encrypted_context
        if include_sensitive and self._encrypted_booking:
            result["_encrypted_booking"] = self._encrypted_booking
            
        return result
    
    def get_safe_context(self) -> Dict[str, Any]:
        """Get conversation context with PII masked."""
        pii_detector = get_pii_detector()
        safe_context = {}
        
        for key, value in self.conversation_context.items():
            if isinstance(value, str):
                safe_context[key] = pii_detector.mask(value)
            elif isinstance(value, dict):
                safe_context[key] = {
                    k: pii_detector.mask(v) if isinstance(v, str) else v
                    for k, v in value.items()
                }
            else:
                safe_context[key] = value
        
        return safe_context


class SessionManager:
    """
    Manages user sessions for conversation state with encryption.
    
    Features:
    - AES-256-GCM encryption for sensitive conversation data
    - PII detection and logging
    - Automatic session expiration
    - Thread-safe operations
    """
    
    def __init__(self, expire_minutes: int = 60, enable_encryption: bool = True):
        """
        Initialize session manager.
        
        Args:
            expire_minutes: Session expiration time in minutes
            enable_encryption: Whether to enable encryption for sensitive data
        """
        self._sessions: Dict[str, Session] = {}
        self._expire_minutes = expire_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        self._enable_encryption = enable_encryption
        
        # Initialize encryption and PII detection
        if enable_encryption:
            self._encryption = get_encryption_service()
            self._pii_detector = get_pii_detector()
            logger.info("Session manager initialized with encryption enabled")
        else:
            self._encryption = None
            self._pii_detector = None
            logger.info("Session manager initialized (encryption disabled)")
    
    async def start_cleanup_task(self):
        """Start background task to clean up expired sessions."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Session cleanup task started")
    
    async def stop_cleanup_task(self):
        """Stop the cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Session cleanup task stopped")
    
    async def _cleanup_loop(self):
        """Background loop to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
    
    async def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        async with self._lock:
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if session.is_expired()
            ]
            for sid in expired_ids:
                del self._sessions[sid]
            
            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired sessions")
    
    async def create_session(
        self,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Session:
        """
        Create a new session with secure token.
        
        Args:
            user_preferences: Optional user preferences (accessibility settings, etc.)
        
        Returns:
            New Session object
        """
        async with self._lock:
            # Generate cryptographically secure session ID
            if self._encryption:
                session_id = self._encryption.generate_session_token()
            else:
                session_id = str(uuid.uuid4())
            
            now = datetime.utcnow()
            
            session = Session(
                session_id=session_id,
                created_at=now,
                last_activity=now,
                expires_at=now + timedelta(minutes=self._expire_minutes),
                user_preferences=user_preferences or {}
            )
            
            self._sessions[session_id] = session
            logger.info(f"Created new encrypted session: {session_id[:8]}...")
            
            return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Session object if found and valid, None otherwise
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None:
                return None
            
            if session.is_expired():
                del self._sessions[session_id]
                logger.info(f"Session expired: {session_id}")
                return None
            
            session.update_activity()
            # Extend expiration on activity
            session.expires_at = datetime.utcnow() + timedelta(minutes=self._expire_minutes)
            
            return session
    
    async def update_session(
        self,
        session_id: str,
        conversation_context: Optional[Dict[str, Any]] = None,
        booking_state: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
        encrypt_sensitive: bool = True
    ) -> Optional[Session]:
        """
        Update session data with optional encryption for sensitive fields.
        
        Args:
            session_id: Session identifier
            conversation_context: Updated conversation context
            booking_state: Updated booking state
            user_preferences: Updated user preferences
            encrypt_sensitive: Whether to encrypt sensitive data
        
        Returns:
            Updated Session object or None if not found
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None or session.is_expired():
                return None
            
            # Update conversation context
            if conversation_context is not None:
                session.conversation_context.update(conversation_context)
                
                # Detect and log PII
                if self._pii_detector:
                    context_str = json.dumps(conversation_context, default=str)
                    pii_found = self._pii_detector.get_pii_summary(context_str)
                    if pii_found:
                        session._pii_summary.update(pii_found)
                        logger.warning(
                            f"PII detected in session {session_id[:8]}...: {pii_found}"
                        )
                
                # Encrypt sensitive context
                if encrypt_sensitive and self._encryption:
                    session._encrypted_context = self._encryption.encrypt(
                        conversation_context
                    )
            
            # Update booking state
            if booking_state is not None:
                session.booking_state.update(booking_state)
                
                # Encrypt booking data (contains personal info)
                if encrypt_sensitive and self._encryption:
                    session._encrypted_booking = self._encryption.encrypt(
                        booking_state
                    )
            
            if user_preferences is not None:
                session.user_preferences.update(user_preferences)
            
            session.update_activity()
            
            return session
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            True if session was deleted, False if not found
        """
        async with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False
    
    async def get_active_session_count(self) -> int:
        """Get count of active sessions."""
        async with self._lock:
            return sum(
                1 for session in self._sessions.values()
                if not session.is_expired()
            )
    
    async def get_decrypted_context(
        self, 
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get decrypted conversation context for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Decrypted conversation context or None
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None or session.is_expired():
                return None
            
            if session._encrypted_context and self._encryption:
                try:
                    return self._encryption.decrypt_json(session._encrypted_context)
                except Exception as e:
                    logger.error(f"Failed to decrypt context: {e}")
                    return session.conversation_context
            
            return session.conversation_context
    
    async def get_decrypted_booking(
        self, 
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get decrypted booking state for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Decrypted booking state or None
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None or session.is_expired():
                return None
            
            if session._encrypted_booking and self._encryption:
                try:
                    return self._encryption.decrypt_json(session._encrypted_booking)
                except Exception as e:
                    logger.error(f"Failed to decrypt booking: {e}")
                    return session.booking_state
            
            return session.booking_state
    
    async def store_sensitive_data(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """
        Store encrypted sensitive data in a session.
        
        Args:
            session_id: Session identifier
            key: Data key
            value: Value to encrypt and store
        
        Returns:
            True if successful
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None or session.is_expired():
                return False
            
            if not self._encryption:
                # Store unencrypted if encryption disabled
                session.conversation_context[key] = value
                return True
            
            # Encrypt and store
            encrypted = self._encryption.encrypt(value)
            session.conversation_context[f"_encrypted_{key}"] = encrypted
            
            # Store masked version for display
            if isinstance(value, str) and self._pii_detector:
                session.conversation_context[key] = self._pii_detector.mask(value)
            else:
                session.conversation_context[key] = "[ENCRYPTED]"
            
            session.update_activity()
            return True
    
    async def retrieve_sensitive_data(
        self,
        session_id: str,
        key: str
    ) -> Optional[Any]:
        """
        Retrieve and decrypt sensitive data from a session.
        
        Args:
            session_id: Session identifier
            key: Data key
        
        Returns:
            Decrypted value or None
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None or session.is_expired():
                return None
            
            encrypted_key = f"_encrypted_{key}"
            
            if encrypted_key in session.conversation_context and self._encryption:
                try:
                    encrypted = session.conversation_context[encrypted_key]
                    return self._encryption.decrypt(encrypted)
                except Exception as e:
                    logger.error(f"Failed to decrypt {key}: {e}")
                    return None
            
            return session.conversation_context.get(key)
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions."""
        async with self._lock:
            total = len(self._sessions)
            active = sum(
                1 for s in self._sessions.values() 
                if not s.is_expired() and s.is_active
            )
            expired = sum(
                1 for s in self._sessions.values() 
                if s.is_expired()
            )
            
            total_pii = {}
            for session in self._sessions.values():
                for pii_type, count in session._pii_summary.items():
                    total_pii[pii_type] = total_pii.get(pii_type, 0) + count
            
            return {
                "total_sessions": total,
                "active_sessions": active,
                "expired_sessions": expired,
                "encryption_enabled": self._enable_encryption,
                "pii_detected_summary": total_pii
            }


# Global session manager instance with encryption enabled
session_manager = SessionManager(
    expire_minutes=settings.SESSION_EXPIRE_MINUTES,
    enable_encryption=True
)
