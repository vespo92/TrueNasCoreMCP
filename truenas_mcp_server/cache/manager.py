"""Cache manager implementation with in-memory and optional Redis support."""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any, Optional, Dict, Callable
from functools import lru_cache
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and metadata."""

    value: Any
    timestamp: float
    ttl: int
    access_count: int = 0
    last_access: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.timestamp > self.ttl

    def access(self) -> Any:
        """Access the cached value and update metadata."""
        self.access_count += 1
        self.last_access = time.time()
        return self.value


@dataclass
class CacheStats:
    """Cache statistics."""

    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert stats to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "evictions": self.evictions,
            "size": self.size,
            "hit_rate": round(self.hit_rate, 2),
        }


class CacheManager:
    """
    Cache manager with TTL support and automatic eviction.

    Features:
    - In-memory caching with TTL
    - LRU eviction when max size is reached
    - Cache statistics
    - Async support
    - Optional Redis backend (future)
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize cache manager.

        Args:
            max_size: Maximum number of cache entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._stats = CacheStats()
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        logger.info(f"Cache manager initialized (max_size={max_size}, default_ttl={default_ttl})")

    async def start(self):
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Cache cleanup task started")

    async def stop(self):
        """Stop background cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Cache cleanup task stopped")

    async def _cleanup_loop(self):
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache cleanup: {e}")

    async def _cleanup_expired(self):
        """Remove expired entries from cache."""
        async with self._lock:
            expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in expired_keys:
                del self._cache[key]
                self._stats.evictions += 1

            if expired_keys:
                self._stats.size = len(self._cache)
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def _make_key(self, key: str, namespace: Optional[str] = None) -> str:
        """
        Create cache key with optional namespace.

        Args:
            key: Cache key
            namespace: Optional namespace prefix

        Returns:
            Namespaced cache key
        """
        if namespace:
            return f"{namespace}:{key}"
        return key

    def _hash_key(self, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hash of arguments as cache key
        """
        key_data = {
            "args": args,
            "kwargs": sorted(kwargs.items()),
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(
        self, key: str, namespace: Optional[str] = None, default: Any = None
    ) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key
            namespace: Optional namespace
            default: Default value if not found

        Returns:
            Cached value or default
        """
        cache_key = self._make_key(key, namespace)

        async with self._lock:
            entry = self._cache.get(cache_key)

            if entry is None:
                self._stats.misses += 1
                logger.debug(f"Cache miss: {cache_key}")
                return default

            if entry.is_expired():
                del self._cache[cache_key]
                self._stats.misses += 1
                self._stats.evictions += 1
                self._stats.size = len(self._cache)
                logger.debug(f"Cache expired: {cache_key}")
                return default

            self._stats.hits += 1
            logger.debug(f"Cache hit: {cache_key} (access_count={entry.access_count + 1})")
            return entry.access()

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, namespace: Optional[str] = None
    ):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if not provided)
            namespace: Optional namespace
        """
        cache_key = self._make_key(key, namespace)
        ttl = ttl or self.default_ttl

        async with self._lock:
            # Evict LRU entry if cache is full
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                await self._evict_lru()

            entry = CacheEntry(value=value, timestamp=time.time(), ttl=ttl)
            self._cache[cache_key] = entry
            self._stats.sets += 1
            self._stats.size = len(self._cache)
            logger.debug(f"Cache set: {cache_key} (ttl={ttl}s)")

    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find LRU entry
        lru_key = min(self._cache.items(), key=lambda x: x[1].last_access)[0]
        del self._cache[lru_key]
        self._stats.evictions += 1
        logger.debug(f"Cache evicted (LRU): {lru_key}")

    async def delete(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key
            namespace: Optional namespace

        Returns:
            True if deleted, False if not found
        """
        cache_key = self._make_key(key, namespace)

        async with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                self._stats.deletes += 1
                self._stats.size = len(self._cache)
                logger.debug(f"Cache deleted: {cache_key}")
                return True

            return False

    async def clear(self, namespace: Optional[str] = None):
        """
        Clear cache entries.

        Args:
            namespace: If provided, only clear entries in this namespace
        """
        async with self._lock:
            if namespace:
                # Clear only entries in namespace
                prefix = f"{namespace}:"
                keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
                for key in keys_to_delete:
                    del self._cache[key]
                logger.info(f"Cleared {len(keys_to_delete)} entries from namespace: {namespace}")
            else:
                # Clear all entries
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cleared all {count} cache entries")

            self._stats.size = len(self._cache)

    async def exists(self, key: str, namespace: Optional[str] = None) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key
            namespace: Optional namespace

        Returns:
            True if key exists and not expired
        """
        cache_key = self._make_key(key, namespace)

        async with self._lock:
            entry = self._cache.get(cache_key)
            if entry is None:
                return False

            if entry.is_expired():
                del self._cache[cache_key]
                self._stats.evictions += 1
                self._stats.size = len(self._cache)
                return False

            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._stats.to_dict()

    def reset_stats(self):
        """Reset cache statistics."""
        self._stats = CacheStats(size=len(self._cache))
        logger.info("Cache statistics reset")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


@lru_cache(maxsize=1)
def get_cache_manager() -> CacheManager:
    """
    Get or create global cache manager instance.

    Returns:
        Global CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        from ..config import get_settings

        settings = get_settings()
        _cache_manager = CacheManager(
            max_size=settings.cache_max_size, default_ttl=settings.cache_ttl
        )
        logger.info("Created global cache manager")

    return _cache_manager
