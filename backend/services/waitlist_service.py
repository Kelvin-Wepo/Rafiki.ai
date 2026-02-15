"""
Waitlist service for managing feature/service access requests.

Handles:
- User sign-ups to join the waitlist
- Status checking for waitlist position
- Activation of waitlist entries
- SMS notifications
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from models.db_models import Waitlist, WaitlistStatus
from services.sms_service import sms_service
from utils.logger import get_logger
from rafiki_settings import get_settings

logger = get_logger(__name__)
settings = get_settings()


class WaitlistService:
    """Service for managing waitlist entries."""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize waitlist service."""
        self.db_session = db_session
    
    def set_db_session(self, session: Session):
        """Set the database session."""
        self.db_session = session
    
    async def join_waitlist(
        self,
        phone_number: str,
        service_interest: str = "general",
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a new user to the waitlist.
        
        Args:
            phone_number: Kenyan phone number
            service_interest: Type of service interested in
            email: Email address
            full_name: Full name
            notes: Additional notes
        
        Returns:
            Response with waitlist entry details
        """
        if not self.db_session:
            return {
                "success": False,
                "error": "Database session not configured"
            }
        
        try:
            # Check if already on waitlist
            existing = self.db_session.query(Waitlist).filter(
                Waitlist.phone_number == phone_number
            ).first()
            
            if existing:
                # If already pending, return info
                if existing.status == WaitlistStatus.PENDING:
                    position = self._get_position(phone_number)
                    return {
                        "success": True,
                        "message": f"You are already on the waitlist at position {position}",
                        "already_joined": True,
                        "position": position,
                        "id": existing.id
                    }
                # If activated, inform them
                elif existing.status == WaitlistStatus.ACTIVATED:
                    return {
                        "success": True,
                        "message": "Your account has already been activated!",
                        "activated": True,
                        "id": existing.id
                    }
            
            # Create new waitlist entry
            entry = Waitlist(
                phone_number=phone_number,
                email=email,
                full_name=full_name,
                service_interest=service_interest,
                notes=notes
            )
            
            self.db_session.add(entry)
            self.db_session.commit()
            
            position = self._get_position(phone_number)
            
            # Send welcome SMS
            await self._send_welcome_sms(phone_number, position)
            
            logger.info(f"User {phone_number} joined waitlist at position {position}")
            
            return {
                "success": True,
                "message": f"Successfully added to waitlist! You are position #{position}",
                "id": entry.id,
                "position": position,
                "joined_at": entry.joined_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error joining waitlist: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_status(self, phone_number: str) -> Dict[str, Any]:
        """
        Check waitlist status for a phone number.
        
        Args:
            phone_number: Kenyan phone number
        
        Returns:
            Status information
        """
        if not self.db_session:
            return {
                "success": False,
                "error": "Database session not configured"
            }
        
        try:
            entry = self.db_session.query(Waitlist).filter(
                Waitlist.phone_number == phone_number
            ).first()
            
            if not entry:
                return {
                    "success": False,
                    "error": "Phone number not found on waitlist"
                }
            
            if entry.status == WaitlistStatus.PENDING:
                position = self._get_position(phone_number)
                return {
                    "success": True,
                    "phone_number": phone_number,
                    "status": "pending",
                    "position": position,
                    "message": f"You are position #{position} on the waitlist",
                    "joined_at": entry.joined_at.isoformat()
                }
            
            elif entry.status == WaitlistStatus.ACTIVATED:
                return {
                    "success": True,
                    "phone_number": phone_number,
                    "status": "activated",
                    "message": "Your account has been activated! You can now access all features.",
                    "activated_at": entry.activated_at.isoformat() if entry.activated_at else None
                }
            
            else:  # CANCELLED
                return {
                    "success": False,
                    "phone_number": phone_number,
                    "status": "cancelled",
                    "message": "Your waitlist entry was cancelled"
                }
        
        except Exception as e:
            logger.error(f"Error checking waitlist status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def activate_entries(self, count: int = 10) -> Dict[str, Any]:
        """
        Activate the next batch of waitlist entries.
        
        Args:
            count: Number of entries to activate
        
        Returns:
            Response with activated entries
        """
        if not self.db_session:
            return {
                "success": False,
                "error": "Database session not configured"
            }
        
        try:
            # Get next pending entries (ordered by priority, then join date)
            pending = self.db_session.query(Waitlist).filter(
                Waitlist.status == WaitlistStatus.PENDING
            ).order_by(
                desc(Waitlist.priority),
                Waitlist.joined_at
            ).limit(count).all()
            
            if not pending:
                return {
                    "success": True,
                    "message": "No pending entries to activate",
                    "activated_count": 0
                }
            
            activated = []
            for entry in pending:
                entry.status = WaitlistStatus.ACTIVATED
                entry.activated_at = datetime.utcnow()
                activated.append(entry.phone_number)
                
                # Send activation SMS
                await self._send_activation_sms(entry.phone_number, entry.full_name or "Valued User")
            
            self.db_session.commit()
            
            logger.info(f"Activated {len(activated)} waitlist entries: {activated}")
            
            return {
                "success": True,
                "message": f"Successfully activated {len(activated)} entries",
                "activated_count": len(activated),
                "activated_phones": activated
            }
        
        except Exception as e:
            logger.error(f"Error activating entries: {e}")
            self.db_session.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_waitlist_stats(self) -> Dict[str, Any]:
        """Get waitlist statistics."""
        if not self.db_session:
            return {
                "success": False,
                "error": "Database session not configured"
            }
        
        try:
            total = self.db_session.query(func.count(Waitlist.id)).scalar() or 0
            pending = self.db_session.query(func.count(Waitlist.id)).filter(
                Waitlist.status == WaitlistStatus.PENDING
            ).scalar() or 0
            activated = self.db_session.query(func.count(Waitlist.id)).filter(
                Waitlist.status == WaitlistStatus.ACTIVATED
            ).scalar() or 0
            
            return {
                "success": True,
                "total": total,
                "pending": pending,
                "activated": activated,
                "cancelled": total - pending - activated
            }
        
        except Exception as e:
            logger.error(f"Error getting waitlist stats: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_position(self, phone_number: str) -> int:
        """Get the position of a phone number in the waitlist."""
        if not self.db_session:
            return -1
        
        try:
            # Count entries with higher priority or earlier join date
            position = self.db_session.query(func.count(Waitlist.id)).filter(
                Waitlist.status == WaitlistStatus.PENDING,
                Waitlist.phone_number != phone_number
            ).filter(
                # Either higher priority, or same priority but earlier join date
            ).scalar() or 0
            
            return position + 1
        except:
            return -1
    
    async def _send_welcome_sms(self, phone_number: str, position: int):
        """Send welcome SMS to new waitlist member."""
        try:
            message = f"Welcome to Rafiki! You've been added to our waitlist at position #{position}. We'll notify you when it's your turn. Thank you for your interest!"
            await sms_service.send_sms(phone_number, message)
        except Exception as e:
            logger.warning(f"Failed to send welcome SMS to {phone_number}: {e}")
    
    async def _send_activation_sms(self, phone_number: str, name: str):
        """Send activation SMS when user is activated."""
        try:
            message = f"Great news, {name}! Your Rafiki account has been activated! You can now access all government services. Log in now to get started!"
            await sms_service.send_sms(phone_number, message)
        except Exception as e:
            logger.warning(f"Failed to send activation SMS to {phone_number}: {e}")


# Singleton instance
_waitlist_service: Optional[WaitlistService] = None


def get_waitlist_service(db_session: Optional[Session] = None) -> WaitlistService:
    """Get or create the waitlist service instance."""
    global _waitlist_service
    
    if _waitlist_service is None:
        _waitlist_service = WaitlistService(db_session)
    elif db_session:
        _waitlist_service.set_db_session(db_session)
    
    return _waitlist_service
