# Test PR Samples

Use these files to test your DevSecOps agent locally.

## Quick Test

### Option 1: Test Vulnerable Code (Will Find Issues)

```bash
# Create test branch
git checkout -b test-vulnerable-code

# Add vulnerable code
cp examples/test-pr-samples/vulnerable-code.py api/auth.py
git add api/auth.py
git commit -m "Add authentication module"
git push origin test-vulnerable-code

# Create PR
gh pr create --title "Add authentication" --body "Testing security review"
```

**Expected Result:** Agent will comment with multiple Critical and High severity issues:
- SQL Injection
- Hardcoded secrets
- Command injection
- Path traversal
- Weak cryptography
- Missing error handling
- Logging sensitive data
- Insecure deserialization
- Missing authentication
- Exposed debug endpoint

### Option 2: Test Secure Code (Clean Review)

```bash
# Create test branch
git checkout -b test-secure-code

# Add secure code
cp examples/test-pr-samples/secure-code.py api/auth.py
git add api/auth.py
git commit -m "Add secure authentication module"
git push origin test-secure-code

# Create PR
gh pr create --title "Add secure authentication" --body "Testing security review"
```

**Expected Result:** Agent will comment with "No major security issues detected"

### Option 3: Test Fix (Before/After)

```bash
# Create branch with vulnerable code
git checkout -b fix-security-issues
cp examples/test-pr-samples/vulnerable-code.py api/auth.py
git add api/auth.py
git commit -m "Add authentication (vulnerable)"
git push origin fix-security-issues

# Create PR - will get security issues flagged
gh pr create --title "Add authentication" --body "Initial implementation"

# Fix the issues
cp examples/test-pr-samples/secure-code.py api/auth.py
git add api/auth.py
git commit -m "Fix security vulnerabilities"
git push origin fix-security-issues

# PR will get updated review showing fixes
```

**Expected Result:** 
1. First review: Multiple security issues
2. Second review: Issues resolved, clean code

## Test Scenarios

### Scenario 1: SQL Injection

```python
# Bad
query = f"SELECT * FROM users WHERE id = {user_id}"

# Good
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

### Scenario 2: Hardcoded Secrets

```python
# Bad
API_KEY = "sk-1234567890"

# Good
API_KEY = os.environ.get("API_KEY")
```

### Scenario 3: Command Injection

```python
# Bad
os.system(f"ping {host}")

# Good
subprocess.run(["ping", host], check=True)
```

### Scenario 4: Dockerfile Security

```dockerfile
# Bad
FROM ubuntu:latest
USER root
COPY . /app

# Good
FROM ubuntu:22.04
USER appuser
COPY --chown=appuser:appuser src/ /app/src/
```

## Testing Tips

1. **Start Simple**: Test with one vulnerability at a time
2. **Check Logs**: Monitor agent logs to see processing
3. **Verify Metrics**: Check `/metrics` endpoint for stats
4. **Test RAG**: Add policies and enable RAG for policy-aware reviews
5. **Test Edge Cases**: Empty diffs, large diffs, binary files

## Monitoring Your Test

```bash
# Watch agent logs
docker-compose logs -f agent

# Check metrics
curl http://localhost:8080/metrics | grep devsecops

# View webhook deliveries
# GitHub → Settings → Webhooks → Recent Deliveries
```

## Cleanup

```bash
# Delete test branches
git branch -D test-vulnerable-code test-secure-code fix-security-issues
git push origin --delete test-vulnerable-code test-secure-code fix-security-issues

# Close test PRs on GitHub
```

## Next Steps

Once testing works:
1. Add your own security policies to `policies/`
2. Customize prompts in `src/devsecops_agent/prompts.py`
3. Deploy to production (see `docs/DEPLOYMENT.md`)
4. Set up monitoring and alerts
