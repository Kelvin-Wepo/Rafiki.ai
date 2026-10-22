import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from rafiki_settings import Settings
from routes import agencies
from routes.agencies import MAX_PAYMENT_KSH, PaymentInitRequest
from utils import rate_limiter as rl
from utils.rate_limit_dep import rate_limit


class _Req:
    def __init__(self, host: str = "1.2.3.4", headers: dict | None = None):
        self.client = type("C", (), {"host": host})()
        self.headers = headers or {}


async def _hit(dep, host: str = "1.2.3.4", headers: dict | None = None):
    return await dep(_Req(host, headers))


def test_client_ip_prefers_cloudflare_and_ignores_spoofed_forwarded_for():
    from utils.rate_limit_dep import client_ip

    # CF-Connecting-IP wins over anything the caller put in X-Forwarded-For.
    assert client_ip(_Req(headers={"cf-connecting-ip": "5.5.5.5", "x-forwarded-for": "9.9.9.9"})) == "5.5.5.5"
    # Without it, only the last (proxy-appended) entry counts, not the spoofable first.
    assert client_ip(_Req(headers={"x-forwarded-for": "6.6.6.6, 7.7.7.7"})) == "7.7.7.7"
    assert client_ip(_Req("8.8.8.8")) == "8.8.8.8"


@pytest.mark.asyncio
async def test_spoofed_forwarded_for_does_not_bypass_limit():
    dep = rate_limit(1, 60)
    cf = {"cf-connecting-ip": "5.5.5.5"}
    await _hit(dep, headers={**cf, "x-forwarded-for": "1.1.1.1"})
    with pytest.raises(HTTPException):
        await _hit(dep, headers={**cf, "x-forwarded-for": "2.2.2.2"})


@pytest.mark.asyncio
async def test_rate_limit_dependency_returns_429_with_retry_after():
    dep = rate_limit(2, 60)
    await _hit(dep)
    await _hit(dep)
    with pytest.raises(HTTPException) as exc:
        await _hit(dep)
    assert exc.value.status_code == 429
    assert int(exc.value.headers["Retry-After"]) >= 1


@pytest.mark.asyncio
async def test_limits_are_per_client_and_per_endpoint():
    a, b = rate_limit(1, 60), rate_limit(1, 60)
    await _hit(a, "1.1.1.1")
    await _hit(a, "2.2.2.2")  # another client is unaffected
    await _hit(b, "1.1.1.1")  # another endpoint is unaffected
    with pytest.raises(HTTPException):
        await _hit(a, "1.1.1.1")


@pytest.mark.parametrize("amount", [0, -5, MAX_PAYMENT_KSH + 1])
def test_payment_amount_must_be_in_range(amount):
    with pytest.raises(ValidationError):
        PaymentInitRequest(session_id="s", phone="0712345678", amount_ksh=amount, service="Test")


def test_payment_amount_accepts_valid_values():
    req = PaymentInitRequest(session_id="s", phone="0712345678", amount_ksh=1200, service="Test")
    assert req.amount_ksh == 1200


@pytest.mark.asyncio
async def test_payment_prompts_are_limited_per_phone(monkeypatch):
    monkeypatch.setattr(agencies, "_phone_prompt_limiter", rl.RateLimiter(max_requests=1, window_seconds=600))
    sent = []

    async def fake_stk(**kwargs):
        sent.append(kwargs)
        return {"success": True, "message": "ok", "display_text": "ok"}

    async def fake_sms(**kwargs):
        return None

    monkeypatch.setattr(agencies, "initiate_stk_push", fake_stk)
    monkeypatch.setattr(agencies, "send_payment_initiated_sms", fake_sms)
    req = PaymentInitRequest(session_id="limit-s", phone="0712345678", amount_ksh=100, service="Test")

    await agencies.initiate_payment(req)
    with pytest.raises(agencies.HTTPException) as exc:
        await agencies.initiate_payment(req)
    assert exc.value.status_code == 429
    assert len(sent) == 1


@pytest.mark.asyncio
async def test_session_debug_endpoint_hidden_unless_debug(monkeypatch):
    monkeypatch.setattr(agencies, "get_settings", lambda: Settings(DEBUG=False))
    with pytest.raises(agencies.HTTPException) as exc:
        await agencies.get_session_info("any-session")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_rate_limiter_prunes_idle_identifiers(monkeypatch):
    monkeypatch.setattr(rl, "CLEANUP_EVERY", 3)
    limiter = rl.RateLimiter(max_requests=5, window_seconds=0)
    for ident in ("a", "b", "c", "d"):
        await limiter.check_rate_limit(ident)
    assert len(limiter._requests) < 4
