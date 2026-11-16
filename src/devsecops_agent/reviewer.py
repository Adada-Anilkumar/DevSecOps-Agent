from __future__ import annotations

from typing import Type, TypeVar
from pydantic import BaseModel

from devsecops_agent.llm_providers import get_llm_provider
from devsecops_agent.schemas import ReviewResult

T = TypeVar("T", bound=BaseModel)


def run_review(
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Direct review (no RAG): uses configured LLM provider (Gemini or OpenAI).
    """
    provider = get_llm_provider()
    return provider.generate(system_prompt, user_message)


def run_structured_review(
    system_prompt: str,
    user_message: str,
    schema: Type[T] = ReviewResult,
) -> T:
    """
    Structured review emitting validated Pydantic model for CI/CD gates, SARIF, and typed APIs.
    """
    provider = get_llm_provider()
    return provider.generate_structured(system_prompt, user_message, schema)
