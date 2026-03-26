"""Map GitHub pull_request events to diff fetch + review + comment."""

from __future__ import annotations

from typing import Any

from devsecops_agent.services.review_service import run_security_review
from devsecops_agent.settings import get_settings
from devsecops_agent.utils.logging_config import get_logger
from devsecops_agent.webhook.github_client import (
    fetch_pr_diff,
    format_comment_body,
    post_issue_comment,
)

logger = get_logger(__name__)


def process_pull_request_event(payload: dict[str, Any]) -> None:
    """
    Synchronous pipeline: fetch diff → LLM review → GitHub issue comment.
    Intended to run inside FastAPI BackgroundTasks after returning 202.
    """
    settings = get_settings()
    
    action = payload.get("action")
    if action not in settings.get_pr_actions():
        logger.info("Skipping pull_request action", action=action)
        return

    pr = payload.get("pull_request") or {}
    repo = payload.get("repository") or {}
    number = pr.get("number")
    full_name = repo.get("full_name")  # owner/repo

    if not full_name or number is None:
        logger.warning("Missing repository.full_name or pull_request.number")
        return

    if not settings.github_token:
        logger.error("GITHUB_TOKEN not set; cannot fetch diff or comment")
        return

    owner, _, repo_name = full_name.partition("/")
    if not repo_name:
        logger.error("Bad full_name", full_name=full_name)
        return

    head = pr.get("head") or {}
    sha = head.get("sha")

    try:
        diff = fetch_pr_diff(owner, repo_name, int(number), settings.github_token)
    except Exception as e:
        logger.exception("Failed to fetch PR diff", error=str(e))
        return

    limit = settings.webhook_max_diff_chars
    truncated = False
    if len(diff) > limit:
        diff = diff[:limit] + "\n\n_(Diff truncated for review — WEBHOOK_MAX_DIFF_CHARS.)_"
        truncated = True

    language = settings.webhook_default_language
    extra = settings.webhook_review_context or ""
    if truncated:
        extra = (extra + "\n" if extra else "") + "Note: diff was truncated before analysis."

    try:
        report = run_security_review(
            diff,
            language=language,
            extra_context=extra or None,
            use_rag=settings.webhook_use_rag,
            rag_k=settings.webhook_rag_k,
            review_mode=settings.webhook_review_mode,
            prompt_style=settings.webhook_prompt_style,
        )
    except Exception as e:
        logger.exception("Security review failed", error=str(e))
        if settings.webhook_post_on_failure:
            report = f"**Review failed** (internal error). Check webhook logs.\n\n`{type(e).__name__}`"
        else:
            return

    body = format_comment_body(report, pr_number=int(number), sha=sha)

    try:
        post_issue_comment(owner, repo_name, int(number), body, settings.github_token)
        logger.info("Posted security review comment", repo=full_name, pr=number)
    except Exception as e:
        logger.exception("Failed to post comment", error=str(e))
