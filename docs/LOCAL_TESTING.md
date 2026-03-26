# Local End-to-End Testing Guide

This guide shows you how to test the complete PR review flow locally.

## Option 1: Using ngrok (Recommended for Quick Testing)

### Step 1: Install ngrok

```bash
# Download from https://ngrok.com/download
# Or using package manager:
# Windows: choco install ngrok
# Mac: brew install ngrok
# Linux: snap install ngrok
```

### Step 2: Setup Environment

```bash
# Copy and edit .env
cp .env.example .env

# Edit .env with your keys:
# OPENAI_API_KEY=sk-...
# GITHUB_TOKEN=ghp_...  (create at https://github.com/settings/tokens)
# GITHUB_WEBHOOK_SECRET=my-secret-123
```

**GitHub Token Permissions:**
- Repository access: The repo you want to test
- Permissions:
  - Pull requests: Read and write
  - Issues: Read and write (PR comments use Issues API)
  - Metadata: Read-only

### Step 3: Start the Agent

```bash
# Install dependencies
pip install -r requirements.txt
pip install -e .

# Start webhook server
python -m devsecops_agent.webhook.serve
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080
```

### Step 4: Expose with ngrok

In a new terminal:

```bash
ngrok http 8080
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8080
```

Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

### Step 5: Configure GitHub Webhook

1. Go to your GitHub repository
2. Settings → Webhooks → Add webhook
3. Configure:
   - **Payload URL**: `https://abc123.ngrok.io/webhook`
   - **Content type**: `application/json`
   - **Secret**: `my-secret-123` (same as in .env)
   - **Events**: Select "Pull requests"
   - **Active**: ✓ Checked

4. Click "Add webhook"

### Step 6: Test with a PR

```bash
# Create a test branch
git checkout -b test-security-review

# Make a change (example: add a potential SQL injection)
cat > test_file.py << 'EOF'
def login(username, password):
    # Vulnerable SQL query
    query = f"SELECT * FROM users WHERE username='{username}'"
    return execute_query(query)
EOF

git add test_file.py
git commit -m "Add login function"
git push origin test-security-review

# Create PR on GitHub
# Or use GitHub CLI:
gh pr create --title "Test security review" --body "Testing the agent"
```

### Step 7: Watch It Work!

1. Check your terminal running the agent - you'll see logs:
```
INFO: Webhook received event=pull_request action=opened
INFO: Starting direct review model=gpt-4o-mini
INFO: Review completed prompt_tokens=1234 completion_tokens=567
INFO: Posted security review comment on test-org/test-repo#1
```

2. Check the PR on GitHub - you'll see an automated comment with the security review!

3. Check ngrok dashboard at http://localhost:4040 to see webhook requests

## Option 2: Using Docker Compose

### Step 1: Setup

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your keys
nano .env
```

### Step 2: Start Services

```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f agent
```

### Step 3: Expose with ngrok

```bash
ngrok http 8080
```

### Step 4: Configure GitHub Webhook

Same as Option 1, Step 5

### Step 5: Test

Same as Option 1, Step 6

## Option 3: Using smee.io (No Installation Required)

### Step 1: Create smee.io Channel

1. Go to https://smee.io
2. Click "Start a new channel"
3. Copy the webhook proxy URL (e.g., `https://smee.io/abc123`)

### Step 2: Install smee-client

```bash
npm install -g smee-client

# Or use npx (no installation):
# npx smee-client --url https://smee.io/abc123 --target http://localhost:8080/webhook
```

### Step 3: Start Agent and Proxy

Terminal 1:
```bash
python -m devsecops_agent.webhook.serve
```

Terminal 2:
```bash
smee-client --url https://smee.io/abc123 --target http://localhost:8080/webhook
```

### Step 4: Configure GitHub Webhook

Use the smee.io URL as the webhook URL: `https://smee.io/abc123`

**Important**: Set `WEBHOOK_ALLOW_UNSIGNED=true` in .env since smee.io doesn't forward signatures properly.

### Step 5: Test

Create a PR and watch the magic happen!

## Testing with RAG (Policy-Aware Reviews)

### Step 1: Add Your Policies

```bash
# Create policy directory
mkdir -p policies

# Add a sample policy
cat > policies/security-standards.md << 'EOF'
# Security Standards

## SQL Injection Prevention
- Always use parameterized queries
- Never concatenate user input into SQL strings
- Use ORM frameworks when possible

## Authentication
- Implement multi-factor authentication
- Use bcrypt or Argon2 for password hashing
- Session tokens must expire after 24 hours
EOF
```

### Step 2: Index Policies

```bash
python -m devsecops_agent --ingest policies --reset
```

You should see:
```
Indexed 3 chunks into .devsecops/chroma
```

### Step 3: Enable RAG in Webhook

Edit `.env`:
```bash
WEBHOOK_USE_RAG=true
WEBHOOK_RAG_K=6
```

### Step 4: Restart Agent

```bash
# If using docker-compose
docker-compose restart agent

# If running directly
# Stop with Ctrl+C and restart:
python -m devsecops_agent.webhook.serve
```

### Step 5: Test

Create a new PR - the review will now reference your policies!

## Troubleshooting

### Webhook Not Receiving Events

**Check 1: Verify webhook delivery**
- GitHub → Settings → Webhooks → Recent Deliveries
- Look for green checkmark (success) or red X (failure)
- Click on delivery to see request/response

**Check 2: Check agent logs**
```bash
# Docker
docker-compose logs -f agent

# Direct
# Check terminal where agent is running
```

**Check 3: Test webhook manually**
```bash
# Test health endpoint
curl http://localhost:8080/health

# Test through ngrok
curl https://abc123.ngrok.io/health
```

### Agent Returns 401 (Invalid Signature)

**Solution 1**: Verify secret matches
```bash
# In .env
GITHUB_WEBHOOK_SECRET=my-secret-123

# In GitHub webhook settings
# Secret field must be: my-secret-123
```

**Solution 2**: For testing only, disable signature check
```bash
# In .env
WEBHOOK_ALLOW_UNSIGNED=true
```

### No Comment Posted on PR

**Check 1**: Verify GitHub token permissions
```bash
# Test token manually
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/user
```

**Check 2**: Check agent logs for errors
```bash
docker-compose logs agent | grep ERROR
```

**Check 3**: Verify token has correct permissions
- Go to https://github.com/settings/tokens
- Check your token has:
  - `repo` scope (for private repos)
  - Or `public_repo` scope (for public repos)

### OpenAI API Errors

**Check 1**: Verify API key
```bash
# Test key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

**Check 2**: Check rate limits
- OpenAI has rate limits based on your tier
- Check https://platform.openai.com/account/rate-limits

**Check 3**: Check billing
- Ensure you have credits: https://platform.openai.com/account/billing

## Example Test Cases

### Test 1: SQL Injection

```python
# test_sql.py
def get_user(username):
    query = f"SELECT * FROM users WHERE name='{username}'"
    return db.execute(query)
```

Expected: Critical issue flagged

### Test 2: Hardcoded Secret

```python
# test_secret.py
API_KEY = "sk-1234567890abcdef"
def call_api():
    return requests.get(url, headers={"Authorization": API_KEY})
```

Expected: Critical issue flagged

### Test 3: Missing Error Handling

```python
# test_error.py
def process_data(data):
    result = risky_operation(data)
    return result
```

Expected: Medium issue flagged

### Test 4: Dockerfile Security

```dockerfile
# Dockerfile
FROM ubuntu:latest
RUN apt-get update
COPY . /app
USER root
CMD ["/app/start.sh"]
```

Expected: Multiple issues (root user, latest tag, etc.)

## Monitoring Your Tests

### View Metrics

```bash
# Check metrics
curl http://localhost:8080/metrics | grep devsecops

# Key metrics to watch:
# - devsecops_review_requests_total
# - devsecops_review_duration_seconds
# - devsecops_tokens_used_total
# - devsecops_estimated_cost_usd_total
```

### View Logs

```bash
# Real-time logs
docker-compose logs -f agent

# Filter for errors
docker-compose logs agent | grep ERROR

# Filter for specific PR
docker-compose logs agent | grep "pr_number=123"
```

## Clean Up

### Stop Services

```bash
# Docker Compose
docker-compose down

# Remove volumes
docker-compose down -v

# Stop ngrok
# Press Ctrl+C in ngrok terminal
```

### Remove Test Data

```bash
# Remove Chroma index
rm -rf .devsecops/

# Remove test branch
git branch -D test-security-review
git push origin --delete test-security-review
```

## Next Steps

Once local testing works:

1. **Deploy to Production**: See [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Add Custom Policies**: Add your org's security policies to `policies/`
3. **Configure Monitoring**: Set up Prometheus + Grafana
4. **Enable Cost Tracking**: Monitor API usage and costs
5. **Scale Up**: Deploy multiple instances with Redis queue

## Quick Reference

```bash
# Start agent locally
python -m devsecops_agent.webhook.serve

# Start with Docker
docker-compose up -d

# Expose with ngrok
ngrok http 8080

# Index policies
python -m devsecops_agent --ingest policies --reset

# Test health
curl http://localhost:8080/health

# View metrics
curl http://localhost:8080/metrics

# View logs
docker-compose logs -f agent

# Stop everything
docker-compose down
```

## Support

- **Webhook not working?** Check GitHub webhook delivery status
- **No comment posted?** Verify GitHub token permissions
- **API errors?** Check OpenAI API key and billing
- **Need help?** Open a GitHub issue with logs
