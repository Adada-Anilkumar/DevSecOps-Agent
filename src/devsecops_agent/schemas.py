"""Structured schemas for DevSecOps Agent reviews and CI/CD integration."""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class Category(str, Enum):
    SECURITY = "SECURITY"
    CORRECTNESS = "CORRECTNESS"
    PERFORMANCE = "PERFORMANCE"
    MAINTAINABILITY = "MAINTAINABILITY"
    INFRASTRUCTURE = "INFRASTRUCTURE"


class ReviewIssue(BaseModel):
    """An individual finding identified in code review."""

    file_path: Optional[str] = Field(
        default=None,
        description="Path of the file containing the finding",
    )
    line_number: Optional[int] = Field(
        default=None,
        description="Relevant line number in the new code/diff",
    )
    category: Category = Field(
        default=Category.SECURITY,
        description="Classification of finding",
    )
    severity: SeverityLevel = Field(
        default=SeverityLevel.MEDIUM,
        description="Severity level of the issue",
    )
    title: str = Field(
        ...,
        description="Concise, descriptive title of the issue",
    )
    description: str = Field(
        ...,
        description="Detailed explanation of the issue, root cause, and potential security or reliability impact",
    )
    suggested_fix: str = Field(
        ...,
        description="Ready-to-apply code fix or concrete remediation instructions",
    )
    educational_note: Optional[str] = Field(
        default=None,
        description="Mentorship context explaining why this pattern is problematic and best practice references (e.g. OWASP, CWE)",
    )


class ReviewResult(BaseModel):
    """Full structured review result suitable for CI/CD gates, SARIF, and UI."""

    summary: str = Field(
        ...,
        description="High-level assessment summary covering security posture and code quality",
    )
    overall_severity: SeverityLevel = Field(
        default=SeverityLevel.INFO,
        description="Overall highest severity rating across all findings",
    )
    recommended_action: str = Field(
        default="COMMENT",
        description="Recommended PR action: APPROVE, COMMENT, or REQUEST_CHANGES",
    )
    positives: List[str] = Field(
        default_factory=list,
        description="Security strengths, clean patterns, and good practices observed",
    )
    issues: List[ReviewIssue] = Field(
        default_factory=list,
        description="List of detected issues and improvement opportunities",
    )

    def to_markdown(self) -> str:
        """Convert structured result into rich, developer-friendly Markdown."""
        lines = [
            "## 🛡️ DevSecOps Security & Quality Assessment",
            "",
            f"**Overall Status**: `{self.overall_severity.value}` | **Recommendation**: **{self.recommended_action}**",
            "",
            "### 📋 Executive Summary",
            self.summary.strip(),
            "",
        ]

        if self.positives:
            lines.append("### ✨ Strengths & Commendable Practices")
            for pos in self.positives:
                lines.append(f"- ✅ {pos}")
            lines.append("")

        if self.issues:
            lines.append("### ⚠️ Key Findings")
            severity_order = {
                SeverityLevel.CRITICAL: 0,
                SeverityLevel.HIGH: 1,
                SeverityLevel.MEDIUM: 2,
                SeverityLevel.LOW: 3,
                SeverityLevel.INFO: 4,
            }
            sorted_issues = sorted(
                self.issues,
                key=lambda x: severity_order.get(x.severity, 99),
            )

            severity_emojis = {
                SeverityLevel.CRITICAL: "🚨",
                SeverityLevel.HIGH: "🔴",
                SeverityLevel.MEDIUM: "🟡",
                SeverityLevel.LOW: "🔵",
                SeverityLevel.INFO: "ℹ️",
            }

            for idx, issue in enumerate(sorted_issues, start=1):
                emoji = severity_emojis.get(issue.severity, "⚠️")
                if issue.file_path and issue.line_number:
                    loc = f"`{issue.file_path}:L{issue.line_number}`"
                elif issue.file_path:
                    loc = f"`{issue.file_path}`"
                else:
                    loc = "General"

                lines.append(f"#### {emoji} {idx}. [{issue.severity.value}] {issue.title}")
                lines.append(f"**Location**: {loc} | **Category**: `{issue.category.value}`\n")
                lines.append(f"{issue.description.strip()}\n")

                if issue.suggested_fix:
                    lines.append("**Suggested Fix:**")
                    lines.append(f"```suggestion\n{issue.suggested_fix.strip()}\n```\n")

                if issue.educational_note:
                    lines.append(f"> 💡 **Why this matters (Mentorship)**: {issue.educational_note.strip()}\n")
        else:
            lines.append("🎉 **No critical vulnerabilities or quality issues identified! Great job!**\n")

        return "\n".join(lines)

    def to_sarif(self) -> Dict[str, Any]:
        """Export findings to SARIF 2.1.0 format for GitHub Code Scanning integration."""
        level_map = {
            SeverityLevel.CRITICAL: "error",
            SeverityLevel.HIGH: "error",
            SeverityLevel.MEDIUM: "warning",
            SeverityLevel.LOW: "note",
            SeverityLevel.INFO: "none",
        }

        results = []
        rules = []
        seen_rules = set()

        for idx, issue in enumerate(self.issues):
            rule_id = f"SEC-{issue.category.value}-{idx+1}"
            if rule_id not in seen_rules:
                seen_rules.add(rule_id)
                rules.append({
                    "id": rule_id,
                    "name": issue.title,
                    "shortDescription": {"text": issue.title},
                    "fullDescription": {"text": issue.description},
                    "defaultConfiguration": {"level": level_map.get(issue.severity, "warning")},
                })

            result_entry: Dict[str, Any] = {
                "ruleId": rule_id,
                "level": level_map.get(issue.severity, "warning"),
                "message": {"text": f"{issue.title}: {issue.description}"},
            }

            if issue.file_path:
                line = issue.line_number or 1
                result_entry["locations"] = [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": issue.file_path},
                            "region": {
                                "startLine": line,
                                "startColumn": 1,
                            },
                        }
                    }
                ]

            results.append(result_entry)

        return {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schematics/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "DevSecOps-Agent",
                            "informationUri": "https://github.com/Adada-Anilkumar/DevSecOps-Agent",
                            "rules": rules,
                        }
                    },
                    "results": results,
                }
            ],
        }
