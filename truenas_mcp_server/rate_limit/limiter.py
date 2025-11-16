"""Rate limiter implementation using token bucket algorithm."""

import asyncio
import time
import logging
from typing import Dict, Optional
from dataclasses import dataclass, field
from functools import lru_cache

from ..exceptions import TrueNASRateLimitError

logger = logging.getLogger(__name__)


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""

    capacity: int  # Maximum tokens
    refill_rate: float  # Tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(default_factory=time.time)

    def __post_init__(self):
        """Initialize with full capacity."""
        self.tokens = float(self.capacity)

    def refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        self.refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait until tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Time to wait in seconds (0 if tokens are available)
        """
        self.refill()

        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate

    @property
    def available_tokens(self) -> float:
        """Get number of available tokens."""
        self.refill()
        return self.tokens


@dataclass
class RateLimitInfo:
    """Rate limit information."""

    limit: int
    remaining: float
    reset_time: float

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for API responses."""
        return {
            "limit": self.limit,
            "remaining": int(self.remaining),
            "reset": int(self.reset_time),
        }


class RateLimiter:
    """
    Rate limiter with token bucket algorithm.

    Features:
    - Token bucket algorithm
    - Per-key rate limiting
    - Configurable limits
    - Async support
    - Statistics tracking
    """

    def __init__(self, rate_per_minute: int = 60, burst: int = 10):
        """
        Initialize rate limiter.

        Args:
            rate_per_minute: Number of requests allowed per minute
            burst: Burst capacity (max tokens in bucket)
        """
        self.rate_per_minute = rate_per_minute
        self.burst = burst
        self.refill_rate = rate_per_minute / 60.0  # Tokens per second

        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()

        logger.info(
            f"Rate limiter initialized (rate={rate_per_minute}/min, burst={burst})"
        )

    async def _get_bucket(self, key: str) -> TokenBucket:
        """
        Get or create token bucket for key.

        Args:
            key: Rate limit key (e.g., user ID, IP address)

        Returns:
            TokenBucket for the key
        """
        async with self._lock:
            if key not in self._buckets:
                self._buckets[key] = TokenBucket(
                    capacity=self.burst, refill_rate=self.refill_rate
                )
                logger.debug(f"Created new token bucket for key: {key}")

            return self._buckets[key]

    async def check_limit(
        self, key: str, tokens: int = 1, raise_on_limit: bool = True
    ) -> bool:
        """
        Check if request is allowed under rate limit.

        Args:
            key: Rate limit key
            tokens: Number of tokens to consume
            raise_on_limit: Whether to raise exception if limit exceeded

        Returns:
            True if allowed, False if rate limited

        Raises:
            TrueNASRateLimitError: If rate limit exceeded and raise_on_limit is True
        """
        bucket = await self._get_bucket(key)

        if bucket.consume(tokens):
            logger.debug(
                f"Rate limit check passed for {key} (tokens remaining: {bucket.available_tokens:.2f})"
            )
            return True

        # Rate limit exceeded
        wait_time = bucket.get_wait_time(tokens)
        reset_time = time.time() + wait_time

        logger.warning(
            f"Rate limit exceeded for {key} (wait: {wait_time:.2f}s, reset: {reset_time})"
        )

        if raise_on_limit:
            raise TrueNASRateLimitError(
                f"Rate limit exceeded. Try again in {wait_time:.1f} seconds.",
                details={
                    "limit": self.rate_per_minute,
                    "remaining": 0,
                    "reset_time": int(reset_time),
                    "wait_time": wait_time,
                },
            )

        return False

    async def get_limit_info(self, key: str) -> RateLimitInfo:
        """
        Get rate limit information for key.

        Args:
            key: Rate limit key

        Returns:
            RateLimitInfo with current state
        """
        bucket = await self._get_bucket(key)

        return RateLimitInfo(
            limit=self.rate_per_minute,
            remaining=bucket.available_tokens,
            reset_time=time.time() + (self.burst - bucket.available_tokens) / self.refill_rate,
        )

    async def reset_limit(self, key: str):
        """
        Reset rate limit for key.

        Args:
            key: Rate limit key to reset
        """
        async with self._lock:
            if key in self._buckets:
                del self._buckets[key]
                logger.info(f"Reset rate limit for key: {key}")

    async def wait_for_token(self, key: str, tokens: int = 1, timeout: Optional[float] = None):
        """
        Wait until tokens are available.

        Args:
            key: Rate limit key
            tokens: Number of tokens needed
            timeout: Maximum time to wait (None for no timeout)

        Raises:
            asyncio.TimeoutError: If timeout is reached
        """
        bucket = await self._get_bucket(key)
        wait_time = bucket.get_wait_time(tokens)

        if wait_time > 0:
            if timeout is not None and wait_time > timeout:
                raise asyncio.TimeoutError(
                    f"Rate limit wait time ({wait_time:.1f}s) exceeds timeout ({timeout}s)"
                )

            logger.debug(f"Waiting {wait_time:.2f}s for rate limit tokens: {key}")
            await asyncio.sleep(wait_time)

        bucket.consume(tokens)

    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics."""
        return {
            "rate_per_minute": self.rate_per_minute,
            "burst": self.burst,
            "active_buckets": len(self._buckets),
            "buckets": {
                key: {
                    "available_tokens": bucket.available_tokens,
                    "capacity": bucket.capacity,
                }
                for key, bucket in self._buckets.items()
            },
        }

    async def cleanup_inactive(self, inactive_threshold: int = 300):
        """
        Clean up inactive buckets.

        Args:
            inactive_threshold: Seconds of inactivity before cleanup
        """
        async with self._lock:
            now = time.time()
            keys_to_remove = []

            for key, bucket in self._buckets.items():
                if now - bucket.last_refill > inactive_threshold:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self._buckets[key]

            if keys_to_remove:
                logger.info(f"Cleaned up {len(keys_to_remove)} inactive rate limit buckets")


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    """
    Get or create global rate limiter instance.

    Returns:
        Global RateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        from ..config import get_settings

        settings = get_settings()
        _rate_limiter = RateLimiter(
            rate_per_minute=settings.rate_limit_per_minute,
            burst=settings.rate_limit_burst,
        )
        logger.info("Created global rate limiter")

    return _rate_limiter
