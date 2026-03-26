"""Token-optimized prompts for cost-efficient reviews with Gemini (FREE) or OpenAI."""

# Compact Comprehensive Review (50% fewer tokens)
SYSTEM_PROMPT_COMPACT = """You are a DevSecOps expert: Security Architect + Lead Reviewer + Penetration Tester + SRE.

## Rules
1. Flag ONLY issues in the diff. No invented vulnerabilities.
2. Cite exact file:line or code pattern.
3. Provide actionable fixes with code.
4. Justify severity with real impact.
5. Think like an attacker.

## Check For
**Security**: SQL injection, XSS, auth bypass, secrets, weak crypto, deserialization, CSRF, path traversal
**Code**: Error handling, resource leaks, race conditions, N+1 queries, complexity
**Infrastructure**: Container security, K8s hardening, IAM, IaC misconfig, CI/CD risks
**SRE**: Logging, monitoring, timeouts, circuit breakers

## Severity
- **Critical**: RCE, auth bypass, data breach, privilege escalation
- **High**: XSS, hardcoded secrets, weak crypto, admin exposure
- **Medium**: Missing rate limit, verbose errors, CSRF
- **Low**: Security headers, outdated deps, code quality

## Output Format

### Summary
Risk: Critical/High/Medium/Low | Findings: 2-3 sentences | Action: Approve/Request Changes/Block

### Critical Issues
**[CRITICAL] Title**
- Location: `file:line`
- Vuln: Description
- Attack: How to exploit
- Impact: Business consequence
- Fix:
```lang
secure code
```
- Test: Verification steps

### High/Medium/Low Issues
(Same structure, more concise for lower severity)

### Strengths
Good practices found

### Recommendations
1. Immediate: Fix before merge
2. Short-term: This sprint
3. Long-term: Architecture
4. Tools: Semgrep, Trivy, Snyk

### References
OWASP/CWE links if applicable
"""

# Ultra-Compact Security-Only (70% fewer tokens)
SECURITY_PROMPT_COMPACT = """Senior AppSec Engineer. Find ONLY security vulnerabilities.

## Scan For
SQL/NoSQL/Command/LDAP injection, XSS, auth bypass, session issues, IDOR, path traversal, privilege escalation, secrets, weak crypto, deserialization, XXE, SSRF, CSRF, rate limit bypass, verbose errors, outdated deps

## Attack Mindset
Can I: inject code? access other users' data? bypass auth? escalate privileges? DoS?

## Output
Same format as comprehensive but security issues only. Be concise.
"""

# Compact Architecture Review
ARCHITECTURE_PROMPT_COMPACT = """Principal Architect. Review code quality and design.

## Check
Architecture, SOLID principles, design patterns, complexity, duplication, error handling, resource management, concurrency, performance, testing, documentation

## Output
Focus on code quality and design, not security.
"""

# Compact Infrastructure Review
INFRASTRUCTURE_PROMPT_COMPACT = """Cloud Security Architect + SRE. Review infrastructure.

## Check
Container security, K8s (SecurityContext, NetworkPolicy, RBAC), Cloud IAM, IaC (Terraform/CF), CI/CD, network security, TLS, monitoring, compliance

## Output
Focus on infrastructure and ops security.
"""


def build_user_message_compact(
    diff_text: str,
    *,
    language: str | None = None,
    extra_context: str | None = None,
    review_mode: str = "comprehensive",
) -> str:
    """Build compact user message (50% fewer tokens).
    
    Args:
        diff_text: Git diff to review
        language: Programming language hint
        extra_context: Additional context
        review_mode: Review type
    """
    parts = ["# PR Review", ""]
    
    # Mode
    mode_map = {
        "comprehensive": "Full review: security + code + infra",
        "security": "Security vulnerabilities only",
        "architecture": "Code quality and design",
        "infrastructure": "Infrastructure and ops security",
    }
    parts.append(f"**Mode**: {mode_map.get(review_mode, mode_map['comprehensive'])}")
    
    # Language with specific checks
    if language:
        lang_checks = {
            "python": "Check: pickle, eval/exec, SQL injection, command injection, path traversal",
            "javascript": "Check: XSS, prototype pollution, eval, npm vulns, command injection",
            "typescript": "Check: any types, XSS, deps, command injection",
            "java": "Check: deserialization, XXE, SQL injection, SSRF",
            "go": "Check: SQL injection, command injection, races, goroutine leaks",
        }
        parts.append(f"**Lang**: {language}")
        for key, check in lang_checks.items():
            if key in language.lower():
                parts.append(f"**Focus**: {check}")
                break
    
    # Auto-detect file types
    detections = []
    if "Dockerfile" in diff_text or "FROM " in diff_text:
        detections.append("Dockerfile: base image, USER, secrets")
    if "kubernetes" in diff_text.lower() or "apiVersion:" in diff_text:
        detections.append("K8s: SecurityContext, NetworkPolicy, RBAC")
    if "terraform" in diff_text.lower():
        detections.append("Terraform: IAM, encryption, exposure")
    if ".github/workflows" in diff_text:
        detections.append("CI/CD: secrets, actions, permissions")
    
    if detections:
        parts.append(f"**Detected**: {'; '.join(detections)}")
    
    parts.append("")
    parts.append("## Diff")
    parts.append("```diff")
    parts.append(diff_text.strip())
    parts.append("```")
    
    if extra_context:
        parts.append("")
        parts.append(f"**Context**: {extra_context.strip()}")
    
    parts.append("")
    parts.append("**Provide**: Executive summary, issues (Critical→Low) with location/attack/impact/fix/test, strengths, recommendations, tools")
    
    return "\n".join(parts)


def get_system_prompt_compact(review_mode: str = "comprehensive") -> str:
    """Get compact system prompt (50% fewer tokens).
    
    Args:
        review_mode: Review type
        
    Returns:
        Compact system prompt
    """
    prompts = {
        "comprehensive": SYSTEM_PROMPT_COMPACT,
        "security": SECURITY_PROMPT_COMPACT,
        "architecture": ARCHITECTURE_PROMPT_COMPACT,
        "infrastructure": INFRASTRUCTURE_PROMPT_COMPACT,
    }
    return prompts.get(review_mode, SYSTEM_PROMPT_COMPACT)


# Token usage comparison (approximate)
# Original comprehensive: ~2500 tokens
# Compact comprehensive: ~1200 tokens (52% reduction)
# Original security: ~800 tokens
# Compact security: ~250 tokens (69% reduction)
# User message original: ~500 tokens
# User message compact: ~250 tokens (50% reduction)
#
# Total savings per review: ~1500-2000 tokens (50-60% reduction)
# With Gemini (FREE): No cost impact, but faster responses
# With OpenAI: Significant cost savings on high-volume usage
