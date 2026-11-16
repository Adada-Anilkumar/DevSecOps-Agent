"""Deterministic static pre-scanner to catch hardcoded secrets and obvious flaws before LLM."""

from __future__ import annotations

import re
from typing import List, Optional

from devsecops_agent.schemas import Category, ReviewIssue, SeverityLevel

SECRET_PATTERNS = [
    (
        "AWS Access Key ID",
        re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
        SeverityLevel.CRITICAL,
        "AWS Access Key ID detected. Committing credentials allows unauthorized access to AWS infrastructure.",
        "# Store credentials in AWS Secrets Manager or use IAM roles / environment variables.",
        "CWE-798: Use of Hard-coded Credentials. AWS keys committed to git are routinely scanned and exploited by botnets within seconds.",
    ),
    (
        "Private Key",
        re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"),
        SeverityLevel.CRITICAL,
        "Asymmetric private key header detected directly in source code.",
        "# Store private keys securely in a vault (e.g. HashiCorp Vault, Azure Key Vault, AWS KMS).",
        "CWE-312: Cleartext Storage of Sensitive Information. Compromise of private keys undermines cryptographic trust and authentication.",
    ),
    (
        "GitHub Personal Access Token",
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,255}"),
        SeverityLevel.CRITICAL,
        "GitHub authentication token detected in source.",
        "# Revoke the token immediately in GitHub settings and load via GITHUB_TOKEN environment secret.",
        "CWE-522: Insufficiently Protected Credentials. Attackers can leverage GitHub PATs to compromise repositories, CI workflows, and release artifacts.",
    ),
    (
        "Slack Bot/User Token",
        re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*"),
        SeverityLevel.HIGH,
        "Slack API token found in source code.",
        "# Use environment variables or Slack App configuration to supply tokens.",
        "CWE-798: Stored credentials can be used to read company internal communication or exfiltrate sensitive files.",
    ),
    (
        "Generic Hardcoded Secret / Password Assignment",
        re.compile(r"""(?i)(?:api[_-]?key|client[_-]?secret|db_password|password|secret_key)\s*=\s*['"][a-zA-Z0-9!@#$%^&*()_+\-={}:;<>?,./~]{8,}['"]"""),
        SeverityLevel.HIGH,
        "Hardcoded plaintext secret or password assignment detected.",
        "# Ingest password from secure environment variable: os.environ.get('SECRET_NAME')",
        "CWE-259: Use of Hard-coded Password. Plaintext secrets embedded in source code are easily leaked via logs, source control, or builds.",
    ),
]


def scan_for_secrets(
    content: str,
    default_filename: Optional[str] = None,
) -> List[ReviewIssue]:
    """Scan content line-by-line for high-confidence hardcoded secrets."""
    findings: List[ReviewIssue] = []
    lines = content.splitlines()

    is_unified_diff = (
        "diff --git " in content
        or "\n@@ " in content
        or content.startswith("@@ ")
    )

    current_file = default_filename

    for idx, raw_line in enumerate(lines, start=1):
        if is_unified_diff:
            # Handle diff file header markers
            if raw_line.startswith("+++ b/"):
                current_file = raw_line[6:].strip()
                continue
            elif raw_line.startswith("+++ "):
                current_file = raw_line[4:].strip()
                continue

            # In diff, only inspect added lines (+)
            if raw_line.startswith("+") and not raw_line.startswith("+++"):
                test_line = raw_line[1:].strip()
            else:
                continue
        else:
            test_line = raw_line.strip()

        for name, pattern, severity, desc, fix, mentor_note in SECRET_PATTERNS:
            if pattern.search(test_line):
                findings.append(
                    ReviewIssue(
                        file_path=current_file,
                        line_number=idx,
                        category=Category.SECURITY,
                        severity=severity,
                        title=f"Hardcoded Secret: {name}",
                        description=desc,
                        suggested_fix=fix,
                        educational_note=mentor_note,
                    )
                )

    return findings
