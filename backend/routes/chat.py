"""
Chat API routes for conversations, messages and transcripts.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from models.schemas import (
    ChatSessionListOut,
    ChatSessionDetailOut,
    ChatMessageCreate,
    ChatMessageOut,
    TranscriptOut,
    UnreadCountOut,
)
from services.auth_service import get_auth_service
from services.chat_agent import generate_text_reply, strip_stage_direction
from services.elevenlabs_service import elevenlabs_service
from utils.logger import get_logger
from datetime import datetime
import os

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])


class ChatTurnRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    language: Optional[str] = "en"


def _parse_dt(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if value:
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00").replace("+00:00", ""))
        except ValueError:
            pass
    return datetime.utcnow()


def session_detail(conv: dict) -> dict:
    msgs = []
    for m in conv.get("messages", []):
        msgs.append({
            "id": m.get("id"),
            "session_id": conv.get("id"),
            "sender": m.get("role") or m.get("sender") or "assistant",
            "content": m.get("content"),
            "audio_url": (m.get("metadata") or {}).get("audio_url") or m.get("audio_url"),
            "created_at": _parse_dt(m.get("timestamp") or m.get("created_at")),
        })
    return {
        "id": conv.get("id"),
        "title": conv.get("title"),
        "status": "active",
        "last_message_preview": (msgs[-1]["content"][:255] if msgs else ""),
        "created_at": _parse_dt(conv.get("created_at")),
        "updated_at": _parse_dt(conv.get("updated_at")),
        "messages": msgs,
    }


async def seed_greeting(conversation_id: str) -> None:
    auth = get_auth_service()
    live = await elevenlabs_service.get_live_agent_config()
    greeting = strip_stage_direction((live.get("first_message") if live.get("success") else None) or "")
    if greeting:
        await auth.add_message(conversation_id, "assistant", greeting)


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
    await seed_greeting(res.get("conversation_id"))
    conv = await auth.get_conversation(res.get("conversation_id"), user_id)
    now = datetime.utcnow()
    preview = ""
    if conv and conv.get("messages"):
        preview = conv["messages"][-1].get("content", "")[:255]
    return {
        "id": res.get("conversation_id"),
        "title": res.get("title"),
        "last_message_preview": preview,
        "updated_at": now,
    }


@router.get("/sessions", response_model=List[ChatSessionListOut])
async def list_sessions(skip: int = Query(0), limit: int = Query(20), user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    sessions = await auth.get_user_conversations(user_id=user_id)
    out = []
    for item in sessions[skip: skip + limit]:
        out.append({
            "id": item.get("id"),
            "title": item.get("title"),
            "last_message_preview": item.get("last_message_preview") or item.get("preview") or "",
            "updated_at": _parse_dt(item.get("updated_at")),
        })
    return out


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailOut)
async def get_session(session_id: str, user=Depends(get_current_user)):
    auth = get_auth_service()
    user_id = user.get("user_id")
    conv = await auth.get_conversation(session_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_detail(conv)


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


@router.post("/sessions/{session_id}/turn", response_model=ChatSessionDetailOut)
async def chat_turn(session_id: str, payload: ChatTurnRequest, user=Depends(get_current_user)):
    """Save the user message, generate a Rafiki reply, and return the full thread."""
    auth = get_auth_service()
    user_id = user.get("user_id")
    conv = await auth.get_conversation(session_id, user_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Session not found")

    text = (payload.message or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Message is required")

    history = conv.get("messages") or []
    await auth.add_message(session_id, "user", text)
    language = "sw" if (payload.language or "").lower().startswith("sw") else "en"
    reply = await generate_text_reply(text, history, language)
    await auth.add_message(session_id, "assistant", reply)
    updated = await auth.get_conversation(session_id, user_id)
    return session_detail(updated or conv)


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
    auth._save_conversations()
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
    return {"count": count, "message": "ok"}


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
