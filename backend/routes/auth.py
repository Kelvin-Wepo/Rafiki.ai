"""
Authentication API routes with security controls.
Implements phone-based OTP authentication via Africa's Talking.
"""

from fastapi import APIRouter, HTTPException, Request, Depends, Header
from fastapi.responses import Response, JSONResponse
from typing import Optional
from datetime import datetime

from backend.models.user import (
    PhoneAuthRequest, OTPVerifyRequest, AuthResponse,
    TranscriptExport
)
from backend.services.auth_service import get_auth_service
from backend.utils.logger import get_logger
from backend.config import get_settings

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
    user_info = auth_service.validate_token(token, ip_address=ip)
    
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
    Sends OTP via SMS using Africa's Talking.
    
    - For new users: Creates account after OTP verification
    - For existing users: Logs in after OTP verification
    
    **Rate Limit:** 3 OTP requests per 5 minutes per phone number
    """
    ip, user_agent = get_client_info(request)
    auth_service = get_auth_service()
    
    result = await auth_service.initiate_login(
        phone_number=body.phone_number,
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
    profile = auth_service.get_user_profile(user["user_id"])
    
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": profile.user_id,
        "phone_masked": profile.phone_masked,
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

    from backend.services.otp_service import get_otp_service as _get_otp_service
    otp_service = _get_otp_service()
    otp = otp_service.get_last_plain_otp(phone)

    if not otp:
        raise HTTPException(status_code=404, detail="OTP not found")

    return {"success": True, "phone": phone, "otp": otp}


# ============== Conversation Endpoints ==============

@router.post("/conversations")
async def create_conversation(
    user: dict = Depends(get_current_user)
):
    """
    Create a new conversation.
    """
    auth_service = get_auth_service()
    conversation = auth_service.create_conversation(user["user_id"])
    
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat()
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
    conversations = auth_service.get_user_conversations(
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
    
    success = auth_service.delete_conversation(conversation_id, user["user_id"])
    
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
    
    Formats: txt, json
    """
    format = body.format if body else "txt"
    if format not in ["txt", "json"]:
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
