"""Run security review (direct or RAG) — single entry for CLI + GitHub webhook."""

from __future__ import annotations

from devsecops_agent.chains.review_chain import run_rag_review
from devsecops_agent.prompts import build_user_message, get_system_prompt
from devsecops_agent.reviewer import run_review


def run_security_review(
    diff_text: str,
    *,
    language: str | None = None,
    extra_context: str | None = None,
    use_rag: bool = False,
    rag_k: int = 6,
    review_mode: str = "comprehensive",
    prompt_style: str = "compact",
) -> str:
    """Run security review with enhanced multi-persona analysis.
    
    Args:
        diff_text: Git diff to review
        language: Programming language hint
        extra_context: Additional context
        use_rag: Enable RAG for policy-aware reviews
        rag_k: Number of policy chunks to retrieve
        review_mode: Review mode (comprehensive, security, architecture, infrastructure)
        prompt_style: Prompt style (detailed or compact for token efficiency)
        
    Returns:
        Markdown-formatted review report
    """
    if use_rag:
        return run_rag_review(
            diff_text,
            language=language,
            extra_context=extra_context,
            rag_k=rag_k,
            review_mode=review_mode,
            prompt_style=prompt_style,
        )
    
    # Get appropriate system prompt for review mode and style
    system_prompt = get_system_prompt(review_mode, prompt_style)
    
    # Build enhanced user message with context enrichment
    user_message = build_user_message(
        diff_text,
        language=language,
        extra_context=extra_context,
        review_mode=review_mode,
        prompt_style=prompt_style,
    )
    
    return run_review(system_prompt, user_message)
