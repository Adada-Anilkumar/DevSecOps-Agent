# Local Setup - Step by Step Guide

## ✅ What We've Done So Far

1. ✅ Verified Python 3.12.10 is installed
2. ✅ Checked all dependencies are installed
3. ✅ Created `.env` file with test configuration
4. ✅ Verified all imports work correctly
5. ✅ Confirmed example test files exist

## 🔑 Step 1: Get Your API Keys

### OpenAI API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy the key (starts with `sk-...`)
4. Save it somewhere safe

### GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Give it a name: "DevSecOps Agent"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `write:discussion` (Write access to discussions)
5. Click "Generate token"
6. Copy the token (starts with `ghp_...`)
7. Save it somewhere safe

## 📝 Step 2: Update .env File

Open `.env` file in your editor and update these lines:

```bash
# Replace with your actual OpenAI API key
OPENAI_API_KEY=sk-your-actual-key-here

# Replace with your actual GitHub token
GITHUB_TOKEN=ghp_your-actual-token-here

# Keep this as is for testing
GITHUB_WEBHOOK_SECRET=my-secret-123

# Keep this true for local testing
WEBHOOK_ALLOW_UNSIGNED=true
```

## 🚀 Step 3: Start the Agent

Open a terminal in the project directory and run:

```powershell
python -m devsecops_agent.webhook.serve
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

✅ **Agent is now running!** Keep this terminal open.

## 🌐 Step 4: Expose with ngrok

### Install ngrok (if not installed)

1. Download from https://ngrok.com/download
2. Extract and add to PATH
3. Sign up for free account at https://ngrok.com
4. Get your auth token from https://dashboard.ngrok.com/get-started/your-authtoken
5. Run: `ngrok config add-authtoken YOUR_TOKEN`

### Start ngrok

Open a **NEW terminal** and run:

```powershell
ngrok http 8080
```

You'll see output like:
```
Forwarding  https://abc123def456.ngrok.io -> http://localhost:8080
```

✅ **Copy the HTTPS URL** (e.g., `https://abc123def456.ngrok.io`)

Keep this terminal open too!

## 🔗 Step 5: Configure GitHub Webhook

1. Go to your GitHub repository
2. Click **Settings** → **Webhooks** → **Add webhook**

3. Fill in the form:
   - **Payload URL**: `https://abc123def456.ngrok.io/webhook` (your ngrok URL + /webhook)
   - **Content type**: `application/json`
   - **Secret**: `my-secret-123` (same as in .env)
   - **Which events**: Select "Let me select individual events"
     - ✅ Check "Pull requests"
     - ❌ Uncheck everything else
   - **Active**: ✅ Checked

4. Click **Add webhook**

You should see a green checkmark ✅ after a few seconds.

## 🧪 Step 6: Create a Test PR

### Option A: Using GitHub CLI (gh)

```powershell
# Create a test branch
git checkout -b test-security-review

# Add vulnerable code
Copy-Item examples\test-pr-samples\vulnerable-code.py test_security.py
git add test_security.py
git commit -m "Add authentication module for testing"
git push origin test-security-review

# Create PR
gh pr create --title "Test: Security Review" --body "Testing the DevSecOps agent"
```

### Option B: Manual Steps

1. Create a new branch:
   ```powershell
   git checkout -b test-security-review
   ```

2. Copy test file:
   ```powershell
   Copy-Item examples\test-pr-samples\vulnerable-code.py test_security.py
   ```

3. Commit and push:
   ```powershell
   git add test_security.py
   git commit -m "Add authentication module for testing"
   git push origin test-security-review
   ```

4. Go to GitHub and create a Pull Request from `test-security-review` to `main`

## 🎉 Step 7: Watch It Work!

### In Terminal 1 (Agent):

You should see logs like:
```
INFO: Webhook received event=pull_request action=opened
INFO: Processing PR owner=your-org repo=your-repo number=1
INFO: Starting direct review model=gpt-4o-mini
INFO: Review completed prompt_tokens=1234 completion_tokens=567
INFO: Posted security review comment on your-org/your-repo#1
```

### In Terminal 2 (ngrok):

You can open http://localhost:4040 to see the webhook requests in ngrok's dashboard.

### On GitHub:

Go to your PR and you should see an automated comment from the agent with:
- Summary of security issues
- Critical/High/Medium/Low findings
- Specific code locations
- Fix suggestions

## 🔍 What to Expect

The agent will find these issues in the vulnerable code:

1. **Critical**: SQL Injection vulnerability
2. **Critical**: Hardcoded API keys and secrets
3. **High**: Command injection vulnerability
4. **High**: Path traversal vulnerability
5. **High**: Weak cryptography (MD5)
6. **Medium**: Missing error handling
7. **Medium**: Logging sensitive data
8. **High**: Insecure deserialization
9. **Critical**: Missing authentication checks
10. **High**: Exposed debug endpoint

## 🛠️ Troubleshooting

### Agent won't start

**Error**: `OPENAI_API_KEY not set`
- **Fix**: Edit `.env` and add your real OpenAI API key

**Error**: Port 8080 already in use
- **Fix**: Change `PORT=8081` in `.env` and restart

### No webhook received

**Check 1**: Is ngrok running?
- Run `ngrok http 8080` in a separate terminal

**Check 2**: Is the webhook URL correct?
- GitHub webhook URL should be: `https://YOUR-NGROK-URL.ngrok.io/webhook`

**Check 3**: Check GitHub webhook deliveries
- Go to Settings → Webhooks → Recent Deliveries
- Look for green checkmark (success) or red X (failure)

### No comment posted

**Check 1**: Is GitHub token valid?
```powershell
curl -H "Authorization: Bearer YOUR_GITHUB_TOKEN" https://api.github.com/user
```

**Check 2**: Check agent logs for errors
- Look in Terminal 1 for any ERROR messages

**Check 3**: Verify token permissions
- Token needs `repo` and `write:discussion` scopes

### OpenAI API errors

**Error**: Rate limit exceeded
- **Fix**: Wait a few minutes or upgrade your OpenAI plan

**Error**: Invalid API key
- **Fix**: Check your API key at https://platform.openai.com/api-keys

**Error**: Insufficient credits
- **Fix**: Add credits at https://platform.openai.com/account/billing

## 📊 Monitoring Your Test

### Check Health

```powershell
curl http://localhost:8080/health
```

Should return: `{"status":"ok","version":"0.3.0"}`

### Check Metrics

```powershell
curl http://localhost:8080/metrics
```

Look for:
- `devsecops_review_requests_total`
- `devsecops_review_duration_seconds`
- `devsecops_tokens_used_total`

### View ngrok Dashboard

Open http://localhost:4040 in your browser to see:
- All webhook requests
- Request/response details
- Timing information

## 🧹 Clean Up

When you're done testing:

1. **Stop the agent**: Press `Ctrl+C` in Terminal 1
2. **Stop ngrok**: Press `Ctrl+C` in Terminal 2
3. **Delete test branch**:
   ```powershell
   git checkout main
   git branch -D test-security-review
   git push origin --delete test-security-review
   ```
4. **Close test PR** on GitHub

## 🎯 Next Steps

Once local testing works:

### 1. Test with Secure Code

```powershell
git checkout -b test-secure-code
Copy-Item examples\test-pr-samples\secure-code.py test_security.py
git add test_security.py
git commit -m "Fix security issues"
git push origin test-secure-code
gh pr create --title "Test: Secure Code" --body "Testing with fixed code"
```

Expected: Agent says "No major security issues detected"

### 2. Add Your Security Policies (RAG)

```powershell
# Create policies directory
New-Item -ItemType Directory -Path policies

# Add your policies
"# SQL Injection`nAlways use parameterized queries" | Out-File policies\sql.md

# Index them
python -m devsecops_agent --ingest policies --reset

# Enable RAG in .env
# WEBHOOK_USE_RAG=true

# Restart agent
```

### 3. Deploy to Production

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for:
- Docker deployment
- Kubernetes deployment
- Cloud providers (GCP, Azure, AWS)

### 4. Set Up Monitoring

```powershell
docker-compose --profile monitoring up -d
```

Access Grafana at http://localhost:3000 (admin/admin)

## 📖 Additional Resources

- **Full Testing Guide**: [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)
- **Visual Flow**: [docs/TESTING_FLOW.md](docs/TESTING_FLOW.md)
- **Deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Operations**: [docs/OPERATIONS.md](docs/OPERATIONS.md)

## ✅ Success Checklist

- [ ] Python 3.10+ installed
- [ ] All dependencies installed
- [ ] .env file configured with real API keys
- [ ] Agent starts without errors
- [ ] ngrok tunnel established
- [ ] GitHub webhook configured
- [ ] Test PR created
- [ ] Webhook received by agent
- [ ] Review processed successfully
- [ ] Comment appears on PR
- [ ] Metrics accessible at /metrics

## 🎉 You're Done!

If you see an automated comment on your PR, congratulations! Your DevSecOps agent is working! 🚀

**Questions?** Check [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md) or open a GitHub issue.
