import pytest
from devsecops_agent.schemas import Category, ReviewIssue, ReviewResult, SeverityLevel


def test_review_result_markdown_generation():
    issue = ReviewIssue(
        file_path="src/auth.py",
        line_number=42,
        category=Category.SECURITY,
        severity=SeverityLevel.CRITICAL,
        title="SQL Injection Vulnerability",
        description="User input directly concatenated into SQL query string.",
        suggested_fix="cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
        educational_note="Use parameterized queries to neutralize SQL injection (OWASP A03:2021).",
    )
    result = ReviewResult(
        summary="Found 1 critical security finding in auth module.",
        overall_severity=SeverityLevel.CRITICAL,
        recommended_action="REQUEST_CHANGES",
        positives=["Clean separation of concerns in router."],
        issues=[issue],
    )

    md = result.to_markdown()
    assert "SQL Injection Vulnerability" in md
    assert "src/auth.py:L42" in md
    assert "REQUEST_CHANGES" in md
    assert "parameterized queries" in md
    assert "Clean separation of concerns" in md


def test_review_result_sarif_export():
    issue = ReviewIssue(
        file_path="app.py",
        line_number=10,
        category=Category.SECURITY,
        severity=SeverityLevel.HIGH,
        title="Insecure HTTP Endpoint",
        description="Sensitive data passed over plain HTTP.",
        suggested_fix="https://api.internal.corp",
    )
    result = ReviewResult(
        summary="High risk configuration.",
        overall_severity=SeverityLevel.HIGH,
        issues=[issue],
    )

    sarif = result.to_sarif()
    assert sarif["version"] == "2.1.0"
    assert len(sarif["runs"]) == 1
    assert len(sarif["runs"][0]["results"]) == 1
    res = sarif["runs"][0]["results"][0]
    assert res["level"] == "error"
    assert res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "app.py"
