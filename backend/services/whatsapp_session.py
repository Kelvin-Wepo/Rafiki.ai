"""
Map a WhatsApp phone number onto an AgentSession and workflow SessionState.

Resume rules:
- Active, unexpired session for this phone hash is reused (including agency,
  VerifiedAttribute / ConsentGrant records attached to that session id).
- Otherwise a new AgentSession is created, voice_id pinned from settings,
  never re-picked later.

TTL: settings.SESSION_EXPIRE_MINUTES, sliding on inbound activity — same
convention as utils.session_manager.SessionManager.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import uuid

from models.user import hash_value, mask_phone_number
from rafiki_settings import get_settings
from services.agency_workflows import SessionState, get_or_create_session, _sessions
from utils.logger import get_logger
from utils.redis_store import get_redis_store

logger = get_logger(__name__)

WAMID_TTL_SECONDS = 48 * 3600


def normalize_wa_phone(raw: str) -> str:
    digits = "".join(ch for ch in (raw or "") if ch.isdigit())
    return digits


def pin_voice_id(existing: Optional[str]) -> str:
    """Never replace a session voice with a language-based default."""
    if existing:
        return existing
    return get_settings().ELEVENLABS_VOICE_ID or "jqcCZkN6Knx8BJ5TBdYR"


class WhatsAppSessionService:
    def __init__(self, store=None):
        self.store = store or get_redis_store()
        self.settings = get_settings()

    def _phone_key(self, phone_hash: str) -> str:
        return f"phone:{phone_hash}"

    def _session_key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def _workflow_key(self, workflow_id: str) -> str:
        return f"workflow:{workflow_id}"

    def _wamid_key(self, wamid: str) -> str:
        return f"wamid:{wamid}"

    def claim_message_id(self, wamid: str) -> bool:
        """Return True if this delivery should be processed (first time)."""
        if not wamid:
            return True
        return self.store.set_nx(self._wamid_key(wamid), WAMID_TTL_SECONDS)

    def get_or_create_for_phone(self, wa_id: str, profile_name: Optional[str] = None) -> Dict[str, Any]:
        phone = normalize_wa_phone(wa_id)
        phone_hash = hash_value(phone)
        now = datetime.utcnow()
        ttl_minutes = self.settings.SESSION_EXPIRE_MINUTES

        pointer = self.store.get_json(self._phone_key(phone_hash)) or {}
        session_id = pointer.get("agent_session_id")
        record = self.store.get_json(self._session_key(session_id)) if session_id else None

        if record and record.get("status") == "active":
            expires_at = datetime.fromisoformat(record["expires_at"])
            if expires_at > now:
                record["last_inbound_at"] = now.isoformat()
                record["expires_at"] = (now + timedelta(minutes=ttl_minutes)).isoformat()
                record["updated_at"] = now.isoformat()
                if profile_name:
                    record["profile_name"] = profile_name
                record["voice_id"] = pin_voice_id(record.get("voice_id"))
                self._persist(phone_hash, record)
                self._hydrate_workflow(record)
                logger.info(
                    "whatsapp_session_resume session_id=%s phone=%s agency=%s",
                    record["id"],
                    record.get("whatsapp_phone_masked"),
                    record.get("current_agency"),
                )
                return record

        workflow_id = str(uuid.uuid4())
        voice_id = pin_voice_id(None)
        record = {
            "id": str(uuid.uuid4()),
            "channel": "whatsapp",
            "status": "active",
            "workflow_session_id": workflow_id,
            "whatsapp_phone": phone,
            "whatsapp_phone_hash": phone_hash,
            "whatsapp_phone_masked": mask_phone_number("+" + phone if not phone.startswith("0") else phone),
            "current_agency": None,
            "voice_id": voice_id,
            "entropy_score": 1.0,
            "profile_name": profile_name,
            "consent_grants": {},
            "verified_attributes": {},
            "handoffs": [],
            "last_inbound_at": now.isoformat(),
            "last_outbound_at": None,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=ttl_minutes)).isoformat(),
        }
        state = get_or_create_session(workflow_id)
        state.voice_id = voice_id
        self._persist(phone_hash, record)
        self._save_workflow(state)
        logger.info(
            "whatsapp_session_create session_id=%s phone=%s voice_id=%s",
            record["id"],
            record["whatsapp_phone_masked"],
            voice_id,
        )
        return record

    def save(self, record: Dict[str, Any]) -> None:
        record["updated_at"] = datetime.utcnow().isoformat()
        self._persist(record["whatsapp_phone_hash"], record)

    def mark_outbound(self, record: Dict[str, Any]) -> None:
        record["last_outbound_at"] = datetime.utcnow().isoformat()
        self.save(record)

    def _persist(self, phone_hash: str, record: Dict[str, Any]) -> None:
        ttl = self.store.default_ttl()
        self.store.set_json(self._session_key(record["id"]), record, ttl)
        self.store.set_json(
            self._phone_key(phone_hash),
            {"agent_session_id": record["id"]},
            ttl,
        )

    def _hydrate_workflow(self, record: Dict[str, Any]) -> SessionState:
        workflow_id = record["workflow_session_id"]
        cached = self.store.get_json(self._workflow_key(workflow_id))
        if workflow_id not in _sessions:
            if cached:
                state = SessionState(
                    session_id=workflow_id,
                    step=cached.get("step", "LANGUAGE_SELECT"),
                    language=cached.get("language", "en"),
                    voice_id=pin_voice_id(cached.get("voice_id") or record.get("voice_id")),
                    agency=cached.get("agency"),
                    service=cached.get("service"),
                    sub_service=cached.get("sub_service"),
                    data=cached.get("data") or {},
                    has_disability=cached.get("has_disability"),
                    payment_ref=cached.get("payment_ref"),
                    awaiting_payment=cached.get("awaiting_payment") or False,
                    payment_amount=cached.get("payment_amount"),
                    payment_description=cached.get("payment_description"),
                    payment_mpesa=cached.get("payment_mpesa"),
                )
                _sessions[workflow_id] = state
            else:
                state = get_or_create_session(workflow_id)
                state.voice_id = pin_voice_id(record.get("voice_id"))
        else:
            state = _sessions[workflow_id]
            if not state.voice_id:
                state.voice_id = pin_voice_id(record.get("voice_id"))
            elif record.get("voice_id") and state.voice_id != record["voice_id"]:
                # Record wins: never let workflow drift to a new default voice.
                state.voice_id = record["voice_id"]
        return state

    def snapshot_workflow(self, record: Dict[str, Any]) -> None:
        workflow_id = record["workflow_session_id"]
        state = _sessions.get(workflow_id)
        if state:
            record["current_agency"] = state.agency
            record["voice_id"] = pin_voice_id(state.voice_id or record.get("voice_id"))
            state.voice_id = record["voice_id"]
            self._save_workflow(state)
            self.save(record)

    def _save_workflow(self, state: SessionState) -> None:
        payload = asdict(state)
        self.store.set_json(self._workflow_key(state.session_id), payload)


_session_service: Optional[WhatsAppSessionService] = None


def get_whatsapp_session_service() -> WhatsAppSessionService:
    global _session_service
    if _session_service is None:
        _session_service = WhatsAppSessionService()
    return _session_service


def reset_whatsapp_session_service_for_tests() -> WhatsAppSessionService:
    global _session_service
    from utils.redis_store import reset_redis_store_for_tests
    store = reset_redis_store_for_tests()
    _session_service = WhatsAppSessionService(store=store)
    return _session_service
