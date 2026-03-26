# 🚀 Quick Start Guide

Get your DevSecOps agent reviewing PRs in 5 minutes!

## Prerequisites

- Python 3.10+
- OpenAI API key: https://platform.openai.com/api-keys
- GitHub token: https://github.com/settings/tokens (needs: repo, issues write)
- ngrok: https://ngrok.com/download

## Setup (2 minutes)

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd devsecops-agent

# 2. Run setup script
# Windows:
.\scripts\setup-local-test.ps1

# Linux/Mac:
chmod +x scripts/setup-local-test.sh
./scripts/setup-local-test.sh

# 3. Edit .env with your keys
# OPENAI_API_KEY=sk-...
# GITHUB_TOKEN=ghp_...
# GITHUB_WEBHOOK_SECRET=my-secret-123
```

## Start Agent (1 minute)

**Terminal 1:**
```bash
python -m devsecops_agent.webhook.serve
```

**Terminal 2:**
```bash
ngrok http 8080
# Copy the HTTPS URL shown (e.g., https://abc123.ngrok.io)
```

## Configure GitHub (1 minute)

1. Go to your repo → **Settings** → **Webhooks** → **Add webhook**
2. Fill in:
   - **Payload URL**: `https://abc123.ngrok.io/webhook` (your ngrok URL)
   - **Content type**: `application/json`
   - **Secret**: `my-secret-123` (from your .env)
   - **Events**: Check "Pull requests"
3. Click **Add webhook**

## Test It! (1 minute)

```bash
# Create test PR with vulnerable code
git checkout -b test-security
cp examples/test-pr-samples/vulnerable-code.py test.py
git add test.py
git commit -m "Add test code"
git push origin test-security

# Create PR (or do it on GitHub)
gh pr create --title "Test security review" --body "Testing agent"
```

**🎉 Done!** Check your PR - the agent will comment with a security review!

## What You'll See

**In Terminal 1 (Agent):**
```
INFO: Webhook received event=pull_request action=opened
INFO: Review completed tokens=2500 cost=$0.0015
INFO: Posted comment on PR #123
```

**On GitHub PR:**
A detailed comment with:
- Summary of security issues
- Critical/High/Medium/Low findings
- Specific code locations
- Fix suggestions

## Common Commands

```bash
# Check health
curl http://localhost:8080/health

# View metrics
curl http://localhost:8080/metrics

# View logs (if using Docker)
docker-compose logs -f agent

# Stop everything
# Ctrl+C in both terminals
```

## Troubleshooting

**No comment on PR?**
1. Check agent logs for errors
2. Check GitHub webhook delivery (Settings → Webhooks → Recent Deliveries)
3. Verify GitHub token has correct permissions

**Agent won't start?**
1. Check .env has valid OPENAI_API_KEY
2. Run: `python -c "from devsecops_agent.settings import get_settings; get_settings()"`

**Webhook signature error?**
1. Verify secret matches in .env and GitHub webhook
2. Or set `WEBHOOK_ALLOW_UNSIGNED=true` in .env (testing only!)

## Next Steps

### Add Your Security Policies (Optional)

```bash
# 1. Create policies
mkdir policies
echo "# SQL Injection\nAlways use parameterized queries" > policies/sql.md

# 2. Index them
python -m devsecops_agent --ingest policies --reset

# 3. Enable RAG in .env
# WEBHOOK_USE_RAG=true

# 4. Restart agent
```

### Deploy to Production

```bash
# Using Docker Compose
make compose-up

# Or see full deployment guide
# docs/DEPLOYMENT.md
```

### Enable Monitoring

```bash
# Start with Prometheus + Grafana
docker-compose --profile monitoring up -d

# Access Grafana at http://localhost:3000
# Default: admin/admin
```

## Test Scenarios

### Test 1: Vulnerable Code (Will Find Issues)
```bash
cp examples/test-pr-samples/vulnerable-code.py api/auth.py
# Create PR → Agent finds 10+ security issues
```

### Test 2: Secure Code (Clean Review)
```bash
cp examples/test-pr-samples/secure-code.py api/auth.py
# Create PR → Agent says "No major security issues"
```

### Test 3: Dockerfile Security
```dockerfile
FROM ubuntu:latest
USER root
COPY . /app
# Create PR → Agent flags security issues
```

## Resources

- **Full Testing Guide**: [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Testing Flow**: [docs/TESTING_FLOW.md](docs/TESTING_FLOW.md)
- **Operations Guide**: [docs/OPERATIONS.md](docs/OPERATIONS.md)

## Support

- **Issues**: Open a GitHub issue
- **Logs**: Check agent terminal or `docker-compose logs agent`
- **Health**: `curl http://localhost:8080/health`
- **Metrics**: `curl http://localhost:8080/metrics`

---

**That's it!** You now have a working AI security agent reviewing your PRs! 🎉
