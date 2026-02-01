"""
Simple rule-based fraud service for quick detection and mitigation.

This implementation uses an in-memory counter / sliding window for rate limiting
and blocklist checks to keep tests self-contained. For production, swap the
storage layer with Redis or another durable store.
"""

import time
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class FraudService:
    """Very small rule-based fraud checks suitable for testing.

    Methods are synchronous to keep integration simple in existing async code.
    """

    def __init__(self):
        # Storage: key -> list of event timestamps (seconds)
        self._events: Dict[str, list[float]] = {}
        # Temporary blocklist: key -> unblock_timestamp
        self._blocklist: Dict[str, float] = {}

        # Default thresholds
        self.otp_limit = 5  # max OTP requests
        self.otp_window = 30 * 60  # window seconds
        self.otp_block_duration = 60 * 60  # block for 1 hour after threshold

        self.otp_fail_limit = 5
        self.otp_fail_window = 60 * 60  # 1 hour
        self.otp_fail_block_duration = 30 * 60  # 30 minutes

    def _now(self) -> float:
        return time.time()

    def _prune(self, key: str, window: int) -> None:
        now = self._now()
        entries = self._events.get(key, [])
        self._events[key] = [t for t in entries if t >= now - window]

    def record_event(self, key: str) -> None:
        """Record an event occurrence for the provided key."""
        now = self._now()
        self._events.setdefault(key, []).append(now)
        logger.debug(f"FraudService: recorded event for {key} @ {now}")

    def check_rate_limit(self, key: str, limit: int, window: int, block_duration: int) -> Dict[str, Any]:
        """Check and enforce a simple sliding window rate limit.

        Returns: {allow: bool, count: int, retry_after: Optional[int], blocked: bool}
        """
        now = self._now()

        # Unblock if time passed
        if key in self._blocklist and self._blocklist[key] <= now:
            del self._blocklist[key]

        if key in self._blocklist:
            retry_after = int(self._blocklist[key] - now)
            return {"allow": False, "count": 0, "retry_after": max(retry_after, 0), "blocked": True}

        self._prune(key, window)
        count = len(self._events.get(key, []))

        if count >= limit:
            # block
            self._blocklist[key] = now + block_duration
            return {"allow": False, "count": count, "retry_after": block_duration, "blocked": True}

        return {"allow": True, "count": count, "retry_after": None, "blocked": False}

    # Convenience helpers specifically for OTP flows
    def check_otp_request(self, phone: str) -> Dict[str, Any]:
        key = f"otp_req:{phone}"
        res = self.check_rate_limit(key, limit=self.otp_limit, window=self.otp_window, block_duration=self.otp_block_duration)
        return res

    def record_otp_request(self, phone: str) -> None:
        self.record_event(f"otp_req:{phone}")

    def check_otp_failures(self, phone: str) -> Dict[str, Any]:
        key = f"otp_fail:{phone}"
        return self.check_rate_limit(key, limit=self.otp_fail_limit, window=self.otp_fail_window, block_duration=self.otp_fail_block_duration)

    def record_otp_failure(self, phone: str) -> None:
        self.record_event(f"otp_fail:{phone}")


# Singleton accessor
_fraud_service: Optional[FraudService] = None


def get_fraud_service() -> FraudService:
    global _fraud_service
    if _fraud_service is None:
        _fraud_service = FraudService()
    return _fraud_service


def set_fraud_service(service: FraudService) -> None:
    """Replace the global singleton with a custom implementation (tests or prod)."""
    global _fraud_service
    _fraud_service = service
