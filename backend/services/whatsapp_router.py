"""
Inbound WhatsApp message routing.

Text is the supported path. Voice notes are detected and acknowledged without
STT so we do not add a download+transcribe hop to the 5s voice budget until
the text channel is proven.

STT recommendation (for the follow-up voice-note slice):
  Use Google Cloud Speech-to-Text with en-KE / sw-KE. We already run Gemini,
  Dialogflow, and Google TTS; WhatsApp voice notes are OGG/Opus which Google
  accepts natively; and Kenyan English + Kiswahili quality is stronger than
  ElevenLabs Scribe today. Keep ElevenLabs for TTS only, with a pinned
  session voice_id, so STT does not compete with synthesis latency.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from rafiki_settings import get_settings
from services.conversation_pipeline import process_citizen_turn
from services.identity_continuity import (
    can_reference_agency_data,
    consent_prompt,
    grant_consent,
    has_consent,
    record_handoff,
    revoke_consent,
)
from services.whatsapp_service import WhatsAppCloudClient
from services.whatsapp_session import WhatsAppSessionService, get_whatsapp_session_service
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

logger = get_logger(__name__)

VOICE_NOTE_ACK = {
    "en": (
        "I received your voice note. Text works best for me right now — "
        "please type your question and I will pick up this same session."
    ),
    "sw": (
        "Nimepokea ujumbe wako wa sauti. Andika swali lako kwa sasa — "
        "nitazidi kipindi hiki kama kilivyo."
    ),
}

UNSUPPORTED_ACK = {
    "en": "I can read text messages on WhatsApp for now. Please type how I can help.",
    "sw": "Kwa sasa ninasoma ujumbe wa maandishi. Tafadhali andika jinsi naweza kusaidia.",
}


def extract_inbound_messages(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten a Cloud API webhook body into channel-agnostic inbound events."""
    events: List[Dict[str, Any]] = []
    for entry in payload.get("entry") or []:
        for change in entry.get("changes") or []:
            value = change.get("value") or {}
            if change.get("field") and change.get("field") != "messages":
                continue
            contacts = {c.get("wa_id"): c for c in (value.get("contacts") or [])}
            for msg in value.get("messages") or []:
                wa_id = msg.get("from") or ""
                contact = contacts.get(wa_id) or {}
                profile = (contact.get("profile") or {}).get("name")
                events.append(_normalize_message(msg, wa_id, profile))
    return events


def _normalize_message(msg: Dict[str, Any], wa_id: str, profile_name: Optional[str]) -> Dict[str, Any]:
    msg_type = msg.get("type") or "unknown"
    text = None
    media_id = None
    if msg_type == "text":
        text = (msg.get("text") or {}).get("body")
    elif msg_type in ("audio", "voice"):
        media = msg.get("audio") or msg.get("voice") or {}
        media_id = media.get("id")
    elif msg_type == "interactive":
        interactive = msg.get("interactive") or {}
        text = (
            (interactive.get("button_reply") or {}).get("title")
            or (interactive.get("list_reply") or {}).get("title")
            or (interactive.get("button_reply") or {}).get("id")
        )
    elif msg_type == "button":
        text = (msg.get("button") or {}).get("text")
    return {
        "wamid": msg.get("id"),
        "from": wa_id,
        "timestamp": msg.get("timestamp"),
        "type": msg_type,
        "text": (text or "").strip() or None,
        "media_id": media_id,
        "profile_name": profile_name,
    }


class WhatsAppRouter:
    def __init__(
        self,
        session_service: Optional[WhatsAppSessionService] = None,
        client: Optional[WhatsAppCloudClient] = None,
    ):
        self.sessions = session_service or get_whatsapp_session_service()
        self.client = client or WhatsAppCloudClient()
        self.settings = get_settings()

    async def handle_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        events = extract_inbound_messages(payload)
        results = []
        for event in events:
            results.append(await self.handle_event(event))
        return {"processed": len(results), "results": results}

    async def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        started = time.perf_counter()
        wamid = event.get("wamid")
        wa_id = event.get("from") or ""
        if not wa_id:
            return {"skipped": True, "reason": "missing_sender"}

        if wamid and not self.sessions.claim_message_id(wamid):
            logger.info("whatsapp_idempotent_skip wamid=%s", wamid)
            return {"skipped": True, "reason": "duplicate", "wamid": wamid}

        limit = await rate_limiter.check_rate_limit(f"whatsapp:{wa_id}")
        if not limit.allowed:
            logger.warning("whatsapp_rate_limited phone=%s", wa_id[:6] + "****")
            return {"skipped": True, "reason": "rate_limited", "wamid": wamid}

        record = self.sessions.get_or_create_for_phone(wa_id, event.get("profile_name"))
        language = "en"
        try:
            from services.agency_workflows import get_or_create_session
            language = get_or_create_session(record["workflow_session_id"]).language or "en"
        except Exception:
            pass

        await self.client.mark_read(wamid or "")

        inbound_type = event.get("type")
        if inbound_type in ("audio", "voice"):
            ack = VOICE_NOTE_ACK.get(language, VOICE_NOTE_ACK["en"])
            await self._outbound(record, wa_id, ack)
            self._log_turn(record, started, inbound_type, None, ack)
            return {"ok": True, "kind": "voice_ack", "session_id": record["id"]}

        text = event.get("text")
        if not text:
            ack = UNSUPPORTED_ACK.get(language, UNSUPPORTED_ACK["en"])
            await self._outbound(record, wa_id, ack)
            self._log_turn(record, started, inbound_type, None, ack)
            return {"ok": True, "kind": "unsupported", "session_id": record["id"]}

        pending = record.get("pending_consent_agency")
        if pending:
            lowered = text.lower()
            if lowered in ("yes", "y", "yeah", "ndio", "ndiyo", "sawa", "ok", "okay"):
                grant_consent(record, pending, "record_lookup")
                record["pending_consent_agency"] = None
                self.sessions.save(record)
            elif lowered in ("no", "n", "hapana", "nope"):
                revoke_consent(record, pending)
                record["pending_consent_agency"] = None
                self.sessions.save(record)
                denied = (
                    "Okay — I will keep to general guidance."
                    if language != "sw"
                    else "Sawa — nitabaki na mwongozo wa jumla."
                )
                await self._outbound(record, wa_id, denied)
                self._log_turn(record, started, "text", None, denied)
                return {"ok": True, "kind": "consent_denied", "session_id": record["id"]}

        previous_agency = record.get("current_agency")
        turn = process_citizen_turn(record["workflow_session_id"], text)
        language = turn.get("language") or language
        new_agency = turn.get("agency")

        extra_prefix = ""
        if new_agency and new_agency != previous_agency:
            event_row = record_handoff(record, previous_agency, new_agency, language)
            extra_prefix = event_row["message_preview"] + "\n\n"

        if new_agency and not can_reference_agency_data(record, new_agency):
            record["pending_consent_agency"] = new_agency
            self.sessions.snapshot_workflow(record)
            prompt = extra_prefix + consent_prompt(new_agency, language)
            await self._outbound(record, wa_id, prompt)
            self._log_turn(record, started, "text", turn.get("rag_confidence"), prompt)
            return {"ok": True, "kind": "consent_prompt", "session_id": record["id"]}

        if new_agency and not has_consent(record, new_agency, "session_guidance"):
            grant_consent(record, new_agency, "session_guidance")

        self.sessions.snapshot_workflow(record)
        reply = extra_prefix + (turn.get("reply") or "")
        await self._outbound(record, wa_id, reply)
        self._log_turn(
            record,
            started,
            "text",
            turn.get("rag_confidence"),
            reply,
            step=turn.get("step"),
        )
        return {
            "ok": True,
            "kind": "text",
            "session_id": record["id"],
            "agency": new_agency,
            "rag_confidence": turn.get("rag_confidence"),
        }

    async def _outbound(self, record: Dict[str, Any], to: str, body: str) -> None:
        last_inbound = record.get("last_inbound_at")
        result = await self.client.send_reply(to, body, last_inbound)
        if result.get("success") or result.get("simulated"):
            self.sessions.mark_outbound(record)
        else:
            logger.error(
                "whatsapp_outbound_failed session_id=%s error=%s",
                record.get("id"),
                result.get("error"),
            )

    def _log_turn(
        self,
        record: Dict[str, Any],
        started: float,
        inbound_type: Optional[str],
        rag_confidence: Optional[float],
        reply: str,
        step: Optional[str] = None,
    ) -> None:
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        logger.info(
            "whatsapp_turn session_id=%s agency=%s step=%s inbound=%s "
            "latency_ms=%s rag_confidence=%s entropy=%s reply_chars=%s",
            record.get("id"),
            record.get("current_agency"),
            step,
            inbound_type,
            latency_ms,
            rag_confidence,
            record.get("entropy_score"),
            len(reply or ""),
        )
