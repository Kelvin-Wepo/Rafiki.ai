import hashlib
import hmac
import json

import pytest

from rafiki_settings import Settings
from routes import agencies
from routes.agencies import paystack_webhook

SECRET = "sk_test_unit_secret"
BODY = json.dumps(
    {"event": "charge.success", "data": {"reference": "RAFIKI-T-1", "amount": 10000, "id": 7}}
).encode()


class _Req:
    def __init__(self, body: bytes, headers: dict):
        self._body = body
        self.headers = headers

    async def body(self) -> bytes:
        return self._body


def _sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()


@pytest.fixture
def fulfilled(monkeypatch):
    calls = []

    async def fake_fulfill(reference, **kwargs):
        calls.append(reference)
        return {"paid": True}

    monkeypatch.setattr(agencies, "fulfill_successful_payment", fake_fulfill)
    return calls


def _with_secret(monkeypatch, secret: str):
    settings = Settings(PAYSTACK_SECRET_KEY=secret)
    monkeypatch.setattr(agencies, "get_settings", lambda: settings)


@pytest.mark.asyncio
async def test_missing_signature_is_rejected(monkeypatch, fulfilled):
    _with_secret(monkeypatch, SECRET)
    with pytest.raises(agencies.HTTPException) as exc:
        await paystack_webhook(_Req(BODY, {}))
    assert exc.value.status_code == 401
    assert fulfilled == []


@pytest.mark.asyncio
async def test_wrong_signature_is_rejected(monkeypatch, fulfilled):
    _with_secret(monkeypatch, SECRET)
    with pytest.raises(agencies.HTTPException) as exc:
        await paystack_webhook(_Req(BODY, {"x-paystack-signature": _sign(BODY, "other")}))
    assert exc.value.status_code == 401
    assert fulfilled == []


@pytest.mark.asyncio
async def test_unconfigured_secret_is_rejected(monkeypatch, fulfilled):
    _with_secret(monkeypatch, "")
    with pytest.raises(agencies.HTTPException) as exc:
        await paystack_webhook(_Req(BODY, {"x-paystack-signature": _sign(BODY)}))
    assert exc.value.status_code == 503
    assert fulfilled == []


@pytest.mark.asyncio
async def test_valid_signature_fulfils_payment(monkeypatch, fulfilled):
    _with_secret(monkeypatch, SECRET)
    result = await paystack_webhook(_Req(BODY, {"x-paystack-signature": _sign(BODY)}))
    assert result == {"status": "ok"}
    assert fulfilled == ["RAFIKI-T-1"]
