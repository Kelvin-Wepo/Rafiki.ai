"""
Session management for conversation state.
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class Session:
    """Represents a user session."""
    session_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    booking_state: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self) -> bool:
        """Check if session has expired."""
        return datetime.utcnow() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "is_active": self.is_active,
            "conversation_context": self.conversation_context,
            "user_preferences": self.user_preferences,
            "booking_state": self.booking_state
        }


class SessionManager:
    """Manages user sessions for conversation state."""
    
    def __init__(self, expire_minutes: int = 60):
        """
        Initialize session manager.
        
        Args:
            expire_minutes: Session expiration time in minutes
        """
        self._sessions: Dict[str, Session] = {}
        self._expire_minutes = expire_minutes
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
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
        Create a new session.
        
        Args:
            user_preferences: Optional user preferences (accessibility settings, etc.)
        
        Returns:
            New Session object
        """
        async with self._lock:
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
            logger.info(f"Created new session: {session_id}")
            
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
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Optional[Session]:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            conversation_context: Updated conversation context
            booking_state: Updated booking state
            user_preferences: Updated user preferences
        
        Returns:
            Updated Session object or None if not found
        """
        async with self._lock:
            session = self._sessions.get(session_id)
            
            if session is None or session.is_expired():
                return None
            
            if conversation_context is not None:
                session.conversation_context.update(conversation_context)
            
            if booking_state is not None:
                session.booking_state.update(booking_state)
            
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


# Global session manager instance
session_manager = SessionManager()
