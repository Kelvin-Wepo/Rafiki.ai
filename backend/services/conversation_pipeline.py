"""
Single citizen-turn pipeline used by WhatsApp (and later other channels).

There is no Decision Graph object in this repo. agency_workflows.handle_message
is the existing step machine, so text and (future) voice transcripts both enter
here. RAG is consulted when the workflow is on the Constitution step so we can
log a confidence score without forking a second reply path.

Latency: this function is CPU/local for the workflow. RAG is optional and
must fail open — a Chroma miss must not add silence on WhatsApp.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.agency_workflows import handle_message, get_or_create_session
from utils.logger import get_logger

logger = get_logger(__name__)


def process_citizen_turn(workflow_session_id: str, user_text: str) -> Dict[str, Any]:
    reply = handle_message(workflow_session_id, user_text)
    state = get_or_create_session(workflow_session_id)
    rag_confidence: Optional[float] = None
    rag_used = False

    if state.step in ("CONSTITUTION", "ANYTHING_ELSE") and user_text and not user_text.startswith("__"):
        rag_confidence, rag_used = _maybe_rag_confidence(user_text)

    return {
        "reply": reply,
        "step": state.step,
        "agency": state.agency,
        "service": state.service,
        "language": state.language,
        "voice_id": state.voice_id,
        "rag_confidence": rag_confidence,
        "rag_used": rag_used,
    }


def _maybe_rag_confidence(query: str) -> tuple[Optional[float], bool]:
    try:
        from services.rag_service import get_rag_service
        rag = get_rag_service()
        if not rag.is_initialized():
            return None, False
        results = rag.query(query, top_k=3)
        if not results:
            return None, True
        return float(results[0].score), True
    except Exception as exc:
        logger.info("RAG skipped for WhatsApp turn: %s", exc)
        return None, False
