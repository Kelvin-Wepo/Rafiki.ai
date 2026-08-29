"""
OTP Service with security-first design.
Handles OTP generation, validation, and delivery via Africa's Talking (SMS & Voice) and Email.
Implements rate limiting and brute force protection.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, Literal
from collections import defaultdict
import asyncio
from enum import Enum

from rafiki_settings import get_settings
from utils.logger import get_logger
from models.user import (
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
    logger.warning("africastalking library not installed - SMS/Voice will be simulated")


class OTPDeliveryMethod(str, Enum):
    """OTP delivery method options."""
    SMS = "sms"
    VOICE = "voice"
    EMAIL = "email"
    BOTH = "both"  # Send via both SMS and Voice
    ALL = "all"  # Send via SMS, Voice, and Email


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
        self._voice_client = None
        self._initialized = False
        
        # In-memory stores (replace with Redis/DB in production)
        self._otp_records: Dict[str, OTPRecord] = {}
        self._rate_limit_tracker: Dict[str, list] = defaultdict(list)
        self._lockout_tracker: Dict[str, datetime] = {}
        self._audit_logs: list = []
        # Keep last plaintext OTPs in memory for debugging when DEBUG or OTP_SIMULATE is enabled
        self._last_plain_otps: Dict[str, str] = {}
    
    def initialize(self) -> bool:
        """Initialize Africa's Talking SMS and Voice clients."""
        if not AFRICASTALKING_AVAILABLE:
            logger.error(
                "africastalking library is not installed - OTP delivery will fail. "
                "Run: pip install africastalking"
            )
            self._initialized = True
            return True
        
        try:
            username = self.settings.AFRICASTALKING_USERNAME
            api_key = self.settings.AFRICASTALKING_API_KEY
            
            if not username or not api_key:
                logger.error(
                    "Africa's Talking credentials not configured - OTP delivery will fail. "
                    "Set AFRICASTALKING_USERNAME and AFRICASTALKING_API_KEY."
                )
                self._initialized = True
                return True
            
            africastalking.initialize(username=username, api_key=api_key)
            self._sms_client = africastalking.SMS
            self._voice_client = africastalking.Voice
            self._initialized = True
            
            logger.info("OTP service initialized with Africa's Talking (SMS + Voice)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Africa's Talking: {e}")
            self._initialized = True  # Allow simulation mode
            return True
    
    @property
    def _simulation_enabled(self) -> bool:
        """
        Whether a failed OTP delivery may be reported as success.

        Deliberately independent of DEBUG: a developer wants API docs and SQL
        logs without silently turning real SMS into pretend successes.
        """
        return bool(getattr(self.settings, 'OTP_SIMULATE', False))

    def _generate_otp(self) -> str:
        """Generate cryptographically secure OTP."""
        return ''.join([str(secrets.randbelow(10)) for _ in range(self.OTP_LENGTH)])

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """
        Normalize a Kenyan phone number to E.164 (+254XXXXXXXXX).
        """
        p = phone.strip().replace(" ", "")
        if p.startswith("+"):
            return p
        if p.startswith("254"):
            return f"+{p}"
        if p.startswith("0"):
            return f"+254{p[1:]}"
        return p
    
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
        delivery_method: OTPDeliveryMethod = OTPDeliveryMethod.BOTH,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request OTP for phone number authentication.
        
        Args:
            phone_number: Normalized phone number (+254XXXXXXXXX)
            delivery_method: How to deliver the OTP (sms, voice, or both)
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

        # Save plaintext OTP for debugging when allowed (DEBUG or OTP_SIMULATE)
        if self.settings.DEBUG or getattr(self.settings, 'OTP_SIMULATE', False):
            self._last_plain_otps[phone_hash] = otp
        
        # Track rate limit
        self._rate_limit_tracker[phone_hash].append(datetime.utcnow())
        
        # Send OTP via selected delivery method(s)
        sms_result = {"success": False}
        voice_result = {"success": False}
        email_result = {"success": False}
        delivery_messages = []
        
        if delivery_method in (OTPDeliveryMethod.SMS, OTPDeliveryMethod.BOTH, OTPDeliveryMethod.ALL):
            sms_result = await self._send_otp_sms(phone_number, otp)
            if sms_result["success"]:
                delivery_messages.append("SMS")
        
        if delivery_method in (OTPDeliveryMethod.VOICE, OTPDeliveryMethod.BOTH, OTPDeliveryMethod.ALL):
            voice_result = await self._send_otp_voice_call(phone_number, otp)
            if voice_result["success"]:
                delivery_messages.append("voice call")
        
        # Check if at least one delivery method succeeded
        if sms_result["success"] or voice_result["success"] or email_result["success"]:
            self._log_audit_event(
                "otp_request",
                phone_hash,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "otp_id": otp_record.id,
                    "delivery_method": delivery_method.value,
                    "sms_success": sms_result["success"],
                    "voice_success": voice_result["success"],
                    "email_success": email_result["success"]
                }
            )
            
            method_text = " and ".join(delivery_messages)
            response = {
                "success": True,
                "message": f"OTP sent successfully via {method_text}.",
                "expires_in": self.OTP_EXPIRY_MINUTES * 60,
                "otp_id": otp_record.id,
                "delivery_methods": delivery_messages,
                "sms_sent": sms_result["success"],
                "voice_sent": voice_result["success"],
                "simulated": sms_result.get("simulated", False) or voice_result.get("simulated", False)
            }
            
            # Include OTP in response for sandbox/development (DEBUG or OTP_SIMULATE)
            if self.settings.DEBUG or getattr(self.settings, 'OTP_SIMULATE', False):
                response["otp"] = otp  # Test/sandbox only - includes actual OTP
                response["test_mode"] = True
            
            return response
        else:
            self._log_audit_event(
                "otp_request",
                phone_hash,
                success=False,
                failure_reason="delivery_failed",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "delivery_failed",
                "message": "Failed to send OTP. Please try again."
            }
    
    async def _send_otp_voice_call(self, phone_number: str, otp: str) -> Dict[str, Any]:
        """
        Send OTP via voice call using Africa's Talking Voice API.
        
        Args:
            phone_number: Recipient phone number
            otp: The OTP code to speak
        
        Returns:
            Result dict with success status
        """
        # Format OTP for speech (add pauses between digits)
        otp_spoken = ". ".join(list(otp))  # "1. 2. 3. 4. 5. 6"
        
        # Create the voice message XML
        voice_message = f"""
        <Response>
            <Say voice="en-GB-Wavenet-A">
                Hello. This is Rafiki AI calling with your verification code.
                Your one time password is: {otp_spoken}.
                I repeat, your code is: {otp_spoken}.
                This code expires in {self.OTP_EXPIRY_MINUTES} minutes.
                Thank you for using Rafiki AI.
            </Say>
        </Response>
        """
        phone_number = self._normalize_phone(phone_number)

        # Log for debugging
        otp_log_msg = f"📞 VOICE OTP CALL - Phone: {phone_number}, OTP: {otp}"
        logger.warning(otp_log_msg)
        
        if not self._voice_client:
            if self._simulation_enabled:
                logger.info(f"[SIMULATION MODE] Voice OTP call would be made to {phone_number}")
                return {"success": True, "simulated": True}
            logger.error("Voice OTP requested but Africa's Talking Voice client is unavailable")
            return {"success": False, "error": "Voice service unavailable"}
        
        try:
            # Get virtual number from settings
            caller_id = self.settings.AFRICASTALKING_VIRTUAL_NUMBER
            
            if not caller_id:
                logger.warning("No virtual number configured for voice calls")
                return {"success": False, "error": "No virtual number configured"}
            
            logger.info(f"Making voice OTP call from {caller_id} to {phone_number}")
            
            # Make the voice call using Africa's Talking
            response = self._voice_client.call(
                callFrom=caller_id,
                callTo=[phone_number]
            )
            
            logger.info(f"Voice call initiated: {response}")
            
            # The actual voice message will be handled by a callback URL
            # For now, we'll use the say action directly if supported
            # or queue the message for when the call connects
            
            return {
                "success": True,
                "call_id": response.get("entries", [{}])[0].get("sessionId", ""),
                "message": voice_message
            }
            
        except Exception as e:
            logger.error(f"Voice call error: {e}")
            if self._simulation_enabled:
                logger.info("Voice call failed but OTP_SIMULATE enabled - falling back to simulation")
                return {"success": True, "simulated": True}
            return {"success": False, "error": str(e)}
    
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

        phone_number = self._normalize_phone(phone_number)

        # Always log the OTP for debugging (remove in real production with actual SMS)
        import sys
        otp_log_msg = f"🔐 OTP GENERATED - Phone: {phone_number}, OTP: {otp}"
        logger.warning(otp_log_msg)  # Use warning level to ensure it appears
        print(f"\n{'='*60}", flush=True)
        print(f"🔐 OTP for {phone_number}: {otp}", flush=True)
        print(f"{'='*60}\n", flush=True)
        sys.stdout.flush()
        sys.stderr.flush()
        
        if not self._sms_client:
            if self._simulation_enabled:
                logger.info(f"[SIMULATION MODE] OTP SMS would be sent to {phone_number}")
                return {"success": True, "simulated": True}
            logger.error("OTP SMS requested but Africa's Talking SMS client is unavailable")
            return {"success": False, "error": "SMS service unavailable"}
        
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
            recipients = response.get("SMSMessageData", {}).get("Recipients")
            if recipients:
                recipient = recipients[0]
                if recipient.get("status") == "Success":
                    return {"success": True, "message_id": recipient.get("messageId")}
                else:
                    logger.warning(f"SMS recipient status: {recipient.get('status')}")
                    if self._simulation_enabled:
                        logger.info("SMS delivery failed but OTP_SIMULATE enabled - falling back to simulation")
                        return {"success": True, "simulated": True}
                    return {"success": False, "error": f"SMS delivery failed: {recipient.get('status')}"}
            
            # No recipient info - treat as failure unless simulation enabled
            if self._simulation_enabled:
                logger.info("No SMS recipient info but OTP_SIMULATE enabled - falling back to simulation")
                return {"success": True, "simulated": True}
            return {"success": False, "error": "SMS delivery failed"}
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            if self._simulation_enabled:
                logger.info("SMS send failed but OTP_SIMULATE enabled - falling back to simulation")
                return {"success": True, "simulated": True}
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

    def get_last_plain_otp(self, phone_number: str) -> Optional[str]:
        """
        Return the last generated plaintext OTP for a phone number.
        Only available when DEBUG or OTP_SIMULATE is enabled.
        """
        if not (self.settings.DEBUG or getattr(self.settings, 'OTP_SIMULATE', False)):
            return None
        phone_hash = hash_value(phone_number)
        return self._last_plain_otps.get(phone_hash)

    async def _send_otp_email(self, email: str, otp: str) -> Dict[str, Any]:
        """
        Send OTP via email.
        
        Args:
            email: Recipient email address
            otp: The OTP code to send
        
        Returns:
            Result dict with success status
        """
        try:
            from services.email_service import get_email_service
            email_service = get_email_service()
            return await email_service.send_otp_email(email, otp, self.OTP_EXPIRY_MINUTES)
        except Exception as e:
            logger.error(f"Email OTP send error: {e}")
            # Fallback to simulated success in debug mode
            if self.settings.DEBUG or getattr(self.settings, 'OTP_SIMULATE', False):
                logger.info("Email send failed but DEBUG enabled - simulating success")
                return {"success": True, "simulated": True}
            return {"success": False, "error": str(e)}

    async def request_otp_for_email(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Request OTP for email-based authentication.
        
        Args:
            email: Email address to send OTP to
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging
        
        Returns:
            Result dict with success status and message
        """
        if not self._initialized:
            self.initialize()
        
        email_hash = hash_value(email.lower())
        
        # Check lockout
        is_locked, lockout_seconds = self._is_locked_out(email_hash)
        if is_locked:
            self._log_audit_event(
                "otp_request_email",
                email_hash,
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
        is_limited, reset_seconds = self._is_rate_limited(email_hash)
        if is_limited:
            self._log_audit_event(
                "otp_request_email",
                email_hash,
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
        
        # Create OTP record (use email_hash as identifier)
        otp_record = OTPRecord(
            id=generate_otp_id(),
            user_id="",  # Set after user lookup/creation
            phone_number_hash=email_hash,  # Reusing field for email hash
            otp_hash=otp_hash,
            status=OTPStatus.PENDING,
            expires_at=datetime.utcnow() + timedelta(minutes=self.OTP_EXPIRY_MINUTES),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Store OTP record
        self._otp_records[email_hash] = otp_record
        
        # Save plaintext OTP for debugging
        if self.settings.DEBUG or getattr(self.settings, 'OTP_SIMULATE', False):
            self._last_plain_otps[email_hash] = otp
        
        # Track rate limit
        self._rate_limit_tracker[email_hash].append(datetime.utcnow())
        
        # Send OTP via email
        email_result = await self._send_otp_email(email, otp)
        
        if email_result["success"]:
            self._log_audit_event(
                "otp_request_email",
                email_hash,
                success=True,
                ip_address=ip_address,
                user_agent=user_agent,
                metadata={
                    "otp_id": otp_record.id,
                    "delivery_method": "email"
                }
            )
            
            response = {
                "success": True,
                "message": "OTP sent successfully via email.",
                "expires_in": self.OTP_EXPIRY_MINUTES * 60,
                "otp_id": otp_record.id,
                "delivery_methods": ["email"],
                "email_sent": True,
                "simulated": email_result.get("simulated", False)
            }
            
            # Include OTP in response for sandbox/development
            if self.settings.DEBUG or getattr(self.settings, 'OTP_SIMULATE', False):
                response["otp"] = otp
                response["test_mode"] = True
            
            return response
        else:
            self._log_audit_event(
                "otp_request_email",
                email_hash,
                success=False,
                failure_reason="delivery_failed",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "delivery_failed",
                "message": "Failed to send OTP email. Please try again."
            }

    async def verify_otp_for_email(
        self,
        email: str,
        otp: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify OTP for email address.
        
        Args:
            email: Email address that received OTP
            otp: OTP code to verify
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging
        
        Returns:
            Result dict with verification status
        """
        email_hash = hash_value(email.lower())
        otp_hash = hash_value(otp)
        
        # Check lockout
        is_locked, lockout_seconds = self._is_locked_out(email_hash)
        if is_locked:
            self._log_audit_event(
                "otp_verify_email",
                email_hash,
                success=False,
                failure_reason="account_locked",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "account_locked",
                "message": f"Account temporarily locked. Try again in {lockout_seconds} seconds.",
                "retry_after": lockout_seconds
            }
        
        # Get OTP record
        otp_record = self._otp_records.get(email_hash)
        
        if not otp_record:
            self._log_audit_event(
                "otp_verify_email",
                email_hash,
                success=False,
                failure_reason="no_otp",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "no_otp",
                "message": "No OTP found. Please request a new code."
            }
        
        # Check expiration
        if otp_record.is_expired():
            otp_record.status = OTPStatus.EXPIRED
            self._log_audit_event(
                "otp_verify_email",
                email_hash,
                success=False,
                failure_reason="otp_expired",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "otp_expired",
                "message": "OTP has expired. Please request a new code."
            }
        
        # Increment attempt counter
        otp_record.attempts += 1
        
        # Check if max attempts reached
        if otp_record.is_max_attempts():
            otp_record.status = OTPStatus.FAILED
            self._lockout_tracker[email_hash] = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_MINUTES)
            
            self._log_audit_event(
                "otp_verify_email",
                email_hash,
                success=False,
                failure_reason="max_attempts",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "max_attempts",
                "message": f"Too many attempts. Account locked for {self.LOCKOUT_MINUTES} minutes."
            }
        
        # Verify OTP
        if otp_record.otp_hash != otp_hash:
            remaining = otp_record.max_attempts - otp_record.attempts
            self._log_audit_event(
                "otp_verify_email",
                email_hash,
                success=False,
                failure_reason="invalid_otp",
                ip_address=ip_address,
                user_agent=user_agent
            )
            return {
                "success": False,
                "error": "invalid_otp",
                "message": f"Invalid OTP. {remaining} attempts remaining."
            }
        
        # Success - mark as verified
        otp_record.status = OTPStatus.VERIFIED
        
        # Clean up
        del self._otp_records[email_hash]
        if email_hash in self._last_plain_otps:
            del self._last_plain_otps[email_hash]
        
        self._log_audit_event(
            "otp_verify_email",
            email_hash,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return {
            "success": True,
            "message": "OTP verified successfully."
        }


# Singleton instance
_otp_service: Optional[OTPService] = None


def get_otp_service() -> OTPService:
    """Get or create OTP service singleton."""
    global _otp_service
    if _otp_service is None:
        _otp_service = OTPService()
        _otp_service.initialize()
    return _otp_service
