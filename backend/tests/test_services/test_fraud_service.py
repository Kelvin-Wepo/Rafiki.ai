"""Tests for FraudService (basic rate limiting and failure tracking)."""

from services.fraud_service import FraudService
import time


def test_otp_rate_limit_basic():
    s = FraudService()
    phone = "+254712345678"

    # Initially allowed
    res = s.check_otp_request(phone)
    assert res["allow"] is True

    # Record up to limit
    for _ in range(s.otp_limit):
        s.record_otp_request(phone)

    res = s.check_otp_request(phone)
    # After reaching limit, next check should block (blocked True)
    assert res["allow"] is False
    assert res["blocked"] is True
    assert res["retry_after"] is not None


def test_otp_failure_blocking():
    s = FraudService()
    phone = "+254712345679"

    # Record failures
    for _ in range(s.otp_fail_limit):
        s.record_otp_failure(phone)

    res = s.check_otp_failures(phone)
    assert res["allow"] is False
    assert res["blocked"] is True
