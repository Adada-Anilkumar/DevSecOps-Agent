"""Track API costs and token usage."""

from __future__ import annotations

from typing import Literal

import tiktoken

from devsecops_agent.utils.logging_config import get_logger
from devsecops_agent.utils.metrics import estimated_cost_usd, tokens_used_total

logger = get_logger(__name__)

# Pricing per 1M tokens (as of 2024)
PRICING = {
    "gpt-4o": {"prompt": 2.50, "completion": 10.00},
    "gpt-4o-mini": {"prompt": 0.150, "completion": 0.600},
    "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
    "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
    "text-embedding-3-small": {"prompt": 0.020, "completion": 0.0},
    "text-embedding-3-large": {"prompt": 0.130, "completion": 0.0},
    "text-embedding-ada-002": {"prompt": 0.100, "completion": 0.0},
}


class CostTracker:
    """Track and estimate API costs."""

    def __init__(self) -> None:
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_cost_usd = 0.0

    def estimate_tokens(self, text: str, model: str = "gpt-4o-mini") -> int:
        """
        Estimate token count for text.

        Args:
            text: Input text
            model: Model name for tokenizer selection

        Returns:
            Estimated token count
        """
        try:
            # Try to get encoding for specific model
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base (used by gpt-4, gpt-3.5-turbo)
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))

    def track_usage(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int = 0,
    ) -> float:
        """
        Track token usage and calculate cost.

        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens

        Returns:
            Estimated cost in USD
        """
        # Update counters
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        # Get pricing (default to gpt-4o-mini if unknown)
        pricing = PRICING.get(model, PRICING["gpt-4o-mini"])

        # Calculate cost (pricing is per 1M tokens)
        prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
        total_cost = prompt_cost + completion_cost

        self.total_cost_usd += total_cost

        # Update metrics
        tokens_used_total.labels(model=model, type="prompt").inc(prompt_tokens)
        if completion_tokens > 0:
            tokens_used_total.labels(model=model, type="completion").inc(
                completion_tokens
            )
        estimated_cost_usd.labels(model=model).inc(total_cost)

        logger.info(
            "API usage tracked",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=round(total_cost, 6),
        )

        return total_cost

    def get_summary(self) -> dict[str, float | int]:
        """Get usage summary."""
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "total_cost_usd": round(self.total_cost_usd, 4),
        }


# Global cost tracker instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
