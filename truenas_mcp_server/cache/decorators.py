"""Cache decorators for easy caching of function results."""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional

from .manager import get_cache_manager

logger = logging.getLogger(__name__)


def cached(
    ttl: Optional[int] = None,
    namespace: Optional[str] = None,
    key_func: Optional[Callable] = None,
    enabled: bool = True,
):
    """
    Decorator to cache async function results.

    Args:
        ttl: Cache TTL in seconds (uses manager default if not provided)
        namespace: Cache namespace for grouping related entries
        key_func: Optional function to generate cache key from args/kwargs
        enabled: Whether caching is enabled (useful for conditional caching)

    Example:
        @cached(ttl=300, namespace="pools")
        async def get_pool(pool_name: str):
            return await api.get(f"/pool/{pool_name}")

        @cached(key_func=lambda name, **kw: f"user:{name}")
        async def get_user(name: str):
            return await api.get(f"/user/{name}")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Skip caching if disabled
            if not enabled:
                return await func(*args, **kwargs)

            # Get cache manager
            cache = get_cache_manager()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: hash function name + arguments
                cache_key = cache._hash_key(func.__name__, *args, **kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key, namespace=namespace)

            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}: {cache_key}")
                return cached_value

            # Cache miss - call function
            logger.debug(f"Cache miss for {func.__name__}: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl, namespace=namespace)

            return result

        # Add cache control methods
        wrapper.cache_clear = lambda: asyncio.create_task(
            get_cache_manager().clear(namespace=namespace)
        )
        wrapper.cache_info = lambda: get_cache_manager().get_stats()

        return wrapper

    return decorator


def cache_invalidate(namespace: str, key: Optional[str] = None):
    """
    Decorator to invalidate cache after function execution.

    Args:
        namespace: Cache namespace to invalidate
        key: Specific key to invalidate (if None, clears entire namespace)

    Example:
        @cache_invalidate(namespace="pools")
        async def create_pool(pool_data: dict):
            return await api.post("/pool", json=pool_data)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Call function first
            result = await func(*args, **kwargs)

            # Invalidate cache
            cache = get_cache_manager()
            if key:
                await cache.delete(key, namespace=namespace)
                logger.debug(f"Invalidated cache key: {namespace}:{key}")
            else:
                await cache.clear(namespace=namespace)
                logger.debug(f"Cleared cache namespace: {namespace}")

            return result

        return wrapper

    return decorator


def conditional_cache(condition_func: Callable[[Any], bool], **cache_kwargs):
    """
    Conditionally cache results based on a predicate function.

    Args:
        condition_func: Function that takes the result and returns True to cache
        **cache_kwargs: Arguments passed to @cached decorator

    Example:
        # Only cache successful API responses
        @conditional_cache(lambda result: result.get("success") is True, ttl=300)
        async def api_call():
            return await make_request()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache = get_cache_manager()
            cache_key = cache._hash_key(func.__name__, *args, **kwargs)
            namespace = cache_kwargs.get("namespace")

            # Try cache first
            cached_value = await cache.get(cache_key, namespace=namespace)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache only if condition is met
            if condition_func(result):
                ttl = cache_kwargs.get("ttl")
                await cache.set(cache_key, result, ttl=ttl, namespace=namespace)
                logger.debug(f"Conditionally cached result for {func.__name__}")

            return result

        return wrapper

    return decorator
