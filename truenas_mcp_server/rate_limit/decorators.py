"""Rate limiting decorators."""

import functools
import logging
from typing import Callable, Optional

from .limiter import get_rate_limiter

logger = logging.getLogger(__name__)


def rate_limit(
    key_func: Optional[Callable] = None,
    tokens: int = 1,
    raise_on_limit: bool = True,
    enabled: bool = True,
):
    """
    Decorator to rate limit function calls.

    Args:
        key_func: Function to extract rate limit key from args/kwargs
                  Default uses first argument or "default"
        tokens: Number of tokens to consume per call
        raise_on_limit: Whether to raise exception on rate limit
        enabled: Whether rate limiting is enabled

    Example:
        @rate_limit(key_func=lambda user, **kw: user.id)
        async def create_dataset(user, dataset_name: str):
            ...

        @rate_limit(tokens=5)  # Expensive operation
        async def import_data():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not enabled:
                return await func(*args, **kwargs)

            # Get rate limiter
            limiter = get_rate_limiter()

            # Extract rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            elif args:
                key = str(args[0])  # Use first argument
            else:
                key = "default"

            # Check rate limit
            await limiter.check_limit(key, tokens=tokens, raise_on_limit=raise_on_limit)

            # Execute function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def adaptive_rate_limit(
    key_func: Optional[Callable] = None, cost_func: Optional[Callable] = None
):
    """
    Decorator for adaptive rate limiting based on operation cost.

    Args:
        key_func: Function to extract rate limit key
        cost_func: Function to calculate token cost from args/result
                   Takes (args, kwargs, result) and returns token cost

    Example:
        @adaptive_rate_limit(
            key_func=lambda user, **kw: user.id,
            cost_func=lambda args, kwargs, result: len(result.get("items", []))
        )
        async def list_items(user):
            # Cost based on number of items returned
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()

            # Extract rate limit key
            if key_func:
                key = key_func(*args, **kwargs)
            elif args:
                key = str(args[0])
            else:
                key = "default"

            # Execute function first
            result = await func(*args, **kwargs)

            # Calculate cost after execution
            if cost_func:
                tokens = cost_func(args, kwargs, result)
            else:
                tokens = 1

            # Consume tokens (don't raise on limit for adaptive)
            await limiter.check_limit(key, tokens=tokens, raise_on_limit=False)

            return result

        return wrapper

    return decorator
