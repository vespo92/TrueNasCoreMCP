"""Retry policies with exponential backoff."""

import asyncio
import logging
from typing import Callable, Optional, Tuple, Type
from functools import wraps
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryPolicy:
    """Retry policy configuration."""

    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)


async def exponential_backoff(
    func: Callable,
    policy: Optional[RetryPolicy] = None,
    *args,
    **kwargs,
):
    """
    Execute function with exponential backoff retry.

    Args:
        func: Async function to execute
        policy: Retry policy configuration
        *args: Function arguments
        **kwargs: Function keyword arguments

    Returns:
        Function result

    Raises:
        Last exception if all retries exhausted
    """
    policy = policy or RetryPolicy()
    last_exception = None

    for attempt in range(policy.max_attempts):
        try:
            return await func(*args, **kwargs)
        except policy.retryable_exceptions as e:
            last_exception = e

            if attempt + 1 >= policy.max_attempts:
                logger.error(f"All {policy.max_attempts} retry attempts exhausted")
                raise

            # Calculate delay with exponential backoff
            delay = min(
                policy.initial_delay * (policy.exponential_base**attempt),
                policy.max_delay,
            )

            # Add jitter if enabled
            if policy.jitter:
                import random

                delay = delay * (0.5 + random.random())

            logger.warning(
                f"Attempt {attempt + 1}/{policy.max_attempts} failed, "
                f"retrying in {delay:.2f}s: {e}"
            )
            await asyncio.sleep(delay)

    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """
    Decorator for automatic retry with exponential backoff.

    Args:
        max_attempts: Maximum retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter
        retryable_exceptions: Tuple of exception types to retry on

    Example:
        @retry(max_attempts=5, initial_delay=0.5)
        async def flaky_api_call():
            ...
    """
    policy = RetryPolicy(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions,
    )

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await exponential_backoff(func, policy, *args, **kwargs)

        return wrapper

    return decorator
