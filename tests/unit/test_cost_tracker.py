"""Test cost tracking functionality."""

from __future__ import annotations

from devsecops_agent.utils.cost_tracker import CostTracker


def test_estimate_tokens():
    """Test token estimation."""
    tracker = CostTracker()

    text = "Hello, world!"
    tokens = tracker.estimate_tokens(text, "gpt-4o-mini")

    assert tokens > 0
    assert isinstance(tokens, int)


def test_track_usage():
    """Test usage tracking."""
    tracker = CostTracker()

    cost = tracker.track_usage("gpt-4o-mini", prompt_tokens=1000, completion_tokens=500)

    assert cost > 0
    assert tracker.total_prompt_tokens == 1000
    assert tracker.total_completion_tokens == 500
    assert tracker.total_cost_usd > 0


def test_track_usage_multiple_calls():
    """Test cumulative tracking."""
    tracker = CostTracker()

    tracker.track_usage("gpt-4o-mini", 1000, 500)
    tracker.track_usage("gpt-4o-mini", 2000, 1000)

    assert tracker.total_prompt_tokens == 3000
    assert tracker.total_completion_tokens == 1500


def test_get_summary():
    """Test usage summary."""
    tracker = CostTracker()

    tracker.track_usage("gpt-4o-mini", 1000, 500)

    summary = tracker.get_summary()

    assert summary["total_prompt_tokens"] == 1000
    assert summary["total_completion_tokens"] == 500
    assert summary["total_tokens"] == 1500
    assert summary["total_cost_usd"] > 0


def test_different_models():
    """Test tracking for different models."""
    tracker = CostTracker()

    cost1 = tracker.track_usage("gpt-4o-mini", 1000, 500)
    cost2 = tracker.track_usage("gpt-4o", 1000, 500)

    # gpt-4o should be more expensive
    assert cost2 > cost1
