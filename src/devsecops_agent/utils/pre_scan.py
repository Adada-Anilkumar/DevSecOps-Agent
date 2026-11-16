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

SUSPICIOUS_ARTIFACT_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".wasm",
    ".asar", ".apk", ".ipa", ".jar", ".whl",
    ".bin", ".pyc", ".o", ".obj", ".class",
}


def detect_binary_artifacts(content: str) -> List[str]:
    """Detect binary or precompiled files referenced in diff or file list."""
    detected = set()
    lines = content.splitlines()

    for line in lines:
        line_clean = line.strip()
        if line_clean.startswith("diff --git "):
            parts = line_clean.split()
            if len(parts) >= 4:
                path = parts[3].lstrip("b/").strip()
                if any(path.lower().endswith(ext) for ext in SUSPICIOUS_ARTIFACT_EXTENSIONS):
                    detected.add(path)
        elif line_clean.startswith("+++ b/") or line_clean.startswith("--- a/"):
            path = line_clean[6:].strip()
            if any(path.lower().endswith(ext) for ext in SUSPICIOUS_ARTIFACT_EXTENSIONS):
                detected.add(path)
        elif "Binary files " in line_clean and " differ" in line_clean:
            parts = line_clean.split()
            for part in parts:
                cleaned_part = part.lstrip("b/").lstrip("a/")
                if any(cleaned_part.lower().endswith(ext) for ext in SUSPICIOUS_ARTIFACT_EXTENSIONS):
                    detected.add(cleaned_part)
        elif not any(line_clean.startswith(prefix) for prefix in ["diff ", "index ", "--- ", "+++ ", "@@ "]):
            if any(line_clean.lower().endswith(ext) for ext in SUSPICIOUS_ARTIFACT_EXTENSIONS) and " " not in line_clean:
                detected.add(line_clean)

    return sorted(list(detected))


def scan_for_secrets(
    content: str,
    default_filename: Optional[str] = None,
) -> List[ReviewIssue]:
    """Scan content line-by-line for high-confidence hardcoded secrets and committed binaries."""
    findings: List[ReviewIssue] = []

    # 1. Check for suspicious binary/precompiled artifacts
    binary_files = detect_binary_artifacts(content)
    for b_file in binary_files:
        findings.append(
            ReviewIssue(
                file_path=b_file,
                line_number=1,
                category=Category.SECURITY,
                severity=SeverityLevel.HIGH,
                title=f"Committed Binary / Compiled Asset: {b_file}",
                description=(
                    f"Committed precompiled binary '{b_file}' detected in changes. "
                    "Precompiled binaries introduce software supply chain blindspots, "
                    "bypass standard source code SAST, and violate SLSA provenance."
                ),
                suggested_fix="Remove compiled binaries from version control; build reproducible binaries during CI/CD or fetch from trusted package registries.",
                educational_note="Supply chain attacks (such as XZ Utils CVE-2024-3094) often leverage committed opaque blobs or pre-packaged binaries to slip past human reviewers.",
            )
        )
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
