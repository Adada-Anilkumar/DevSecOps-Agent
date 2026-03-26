"""GitHub REST: verify webhook, fetch PR diff, post issue comment."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

from devsecops_agent.settings import get_settings
from devsecops_agent.utils.logging_config import get_logger

logger = get_logger(__name__)

GITHUB_MAX_COMMENT = 65536


def github_api_base() -> str:
    settings = get_settings()
    return settings.github_api_url.rstrip("/")


def verify_webhook_signature(secret: str, raw_body: bytes, signature_header: str | None) -> bool:
    """Validate X-Hub-Signature-256 (sha256 HMAC of raw payload)."""
    if not signature_header or not secret:
        return False
    if not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    received = signature_header[len("sha256=") :].strip()
    return hmac.compare_digest(expected, received)


def _headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "devsecops-agent-webhook",
    }


def fetch_pr_diff(owner: str, repo: str, pull_number: int, token: str) -> str:
    """GET pull as unified diff (application/vnd.github.diff)."""
    url = f"{github_api_base()}/repos/{owner}/{repo}/pulls/{pull_number}"
    with httpx.Client(timeout=120.0) as client:
        r = client.get(
            url,
            headers={
                **_headers(token),
                "Accept": "application/vnd.github.diff",
            },
        )
    r.raise_for_status()
    return r.text


def post_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    token: str,
) -> dict[str, Any]:
    """POST /repos/{owner}/{repo}/issues/{n}/comments (PRs use issue id)."""
    if len(body) > GITHUB_MAX_COMMENT:
        tail = "\n\n_(Comment truncated to GitHub limit.)_"
        body = body[: GITHUB_MAX_COMMENT - len(tail)] + tail

    url = f"{github_api_base()}/repos/{owner}/{repo}/issues/{issue_number}/comments"
    with httpx.Client(timeout=60.0) as client:
        r = client.post(
            url,
            headers=_headers(token),
            json={"body": body},
        )
    if r.status_code >= 400:
        logger.error("GitHub comment API error", status=r.status_code, response=r.text[:500])
    r.raise_for_status()
    return r.json()


def format_comment_body(report: str, *, pr_number: int, sha: str | None = None) -> str:
    """Wrap report so it is identifiable as bot output."""
    meta = f"**DevSecOps security review** · PR #{pr_number}"
    if sha:
        meta += f" · `{sha[:7]}`"
    marker = "<!-- devsecops-agent -->"
    return f"{marker}\n\n{meta}\n\n---\n\n{report}"
