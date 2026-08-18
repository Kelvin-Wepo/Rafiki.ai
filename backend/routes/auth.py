"""
Authentication API routes with security controls.
Implements phone-based OTP authentication via Africa's Talking.
Supports password-based registration and login.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import Response, JSONResponse
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import re

from models.user import (
    PhoneAuthRequest, OTPVerifyRequest, AuthResponse,
    TranscriptExport, OTPDeliveryMethod as UserOTPDeliveryMethod
)
from services.auth_service import get_auth_service
from utils.logger import get_logger
from rafiki_settings import get_settings

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============== Request Models ==============

def normalize_kenyan_phone(v: str) -> str:
    """
    Normalize a Kenyan phone number to E.164 (+254XXXXXXXXX).

    OTPs are stored keyed by the (hashed) normalized phone at registration,
    so every endpoint that looks an OTP up MUST normalize the same way
    """
    v = re.sub(r'[\s\-]', '', v)
    if v.startswith('0'):
        v = '+254' + v[1:]
    elif v.startswith('254'):
        v = '+' + v
    elif not v.startswith('+'):
        v = '+254' + v
    return v


class RegisterRequest(BaseModel):
    """User registration request."""
    full_name: str = Field(..., min_length=3, max_length=200)
    email: str = Field(...)
    phone: str = Field(...)
    id_number: str = Field(..., min_length=7, max_length=8)
    password: str = Field(..., min_length=8)
    has_disability: bool = Field(default=False)
    otp_delivery: str = Field(default="sms", description="OTP delivery method: sms, voice, email, both, all")
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v):
            raise ValueError('Invalid email address')
        return v.lower().strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        v = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+254|254|0)?[17]\d{8}$', v):
            raise ValueError('Invalid Kenyan phone number')
        # Normalize to +254 format
        if v.startswith('0'):
            v = '+254' + v[1:]
        elif v.startswith('254'):
            v = '+' + v
        elif not v.startswith('+'):
            v = '+254' + v
        return v
    
    @validator('id_number')
    def validate_id_number(cls, v):
        if not re.match(r'^\d{7,8}$', v):
            raise ValueError('ID number must be 7-8 digits')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one number')
        return v


class VerifyRegistrationRequest(BaseModel):
    """Verify OTP to complete registration."""
    email: str = Field(...)
    phone: str = Field(...)
    otp: str = Field(..., min_length=6, max_length=6)
    
    @validator('email')
    def validate_email(cls, v):
        v = v.strip().lower()
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v):
            raise ValueError('Invalid email address')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        v = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+254|254|0)?[17]\d{8}$', v):
            raise ValueError('Invalid Kenyan phone number')
        if v.startswith('0'):
            v = '+254' + v[1:]
        elif v.startswith('254'):
            v = '+' + v
        elif not v.startswith('+'):
            v = '+254' + v
        return v

    @validator('otp')
    def validate_otp(cls, v):
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP must be exactly 6 digits')
        return v


class PasswordLoginRequest(BaseModel):
    """Password-based login request."""
    identifier: str = Field(..., description="Email or phone number")
    password: str = Field(...)
    
    @validator('identifier')
    def validate_identifier(cls, v):
        v = v.strip()
        # Check if it's an email
        if '@' in v:
            if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', v):
                raise ValueError('Invalid email address')
            return v.lower()
        # Otherwise treat as phone
        v = re.sub(r'[\s\-]', '', v)
        if re.match(r'^(\+254|254|0)?[17]\d{8}$', v):
            if v.startswith('0'):
                v = '+254' + v[1:]
            elif v.startswith('254'):
                v = '+' + v
            elif not v.startswith('+'):
                v = '+254' + v
        return v


class ResendOTPRequest(BaseModel):
    """Request to resend OTP."""
    email: Optional[str] = None
    phone: Optional[str] = None
    delivery_method: str = Field(default="sms")

    @validator('phone')
    def normalize_phone(cls, v):
        # Must match RegisterRequest's normalization or the OTP lookup misses
        return normalize_kenyan_phone(v) if v else v
    def validate_phone(cls, v):
        if v is None:
            return v
        v = re.sub(r'[\s\-]', '', v)
        if not re.match(r'^(\+254|254|0)?[17]\d{8}$', v):
            raise ValueError('Invalid Kenyan phone number')
        if v.startswith('0'):
            v = '+254' + v[1:]
        elif v.startswith('254'):
            v = '+' + v
        elif not v.startswith('+'):
            v = '+254' + v
        return v


class CreateConversationRequest(BaseModel):
    """Create a new conversation request."""
    title: Optional[str] = Field(default="New Conversation")


def get_client_info(request: Request) -> tuple:
    """Extract client IP and user agent from request."""
    # Get real IP (handle proxies)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None
    
    user_agent = request.headers.get("User-Agent", "")
    
    return ip, user_agent


async def get_current_user(
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """Dependency to get current authenticated user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    auth_service = get_auth_service()
    
    ip, _ = get_client_info(request) if request else (None, None)
    user_info = await auth_service.validate_token(token, ip_address=ip)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_info


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    request: Request = None
):
    """Dependency to optionally get current user (doesn't fail if not authenticated)."""
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, request)
    except HTTPException:
        return None


# ============== Authentication Endpoints ==============

@router.post("/login", response_model=dict)
async def initiate_login(
    request: Request,
    body: PhoneAuthRequest
):
    """
    Initiate login/registration with phone number.
    Sends OTP via SMS and/or Voice Call using Africa's Talking.
    
    - For new users: Creates account after OTP verification
    - For existing users: Logs in after OTP verification
    - **delivery_method**: 'sms', 'voice', or 'both' (default: 'both')
    
    **Rate Limit:** 3 OTP requests per 5 minutes per phone number
    """
    ip, user_agent = get_client_info(request)
    auth_service = get_auth_service()
    
    result = await auth_service.initiate_login(
        phone_number=body.phone_number,
        delivery_method=body.delivery_method.value,
        ip_address=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        status_code = 429 if result.get("error") in ["rate_limited", "too_many_attempts"] else 400
        raise HTTPException(status_code=status_code, detail=result)
    
    return result


@router.post("/verify-otp", response_model=dict)
async def verify_otp(
    request: Request,
    body: OTPVerifyRequest
):
    """
    Verify OTP and complete authentication.
    
    Returns JWT access token on success.
    
    **Security:**
    - OTP expires after 5 minutes
    - Max 5 verification attempts
    - Account locked for 15 minutes after max failed attempts
    """
    ip, user_agent = get_client_info(request)
    auth_service = get_auth_service()
    
    result = await auth_service.verify_and_login(
        phone_number=body.phone_number,
        otp=body.otp,
        ip_address=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        error = result.get("error", "verification_failed")
        if error in ["account_locked", "max_attempts"]:
            status_code = 429
        elif error in ["otp_expired", "no_otp"]:
            status_code = 400
        else:
            status_code = 401
        raise HTTPException(status_code=status_code, detail=result)
    
    return result


# ============== Password-Based Registration & Login ==============

@router.post("/register", response_model=dict)
async def register_user(
    request: Request,
    body: RegisterRequest
):
    """
    Register a new user with full profile data.
    Sends OTP for verification via selected method (sms, voice, email, both, all).
    
    After registration, user must verify their phone/email with /verify-registration.
    
    **Fields:**
    - full_name: User's full name as on National ID
    - email: Valid email address
    - phone: Kenyan phone number (+254XXXXXXXXX)
    - id_number: 7-8 digit National ID number
    - password: At least 8 chars, 1 uppercase, 1 number
    - has_disability: Optional disability flag
    - otp_delivery: How to send OTP (sms, voice, email, both, all)
    """
    ip, user_agent = get_client_info(request)
    auth_service = get_auth_service()
    
    result = await auth_service.register_user(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        id_number=body.id_number,
        password=body.password,
        has_disability=body.has_disability,
        otp_delivery=body.otp_delivery,
        ip_address=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        error = result.get("error", "registration_failed")
        if error == "rate_limited":
            status_code = 429
        elif error in ["email_exists", "phone_exists", "id_exists"]:
            status_code = 409
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=result)
    
    return result


@router.post("/verify-registration", response_model=dict)
async def verify_registration(
    request: Request,
    body: VerifyRegistrationRequest
):
    """
    Verify OTP and complete user registration.
    
    Returns JWT access token and session_id on success.
    """
    ip, user_agent = get_client_info(request)
    auth_service = get_auth_service()
    
    result = await auth_service.verify_registration(
        email=body.email,
        phone=body.phone,
        otp=body.otp,
        ip_address=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        error = result.get("error", "verification_failed")
        if error in ["account_locked", "max_attempts"]:
            status_code = 429
        elif error in ["otp_expired", "no_otp", "user_not_found"]:
            status_code = 400
        else:
            status_code = 401
        raise HTTPException(status_code=status_code, detail=result)
    
    return result


@router.post("/login/password", response_model=dict)
async def password_login(
    request: Request,
    body: PasswordLoginRequest
):
    """
    Login with email/phone and password.
    
    Returns JWT access token and session_id on success.
    
    **Security:**
    - Account locked after 5 failed attempts for 15 minutes
    """
    ip, user_agent = get_client_info(request)
    auth_service = get_auth_service()
    
    result = await auth_service.login_with_password(
        identifier=body.identifier,
        password=body.password,
        ip_address=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        error = result.get("error", "login_failed")
        if error == "account_locked":
            status_code = 429
        elif error == "invalid_credentials":
            status_code = 401
        elif error == "account_pending":
            status_code = 403
        else:
            status_code = 400
        raise HTTPException(status_code=status_code, detail=result)
    
    return result


@router.post("/resend-otp", response_model=dict)
async def resend_otp(
    request: Request,
    body: ResendOTPRequest
):
    """
    Resend OTP to email or phone.
    
    **Rate Limit:** 3 OTP requests per 5 minutes
    """
    ip, user_agent = get_client_info(request)
    auth_service = get_auth_service()
    
    result = await auth_service.resend_otp(
        email=body.email,
        phone=body.phone,
        delivery_method=body.delivery_method,
        ip_address=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        status_code = 429 if result.get("error") == "rate_limited" else 400
        raise HTTPException(status_code=status_code, detail=result)
    
    return result


@router.post("/logout")
async def logout(
    request: Request,
    authorization: str = Header(...)
):
    """
    Logout and invalidate current session.
    """
    ip, user_agent = get_client_info(request)
    
    # Extract token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    auth_service = get_auth_service()
    
    result = await auth_service.logout(
        token=token,
        ip_address=ip,
        user_agent=user_agent
    )
    
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["message"])
    
    return result


@router.get("/me")
async def get_current_user_profile(
    user: dict = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    """
    auth_service = get_auth_service()
    profile = await auth_service.get_user_profile(user["user_id"])
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "phone_masked": profile.phone_masked,
        "email_masked": profile.email_masked,
        "status": profile.status,
        "created_at": profile.created_at.isoformat(),
        "last_login": profile.last_login.isoformat() if profile.last_login else None
    }


@router.get("/validate")
async def validate_token(
    user: dict = Depends(get_current_user)
):
    """
    Validate current token and return basic user info.
    Used by frontend to check auth status on app load.
    """
    return {
        "valid": True,
        "user_id": user["user_id"],
        "phone_masked": user["phone_masked"],
        "expires": user.get("exp")
    }


@router.get("/debug/last-otp")
async def debug_last_otp(
    phone: str
):
    """
    Debug endpoint to retrieve the last generated OTP for a phone number.
    Only available when DEBUG or OTP_SIMULATE is enabled. Do NOT enable in production.
    """
    settings = get_settings()
    if not (settings.DEBUG or getattr(settings, 'OTP_SIMULATE', False)):
        raise HTTPException(status_code=403, detail="Debug endpoint not allowed")

    from services.otp_service import get_otp_service as _get_otp_service
    otp_service = _get_otp_service()
    otp = otp_service.get_last_plain_otp(phone)

    if not otp:
        raise HTTPException(status_code=404, detail="OTP not found")

    return {"success": True, "phone": phone, "otp": otp}


# ============== Conversation Endpoints ==============

@router.post("/conversations")
async def create_conversation(
    body: CreateConversationRequest,
    user: dict = Depends(get_current_user)
):
    """
    Create a new conversation.
    """
    auth_service = get_auth_service()
    conversation = await auth_service.create_conversation(
        user_id=user["user_id"],
        title=body.title
    )
    
    return {
        "id": conversation["conversation_id"],
        "conversation_id": conversation["conversation_id"],
        "title": conversation["title"],
        "created_at": conversation["created_at"]
    }


@router.get("/conversations")
async def list_conversations(
    user: dict = Depends(get_current_user),
    include_archived: bool = False
):
    """
    Get all conversations for current user.
    """
    auth_service = get_auth_service()
    conversations = await auth_service.get_user_conversations(
        user["user_id"],
        include_archived=include_archived
    )
    
    return {
        "conversations": [
            {
                "id": c.id,
                "title": c.title,
                "preview": c.preview,
                "message_count": c.message_count,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat()
            }
            for c in conversations
        ]
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get a specific conversation with all messages.
    """
    auth_service = get_auth_service()
    conversation = auth_service.get_conversation(conversation_id, user["user_id"])
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "messages": conversation.messages,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat()
    }


@router.post("/conversations/{conversation_id}/messages")
async def add_message(
    conversation_id: str,
    body: dict,
    user: dict = Depends(get_current_user)
):
    """
    Add a message to a conversation.
    """
    auth_service = get_auth_service()
    
    # Verify ownership
    conversation = auth_service.get_conversation(conversation_id, user["user_id"])
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    message = auth_service.add_message(
        conversation_id=conversation_id,
        role=body.get("role", "user"),
        content=body.get("content", ""),
        metadata=body.get("metadata")
    )
    
    if not message:
        raise HTTPException(status_code=400, detail="Failed to add message")
    
    return message


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete (archive) a conversation.
    """
    auth_service = get_auth_service()
    
    success = await auth_service.delete_conversation(conversation_id, user["user_id"])
    
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"success": True, "message": "Conversation deleted"}


@router.post("/conversations/{conversation_id}/export")
async def export_transcript(
    conversation_id: str,
    body: TranscriptExport = None,
    user: dict = Depends(get_current_user)
):
    """
    Export conversation transcript as downloadable file.
    
    Formats: txt, json, pdf
    """
    format = body.format if body else "txt"
    if format not in ["txt", "json", "pdf"]:
        format = "txt"
    
    auth_service = get_auth_service()
    
    export_data = auth_service.export_transcript(
        conversation_id=conversation_id,
        user_id=user["user_id"],
        format=format
    )
    
    if not export_data:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return Response(
        content=export_data["content"],
        media_type=export_data["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{export_data["filename"]}"'
        }
    )


@router.get("/history")
async def get_user_history(
    user: dict = Depends(get_current_user)
):
    """
    Get authenticated user history including conversations and payment receipts.
    """
    auth_service = get_auth_service()
    history = await auth_service.get_user_history(user["user_id"])
    return history


@router.get("/receipts/{receipt_ref}/download")
async def download_receipt(
    receipt_ref: str,
    user: dict = Depends(get_current_user)
):
    """
    Download a PDF receipt for a booking or application record.
    """
    auth_service = get_auth_service()
    export_data = await auth_service.export_receipt(
        user_id=user["user_id"],
        receipt_ref=receipt_ref
    )
    
    if not export_data or not export_data.get("success"):
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    return Response(
        content=export_data["content"],
        media_type=export_data["content_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{export_data["filename"]}"'
        }
    )


# ============== Africa's Talking Voice Callbacks ==============

@router.post("/voice/callback")
async def voice_callback(request: Request):
    """
    Handle Africa's Talking Voice call callback.
    This endpoint is called when a voice call connects.
    Returns TwiML-like XML to speak the OTP to the user.
    """
    try:
        # Parse form data from Africa's Talking
        form_data = await request.form()
        
        session_id = form_data.get("sessionId", "")
        caller_number = form_data.get("callerNumber", "")
        destination_number = form_data.get("destinationNumber", "")
        is_active = form_data.get("isActive", "0")
        
        logger.info(f"📞 Voice callback - Session: {session_id}, To: {destination_number}, Active: {is_active}")
        
        # Get OTP service to retrieve pending OTP for this number
        from services.otp_service import get_otp_service
        from models.user import hash_value
        
        otp_service = get_otp_service()
        phone_hash = hash_value(destination_number)
        
        # Retrieve the OTP (stored in debug mode)
        otp = otp_service._last_plain_otps.get(phone_hash, "")
        
        if otp:
            otp_spoken = ". ".join(list(otp))
            response_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="en-GB-Wavenet-A" playBeep="false">
        Hello. This is Rafiki AI calling with your verification code.
        Your one time password is: {otp_spoken}.
        I repeat, your code is: {otp_spoken}.
        This code expires in 5 minutes.
        Thank you for using Rafiki AI.
    </Say>
</Response>"""
        else:
            response_xml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="en-GB-Wavenet-A" playBeep="false">
        Hello. This is Rafiki AI.
        Sorry, we could not find a verification code for your number.
        Please request a new code from the application.
        Thank you.
    </Say>
</Response>"""
        
        return Response(
            content=response_xml,
            media_type="application/xml"
        )
        
    except Exception as e:
        logger.error(f"Voice callback error: {e}")
        return Response(
            content="""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, an error occurred. Please try again later.</Say>
</Response>""",
            media_type="application/xml"
        )


@router.post("/voice/event")
async def voice_event(request: Request):
    """
    Handle Africa's Talking Voice call events (hangup, etc.).
    """
    try:
        form_data = await request.form()
        
        session_id = form_data.get("sessionId", "")
        direction = form_data.get("direction", "")
        destination_number = form_data.get("destinationNumber", "")
        call_duration = form_data.get("durationInSeconds", "0")
        currency_code = form_data.get("currencyCode", "")
        amount = form_data.get("amount", "0")
        
        logger.info(
            f"📞 Voice event - Session: {session_id}, "
            f"Direction: {direction}, Duration: {call_duration}s, "
            f"Cost: {currency_code} {amount}"
        )
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Voice event error: {e}")
        return {"status": "error", "message": str(e)}


# ============== Security/Admin Endpoints ==============

@router.get("/audit-logs")
async def get_audit_logs(
    user: dict = Depends(get_current_user),
    limit: int = 50
):
    """
    Get audit logs for current user's authentication events.
    
    **National Security Compliance:** All auth events are logged.
    """
    auth_service = get_auth_service()
    
    logs = auth_service.get_audit_logs(
        user_id=user["user_id"],
        limit=min(limit, 100)
    )
    
    return {
        "logs": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "success": log.success,
                "failure_reason": log.failure_reason,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ]
    }
