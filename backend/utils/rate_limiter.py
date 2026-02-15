"""
Rate limiting implementation to prevent abuse.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RateLimitInfo:
    """Information about rate limit status."""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after_seconds: Optional[int] = None


class RateLimiter:
    """
    Token bucket rate limiter implementation.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: Dict[str, list] = {}
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, identifier: str) -> RateLimitInfo:
        """
        Check if request is allowed for the given identifier.
        
        Args:
            identifier: Unique identifier (IP address, session ID, etc.)
        
        Returns:
            RateLimitInfo with status and details
        """
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self._window_seconds)
            
            # Initialize or get request list for identifier
            if identifier not in self._requests:
                self._requests[identifier] = []
            
            # Remove old requests outside the window
            self._requests[identifier] = [
                timestamp for timestamp in self._requests[identifier]
                if timestamp > window_start
            ]
            
            current_requests = len(self._requests[identifier])
            remaining = max(0, self._max_requests - current_requests)
            
            # Calculate reset time
            if self._requests[identifier]:
                oldest_request = min(self._requests[identifier])
                reset_time = oldest_request + timedelta(seconds=self._window_seconds)
            else:
                reset_time = now + timedelta(seconds=self._window_seconds)
            
            if current_requests >= self._max_requests:
                retry_after = int((reset_time - now).total_seconds())
                logger.warning(f"Rate limit exceeded for {identifier}")
                return RateLimitInfo(
                    allowed=False,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after_seconds=max(1, retry_after)
                )
            
            # Record this request
            self._requests[identifier].append(now)
            
            return RateLimitInfo(
                allowed=True,
                remaining=remaining - 1,
                reset_time=reset_time
            )
    
    async def get_status(self, identifier: str) -> RateLimitInfo:
        """
        Get rate limit status without consuming a request.
        
        Args:
            identifier: Unique identifier
        
        Returns:
            RateLimitInfo with current status
        """
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self._window_seconds)
            
            if identifier not in self._requests:
                return RateLimitInfo(
                    allowed=True,
                    remaining=self._max_requests,
                    reset_time=now + timedelta(seconds=self._window_seconds)
                )
            
            # Count valid requests
            valid_requests = [
                ts for ts in self._requests[identifier]
                if ts > window_start
            ]
            
            remaining = max(0, self._max_requests - len(valid_requests))
            
            if valid_requests:
                oldest = min(valid_requests)
                reset_time = oldest + timedelta(seconds=self._window_seconds)
            else:
                reset_time = now + timedelta(seconds=self._window_seconds)
            
            return RateLimitInfo(
                allowed=remaining > 0,
                remaining=remaining,
                reset_time=reset_time
            )
    
    async def reset(self, identifier: str) -> None:
        """
        Reset rate limit for an identifier.
        
        Args:
            identifier: Unique identifier to reset
        """
        async with self._lock:
            if identifier in self._requests:
                del self._requests[identifier]
                logger.info(f"Rate limit reset for {identifier}")
    
    async def cleanup_old_entries(self) -> int:
        """
        Clean up old entries to free memory.
        
        Returns:
            Number of entries cleaned up
        """
        async with self._lock:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self._window_seconds)
            cleaned = 0
            
            identifiers_to_remove = []
            
            for identifier, timestamps in self._requests.items():
                # Filter valid timestamps
                valid_timestamps = [ts for ts in timestamps if ts > window_start]
                
                if not valid_timestamps:
                    identifiers_to_remove.append(identifier)
                    cleaned += 1
                else:
                    self._requests[identifier] = valid_timestamps
            
            for identifier in identifiers_to_remove:
                del self._requests[identifier]
            
            if cleaned:
                logger.debug(f"Cleaned up {cleaned} rate limit entries")
            
            return cleaned


# Global rate limiter instance
rate_limiter = RateLimiter()
