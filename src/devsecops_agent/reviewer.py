from __future__ import annotations

from devsecops_agent.llm_providers import get_llm_provider


def run_review(
    system_prompt: str,
    user_message: str,
) -> str:
    """
    Direct review (no RAG): uses configured LLM provider (Gemini or OpenAI).
    """
    provider = get_llm_provider()
    return provider.generate(system_prompt, user_message)
