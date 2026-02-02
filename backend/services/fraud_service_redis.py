"""
Redis-backed FraudService implementation.

This preserves the same public API as the in-memory `FraudService` so callers
can swap implementations without changing business logic. The implementation
uses Redis sorted sets to store event timestamps and Redis keys with TTL to
represent temporary blocks.

The module accepts a redis client compatible with `redis.Redis` or a fakeredis
instance for testing.
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class RedisFraudService:
    """Redis-backed rule-based fraud detection.

    Methods mirror the in-memory `FraudService` from `fraud_service.py`.
    """

    def __init__(self, redis_client, namespace: str = "rafiki:fraud"):
        self.redis = redis_client
        self.ns = namespace.rstrip(":")

        # Default thresholds (same as in-memory implementation)
        self.otp_limit = 5
        self.otp_window = 30 * 60
        self.otp_block_duration = 60 * 60

        self.otp_fail_limit = 5
        self.otp_fail_window = 60 * 60
        self.otp_fail_block_duration = 30 * 60

    def _now(self) -> int:
        return int(time.time())

    def _events_key(self, key: str) -> str:
        return f"{self.ns}:events:{key}"

    def _block_key(self, key: str) -> str:
        return f"{self.ns}:block:{key}"

    # Core primitives
    def record_event(self, key: str) -> None:
        k = self._events_key(key)
        # Use seconds for the score so pruning logic using windows (seconds) works.
        now_s = int(time.time())
        # Use high-resolution timestamp as member to ensure uniqueness when multiple
        # events occur within the same second (avoids being collapsed by zset uniqueness)
        now_ns = time.time_ns()
        try:
            # member -> score mapping
            self.redis.zadd(k, {str(now_ns): now_s})
            # Set an expiry slightly longer than the maximum window we might query
            self.redis.expire(k, 24 * 3600)
            logger.debug(f"RedisFraudService: recorded event {key} @ {now_s} (member {now_ns})")
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Failed to write event to redis: %s", exc)

    def check_rate_limit(self, key: str, limit: int, window: int, block_duration: int) -> Dict[str, Any]:
        now = self._now()
        blockk = self._block_key(key)

        try:
            ttl = self.redis.ttl(blockk)
            if ttl and ttl > 0:
                return {"allow": False, "count": 0, "retry_after": int(ttl), "blocked": True}

            k = self._events_key(key)
            # Remove entries older than window
            cutoff = now - window
            self.redis.zremrangebyscore(k, 0, cutoff - 1)
            count = self.redis.zcard(k)

            if count >= limit:
                # set block key with TTL
                self.redis.set(blockk, "1", ex=block_duration)
                return {"allow": False, "count": int(count), "retry_after": int(block_duration), "blocked": True}

            return {"allow": True, "count": int(count), "retry_after": None, "blocked": False}
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Redis error while checking rate limit: %s", exc)
            # Fail-open: if Redis fails, allow actions to avoid degrading UX
            return {"allow": True, "count": 0, "retry_after": None, "blocked": False}

    # OTP helpers
    def check_otp_request(self, phone: str) -> Dict[str, Any]:
        key = f"otp_req:{phone}"
        return self.check_rate_limit(key, limit=self.otp_limit, window=self.otp_window, block_duration=self.otp_block_duration)

    def record_otp_request(self, phone: str) -> None:
        self.record_event(f"otp_req:{phone}")

    def check_otp_failures(self, phone: str) -> Dict[str, Any]:
        key = f"otp_fail:{phone}"
        return self.check_rate_limit(key, limit=self.otp_fail_limit, window=self.otp_fail_window, block_duration=self.otp_fail_block_duration)

    def record_otp_failure(self, phone: str) -> None:
        self.record_event(f"otp_fail:{phone}")


# Convenience factory
def create_redis_fraud_service(redis_client, namespace: Optional[str] = None) -> RedisFraudService:
    ns = namespace if namespace is not None else "rafiki:fraud"
    return RedisFraudService(redis_client, ns)
