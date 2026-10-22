"""FastAPI dependency factory for per-endpoint rate limits keyed by client IP."""

from fastapi import HTTPException, Request

from utils.rate_limiter import RateLimiter


def client_ip(request: Request) -> str:
    """Caller IP that a client cannot choose.

    Render serves traffic through Cloudflare, which overwrites CF-Connecting-IP on
    every request, so it is trustworthy there. X-Forwarded-For is not: clients can
    prepend anything, so only its last entry (appended by our own proxy) is used,
    and only when the Cloudflare header is absent. Falls back to the socket peer.
    """
    cf_ip = request.headers.get("cf-connecting-ip", "").strip()
    if cf_ip:
        return cf_ip
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[-1].strip() or "unknown"
    return request.client.host if request.client else "unknown"


def rate_limit(max_requests: int, window_seconds: int = 60):
    """Return a dependency allowing `max_requests` per `window_seconds` per client IP.

    Each call creates its own limiter, so endpoints are limited independently.
    """
    limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)

    async def dependency(request: Request) -> None:
        result = await limiter.check_rate_limit(client_ip(request))
        if not result.allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down and try again shortly.",
                headers={"Retry-After": str(result.retry_after_seconds or 1)},
            )

    return dependency
