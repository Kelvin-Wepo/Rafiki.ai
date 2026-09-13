import pytest

from routes.agencies import fulfill_successful_payment, maybe_initiate_workflow_payment
from services.agency_workflows import clear_session, get_or_create_session


def _payment_session(session_id: str):
    clear_session(session_id)
    state = get_or_create_session(session_id)
    state.awaiting_payment = True
    state.payment_amount = 100
    state.payment_mpesa = "0712345678"
    state.data["mpesa"] = "0712345678"
    state.service = "Logbook Search"
    state.agency = "NTSA"
    state.language = "en"
    return state


@pytest.mark.asyncio
async def test_maybe_initiate_sends_stk_and_prompt_sms_once(monkeypatch):
    sid = "stk-once-session"
    _payment_session(sid)
    stk_calls = []
    sms_calls = []

    async def fake_stk(**kwargs):
        stk_calls.append(kwargs)
        return {
            "success": True,
            "display_text": "Check your phone and enter your M-PESA PIN.",
        }

    async def fake_sms(**kwargs):
        sms_calls.append(kwargs)

    monkeypatch.setattr("routes.agencies.initiate_stk_push", fake_stk)
    monkeypatch.setattr("routes.agencies.send_payment_initiated_sms", fake_sms)
    monkeypatch.setattr(
        "routes.agencies.save_application",
        lambda **kwargs: {"application_ref": "APP-1"},
    )
    monkeypatch.setattr("routes.agencies.get_application_by_payment_ref", lambda ref: None)
    monkeypatch.setattr("routes.agencies.get_agency_booking_by_payment_ref", lambda ref: None)

    first = await maybe_initiate_workflow_payment(sid)
    second = await maybe_initiate_workflow_payment(sid)

    assert first["stk_sent"] is True
    assert second["stk_sent"] is True
    assert first["payment_ref"] == second["payment_ref"]
    assert len(stk_calls) == 1
    assert len(sms_calls) == 1
    assert stk_calls[0]["phone"] == "0712345678"


@pytest.mark.asyncio
async def test_fulfill_sends_one_confirmation_sms(monkeypatch):
    sid = "pay-confirm-session"
    state = _payment_session(sid)
    state.payment_ref = "RAFIKI-REF-99"
    sms_calls = []

    async def fake_sms(**kwargs):
        sms_calls.append(kwargs)

    monkeypatch.setattr("routes.agencies.send_payment_confirmed_sms", fake_sms)
    monkeypatch.setattr("routes.agencies.get_application_by_payment_ref", lambda ref: {
        "application_ref": "APP-9",
        "service": "Logbook Search",
        "applicant": {"phone": "0712345678"},
        "payment": {"amount": 100, "confirmation_sms_sent": False},
    })
    monkeypatch.setattr("routes.agencies.get_agency_booking_by_payment_ref", lambda ref: None)
    monkeypatch.setattr("routes.agencies.mark_application_paid", lambda *a, **k: {"application_ref": "APP-9"})
    monkeypatch.setattr("routes.agencies.mark_agency_booking_paid", lambda *a, **k: None)
    monkeypatch.setattr("routes.agencies.mark_app_sms_sent", lambda ref: None)
    monkeypatch.setattr("routes.agencies.mark_booking_sms_sent", lambda ref: None)
    monkeypatch.setattr("routes.agencies.app_sms_already_sent", lambda ref: False)
    monkeypatch.setattr("routes.agencies.booking_sms_already_sent", lambda ref: False)

    first = await fulfill_successful_payment("RAFIKI-REF-99", amount_ksh=100, transaction_id="tx-1")
    monkeypatch.setattr("routes.agencies.app_sms_already_sent", lambda ref: True)
    second = await fulfill_successful_payment("RAFIKI-REF-99", amount_ksh=100, transaction_id="tx-1")

    assert first["sms_sent"] is True
    assert second["already_notified"] is True
    assert len(sms_calls) == 1
    assert sms_calls[0]["phone"] == "0712345678"
    assert get_or_create_session(sid).awaiting_payment is False
