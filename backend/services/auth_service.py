"""
Authentication Service with security-first design.
Handles user registration, login, session management, and JWT tokens.
Implements National Security compliance with audit logging.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import jwt, JWTError

from rafiki_settings import get_settings
from utils.logger import get_logger
from models.user import (
    User, Session, Conversation, UserStatus, AuthProvider,
    UserProfile, ConversationSummary, AuthAuditLog,
    hash_value, mask_phone_number,
    generate_user_id, generate_session_id, generate_conversation_id, generate_audit_id
)
from services.otp_service import get_otp_service

logger = get_logger(__name__)


class AuthService:
    """
    Authentication service with security controls.
    
    Security Features:
    - JWT tokens with expiration
    - Session management
    - Phone number hashing (never store plain)
    - Audit logging for all auth events
    - Brute force protection (delegated to OTP service)
    """
    
    # JWT settings
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    def __init__(self):
        """Initialize auth service."""
        self.settings = get_settings()
        # Initialize OTP service lazily to allow tests to patch get_otp_service()
        self.otp_service = None
        
        # In-memory stores (replace with database in production)
        self._users: Dict[str, User] = {}  # user_id -> User
        self._users_by_phone: Dict[str, str] = {}  # phone_hash -> user_id
        self._sessions: Dict[str, Session] = {}  # session_id -> Session
        self._conversations: Dict[str, Conversation] = {}  # conv_id -> Conversation
        self._user_conversations: Dict[str, List[str]] = {}  # user_id -> [conv_ids]
        self._audit_logs: List[AuthAuditLog] = []
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret key."""
        return self.settings.SECRET_KEY or self.settings.SESSION_SECRET_KEY
    
    def _create_access_token(
        self,
        user_id: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token."""
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user_id,
            "type": "access",
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # Unique token ID
        }
        
        return jwt.encode(payload, self._get_jwt_secret(), algorithm=self.JWT_ALGORITHM)
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                self._get_jwt_secret(),
                algorithms=[self.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token validation failed: {e}")
            return None
    
    def _log_audit_event(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        phone_hash: Optional[str] = None,
        success: bool = True,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Log authentication event for audit trail."""
        audit_log = AuthAuditLog(
            id=generate_audit_id(),
            event_type=event_type,
            user_id=user_id,
            phone_number_hash=phone_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            metadata=metadata
        )
        self._audit_logs.append(audit_log)
        
        if success:
            logger.info(f"Auth event: {event_type} - User: {user_id}")
        else:
            logger.warning(f"Auth event: {event_type} - Failed: {failure_reason}")
    
    async def initiate_login(
        self,
        phone_number: str,
        delivery_method: str = "both",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate login/registration with phone number.
        Sends OTP via Africa's Talking (SMS, Voice, or Both).
        
        Args:
            phone_number: Normalized Kenyan phone number
            delivery_method: How to deliver OTP ('sms', 'voice', or 'both')
            ip_address: Client IP for audit
            user_agent: Client user agent for audit
        
        Returns:
            Result with OTP request status
        """
        phone_hash = hash_value(phone_number)
        
        # Check if user exists
        is_new_user = phone_hash not in self._users_by_phone
        
        # Fraud checks (rate limit OTP requests)
        from services.fraud_service import get_fraud_service as _get_fraud_service
        fraud = _get_fraud_service()

        otp_check = fraud.check_otp_request(phone_number)
        if not otp_check["allow"]:
            # Log audit event and return rate-limited response
            self._log_audit_event(
                "otp_request_rate_limited",
                phone_hash=hash_value(phone_number),
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"retry_after": otp_check.get("retry_after")}
            )
            return {"success": False, "error": "rate_limited", "message": "Too many OTP requests. Please try again later."}

        # Request OTP (import at call time so tests can patch services.otp_service.get_otp_service)
        from services.otp_service import get_otp_service as _get_otp_service, OTPDeliveryMethod
        otp_service = _get_otp_service()
        
        # Convert string to enum
        try:
            delivery_enum = OTPDeliveryMethod(delivery_method.lower())
        except ValueError:
            delivery_enum = OTPDeliveryMethod.BOTH

        # Support both `send_otp` (preferred) and `request_otp` method names in OTP implementations
        if hasattr(otp_service, 'send_otp'):
            otp_result = await otp_service.send_otp(
                phone_number,
                delivery_method=delivery_enum,
                ip_address=ip_address,
                user_agent=user_agent
            )
        elif hasattr(otp_service, 'request_otp'):
            otp_result = await otp_service.request_otp(
                phone_number,
                delivery_method=delivery_enum,
                ip_address=ip_address,
                user_agent=user_agent
            )
        else:
            # Unknown OTP method contract
            return {"success": False, "error": "OTP service does not support sending OTP"}

        # Record the OTP request (successful or not) so fraud counters capture attempts
        fraud.record_otp_request(phone_number)

        if otp_result["success"]:
            self._log_audit_event(
                "login_initiated",
                phone_hash=phone_hash,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"is_new_user": is_new_user}
            )
            response = {
                "success": True,
                "message": otp_result["message"],
                "is_new_user": is_new_user,
                "expires_in": otp_result.get("expires_in", 300),
                "phone_masked": mask_phone_number(phone_number)
            }
            # Pass through OTP for sandbox/testing
            if otp_result.get("test_mode") and otp_result.get("otp"):
                response["otp"] = otp_result["otp"]
            
            return response
        else:
            return otp_result
    
    async def verify_and_login(
        self,
        phone_number: str,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify OTP and complete login/registration.
        
        Args:
            phone_number: Phone number
            otp: OTP code
            ip_address: Client IP
            user_agent: Client user agent
        
        Returns:
            Auth result with JWT token if successful
        """
        # Verify OTP (import at call time so tests can patch services.otp_service.get_otp_service)
        # Before verifying, check if this phone is blocked due to many recent failures
        from services.fraud_service import get_fraud_service as _get_fraud_service
        fraud = _get_fraud_service()
        fail_check = fraud.check_otp_failures(phone_number)
        if not fail_check["allow"]:
            self._log_audit_event(
                "otp_verify_blocked",
                phone_hash=hash_value(phone_number),
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"retry_after": fail_check.get("retry_after")}
            )
            return {"success": False, "error": "blocked", "message": "Too many failed OTP attempts. Try later."}

        from services.otp_service import get_otp_service as _get_otp_service
        otp_service = _get_otp_service()
        verify_result = await otp_service.verify_otp(
            phone_number,
            otp,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # If verification failed, record the failure for rate limiting
        if not verify_result["success"]:
            fraud.record_otp_failure(phone_number)
            return verify_result
        
        phone_hash = hash_value(phone_number)
        
        # Get or create user
        if phone_hash in self._users_by_phone:
            # Existing user
            user_id = self._users_by_phone[phone_hash]
            user = self._users[user_id]
            user.last_login = datetime.utcnow()
            user.failed_attempts = 0
            is_new_user = False
        else:
            # New user registration
            user_id = generate_user_id()
            user = User(
                id=user_id,
                phone_number_hash=phone_hash,
                phone_number_masked=mask_phone_number(phone_number),
                auth_provider=AuthProvider.PHONE,
                status=UserStatus.ACTIVE,
                last_login=datetime.utcnow()
            )
            self._users[user_id] = user
            self._users_by_phone[phone_hash] = user_id
            self._user_conversations[user_id] = []
            is_new_user = True
        
        # Create session
        access_token = self._create_access_token(user_id)
        session_id = generate_session_id()
        
        session = Session(
            id=session_id,
            user_id=user_id,
            token_hash=hash_value(access_token),
            expires_at=datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent
        )
        self._sessions[session_id] = session
        
        self._log_audit_event(
            "login_success",
            user_id=user_id,
            phone_hash=phone_hash,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"is_new_user": is_new_user, "session_id": session_id}
        )
        
        return {
            "success": True,
            "message": "Login successful",
            "user_id": user_id,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "is_new_user": is_new_user,
            "user": {
                "id": user_id,
                "phone_masked": user.phone_number_masked,
                "status": user.status,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None
            }
        }
    
    async def validate_token(
        self,
        token: str,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return user info. Async wrapper so tests can await it.
        """
        payload = self._verify_token(token)
        
        if not payload:
            return None
        
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        # If user exists, confirm status; otherwise allow token-based validation
        user = self._users.get(user_id)
        if user and user.status != UserStatus.ACTIVE:
            logger.warning(f"User {user_id} has non-active status: {user.status}")
            return None
        
        return {
            "user_id": user_id,
            "phone_masked": user.phone_number_masked if user else None,
            "status": user.status if user else None,
            "exp": payload.get("exp")
        }
    
    async def logout(
        self,
        token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Logout user and invalidate session.
        
        Args:
            token: JWT access token
            ip_address: Client IP
            user_agent: Client user agent
        
        Returns:
            Logout result
        """
        payload = self._verify_token(token)
        
        if not payload:
            return {"success": False, "error": "invalid_token", "message": "Invalid or expired token"}
        
        user_id = payload.get("sub")
        token_hash = hash_value(token)
        
        # Find and invalidate session
        session_to_remove = None
        for session_id, session in self._sessions.items():
            if session.token_hash == token_hash:
                session_to_remove = session_id
                break
        
        if session_to_remove:
            del self._sessions[session_to_remove]
        
        self._log_audit_event(
            "logout",
            user_id=user_id,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {"success": True, "message": "Logged out successfully"}
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        user = self._users.get(user_id)
        
        if not user:
            return None
        
        return UserProfile(
            user_id=user.id,
            phone_masked=user.phone_number_masked,
            status=user.status,
            created_at=user.created_at,
            last_login=user.last_login
        )
    
    # ============== Conversation Management ==============
    
    async def create_conversation(self, user_id: str, title: str = "New Conversation") -> Dict[str, Any]:
        """Create a new conversation for user and return a minimal result dict."""
        conv_id = generate_conversation_id()
        
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            title=title,
            messages=[]
        )
        
        self._conversations[conv_id] = conversation
        
        if user_id not in self._user_conversations:
            self._user_conversations[user_id] = []
        self._user_conversations[user_id].append(conv_id)
        
        logger.info(f"Created conversation {conv_id} for user {user_id}")
        return {"success": True, "conversation_id": conv_id, "title": title}    

    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> Optional[dict]:
        """Add message to conversation and return operation result."""
        conversation = self._conversations.get(conversation_id)
        
        if not conversation:
            return {"success": False, "error": "Conversation not found"}
        
        message = {
            "id": secrets.token_hex(8),
            "role": role,  # "user" or "assistant"
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        conversation.messages.append(message)
        conversation.updated_at = datetime.utcnow()
        
        # Update title from first user message if still default
        if conversation.title == "New Conversation" and role == "user":
            conversation.title = content[:50] + ("..." if len(content) > 50 else "")
        
        return {"success": True, "message_id": message["id"]}    

    
    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[dict]:
        """Get conversation by ID and return as dict."""
        conversation = self._conversations.get(conversation_id)
        
        if not conversation or conversation.user_id != user_id:
            return None
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "messages": conversation.messages,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat()
        }
    
    async def get_user_conversations(
        self,
        user_id: str,
        include_archived: bool = False
    ) -> List[dict]:
        """Get all conversations for user and return list of summaries as dicts."""
        conv_ids = self._user_conversations.get(user_id, [])
        
        summaries = []
        for conv_id in conv_ids:
            conv = self._conversations.get(conv_id)
            if conv and (include_archived or not conv.is_archived):
                preview = ""
                if conv.messages:
                    first_msg = conv.messages[0]
                    preview = first_msg["content"][:100] + ("..." if len(first_msg["content"]) > 100 else "")
                
                summaries.append({
                    "id": conv.id,
                    "title": conv.title,
                    "preview": preview,
                    "message_count": len(conv.messages),
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat()
                })
        
        # Sort by updated_at descending
        return sorted(summaries, key=lambda x: x["updated_at"], reverse=True)
    
    async def archive_conversation(self, conversation_id: str, user_id: str) -> Dict[str, Any]:
        """Archive a conversation and return result dict."""
        conversation = await self.get_conversation(conversation_id, user_id)
        
        if not conversation:
            return {"success": False, "error": "Conversation not found"}
        
        # Mark the stored conversation object as archived
        conv_obj = self._conversations.get(conversation_id)
        if conv_obj:
            conv_obj.is_archived = True
            return {"success": True}
        return {"success": False, "error": "Conversation could not be archived"}
    
    def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation (soft delete - just archive)."""
        return self.archive_conversation(conversation_id, user_id)
    
    async def export_transcript(
        self,
        conversation_id: str,
        user_id: str,
        format: str = "txt"
    ) -> Optional[Dict[str, Any]]:
        """
        Export conversation transcript and return success wrapper.
        """
        conversation = await self.get_conversation(conversation_id, user_id)
        
        if not conversation:
            return {"success": False, "error": "Conversation not found"}
        
        if format == "json":
            import json
            content = json.dumps({
                "id": conversation["id"],
                "title": conversation["title"],
                "created_at": conversation["created_at"],
                "messages": conversation["messages"]
            }, indent=2)
            filename = f"rafiki_transcript_{conversation['id']}.json"
            content_type = "application/json"
        else:
            # Plain text format
            lines = [
                f"Rafiki.ai Conversation Transcript",
                f"Title: {conversation['title']}",
                f"Date: {conversation['created_at']}",
                f"{'='*50}",
                ""
            ]
            
            for msg in conversation['messages']:
                role = "You" if msg["role"] == "user" else "Rafiki"
                timestamp = msg.get("timestamp", "")
                lines.append(f"[{timestamp}] {role}:")
                lines.append(msg["content"])
                lines.append("")
            
            content = "\n".join(lines)
            filename = f"rafiki_transcript_{conversation['id']}.txt"
            content_type = "text/plain"
        
        return {"success": True, "content": content, "filename": filename, "content_type": content_type}
    
    # ============== Audit & Admin ==============
    
    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[dict]:
        """Get audit logs for security review and return list of dicts."""
        logs = self._audit_logs
        
        if user_id:
            logs = [l for l in logs if l.user_id == user_id]
        
        if event_type:
            logs = [l for l in logs if l.event_type == event_type]
        
        sliced = sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]
        return [l.dict() if hasattr(l, 'dict') else l.__dict__ for l in sliced]


# Singleton instance
_auth_service: Optional[AuthService] = None


def get_auth_service() -> AuthService:
    """Get or create auth service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service
