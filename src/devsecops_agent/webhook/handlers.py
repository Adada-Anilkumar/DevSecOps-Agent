"""Map GitHub pull_request events to diff fetch + review + comment/inline review."""

from __future__ import annotations

from typing import Any

from devsecops_agent.schemas import ReviewResult
from devsecops_agent.services.review_service import review_code
from devsecops_agent.settings import get_settings
from devsecops_agent.utils.logging_config import get_logger
from devsecops_agent.webhook.github_client import (
    fetch_pr_diff,
    format_comment_body,
    post_issue_comment,
    post_pr_review,
)

logger = get_logger(__name__)


def process_pull_request_event(payload: dict[str, Any]) -> None:
    """Synchronous pipeline: fetch diff → AI review → GitHub PR review / comment."""
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
        review_result = review_code(
            diff,
            is_diff=True,
            language=language,
            extra_context=extra or None,
            use_rag=settings.webhook_use_rag,
            rag_k=settings.webhook_rag_k,
            review_mode=settings.webhook_review_mode,
            prompt_style=settings.webhook_prompt_style,
            enable_prescan=True,
            output_format="structured",
        )
    except Exception as e:
        logger.exception("Security review failed", error=str(e))
        if settings.webhook_post_on_failure:
            err_body = format_comment_body(
                f"**Review failed** (internal error). Check webhook logs.\n\n`{type(e).__name__}`",
                pr_number=int(number),
                sha=sha,
            )
            post_issue_comment(owner, repo_name, int(number), err_body, settings.github_token)
        return

    # Post PR review with inline comments if sha is available and review is structured
    if isinstance(review_result, ReviewResult) and sha:
        try:
            post_pr_review(owner, repo_name, int(number), sha, review_result, settings.github_token)
            logger.info("Posted structured PR review with inline comments", repo=full_name, pr=number)
            return
        except Exception as e:
            logger.warning("Failed posting inline PR review, falling back to issue comment", error=str(e))

    # Fallback to issue comment
    report_text = review_result.to_markdown() if isinstance(review_result, ReviewResult) else str(review_result)
    body = format_comment_body(report_text, pr_number=int(number), sha=sha)

    try:
        post_issue_comment(owner, repo_name, int(number), body, settings.github_token)
        logger.info("Posted security review comment", repo=full_name, pr=number)
    except Exception as e:
        logger.exception("Failed to post comment", error=str(e))
