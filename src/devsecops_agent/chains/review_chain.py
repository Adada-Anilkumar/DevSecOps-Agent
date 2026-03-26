"""
LangChain pipeline for DevSecOps PR review.

Flow (when --rag):
  1. RunnableLambda: retrieve_context(diff)  ->  policy text
  2. RunnablePassthrough: merge into user message
  3. ChatOpenAI (chat model): generate report

Embeddings appear only inside Chroma + OpenAIEmbeddings during retrieve;
the review text is always from the chat model, not from the embedding model.
"""

from __future__ import annotations

import time
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI

from devsecops_agent.prompts import build_user_message, get_system_prompt
from devsecops_agent.rag.retrieve import retrieve_context
from devsecops_agent.settings import get_settings
from devsecops_agent.utils.cost_tracker import get_cost_tracker
from devsecops_agent.utils.logging_config import get_logger
from devsecops_agent.utils.metrics import (
    review_duration_seconds,
    review_requests_total,
)

logger = get_logger(__name__)


def _augment_inputs(payload: dict[str, Any]) -> dict[str, Any]:
    diff_text = payload["diff_text"]
    review_mode = payload.get("review_mode", "comprehensive")
    prompt_style = payload.get("prompt_style", "compact")
    rag_text = retrieve_context(diff_text, k=int(payload.get("rag_k", 6)))
    base_user = build_user_message(
        diff_text,
        language=payload.get("language"),
        extra_context=payload.get("extra_context"),
        review_mode=review_mode,
        prompt_style=prompt_style,
    )
    if rag_text:
        user_content = (
            "Use the following retrieved internal policy/runbook excerpts when they "
            "apply. Do not treat them as facts about this PR—only the diff is authoritative "
            "for what changed. Cite policy only when it strengthens a finding.\n\n"
            "--- RETRIEVED CONTEXT ---\n"
            f"{rag_text}\n"
            "--- END RETRIEVED CONTEXT ---\n\n"
            f"{base_user}"
        )
    else:
        user_content = (
            base_user
            + "\n\n(No policy chunks retrieved; index may be empty. Review using diff only.)"
        )
    
    # Get appropriate system prompt for review mode and style
    system_prompt = get_system_prompt(review_mode, prompt_style)
    
    return {"system": system_prompt, "user": user_content}


def build_rag_review_chain(rag_k: int = 6):
    """LCEL chain: retrieve + augment + chat model -> Markdown report."""
    settings = get_settings()
    
    llm_kwargs: dict[str, Any] = {
        "model": settings.openai_model,
        "temperature": 0.2,
        "api_key": settings.openai_api_key,
        "timeout": settings.openai_timeout,
        "max_retries": 0,  # We handle retries elsewhere
    }
    if settings.openai_base_url:
        llm_kwargs["base_url"] = settings.openai_base_url
        
    llm = ChatOpenAI(**llm_kwargs)
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "{system}"),
            ("human", "{user}"),
        ]
    )
    return (
        RunnablePassthrough.assign(rag_k=lambda _: rag_k)
        | RunnableLambda(_augment_inputs)
        | prompt
        | llm
        | StrOutputParser()
    )


def run_rag_review(
    diff_text: str,
    *,
    language: str | None = None,
    extra_context: str | None = None,
    rag_k: int = 6,
    review_mode: str = "comprehensive",
    prompt_style: str = "compact",
) -> str:
    settings = get_settings()
    start_time = time.time()
    
    try:
        logger.info("Starting RAG review", model=settings.openai_model, rag_k=rag_k, review_mode=review_mode, prompt_style=prompt_style)
        
        chain = build_rag_review_chain(rag_k=rag_k)
        result = chain.invoke(
            {
                "diff_text": diff_text,
                "language": language,
                "extra_context": extra_context,
                "review_mode": review_mode,
                "prompt_style": prompt_style,
            }
        )
        
        # Track metrics
        duration = time.time() - start_time
        review_duration_seconds.labels(use_rag="true").observe(duration)
        review_requests_total.labels(status="success", use_rag="true").inc()
        
        logger.info("RAG review completed", duration_seconds=round(duration, 2))
        
        return result
        
    except Exception as e:
        logger.error("RAG review failed", error=str(e), exc_info=True)
        review_requests_total.labels(status="error", use_rag="true").inc()
        raise
