"""
Shared Redis helper with in-memory TTL fallback.

Session TTL matches SessionManager / settings.SESSION_EXPIRE_MINUTES.
Redis is optional: fraud detection already treats it as swap-in storage, and
conversation sessions in this repo were in-process dicts. WhatsApp uses this
store so webhook retries and multi-worker deploys share session + idempotency
keys without inventing a second expiry convention.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

from rafiki_settings import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class InMemoryTTLStore:
    """Process-local dict with the same get/set/setnx/expire surface as Redis."""

    def __init__(self):
        self._data: Dict[str, tuple[str, float]] = {}

    def _prune(self, key: str) -> None:
        item = self._data.get(key)
        if item and item[1] <= time.time():
            self._data.pop(key, None)

    def get(self, key: str) -> Optional[str]:
        self._prune(key)
        item = self._data.get(key)
        return item[0] if item else None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> None:
        ttl = ex if ex is not None else get_settings().SESSION_EXPIRE_MINUTES * 60
        self._data[key] = (value, time.time() + ttl)

    def setnx(self, key: str, value: str, ex: int) -> bool:
        self._prune(key)
        if key in self._data:
            return False
        self._data[key] = (value, time.time() + ex)
        return True

    def expire(self, key: str, ex: int) -> None:
        self._prune(key)
        if key in self._data:
            value, _ = self._data[key]
            self._data[key] = (value, time.time() + ex)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class RedisJSONStore:
    """
    JSON get/set over Redis, or InMemoryTTLStore when REDIS_URL is unset
    or the redis package/client is unavailable.
    """

    def __init__(self, namespace: str = "rafiki:wa"):
        self.ns = namespace.rstrip(":")
        self._memory = InMemoryTTLStore()
        self._redis = None
        self._use_memory = True
        self._connect()

    def _connect(self) -> None:
        settings = get_settings()
        url = (getattr(settings, "REDIS_URL", None) or "").strip()
        if not url:
            logger.info("REDIS_URL not set — WhatsApp session store using in-memory TTL fallback")
            return
        try:
            import redis as redis_lib
            client = redis_lib.Redis.from_url(url, decode_responses=True)
            client.ping()
            self._redis = client
            self._use_memory = False
            logger.info("WhatsApp session store connected to Redis")
        except Exception as exc:
            logger.warning(
                "Redis unavailable (%s) — WhatsApp session store using in-memory TTL fallback",
                exc,
            )
            self._redis = None
            self._use_memory = True

    def _key(self, key: str) -> str:
        return f"{self.ns}:{key}"

    def default_ttl(self) -> int:
        return get_settings().SESSION_EXPIRE_MINUTES * 60

    def get_json(self, key: str) -> Optional[Dict[str, Any]]:
        raw = self._get_raw(self._key(key))
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.error("Corrupt JSON in session store key %s", key)
            return None

    def set_json(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> None:
        payload = json.dumps(value, default=str)
        self._set_raw(self._key(key), payload, ttl or self.default_ttl())

    def touch(self, key: str, ttl: Optional[int] = None) -> None:
        seconds = ttl or self.default_ttl()
        namespaced = self._key(key)
        if self._use_memory:
            self._memory.expire(namespaced, seconds)
            return
        try:
            self._redis.expire(namespaced, seconds)
        except Exception as exc:
            logger.warning("Redis expire failed: %s", exc)

    def set_nx(self, key: str, ttl: int) -> bool:
        """Return True if this caller won the idempotency lock."""
        namespaced = self._key(key)
        if self._use_memory:
            return self._memory.setnx(namespaced, "1", ttl)
        try:
            return bool(self._redis.set(namespaced, "1", nx=True, ex=ttl))
        except Exception as exc:
            logger.warning("Redis SET NX failed (%s) — falling back to memory", exc)
            return self._memory.setnx(namespaced, "1", ttl)

    def _get_raw(self, namespaced: str) -> Optional[str]:
        if self._use_memory:
            return self._memory.get(namespaced)
        try:
            return self._redis.get(namespaced)
        except Exception as exc:
            logger.warning("Redis GET failed: %s", exc)
            return self._memory.get(namespaced)

    def _set_raw(self, namespaced: str, value: str, ttl: int) -> None:
        if self._use_memory:
            self._memory.set(namespaced, value, ex=ttl)
            return
        try:
            self._redis.set(namespaced, value, ex=ttl)
        except Exception as exc:
            logger.warning("Redis SET failed (%s) — writing to memory", exc)
            self._memory.set(namespaced, value, ex=ttl)


_store: Optional[RedisJSONStore] = None


def get_redis_store() -> RedisJSONStore:
    global _store
    if _store is None:
        _store = RedisJSONStore()
    return _store


def reset_redis_store_for_tests() -> RedisJSONStore:
    """Replace the singleton with a fresh in-memory store."""
    global _store
    _store = RedisJSONStore()
    _store._use_memory = True
    _store._redis = None
    _store._memory = InMemoryTTLStore()
    return _store
