import pytest

from services.paystack_service import initiate_stk_push, verify_payment


class _FakeSettings:
    PAYSTACK_SECRET_KEY = "sk_test_x"
    PAYSTACK_CALLBACK_URL = "https://example.com/api/agencies/payments/webhook"


class _EmptySettings:
    PAYSTACK_SECRET_KEY = ""
    PAYSTACK_CALLBACK_URL = ""


class _FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response, captured):
        self._response = response
        self._captured = captured

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def post(self, url, json=None, headers=None):
        self._captured["url"] = url
        self._captured["json"] = json
        self._captured["headers"] = headers
        return self._response

    async def get(self, url, headers=None):
        self._captured["url"] = url
        self._captured["headers"] = headers
        return self._response


@pytest.mark.asyncio
async def test_initiate_stk_uses_254_without_plus(monkeypatch):
    captured = {}
    monkeypatch.setattr("services.paystack_service.get_settings", lambda: _FakeSettings())
    monkeypatch.setattr(
        "services.paystack_service.httpx.AsyncClient",
        lambda timeout=30: _FakeClient(
            _FakeResponse(
                payload={
                    "status": True,
                    "data": {
                        "status": "pay_offline",
                        "display_text": "Please complete authorization on your phone",
                    },
                }
            ),
            captured,
        ),
    )

    result = await initiate_stk_push(
        phone="0712345678",
        amount_ksh=50,
        email="user@rafiki.ai",
        reference="RAFIKI-TEST-1",
    )

    assert result["success"] is True
    assert captured["json"]["mobile_money"]["phone"] == "254712345678"
    assert not captured["json"]["mobile_money"]["phone"].startswith("+")
    assert captured["json"]["currency"] == "KES"
    assert captured["json"]["callback_url"] == _FakeSettings.PAYSTACK_CALLBACK_URL
    assert result["display_text"].lower().find("phone") >= 0


@pytest.mark.asyncio
async def test_initiate_stk_fails_without_secret_key(monkeypatch):
    monkeypatch.setattr("services.paystack_service.get_settings", lambda: _EmptySettings())
    result = await initiate_stk_push(
        phone="0712345678",
        amount_ksh=50,
        email="user@rafiki.ai",
        reference="RAFIKI-TEST-2",
    )
    assert result["success"] is False
    assert "not configured" in result["message"].lower()


@pytest.mark.asyncio
async def test_verify_without_secret_key_is_not_paid(monkeypatch):
    monkeypatch.setattr("services.paystack_service.get_settings", lambda: _EmptySettings())
    result = await verify_payment("RAFIKI-TEST-3")
    assert result["paid"] is False
