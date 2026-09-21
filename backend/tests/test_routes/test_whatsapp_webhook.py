"""WhatsApp Cloud API webhook signature, verification, and simulate endpoint."""

import hashlib
import hmac
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks
from starlette.requests import Request

from routes.whatsapp import inbound_webhook, simulate_inbound, verify_webhook
from services.whatsapp_service import verify_webhook_signature

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "whatsapp"


def _sign(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _request(body: bytes, headers: dict) -> Request:
    encoded = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()]

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/whatsapp/webhook",
            "raw_path": b"/whatsapp/webhook",
            "query_string": b"",
            "headers": encoded,
            "client": ("127.0.0.1", 123),
            "server": ("test", 80),
        },
        receive,
    )


class TestWebhookSignature:
    def test_valid_signature(self):
        body = b'{"object":"whatsapp_business_account"}'
        header = _sign("app-secret", body)
        assert verify_webhook_signature(body, header, "app-secret") is True

    def test_invalid_signature(self):
        body = b'{"object":"whatsapp_business_account"}'
        assert verify_webhook_signature(body, "sha256=deadbeef", "app-secret") is False

    def test_missing_header(self):
        assert verify_webhook_signature(b"{}", None, "app-secret") is False

    def test_wrong_algorithm(self):
        assert verify_webhook_signature(b"{}", "sha1=abc", "app-secret") is False


class TestVerifyChallenge:
    @pytest.mark.asyncio
    async def test_subscribe_success(self):
        settings = MagicMock()
        settings.WHATSAPP_VERIFY_TOKEN = "verify-me"
        settings.DEBUG = True
        with patch("routes.whatsapp.get_settings", return_value=settings):
            response = await verify_webhook(
                hub_mode="subscribe",
                hub_challenge="challenge-token-99",
                hub_verify_token="verify-me",
            )
        assert response.body == b"challenge-token-99"

    @pytest.mark.asyncio
    async def test_subscribe_wrong_token(self):
        from fastapi import HTTPException

        settings = MagicMock()
        settings.WHATSAPP_VERIFY_TOKEN = "verify-me"
        settings.DEBUG = True
        with patch("routes.whatsapp.get_settings", return_value=settings):
            with pytest.raises(HTTPException) as exc:
                await verify_webhook(
                    hub_mode="subscribe",
                    hub_challenge="challenge-token-99",
                    hub_verify_token="nope",
                )
        assert exc.value.status_code == 403


class TestInboundWebhook:
    @pytest.mark.asyncio
    async def test_rejects_bad_signature_when_required(self):
        from fastapi import HTTPException

        settings = MagicMock()
        settings.DEBUG = False
        settings.WHATSAPP_REQUIRE_SIGNATURE = True
        settings.WHATSAPP_APP_SECRET = "app-secret"
        body = json.dumps({"object": "whatsapp_business_account", "entry": []}).encode()
        request = _request(body, {"content-type": "application/json", "x-hub-signature-256": "sha256=deadbeef"})
        with patch("routes.whatsapp.get_settings", return_value=settings):
            with pytest.raises(HTTPException) as exc:
                await inbound_webhook(request, BackgroundTasks())
        assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_accepts_signed_payload(self):
        settings = MagicMock()
        settings.DEBUG = False
        settings.WHATSAPP_REQUIRE_SIGNATURE = True
        settings.WHATSAPP_APP_SECRET = "app-secret"
        payload = json.loads((FIXTURES / "inbound_text.json").read_text())
        body = json.dumps(payload).encode()
        request = _request(
            body,
            {
                "content-type": "application/json",
                "x-hub-signature-256": _sign("app-secret", body),
            },
        )
        with patch("routes.whatsapp.get_settings", return_value=settings), patch(
            "routes.whatsapp._process_payload", new_callable=AsyncMock, return_value={"processed": 1}
        ):
            response = await inbound_webhook(request, BackgroundTasks())
        assert response.status_code == 200
        assert json.loads(response.body)["status"] == "accepted"

    @pytest.mark.asyncio
    async def test_simulate_replays_fixture_in_debug(self):
        settings = MagicMock()
        settings.DEBUG = True
        payload = json.loads((FIXTURES / "inbound_text.json").read_text())
        body = json.dumps(payload).encode()
        request = _request(body, {"content-type": "application/json"})
        with patch("routes.whatsapp.get_settings", return_value=settings), patch(
            "routes.whatsapp._process_payload", new_callable=AsyncMock, return_value={"processed": 1}
        ):
            result = await simulate_inbound(request)
        assert result["status"] == "ok"
