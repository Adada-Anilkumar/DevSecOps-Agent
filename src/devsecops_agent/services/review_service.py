"""Run security review (direct, structured, or RAG) — unified entry for CLI, API, & GitHub webhook."""

from __future__ import annotations

from typing import Optional, Union

from devsecops_agent.prompts import build_user_message, get_system_prompt
from devsecops_agent.reviewer import run_review, run_structured_review
from devsecops_agent.schemas import Category, ReviewIssue, ReviewResult, SeverityLevel
from devsecops_agent.utils.logging_config import get_logger
from devsecops_agent.utils.pre_scan import scan_for_secrets

logger = get_logger(__name__)


def review_code(
    content: str,
    *,
    is_diff: bool = True,
    language: Optional[str] = None,
    extra_context: Optional[str] = None,
    use_rag: bool = False,
    rag_k: int = 6,
    review_mode: str = "comprehensive",
    prompt_style: str = "compact",
    enable_prescan: bool = True,
    with_rea: bool = False,
    target_artifact: Optional[str] = None,
    output_format: str = "structured",  # "structured" | "markdown"
) -> Union[ReviewResult, str]:
    """Universal code and diff review entry point with deterministic pre-scan & structured output.

    Args:
        content: Unified git diff, single file content, or code snippet
        is_diff: True if content is a unified diff, False if source snippet/file
        language: Programming language / runtime hint
        extra_context: Additional architecture or deployment context
        use_rag: Whether to augment with RAG vector store policy
        rag_k: Top-K chunks to retrieve when RAG is active
        review_mode: comprehensive, security, architecture, infrastructure
        prompt_style: detailed, compact, or ultra
        enable_prescan: Run regex pre-scan for hardcoded secrets & critical keys
        with_rea: Enable morluto/rea reverse engineering for binary/packaged assets
        target_artifact: Direct path to binary/ASAR/bundle artifact to inspect
        output_format: "structured" (returns ReviewResult) or "markdown" (returns str)
    """
    prescan_issues: list[ReviewIssue] = []
    if enable_prescan:
        prescan_issues = scan_for_secrets(content)
        if prescan_issues:
            logger.info("Deterministic pre-scanner flagged issues", count=len(prescan_issues))

    # Optional morluto/rea reverse engineering inspection
    if with_rea or target_artifact:
        try:
            from devsecops_agent.analyzers.rea_bridge import REABridge
            from devsecops_agent.utils.pre_scan import detect_binary_artifacts

            bridge = REABridge()
            artifacts_to_scan = [target_artifact] if target_artifact else detect_binary_artifacts(content)

            for art_path in artifacts_to_scan:
                if art_path:
                    res = bridge.analyze_artifact(art_path)
                    rea_issues = bridge.convert_analysis_to_issues(art_path, res)
                    prescan_issues.extend(rea_issues)
        except Exception as e:
            logger.warning("Reverse engineering analysis error via REA bridge", error=str(e))

    # If RAG is requested, run via LCEL chain
    if use_rag:
        from devsecops_agent.chains.review_chain import run_rag_review
        report = run_rag_review(
            content,
            language=language,
            extra_context=extra_context,
            rag_k=rag_k,
            review_mode=review_mode,
            prompt_style=prompt_style,
        )
        if output_format == "structured":
            # Wrap RAG markdown result in ReviewResult structure
            highest_sev = SeverityLevel.CRITICAL if prescan_issues else SeverityLevel.INFO
            res = ReviewResult(
                summary="Policy-augmented security review completed.",
                overall_severity=highest_sev,
                recommended_action="REQUEST_CHANGES" if prescan_issues else "COMMENT",
                issues=prescan_issues,
            )
            return res
        return report

    # Build prompts
    system_prompt = get_system_prompt(review_mode, prompt_style)
    user_message = build_user_message(
        content,
        is_diff=is_diff,
        language=language,
        extra_context=extra_context,
        review_mode=review_mode,
        prompt_style=prompt_style,
    )

    if output_format == "structured":
        result = run_structured_review(system_prompt, user_message, schema=ReviewResult)
        # Merge deterministic pre-scan issues if any
        if prescan_issues:
            result.issues = prescan_issues + result.issues
            result.overall_severity = SeverityLevel.CRITICAL
            result.recommended_action = "REQUEST_CHANGES"
        return result

    # Standard Markdown flow
    markdown_report = run_review(system_prompt, user_message)
    if prescan_issues:
        prescan_summary = "\n".join([f"- 🚨 **CRITICAL**: {issue.title} - {issue.description}" for issue in prescan_issues])
        markdown_report = f"### 🛡️ Critical Pre-Scan Alerts\n{prescan_summary}\n\n---\n\n{markdown_report}"
    return markdown_report


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
    """Backwards-compatible wrapper returning markdown report."""
    result = review_code(
        diff_text,
        is_diff=True,
        language=language,
        extra_context=extra_context,
        use_rag=use_rag,
        rag_k=rag_k,
        review_mode=review_mode,
        prompt_style=prompt_style,
        enable_prescan=True,
        output_format="markdown",
    )
    return str(result)
