"""
Chat API routes for conversations, messages and transcripts.
"""
from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse
from models.schemas import (
    ChatSessionListOut,
    ChatSessionDetailOut,
    ChatMessageCreate,
    ChatMessageOut,
    TranscriptOut,
    UnreadCountOut,
)
from services.auth_service import get_auth_service
from utils.logger import get_logger
from datetime import datetime
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])


async def get_current_user(authorization: str = Header(None)):
    """Simple auth dependency using Authorization header Bearer token.
    Returns a dict with user_id or raises 401.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    auth = get_auth_service()
    info = await auth.validate_token(token)
    if not info:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return info


@router.post("/sessions", response_model=ChatSessionListOut)
async def create_session(user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id") or user.get("user_id")
    res = await auth.create_conversation(user_id=user_id)
    # Construct minimal session out
    now = datetime.utcnow()
    return {
        "id": res.get("conversation_id"),
        "title": res.get("title"),
        "last_message_preview": "",
        "updated_at": now,
    }


@router.get("/sessions", response_model=List[ChatSessionListOut])
async def list_sessions(skip: int = Query(0), limit: int = Query(20), user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    sessions = await auth.get_user_conversations(user_id=user_id)
    # simple pagination
    return sessions[skip: skip + limit]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailOut)
async def get_session(session_id: str, user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    conv = await auth.get_conversation(session_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")
    # Map messages to ChatMessageOut
    msgs = []
    for m in conv.get("messages", []):
        msgs.append({
            "id": m.get("id"),
            "session_id": conv.get("id"),
            "sender": m.get("role"),
            "content": m.get("content"),
            "audio_url": m.get("audio_url"),
            "created_at": datetime.fromisoformat(m.get("timestamp")) if m.get("timestamp") else datetime.utcnow(),
        })
    return {
        "id": conv.get("id"),
        "title": conv.get("title"),
        "status": "active",
        "last_message_preview": (msgs[-1]["content"][:255] if msgs else ""),
        "created_at": datetime.fromisoformat(conv.get("created_at")),
        "updated_at": datetime.fromisoformat(conv.get("updated_at")),
        "messages": msgs,
    }


@router.post("/sessions/{session_id}/messages", response_model=dict)
async def post_message(session_id: str, payload: ChatMessageCreate, user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    # ensure session belongs to user
    conv = await auth.get_conversation(session_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")
    res = await auth.add_message(session_id, payload.sender, payload.content, metadata={"audio_url": payload.audio_url})
    if not res or not res.get("success"):
        raise HTTPException(status_code=500, detail="Failed to add message")
    return {"success": True, "message_id": res.get("message_id")}


@router.patch("/sessions/{session_id}", response_model=dict)
async def patch_session(session_id: str, title: str | None = None, status: str | None = None, user=Depends(get_current_user)):
    # minimal update support: rename or close
    auth = get_auth_service()
    user_id = user.get("user_id")
    conv = await auth.get_conversation(session_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")
    # Update in-memory object
    conv_obj = auth._conversations.get(session_id)
    if title is not None:
        conv_obj.title = title
    if status is not None and status.lower() == 'closed':
        conv_obj.is_archived = True
    return {"success": True}


@router.get("/transcripts", response_model=List[TranscriptOut])
async def list_transcripts(skip: int = Query(0), limit: int = Query(20), user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    items = auth.list_transcripts_for_user(user_id)
    # convert generated_at to datetime
    out = []
    for it in items[skip: skip + limit]:
        out.append({
            "transcript_id": it.get('transcript_id'),
            "conversation_id": it.get('conversation_id'),
            "filename": it.get('filename'),
            "file_path": it.get('file_path'),
            "content_type": it.get('content_type'),
            "is_read": it.get('is_read'),
            "generated_at": datetime.fromisoformat(it.get('generated_at'))
        })
    return out


@router.get("/transcripts/{transcript_id}/download")
async def download_transcript(transcript_id: str, user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    meta = auth.get_transcript(transcript_id, user_id)
    if not meta:
        raise HTTPException(status_code=404, detail="Transcript not found")
    path = meta.get('file_path')
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    # mark read
    auth.mark_transcript_read(transcript_id, user_id)
    return FileResponse(path, filename=meta.get('filename'), media_type=meta.get('content_type'))


@router.get("/transcripts/unread-count", response_model=UnreadCountOut)
async def unread_count(user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    count = auth.unread_transcripts_count(user_id)
    return {"count": count}


@router.post("/sessions/{session_id}/generate-transcript", response_model=dict)
async def generate_transcript(session_id: str, format: str = "pdf", user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    # ensure session exists
    conv = await auth.get_conversation(session_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")
    res = await auth.generate_and_store_transcript(session_id, user_id, format=format)
    if not res or not res.get('success'):
        raise HTTPException(status_code=500, detail="Failed to generate transcript")
    return {"success": True, "transcript": res.get('transcript')}
