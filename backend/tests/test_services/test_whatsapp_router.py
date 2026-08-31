"""WhatsApp routing, idempotency, and session resume."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from services.agency_workflows import _sessions
from services.identity_continuity import store_verified_attribute
from services.whatsapp_router import WhatsAppRouter, extract_inbound_messages
from services.whatsapp_session import (
    pin_voice_id,
    reset_whatsapp_session_service_for_tests,
)
from services.whatsapp_service import split_whatsapp_text, within_customer_window

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"


class FakeWhatsAppClient:
    def __init__(self):
        self.sent = []
        self.configured = True

    async def mark_read(self, message_id: str) -> None:
        return None

    async def send_reply(self, to, body, last_inbound_at_iso):
        self.sent.append({"to": to, "body": body, "last_inbound_at_iso": last_inbound_at_iso})
        return {"success": True, "simulated": True}


@pytest.fixture
def wa_router():
    _sessions.clear()
    sessions = reset_whatsapp_session_service_for_tests()
    client = FakeWhatsAppClient()
    return WhatsAppRouter(session_service=sessions, client=client), sessions, client


def _payload(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _text_event(wamid: str, body: str, wa_id: str = "254712345678") -> dict:
    return {
        "wamid": wamid,
        "from": wa_id,
        "type": "text",
        "text": body,
        "profile_name": "Amina Otieno",
        "media_id": None,
        "timestamp": "1710000000",
    }


class TestPayloadExtraction:
    def test_extracts_text_fixture(self):
        events = extract_inbound_messages(_payload("inbound_text.json"))
        assert len(events) == 1
        assert events[0]["from"] == "254712345678"
        assert events[0]["text"] == "1"
        assert events[0]["type"] == "text"

    def test_extracts_voice_note_fixture(self):
        events = extract_inbound_messages(_payload("inbound_audio.json"))
        assert events[0]["type"] == "audio"
        assert events[0]["media_id"] == "MEDIA_ID_VOICE_NOTE"
        assert events[0]["text"] is None


class TestSessionResume:
    @pytest.mark.asyncio
    async def test_same_phone_resumes_workflow_session(self, wa_router):
        router, sessions, _client = wa_router
        first = await router.handle_event(_text_event("wamid.one", "1"))
        second = await router.handle_event(_text_event("wamid.two", "1"))
        assert first["session_id"] == second["session_id"]
        record = sessions.store.get_json(f"session:{first['session_id']}")
        assert record["workflow_session_id"] in _sessions
        assert record["voice_id"] == pin_voice_id(None)

    @pytest.mark.asyncio
    async def test_voice_id_stays_pinned(self, wa_router):
        router, sessions, _client = wa_router
        result = await router.handle_event(_text_event("wamid.voicepin", "1"))
        record = sessions.store.get_json(f"session:{result['session_id']}")
        original = record["voice_id"]
        record["voice_id"] = original
        sessions.save(record)
        again = await router.handle_event(_text_event("wamid.voicepin2", "2"))
        resumed = sessions.store.get_json(f"session:{again['session_id']}")
        assert resumed["voice_id"] == original
        assert _sessions[resumed["workflow_session_id"]].voice_id == original


class TestIdempotencyAndRouting:
    @pytest.mark.asyncio
    async def test_duplicate_wamid_is_skipped(self, wa_router):
        router, _sessions_svc, client = wa_router
        event = _text_event("wamid.dup", "1")
        first = await router.handle_event(event)
        second = await router.handle_event(event)
        assert first.get("ok") is True
        assert second.get("skipped") is True
        assert second.get("reason") == "duplicate"
        assert len(client.sent) == 1

    @pytest.mark.asyncio
    async def test_voice_note_acks_without_stt(self, wa_router):
        router, _sessions_svc, client = wa_router
        events = extract_inbound_messages(_payload("inbound_audio.json"))
        result = await router.handle_event(events[0])
        assert result["kind"] == "voice_ack"
        assert "voice note" in client.sent[0]["body"].lower()

    @pytest.mark.asyncio
    async def test_handoff_message_on_agency_change(self, wa_router):
        router, _sessions_svc, client = wa_router
        # Language 1 (English) → disability No → Agencies → NTSA
        await router.handle_event(_text_event("wamid.a", "1"))
        await router.handle_event(_text_event("wamid.b", "no"))
        await router.handle_event(_text_event("wamid.c", "1"))
        result = await router.handle_event(_text_event("wamid.d", "1"))
        assert result.get("agency") == "NTSA"
        assert any("NTSA" in (row["body"] or "") and "no need to re-verify" in (row["body"] or "") for row in client.sent)

    @pytest.mark.asyncio
    async def test_consent_prompt_when_verified_attrs_exist(self, wa_router):
        router, sessions, client = wa_router
        first = await router.handle_event(_text_event("wamid.c1", "1"))
        record = sessions.store.get_json(f"session:{first['session_id']}")
        store_verified_attribute(record, "national_id", "abc123", source_agency="NRB")
        sessions.save(record)
        await router.handle_event(_text_event("wamid.c2", "no"))
        await router.handle_event(_text_event("wamid.c3", "1"))
        result = await router.handle_event(_text_event("wamid.c4", "3"))  # KRA
        assert result["kind"] == "consent_prompt"
        assert "consent" in client.sent[-1]["body"].lower() or "YES" in client.sent[-1]["body"]


class TestHelpers:
    def test_split_long_text(self):
        chunks = split_whatsapp_text("a" * 5000, limit=1000)
        assert len(chunks) == 5
        assert all(len(c) <= 1000 for c in chunks)

    def test_customer_window(self):
        from datetime import datetime, timedelta
        recent = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        old = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        assert within_customer_window(recent) is True
        assert within_customer_window(old) is False
        assert within_customer_window(None) is False
