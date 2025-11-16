"""Circuit breaker pattern implementation."""

import asyncio
import time
import logging
from typing import Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before trying half-open
    expected_exception: type = Exception  # Exception type to track


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Circuit breaker for fault tolerance.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail fast
    - HALF_OPEN: Testing recovery, limited requests allowed

    Features:
    - Automatic failure detection
    - Fail-fast behavior
    - Automatic recovery attempts
    - Configurable thresholds
    """

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        """
        Initialize circuit breaker.

        Args:
            config: Circuit breaker configuration
        """
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.last_state_change = time.time()

        logger.info(
            f"Circuit breaker initialized (threshold={self.config.failure_threshold}, "
            f"timeout={self.config.timeout}s)"
        )

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time >= self.config.timeout:
                logger.info("Circuit breaker transitioning to HALF_OPEN (timeout reached)")
                self._transition_to_half_open()
            else:
                raise CircuitBreakerError(
                    f"Circuit breaker is OPEN (wait {self.config.timeout - (time.time() - self.last_failure_time):.1f}s)"
                )

        try:
            # Execute function
            result = await func(*args, **kwargs)

            # Success
            self._on_success()
            return result

        except self.config.expected_exception as e:
            # Expected failure
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.debug(
                f"Circuit breaker success in HALF_OPEN ({self.success_count}/{self.config.success_threshold})"
            )

            if self.success_count >= self.config.success_threshold:
                self._transition_to_closed()
        else:
            # Reset failure count on success
            self.failure_count = 0

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        logger.warning(
            f"Circuit breaker failure ({self.failure_count}/{self.config.failure_threshold}) "
            f"in state {self.state}"
        )

        if self.state == CircuitState.HALF_OPEN:
            # Failure in HALF_OPEN immediately reopens circuit
            self._transition_to_open()
        elif self.failure_count >= self.config.failure_threshold:
            self._transition_to_open()

    def _transition_to_open(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        self.last_state_change = time.time()
        logger.error(
            f"Circuit breaker OPENED (failures={self.failure_count}, "
            f"timeout={self.config.timeout}s)"
        )

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0
        self.last_state_change = time.time()
        logger.info("Circuit breaker entered HALF_OPEN state")

    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = time.time()
        logger.info("Circuit breaker CLOSED (recovered)")

    def reset(self):
        """Manually reset circuit breaker to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")

    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "time_in_state": time.time() - self.last_state_change,
        }


def circuit_breaker(
    failure_threshold: int = 5,
    success_threshold: int = 2,
    timeout: float = 60.0,
    expected_exception: type = Exception,
):
    """
    Decorator to apply circuit breaker pattern.

    Args:
        failure_threshold: Number of failures before opening circuit
        success_threshold: Number of successes to close from half-open
        timeout: Seconds before attempting recovery
        expected_exception: Exception type to track

    Example:
        @circuit_breaker(failure_threshold=3, timeout=30.0)
        async def unstable_api_call():
            ...
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        timeout=timeout,
        expected_exception=expected_exception,
    )
    breaker = CircuitBreaker(config)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        wrapper.circuit_breaker = breaker  # Expose breaker for inspection
        return wrapper

    return decorator
