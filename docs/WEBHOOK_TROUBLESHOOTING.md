# Webhook Troubleshooting Guide

## ✅ Issue Fixed: Logger Event Parameter

**Error**: `TypeError: BoundLogger.info() got multiple values for argument 'event'`

**Cause**: `structlog` reserves the `event` parameter for the log message itself.

**Fix**: Changed `event=` to `event_type=` in logging calls.

**Status**: ✅ Fixed in `src/devsecops_agent/webhook/app.py`

## 🚀 Testing Your Webhook

### Step 1: Start the Agent

```bash
python -m devsecops_agent.webhook.serve
```

**Expected output**:
```
INFO:     Started server process [844]
INFO:     Waiting for application startup.
2026-03-26T10:46:54.337552Z [info] Starting DevSecOps Agent version=0.3.0
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Step 2: Start ngrok (New Terminal)

```bash
ngrok http 8080
```

**Expected output**:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8080
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`)

### Step 3: Configure GitHub Webhook

1. Go to your repo → **Settings** → **Webhooks** → **Add webhook**
2. Fill in:
   - **Payload URL**: `https://abc123.ngrok.io/webhook`
   - **Content type**: `application/json`
   - **Secret**: (from your `.env` file - `GITHUB_WEBHOOK_SECRET`)
   - **Events**: Select "Pull requests"
   - **Active**: ✅
3. Click **Add webhook**

### Step 4: Create Test PR

```bash
# Create test branch
git checkout -b test-webhook

# Add test file
cp examples/test-pr-samples/vulnerable-code.py test.py
git add test.py
git commit -m "Test webhook"
git push origin test-webhook

# Create PR
gh pr create --title "Test webhook" --body "Testing DevSecOps agent"
```

### Step 5: Verify Success

**In agent terminal**, you should see:
```
2026-03-26T10:50:00.123456Z [info] Webhook received event_type=pull_request action=opened
2026-03-26T10:50:01.234567Z [info] Starting Gemini review model=gemini-2.5-flash
2026-03-26T10:50:15.345678Z [info] Review completed prompt_tokens=2500 completion_tokens=1200
2026-03-26T10:50:16.456789Z [info] Posted security review comment repo=owner/repo pr=123
```

**On GitHub PR**, you should see:
- 🤖 Comment from your agent with security review

**In GitHub webhook deliveries**:
- Go to Settings → Webhooks → Your webhook → Recent Deliveries
- Should see ✅ green checkmark with "200 OK"

## 🔍 Common Issues & Fixes

### Issue 1: "Webhook signature invalid"

**Error in logs**:
```
WARNING: Webhook signature invalid
```

**Cause**: Secret mismatch between `.env` and GitHub webhook

**Fix**:
1. Check `.env`: `GITHUB_WEBHOOK_SECRET=your-secret`
2. Check GitHub webhook secret matches exactly
3. Restart agent: `Ctrl+C` then `python -m devsecops_agent.webhook.serve`

### Issue 2: "GITHUB_TOKEN not set"

**Error in logs**:
```
ERROR: GITHUB_TOKEN not set; cannot fetch diff or comment
```

**Cause**: Missing GitHub token in `.env`

**Fix**:
1. Create GitHub token: https://github.com/settings/tokens
   - Scopes: `repo`, `write:discussion`
2. Add to `.env`: `GITHUB_TOKEN=ghp_your_token_here`
3. Restart agent

### Issue 3: "Failed to fetch PR diff"

**Error in logs**:
```
ERROR: Failed to fetch PR diff error=401 Unauthorized
```

**Cause**: Invalid or expired GitHub token

**Fix**:
1. Verify token: `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user`
2. If expired, create new token
3. Update `.env` and restart agent

### Issue 4: "No comment posted on PR"

**Symptoms**: Agent runs but no comment appears

**Possible causes**:
1. **Token lacks permissions**
   - Fix: Ensure token has `repo` and `write:discussion` scopes
2. **Review failed silently**
   - Fix: Check logs for errors
3. **WEBHOOK_POST_ON_FAILURE=false**
   - Fix: Set to `true` in `.env` to see error comments

### Issue 5: "Connection refused" from ngrok

**Error**: `Connection refused` when GitHub tries to deliver webhook

**Cause**: Agent not running or ngrok not forwarding

**Fix**:
1. Ensure agent is running: `python -m devsecops_agent.webhook.serve`
2. Ensure ngrok is running: `ngrok http 8080`
3. Update GitHub webhook URL with new ngrok URL (changes on restart)

### Issue 6: "Rate limit exceeded"

**Error in logs**:
```
ERROR: Rate limit exceeded
```

**Cause**: Too many requests from same IP

**Fix**:
1. Increase limit in `.env`: `RATE_LIMIT_PER_MINUTE=20`
2. Or disable for testing: `RATE_LIMIT_ENABLED=false`
3. Restart agent

### Issue 7: "Gemini API key invalid"

**Error in logs**:
```
ERROR: Gemini review failed error=Invalid API key
```

**Cause**: Invalid or missing Gemini API key

**Fix**:
1. Get key: https://aistudio.google.com/app/apikey
2. Add to `.env`: `GEMINI_API_KEY=AIza...`
3. Restart agent

### Issue 8: "Module not found" errors

**Error**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Cause**: Missing dependencies

**Fix**:
```bash
pip install -r requirements.txt
pip install -e .
```

## 🧪 Manual Testing

### Test Health Endpoint

```bash
curl http://localhost:8080/health
```

**Expected**:
```json
{"status":"ok","version":"0.3.0"}
```

### Test Metrics Endpoint

```bash
curl http://localhost:8080/metrics
```

**Expected**: Prometheus metrics output

### Test Webhook Manually (Without GitHub)

```bash
# Create test payload
cat > test-payload.json << 'EOF'
{
  "action": "opened",
  "pull_request": {
    "number": 123,
    "head": {"sha": "abc123"}
  },
  "repository": {
    "full_name": "owner/repo"
  }
}
EOF

# Send test webhook (without signature - for testing only)
curl -X POST http://localhost:8080/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: pull_request" \
  -d @test-payload.json
```

**Note**: This only works if `WEBHOOK_ALLOW_UNSIGNED=true` in `.env`

## 📊 Monitoring

### Check Logs

```bash
# Real-time logs
python -m devsecops_agent.webhook.serve

# Or with Docker
docker-compose logs -f agent
```

### Check Metrics

```bash
# Token usage
curl http://localhost:8080/metrics | grep tokens

# Review count
curl http://localhost:8080/metrics | grep review_requests_total

# Error count
curl http://localhost:8080/metrics | grep review_errors_total
```

### Check GitHub Webhook Deliveries

1. Go to repo → Settings → Webhooks
2. Click your webhook
3. Click "Recent Deliveries"
4. Check status codes:
   - ✅ 200 OK - Success
   - ❌ 500 - Server error (check agent logs)
   - ❌ 401 - Signature invalid
   - ❌ Connection refused - Agent not running

## 🎯 Verification Checklist

Before creating a PR, verify:

- [ ] Agent running: `python -m devsecops_agent.webhook.serve`
- [ ] ngrok running: `ngrok http 8080`
- [ ] Health check: `curl http://localhost:8080/health` returns OK
- [ ] `.env` has `GEMINI_API_KEY`
- [ ] `.env` has `GITHUB_TOKEN`
- [ ] `.env` has `GITHUB_WEBHOOK_SECRET`
- [ ] GitHub webhook configured with correct URL
- [ ] GitHub webhook secret matches `.env`
- [ ] GitHub webhook events include "Pull requests"
- [ ] GitHub webhook is Active (✅)

## 🚀 Quick Fix Commands

```bash
# Restart agent
Ctrl+C
python -m devsecops_agent.webhook.serve

# Restart ngrok (get new URL)
Ctrl+C
ngrok http 8080
# Update GitHub webhook with new URL

# Check configuration
python -c "from devsecops_agent.settings import get_settings; s = get_settings(); print(f'Provider: {s.llm_provider}, Model: {s.get_model_name()}')"

# Test imports
python -c "from devsecops_agent.webhook.app import app; print('✅ OK')"

# Verify dependencies
pip list | grep -E "fastapi|uvicorn|structlog|prometheus"
```

## 📞 Still Having Issues?

1. **Check logs** for specific error messages
2. **Verify configuration** in `.env`
3. **Test health endpoint**: `curl http://localhost:8080/health`
4. **Check GitHub webhook deliveries** for error details
5. **Try with `WEBHOOK_ALLOW_UNSIGNED=true`** to isolate signature issues
6. **Check ngrok URL** hasn't changed (restart ngrok = new URL)

---

**Your webhook should now work perfectly!** 🎉

If you see the agent posting comments on your PRs, everything is working correctly.
