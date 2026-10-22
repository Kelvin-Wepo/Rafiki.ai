"""Voice / Access signup: SMS OTP then welcome SMS."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.auth_service import AuthService


@pytest.mark.asyncio
async def test_start_voice_registration_sends_sms_otp():
    service = AuthService()
    session = MagicMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)
    otp = AsyncMock()
    otp.request_otp = AsyncMock(
        return_value={"success": True, "expires_in": 300, "sms_sent": True, "test_mode": True, "otp": "123456"}
    )

    with patch("services.auth_service.AsyncSessionLocal", return_value=cm), patch.object(
        service, "_get_user_by_phone_hash", AsyncMock(return_value=None)
    ), patch.object(service, "_get_user_by_id_number_hash", AsyncMock(return_value=None)), patch(
        "services.otp_service.get_otp_service", return_value=otp
    ):
        result = await service.start_voice_registration(
            full_name="Jane Wanjiku",
            phone="+254712345678",
            id_number="12345678",
            language="en",
        )

    assert result["success"] is True
    assert result["requires_verification"] is True
    assert result["otp"] == "123456"
    otp.request_otp.assert_awaited()


@pytest.mark.asyncio
async def test_verify_voice_registration_sends_welcome_sms():
    service = AuthService()
    from models.user import hash_value

    phone = "+254712345678"
    phone_hash = hash_value(phone)
    service._pending_voice_registrations[phone_hash] = {
        "full_name": "Jane Wanjiku",
        "phone": phone,
        "phone_hash": phone_hash,
        "id_number_hash": hash_value("12345678"),
        "language": "en",
    }

    created = MagicMock()
    created.id = "user-voice-1"
    created.full_name = "Jane Wanjiku"
    created.email_masked = None
    created.phone_number_masked = "+254***678"
    created.status = "active"
    created.has_disability = True

    session = MagicMock()

    def add_user(obj):
        obj.id = created.id
        obj.full_name = created.full_name
        obj.email_masked = None
        obj.phone_number_masked = created.phone_number_masked
        obj.status = created.status
        obj.has_disability = True

    session.add = add_user
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=session)
    cm.__aexit__ = AsyncMock(return_value=False)

    otp = AsyncMock()
    otp.verify_otp = AsyncMock(return_value={"success": True})
    sms = AsyncMock()
    sms.send_sms = AsyncMock(return_value={"success": True})

    with patch("services.auth_service.AsyncSessionLocal", return_value=cm), patch(
        "services.otp_service.get_otp_service", return_value=otp
    ), patch("services.sms_service.sms_service", sms), patch.object(
        service, "_create_session", AsyncMock(return_value=MagicMock(id="sess-1"))
    ):
        result = await service.verify_voice_registration(phone, "123456")

    assert result["success"] is True
    assert result["sms_sent"] is True
    sms.send_sms.assert_awaited()
    assert "Welcome Jane" in sms.send_sms.await_args.args[1]
