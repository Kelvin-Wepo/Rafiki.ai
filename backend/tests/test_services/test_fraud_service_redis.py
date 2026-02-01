"""Tests for Redis-backed FraudService.

These tests use `fakeredis` to emulate Redis. If `fakeredis` is not installed,
pytest will skip the tests so CI won't fail in environments where Redis testing
libraries are not available.
"""

import pytest

pytest.importorskip("fakeredis")
import fakeredis
from services.fraud_service_redis import create_redis_fraud_service


def test_redis_otp_rate_limit_basic():
    r = fakeredis.FakeRedis()
    s = create_redis_fraud_service(r)
    phone = "+254712345678"

    res = s.check_otp_request(phone)
    assert res["allow"] is True

    # Record up to limit
    for _ in range(s.otp_limit):
        s.record_otp_request(phone)

    res = s.check_otp_request(phone)
    assert res["allow"] is False
    assert res["blocked"] is True
    assert res["retry_after"] is not None


def test_redis_otp_failure_blocking():
    r = fakeredis.FakeRedis()
    s = create_redis_fraud_service(r)
    phone = "+254712345679"

    for _ in range(s.otp_fail_limit):
        s.record_otp_failure(phone)

    res = s.check_otp_failures(phone)
    assert res["allow"] is False
    assert res["blocked"] is True


def test_redis_scoped_events_and_expiry():
    r = fakeredis.FakeRedis()
    s = create_redis_fraud_service(r)
    phone = "+254700000000"

    # record one event and ensure ZSET key exists
    s.record_otp_request(phone)
    key = f"{s.ns}:events:otp_req:{phone}"
    assert r.zcard(key) == 1

    # Manually advance clock or emulate pruning by inserting old timestamp
    old_ts = 1
    r.zadd(key, {str(old_ts): old_ts})

    # check_rate_limit will prune the old event when window is small
    s.otp_window = 1
    # record another recent event to ensure pruning works
    s.record_otp_request(phone)

    res = s.check_otp_request(phone)
    # only recent events should be counted (<= 2)
    assert res["count"] <= 2


def test_set_global_fraud_service_override():
    # Ensure that the module-level setter can replace the singleton used by code
    from services.fraud_service import set_fraud_service, get_fraud_service

    r = fakeredis.FakeRedis()
    redis_svc = create_redis_fraud_service(r)

    # replace and assert
    set_fraud_service(redis_svc)
    g = get_fraud_service()
    assert g is redis_svc
