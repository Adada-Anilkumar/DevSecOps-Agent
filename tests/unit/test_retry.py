"""Test retry logic."""

from __future__ import annotations

import pytest

from devsecops_agent.utils.retry import RetryError, retry_with_backoff


def test_retry_success_first_attempt():
    """Test successful execution on first attempt."""
    call_count = 0

    @retry_with_backoff(max_attempts=3)
    def successful_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = successful_func()

    assert result == "success"
    assert call_count == 1


def test_retry_success_after_failures():
    """Test successful execution after retries."""
    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("Temporary error")
        return "success"

    result = flaky_func()

    assert result == "success"
    assert call_count == 3


def test_retry_exhausted():
    """Test retry exhaustion."""

    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    def always_fails():
        raise ValueError("Permanent error")

    with pytest.raises(RetryError, match="Failed after 3 attempts"):
        always_fails()


def test_retry_specific_exceptions():
    """Test retry only on specific exceptions."""

    @retry_with_backoff(
        max_attempts=3, initial_delay=0.1, exceptions=(ValueError,)
    )
    def raises_type_error():
        raise TypeError("Wrong exception type")

    # Should not retry TypeError
    with pytest.raises(TypeError):
        raises_type_error()


def test_retry_backoff():
    """Test exponential backoff timing."""
    import time

    call_times = []

    @retry_with_backoff(
        max_attempts=3, initial_delay=0.1, exponential_base=2.0
    )
    def timed_func():
        call_times.append(time.time())
        raise ValueError("Error")

    with pytest.raises(RetryError):
        timed_func()

    # Check that delays increase
    assert len(call_times) == 3
    delay1 = call_times[1] - call_times[0]
    delay2 = call_times[2] - call_times[1]
    assert delay2 > delay1
