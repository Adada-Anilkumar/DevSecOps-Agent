"""Retry utilities with exponential backoff."""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

from devsecops_agent.utils.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    pass


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        exceptions: Tuple of exceptions to catch and retry
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = initial_delay
            last_exception: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.error(
                            "All retry attempts exhausted",
                            function=func.__name__,
                            exc_info=True,
                        )
                        raise RetryError(
                            f"Failed after {max_attempts} attempts: {e}"
                        ) from e

                    logger.warning(
                        "Retry attempt failed",
                        attempt=attempt,
                        max_attempts=max_attempts,
                        function=func.__name__,
                        error=str(e),
                        retry_delay=round(delay, 2),
                    )
                    time.sleep(delay)
                    delay = min(delay * exponential_base, max_delay)

            # Should never reach here, but for type safety
            if last_exception:
                raise last_exception
            raise RetryError("Unexpected retry state")

        return wrapper

    return decorator
