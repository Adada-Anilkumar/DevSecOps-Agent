# Advanced Review Modes - Multi-Persona Analysis

Your DevSecOps Agent now thinks like a **complete security team** with specialized review modes!

## 🎭 Multi-Persona Architecture

The agent embodies 5 expert personas working together:

### 🔐 Security Architect
- OWASP Top 10 vulnerabilities
- Threat modeling and attack vectors
- Defense-in-depth strategies
- Cryptography and secrets management

### 👨‍💻 Lead Code Reviewer
- Clean code principles (SOLID, DRY)
- Design patterns and anti-patterns
- Performance optimization
- Error handling and resource management

### 🛡️ Application Security Tester
- Penetration testing mindset
- Exploitability analysis
- Business logic flaws
- Attack scenario simulation

### 🏗️ Infrastructure Architect
- Container and Kubernetes security
- Cloud IAM and network security
- IaC security (Terraform, CloudFormation)
- CI/CD pipeline security

### 📊 SRE Lead
- Observability and monitoring
- Reliability and scalability
- Incident response readiness
- Security metrics and alerting

## 🎯 Review Modes

### 1. Comprehensive Mode (Default)
**Best for**: Complete production-ready reviews

Analyzes ALL aspects:
- ✅ Security vulnerabilities
- ✅ Code quality and architecture
- ✅ Infrastructure security
- ✅ Performance and reliability
- ✅ Best practices

```bash
# .env
WEBHOOK_REVIEW_MODE=comprehensive
```

**Output includes**:
- Executive summary with risk level
- Critical/High/Medium/Low security issues
- Code quality issues
- Architecture recommendations
- Infrastructure security
- Tool suggestions (SAST/DAST)

### 2. Security-Focused Mode
**Best for**: Fast security-only scans

Focuses EXCLUSIVELY on vulnerabilities:
- ✅ OWASP Top 10
- ✅ Injection flaws
- ✅ Authentication/authorization
- ✅ Sensitive data exposure
- ✅ Attack vectors

```bash
# .env
WEBHOOK_REVIEW_MODE=security
```

**Ignores**: Code style, performance (unless security-related)

### 3. Architecture Mode
**Best for**: Code quality and design reviews

Focuses on:
- ✅ Design patterns
- ✅ SOLID principles
- ✅ Code complexity
- ✅ Maintainability
- ✅ Testing strategy

```bash
# .env
WEBHOOK_REVIEW_MODE=architecture
```

**Ignores**: Security vulnerabilities (unless they impact design)

### 4. Infrastructure Mode
**Best for**: DevOps and cloud security

Focuses on:
- ✅ Container security (Dockerfile, K8s)
- ✅ Cloud IAM and permissions
- ✅ IaC security (Terraform, etc.)
- ✅ CI/CD pipeline security
- ✅ Network and TLS configuration

```bash
# .env
WEBHOOK_REVIEW_MODE=infrastructure
```

**Ignores**: Application code (focuses on infrastructure)

## 🚀 Enhanced Features

### 1. Language-Specific Analysis

The agent automatically detects your language and applies specific checks:

**Python**:
- Pickle deserialization vulnerabilities
- eval/exec usage
- SQL injection (SQLAlchemy, raw queries)
- Command injection (subprocess, os.system)

**JavaScript/TypeScript**:
- XSS vulnerabilities
- Prototype pollution
- npm dependency vulnerabilities
- Command injection (child_process)

**Java**:
- Deserialization vulnerabilities
- XXE attacks
- SQL injection (JDBC)
- SSRF vulnerabilities

**Go**:
- SQL injection
- Race conditions
- Goroutine leaks
- Command injection

### 2. Automatic File Type Detection

Detects and applies specialized checks:

**Dockerfile**:
- Base image security
- USER directive (non-root)
- Secrets in layers
- Minimal attack surface

**Kubernetes**:
- SecurityContext settings
- NetworkPolicies
- RBAC configuration
- Resource limits

**Terraform/IaC**:
- IAM permissions (least privilege)
- Encryption at rest/transit
- Public exposure risks
- Secrets management

**CI/CD Pipelines**:
- Secrets handling
- Third-party action security
- Pipeline permissions
- Artifact integrity

### 3. Attack-Minded Analysis

For every security issue, the agent provides:

**Attack Scenario**: How would an attacker exploit this?
```
An attacker could inject SQL: ' OR '1'='1
This bypasses authentication and grants admin access.
```

**Business Impact**: What's the real-world damage?
```
- Data breach: All user records exposed
- Compliance violation: GDPR fine up to €20M
- Reputation damage: Customer trust lost
```

**Exploitability**: How easy is it to exploit?
```
Critical: Exploitable via public API with no authentication
High: Requires authenticated user account
Medium: Requires specific conditions or timing
Low: Requires insider access or complex setup
```

### 4. Actionable Fixes

Every issue includes copy-paste ready code:

**Before** (Vulnerable):
```python
query = f"SELECT * FROM users WHERE id={user_id}"
cursor.execute(query)
```

**After** (Secure):
```python
query = "SELECT * FROM users WHERE id=?"
cursor.execute(query, (user_id,))
```

**Verification**:
```bash
# Test with malicious input
user_id = "1 OR 1=1"
# Should fail safely, not return all users
```

## 📊 Output Format

### Executive Summary
```markdown
🎯 Executive Summary
- Risk Level: High
- Key Findings: SQL injection in auth.py, hardcoded API key in config.py
- Recommendation: Block Merge - Critical issues must be fixed
```

### Detailed Issues
```markdown
🚨 Critical Issues

[CRITICAL] SQL Injection in User Authentication
- Location: `src/auth.py:45`
- Vulnerability: Unsanitized user input in SQL query
- Attack Scenario: Attacker sends `' OR '1'='1` to bypass login
- Business Impact: Complete database access, data breach, GDPR violation
- Fix:
  ```python
  # Use parameterized queries
  cursor.execute("SELECT * FROM users WHERE username=?", (username,))
  ```
- Verification: Test with `username = "' OR '1'='1"`
```

### Security Strengths
```markdown
✅ Security Strengths
- Proper use of bcrypt for password hashing
- JWT tokens with expiration
- Rate limiting on API endpoints
```

### Recommendations
```markdown
🔧 Recommendations

Immediate Actions (Before Merge):
1. Fix SQL injection in auth.py
2. Remove hardcoded API key from config.py

Short-term (This Sprint):
3. Add input validation middleware
4. Implement CSRF protection

Long-term (Next Quarter):
5. Migrate to ORM (SQLAlchemy)
6. Add security headers middleware

Tooling:
- Run Semgrep for SAST: `semgrep --config=auto .`
- Scan dependencies: `pip-audit`
- Container scan: `trivy image myapp:latest`
```

## 🎓 Usage Examples

### Example 1: Comprehensive Review (Default)
```bash
# Review everything
git diff main...feature | python -m devsecops_agent --diff -
```

**Result**: Security + Code Quality + Architecture + Infrastructure

### Example 2: Security-Only Quick Scan
```bash
# .env
WEBHOOK_REVIEW_MODE=security

# Fast security scan before merge
git diff main...feature | python -m devsecops_agent --diff -
```

**Result**: Only security vulnerabilities, faster review

### Example 3: Architecture Review for Refactoring
```bash
# .env
WEBHOOK_REVIEW_MODE=architecture

# Review code quality during refactoring
git diff main...refactor | python -m devsecops_agent --diff -
```

**Result**: Design patterns, SOLID principles, code quality

### Example 4: Infrastructure Review for DevOps
```bash
# .env
WEBHOOK_REVIEW_MODE=infrastructure

# Review Dockerfile and K8s changes
git diff main...devops | python -m devsecops_agent --diff -
```

**Result**: Container security, K8s hardening, cloud IAM

## 🔧 Configuration

### In .env File
```bash
# Choose review mode
WEBHOOK_REVIEW_MODE=comprehensive  # or security, architecture, infrastructure

# Add language hint for better analysis
WEBHOOK_DEFAULT_LANGUAGE=Python 3.11

# Add context for domain-specific checks
WEBHOOK_REVIEW_CONTEXT=Production banking app; PCI-DSS compliance required; handles credit card data
```

### In CLI
```bash
# Comprehensive review with context
python -m devsecops_agent \
  --diff changes.diff \
  --language "Python 3.11" \
  --context "Production API; handles PII"
```

## 🎯 Best Practices

### 1. Use Appropriate Mode for Context

**Pre-merge security gate**: Use `security` mode
```bash
WEBHOOK_REVIEW_MODE=security
```

**Code review**: Use `comprehensive` mode
```bash
WEBHOOK_REVIEW_MODE=comprehensive
```

**Infrastructure changes**: Use `infrastructure` mode
```bash
WEBHOOK_REVIEW_MODE=infrastructure
```

### 2. Provide Context

**Good**:
```bash
WEBHOOK_REVIEW_CONTEXT=Production payment service; PCI-DSS Level 1; handles credit cards; 10M+ transactions/day
```

**Bad**:
```bash
WEBHOOK_REVIEW_CONTEXT=Payment service
```

### 3. Specify Language

**Good**:
```bash
WEBHOOK_DEFAULT_LANGUAGE=Python 3.11 with Django 4.2
```

**Bad**:
```bash
WEBHOOK_DEFAULT_LANGUAGE=Python
```

### 4. Combine with RAG for Policy Enforcement

```bash
# Index your security policies
python -m devsecops_agent --ingest policies/ --reset

# Enable RAG in reviews
WEBHOOK_USE_RAG=true
WEBHOOK_REVIEW_MODE=comprehensive
```

**Result**: Agent references YOUR policies in reviews!

## 📈 Performance Comparison

| Mode | Speed | Depth | Use Case |
|------|-------|-------|----------|
| **Security** | ⚡⚡⚡ Fast | 🔍 Focused | Pre-merge gate |
| **Architecture** | ⚡⚡ Medium | 🔍🔍 Detailed | Code review |
| **Infrastructure** | ⚡⚡ Medium | 🔍🔍 Detailed | DevOps changes |
| **Comprehensive** | ⚡ Slower | 🔍🔍🔍 Complete | Production review |

## 🎓 Training the Agent

### Add Custom Policies (RAG)

```bash
# Create policy directory
mkdir policies

# Add your security standards
cat > policies/sql-injection.md << 'EOF'
# SQL Injection Prevention

## Standard
ALL database queries MUST use parameterized queries or ORM.

## Examples
✅ Good: cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
❌ Bad: cursor.execute(f"SELECT * FROM users WHERE id={user_id}")

## Severity
SQL injection is ALWAYS Critical severity.
EOF

# Index policies
python -m devsecops_agent --ingest policies --reset

# Enable in reviews
WEBHOOK_USE_RAG=true
```

**Result**: Agent will cite YOUR policies in reviews!

## 🚀 Advanced Tips

### 1. Different Modes for Different Repos

**Frontend repo** (JavaScript/React):
```bash
WEBHOOK_REVIEW_MODE=security
WEBHOOK_DEFAULT_LANGUAGE=TypeScript
WEBHOOK_REVIEW_CONTEXT=Public-facing SPA; XSS and CSRF critical
```

**Backend API** (Python/Django):
```bash
WEBHOOK_REVIEW_MODE=comprehensive
WEBHOOK_DEFAULT_LANGUAGE=Python 3.11
WEBHOOK_REVIEW_CONTEXT=REST API; handles PII; GDPR compliance required
```

**Infrastructure repo** (Terraform):
```bash
WEBHOOK_REVIEW_MODE=infrastructure
WEBHOOK_REVIEW_CONTEXT=AWS production; multi-region; PCI-DSS Level 1
```

### 2. Severity Tuning

The agent automatically adjusts severity based on context:

**With context** "Production banking app; PCI-DSS":
- Missing rate limiting: **High** (DoS risk in banking)

**Without context**:
- Missing rate limiting: **Medium** (general best practice)

### 3. Integration with CI/CD

```yaml
# .github/workflows/security.yml
name: Security Review

on: [pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Security-focused review
        env:
          WEBHOOK_REVIEW_MODE: security
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          git diff origin/main...HEAD > changes.diff
          python -m devsecops_agent --diff changes.diff
```

## 📚 References

- **OWASP Top 10**: https://owasp.org/www-project-top-ten/
- **CWE Top 25**: https://cwe.mitre.org/top25/
- **NIST Cybersecurity Framework**: https://www.nist.gov/cyberframework
- **Cloud Security Alliance**: https://cloudsecurityalliance.org/

## 🎉 Summary

Your agent now provides:

✅ **Multi-persona analysis** - 5 expert perspectives  
✅ **Specialized review modes** - Choose your focus  
✅ **Language-specific checks** - Tailored to your stack  
✅ **Auto file detection** - Smart context awareness  
✅ **Attack scenarios** - Real-world exploitation  
✅ **Actionable fixes** - Copy-paste ready code  
✅ **Business impact** - Understand the risk  
✅ **Tool suggestions** - Automate with SAST/DAST  

**Result**: Production-grade security reviews that think like your entire security team!
