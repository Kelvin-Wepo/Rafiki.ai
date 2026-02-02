"""
OTP Service with security-first design.
Handles OTP generation, validation, and SMS delivery via Africa's Talking.
Implements rate limiting and brute force protection.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from collections import defaultdict
import asyncio

from backend.config import get_settings
from backend.utils.logger import get_logger
from backend.models.user import (
    OTPRecord, OTPStatus, AuthAuditLog,
    hash_value, generate_otp_id, generate_audit_id
)

logger = get_logger(__name__)

# Try to import africastalking
try:
    import africastalking
    AFRICASTALKING_AVAILABLE = True
except ImportError:
    AFRICASTALKING_AVAILABLE = False
    logger.warning("africastalking library not installed - SMS will be simulated")


class OTPService:
    """
    OTP service with rate limiting and security controls.
    
    Security Features:
    - OTP stored as hash only
    - Rate limiting per phone number
    - Brute force protection
    - Audit logging for all events
    - Automatic expiration
    """
    
    # Rate limiting: max requests per phone number
    MAX_OTP_REQUESTS_PER_WINDOW = 3
    RATE_LIMIT_WINDOW_MINUTES = 5
    
    # OTP settings
    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 5
    MAX_VERIFY_ATTEMPTS = 5
    
    # Cooldown after max attempts
    LOCKOUT_MINUTES = 15
    
    def __init__(self):
        """Initialize OTP service."""
        self.settings = get_settings()
        self._sms_client = None
        self._initialized = False
        
        # In-memory stores (replace with Redis/DB in production)
        self._otp_records: Dict[str, OTPRecord] = {}
        self._rate_limit_tracker: Dict[str, list] = defaultdict(list)
        self._lockout_tracker: Dict[str, datetime] = {}
        self._audit_logs: list = []
    
    def initialize(self) -> bool:
        """Initialize Africa's Talking SMS client."""
        if not AFRICASTALKING_AVAILABLE:
            logger.warning("Africa's Talking not available - using simulation mode")
            self._initialized = True
            return True
        
        try:
            username = self.settings.AFRICASTALKING_USERNAME
            api_key = self.settings.AFRICASTALKING_API_KEY
            
            if not username or not api_key:
                logger.warning("Africa's Talking credentials not configured - using simulation mode")
                self._initialized = True
                return True
            
            africastalking.initialize(username=username, api_key=api_key)
            self._sms_client = africastalking.SMS
            self._initialized = True
            
            logger.info("OTP service initialized with Africa's Talking")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking: {e}")
            self._initialized = True  # Allow simulation mode
            return True
    
    def _generate_otp(self) -> str:
        """Generate cryptographically secure OTP."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.OTP_LENGTH)])
    
    def _is_rate_limited(self, phone_hash: str) -> Tuple[bool, Optional[int]]:
        """
        Check if phone number is rate limited.
        
        Returns:
            Tuple of (is_limited, seconds_until_reset)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.RATE_LIMIT_WINDOW_MINUTES)
        
        # Clean old entries
        self._rate_limit_tracker[phone_hash] = [
            ts for ts in self._rate_limit_tracker[phone_hash]
            if ts > window_start
        ]
        
        # Check limit
        if len(self._rate_limit_tracker[phone_hash]) >= self.MAX_OTP_REQUESTS_PER_WINDOW:
            oldest = min(self._rate_limit_tracker[phone_hash])
            reset_time = oldest + timedelta(minutes=self.RATE_LIMIT_WINDOW_MINUTES)
            seconds_remaining = int((reset_time - now).total_seconds())
            return True, max(0, seconds_remaining)
        
        return False, None
    
    def _is_locked_out(self, phone_hash: str) -> Tuple[bool, Optional[int]]:
        """
        Check if phone number is locked out due to too many failed attempts.
        
        Returns:
            Tuple of (is_locked, seconds_until_unlock)
        """
        if phone_hash not in self._lockout_tracker:
            return False, None
        
        lockout_until = self._lockout_tracker[phone_hash]
        now = datetime.utcnow()
        
        if now >= lockout_until:
            del self._lockout_tracker[phone_hash]
            return False, None
        
        seconds_remaining = int((lockout_until - now).total_seconds())
        return True, seconds_remaining
    
    def _log_audit_event(
        self,
        event_type: str,
        phone_hash: str,
        success: bool,
        failure_reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """Log authentication event for audit trail."""
        audit_log = AuthAuditLog(
            id=generate_audit_id(),
            event_type=event_type,
            phone_number_hash=phone_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason,
            metadata=metadata
        )
        self._audit_logs.append(audit_log)
        
        # Log to system logger as well
        if success:
            logger.info(f"Auth event: {event_type} - Success")
        else:
            logger.warning(f"Auth event: {event_type} - Failed: {failure_reason}")
    
    async def request_otp(
        self,
        phone_number: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request OTP for phone number authentication.
        
        Args:
            phone_number: Normalized phone number (+254XXXXXXXXX)
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging
        
        Returns:
            Result dict with success status and message
        """
        if not self._initialized:
            self.initialize()
        
        phone_hash = hash_value(phone_number)
        
        # Check lockout
        is_locked, lockout_seconds = self._is_locked_out(phone_hash)
        if is_locked:
            self._log_audit_event(
                "otp_request",
                phone_hash,
                success=False,
                failure_reason="account_locked",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "too_many_attempts",
                "message": f"Too many failed attempts. Try again in {lockout_seconds} seconds.",
                "retry_after": lockout_seconds
            }
        
        # Check rate limit
        is_limited, reset_seconds = self._is_rate_limited(phone_hash)
        if is_limited:
            self._log_audit_event(
                "otp_request",
                phone_hash,
                success=False,
                failure_reason="rate_limited",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "rate_limited",
                "message": f"Too many OTP requests. Try again in {reset_seconds} seconds.",
                "retry_after": reset_seconds
            }
        
        # Generate OTP
        otp = self._generate_otp()
        otp_hash = hash_value(otp)
        
        # Create OTP record
        otp_record = OTPRecord(
            id=generate_otp_id(),
            user_id="",  # Set after user lookup/creation
            phone_number_hash=phone_hash,
            otp_hash=otp_hash,
            status=OTPStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(minutes=self.OTP_EXPIRY_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store OTP record
        self._otp_records[phone_hash] = otp_record
        
        # Track rate limit
        self._rate_limit_tracker[phone_hash].append(datetime.utcnow())
        
        # Send SMS
        sms_result = await self._send_otp_sms(phone_number, otp)
        
        if sms_result["success"]:
            self._log_audit_event(
                "otp_request",
                phone_hash,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"otp_id": otp_record.id}
            )
            return {
                "success": True,
                "message": "OTP sent successfully. Check your SMS.",
                "expires_in": self.OTP_EXPIRY_MINUTES * 60,
                "otp_id": otp_record.id
            }
        else:
            self._log_audit_event(
                "otp_request",
                phone_hash,
                success=False,
                failure_reason="sms_delivery_failed",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "sms_failed",
                "message": "Failed to send OTP. Please try again."
            }
    
    async def _send_otp_sms(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """
        Send OTP via SMS using Africa's Talking.
        
        Args:
            phone_number: Recipient phone number
            otp: The OTP code to send
        
        Returns:
            Result dict with success status
        """
        message = f"Your Rafiki.ai verification code is: {otp}. Valid for {self.OTP_EXPIRY_MINUTES} minutes. Do not share this code."
        
        # Always log the OTP for debugging (remove in real production with actual SMS)
        import sys
        otp_log_msg = f"🔐 OTP GENERATED - Phone: {phone_number}, OTP: {otp}"
        logger.warning(otp_log_msg)  # Use warning level to ensure it appears
        print(f"\n{'='*60}", flush=True)
        print(f"🔐 OTP for {phone_number}: {otp}", flush=True)
        print(f"{'='*60}\n", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        
        # If SMS client not available, simulate
        if not self._sms_client:
            logger.info(f"[SIMULATION MODE] OTP SMS would be sent to {phone_number}")
            return {"success": True, "simulated": True}
        
        try:
            # Send via Africa's Talking
            sender_id = self.settings.AFRICASTALKING_SENDER_ID
            
            response = self._sms_client.send(
                message=message,
                recipients=[phone_number],
                sender_id=sender_id if sender_id else None
            )
            
            logger.info(f"SMS sent: {response}")
            
            # Check response
            if response.get("SMSMessageData", {}).get("Recipients"):
                recipient = response["SMSMessageData"]["Recipients"][0]
                if recipient.get("status") == "Success":
                    return {"success": True, "message_id": recipient.get("messageId")}
            
            return {"success": False, "error": "SMS delivery failed"}
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return {"success": False, "error": str(e)}
    
    async def verify_otp(
        self,
        phone_number: str,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify OTP for phone number.
        
        Args:
            phone_number: Phone number that received OTP
            otp: OTP code to verify
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging
        
        Returns:
            Result dict with verification status
        """
        phone_hash = hash_value(phone_number)
        otp_hash = hash_value(otp)
        
        # Check lockout
        is_locked, lockout_seconds = self._is_locked_out(phone_hash)
        if is_locked:
            self._log_audit_event(
                "otp_verify",
                phone_hash,
                success=False,
                failure_reason="account_locked",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "account_locked",
                "message": f"Account locked. Try again in {lockout_seconds} seconds.",
                "retry_after": lockout_seconds
            }
        
        # Get OTP record
        otp_record = self._otp_records.get(phone_hash)
        
        if not otp_record:
            self._log_audit_event(
                "otp_verify",
                phone_hash,
                success=False,
                failure_reason="no_otp_found",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "no_otp",
                "message": "No OTP request found. Please request a new OTP."
            }
        
        # Check expiration
        if otp_record.is_expired():
            otp_record.status = OTPStatus.EXPIRED
            self._log_audit_event(
                "otp_verify",
                phone_hash,
                success=False,
                failure_reason="otp_expired",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "otp_expired",
                "message": "OTP has expired. Please request a new one."
            }
        
        # Check max attempts
        if otp_record.is_max_attempts():
            otp_record.status = OTPStatus.FAILED
            # Lock out the phone number
            self._lockout_tracker[phone_hash] = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_MINUTES)
            
            self._log_audit_event(
                "otp_verify",
                phone_hash,
                success=False,
                failure_reason="max_attempts_exceeded",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "max_attempts",
                "message": f"Too many failed attempts. Account locked for {self.LOCKOUT_MINUTES} minutes."
            }
        
        # Increment attempt counter
        otp_record.attempts += 1
        
        # Verify OTP
        if otp_record.otp_hash != otp_hash:
            remaining_attempts = otp_record.max_attempts - otp_record.attempts
            self._log_audit_event(
                "otp_verify",
                phone_hash,
                success=False,
                failure_reason="invalid_otp",
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={"attempts": otp_record.attempts}
            )
            return {
                "success": False,
                "error": "invalid_otp",
                "message": f"Invalid OTP. {remaining_attempts} attempts remaining.",
                "attempts_remaining": remaining_attempts
            }
        
        # OTP verified successfully
        otp_record.status = OTPStatus.VERIFIED
        
        # Clean up
        del self._otp_records[phone_hash]
        
        self._log_audit_event(
            "otp_verify",
            phone_hash,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "OTP verified successfully.",
            "phone_hash": phone_hash
        }
    
    def get_audit_logs(
        self,
        phone_hash: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Get audit logs for security review.
        
        Args:
            phone_hash: Filter by phone number hash
            event_type: Filter by event type
            limit: Maximum number of records
        
        Returns:
            List of audit log records
        """
        logs = self._audit_logs
        
        if phone_hash:
            logs = [l for l in logs if l.phone_number_hash == phone_hash]
        
        if event_type:
            logs = [l for l in logs if l.event_type == event_type]
        
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)[:limit]


# Singleton instance
_otp_service: Optional[OTPService] = None


def get_otp_service() -> OTPService:
    """Get or create OTP service singleton."""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
        _otp_service.initialize()
    return _otp_service
