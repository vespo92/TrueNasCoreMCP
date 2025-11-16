"""Decorators for automatic metrics tracking."""

import functools
import time
import logging
from typing import Callable, Optional

from .collector import get_metrics_collector

logger = logging.getLogger(__name__)


def track_time(metric_name: Optional[str] = None, labels: Optional[dict] = None):
    """
    Decorator to track function execution time.

    Args:
        metric_name: Name of the metric (defaults to function name)
        labels: Optional labels for the metric

    Example:
        @track_time()
        async def fetch_pools():
            ...

        @track_time("api_call_duration", {"endpoint": "pools"})
        async def get_pools():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            name = metric_name or f"{func.__name__}_duration_seconds"

            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metrics.histogram(name, labels).observe(duration)
                logger.debug(f"{func.__name__} took {duration:.3f}s")

        return wrapper

    return decorator


def track_counter(metric_name: Optional[str] = None, labels: Optional[dict] = None, amount: int = 1):
    """
    Decorator to increment counter on function call.

    Args:
        metric_name: Name of the counter (defaults to function name + "_calls_total")
        labels: Optional labels for the metric
        amount: Amount to increment by

    Example:
        @track_counter()
        async def create_dataset():
            ...

        @track_counter("user_creations_total", {"type": "manual"})
        async def create_user():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            name = metric_name or f"{func.__name__}_calls_total"

            # Increment counter
            metrics.counter(name, labels).inc(amount)

            # Call function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def track_errors(
    error_metric: Optional[str] = None,
    success_metric: Optional[str] = None,
    labels: Optional[dict] = None,
):
    """
    Decorator to track function errors and successes.

    Args:
        error_metric: Name of error counter
        success_metric: Name of success counter
        labels: Optional labels for metrics

    Example:
        @track_errors()
        async def risky_operation():
            ...

        @track_errors("api_errors_total", "api_success_total")
        async def api_call():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            error_name = error_metric or f"{func.__name__}_errors_total"
            success_name = success_metric or f"{func.__name__}_success_total"

            try:
                result = await func(*args, **kwargs)
                # Success
                metrics.counter(success_name, labels).inc()
                return result
            except Exception as e:
                # Error
                error_labels = {**(labels or {}), "error_type": type(e).__name__}
                metrics.counter(error_name, error_labels).inc()
                raise

        return wrapper

    return decorator


def track_in_progress(gauge_name: Optional[str] = None, labels: Optional[dict] = None):
    """
    Decorator to track in-progress function calls.

    Args:
        gauge_name: Name of the gauge
        labels: Optional labels for the metric

    Example:
        @track_in_progress()
        async def long_running_task():
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            metrics = get_metrics_collector()
            name = gauge_name or f"{func.__name__}_in_progress"

            gauge = metrics.gauge(name, labels)
            gauge.inc()

            try:
                return await func(*args, **kwargs)
            finally:
                gauge.dec()

        return wrapper

    return decorator
