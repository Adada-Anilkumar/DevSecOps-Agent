# End-to-End Testing Flow

## Visual Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     LOCAL TESTING SETUP                         │
└─────────────────────────────────────────────────────────────────┘

Step 1: Setup Environment
┌──────────────┐
│ Run setup    │
│ script       │──→ Creates .env
└──────────────┘    Installs deps
                    Validates config

Step 2: Start Services
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Start Agent  │    │ Start ngrok  │    │ Copy ngrok   │
│ (Port 8080)  │───→│ Tunnel       │───→│ HTTPS URL    │
└──────────────┘    └──────────────┘    └──────────────┘

Step 3: Configure GitHub
┌──────────────┐    ┌──────────────┐
│ Add Webhook  │    │ Set Secret   │
│ in GitHub    │───→│ & Events     │
└──────────────┘    └──────────────┘

Step 4: Create Test PR
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Create       │    │ Add Vuln     │    │ Push &       │
│ Branch       │───→│ Code         │───→│ Create PR    │
└──────────────┘    └──────────────┘    └──────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     WEBHOOK PROCESSING                          │
└─────────────────────────────────────────────────────────────────┘

GitHub PR Event
      │
      ▼
┌─────────────────┐
│ GitHub sends    │
│ webhook POST    │
│ to ngrok URL    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ngrok forwards  │
│ to localhost    │
│ :8080/webhook   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Webhook Handler                      │
│                                                                 │
│  1. Verify HMAC signature                                       │
│  2. Validate payload size                                       │
│  3. Parse JSON                                                  │
│  4. Check event type (pull_request)                             │
│  5. Return 202 Accepted                                         │
│  6. Queue background task                                       │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Background Processing                        │
│                                                                 │
│  1. Extract PR info (owner, repo, number)                       │
│  2. Fetch PR diff via GitHub API                                │
│  3. Truncate if too large                                       │
│  4. Optional: Retrieve policy chunks (RAG)                      │
│  5. Build prompt with diff + context                            │
│  6. Call OpenAI API                                             │
│  7. Parse response                                              │
│  8. Format as markdown comment                                  │
│  9. Post comment via GitHub API                                 │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Comment appears │
│ on GitHub PR    │
└─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     MONITORING & METRICS                        │
└─────────────────────────────────────────────────────────────────┘

Throughout the process:

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Structured   │    │ Prometheus   │    │ Cost         │
│ Logs         │    │ Metrics      │    │ Tracking     │
└──────────────┘    └──────────────┘    └──────────────┘
      │                   │                    │
      ▼                   ▼                    ▼
┌─────────────────────────────────────────────────────┐
│  View in:                                           │
│  - Terminal logs                                    │
│  - /metrics endpoint                                │
│  - Grafana dashboard                                │
└─────────────────────────────────────────────────────┘
```

## Detailed Step-by-Step

### Phase 1: Initial Setup (One-time)

```bash
# 1. Clone repo
git clone <repo-url>
cd devsecops-agent

# 2. Run setup script
./scripts/setup-local-test.sh

# 3. Edit .env with your keys
nano .env
```

**What happens:**
- ✅ Dependencies installed
- ✅ Configuration validated
- ✅ Environment ready

### Phase 2: Start Services

**Terminal 1 - Agent:**
```bash
python -m devsecops_agent.webhook.serve
```

**Terminal 2 - ngrok:**
```bash
ngrok http 8080
```

**What happens:**
- ✅ Agent listening on port 8080
- ✅ ngrok creates public HTTPS URL
- ✅ Requests forwarded: Internet → ngrok → localhost

### Phase 3: GitHub Configuration

1. Copy ngrok URL: `https://abc123.ngrok.io`
2. Go to GitHub repo → Settings → Webhooks
3. Add webhook:
   - URL: `https://abc123.ngrok.io/webhook`
   - Secret: (from .env)
   - Events: Pull requests

**What happens:**
- ✅ GitHub knows where to send events
- ✅ Signature verification configured
- ✅ Only PR events will be sent

### Phase 4: Create Test PR

```bash
# Create branch
git checkout -b test-security-review

# Add vulnerable code
cp examples/test-pr-samples/vulnerable-code.py api/auth.py
git add api/auth.py
git commit -m "Add authentication module"
git push origin test-security-review

# Create PR
gh pr create --title "Add authentication" --body "Testing"
```

**What happens:**
- ✅ PR created on GitHub
- ✅ GitHub sends webhook to ngrok
- ✅ Agent receives and processes
- ✅ Comment posted automatically

### Phase 5: Watch It Work

**In Terminal 1 (Agent logs):**
```
INFO: Webhook received event=pull_request action=opened
INFO: Processing PR owner=myorg repo=myrepo number=123
INFO: Fetched diff: 1234 bytes
INFO: Starting review model=gpt-4o-mini
INFO: Review completed tokens=2500 cost=$0.0015
INFO: Posted comment on PR #123
```

**In ngrok Dashboard (http://localhost:4040):**
- See webhook POST request
- View request/response details
- Check timing and status codes

**On GitHub PR:**
- See automated comment with security review
- Multiple issues flagged with severity
- Specific fixes suggested

## Troubleshooting Flow

```
Issue: No comment on PR
│
├─→ Check 1: Agent logs
│   └─→ See errors? → Fix configuration
│
├─→ Check 2: GitHub webhook delivery
│   └─→ Failed? → Check ngrok URL
│
├─→ Check 3: GitHub token permissions
│   └─→ Missing? → Update token scopes
│
└─→ Check 4: OpenAI API
    └─→ Error? → Check API key & billing
```

## Success Indicators

✅ **Agent Started:**
```
INFO: Started server process
INFO: Uvicorn running on http://0.0.0.0:8080
```

✅ **ngrok Connected:**
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8080
```

✅ **Webhook Received:**
```
INFO: Webhook received event=pull_request action=opened
```

✅ **Review Completed:**
```
INFO: Review completed prompt_tokens=1234 completion_tokens=567
```

✅ **Comment Posted:**
```
INFO: Posted security review comment on org/repo#123
```

## Testing Checklist

- [ ] Setup script runs successfully
- [ ] Agent starts without errors
- [ ] ngrok tunnel established
- [ ] GitHub webhook configured
- [ ] Test PR created
- [ ] Webhook received by agent
- [ ] Review processed
- [ ] Comment appears on PR
- [ ] Metrics available at /metrics
- [ ] Logs show complete flow

## Next Steps After Successful Test

1. **Add Real Policies:**
   ```bash
   mkdir policies
   # Add your org's security policies
   python -m devsecops_agent --ingest policies --reset
   ```

2. **Enable RAG:**
   ```bash
   # In .env
   WEBHOOK_USE_RAG=true
   ```

3. **Deploy to Production:**
   - See `docs/DEPLOYMENT.md`
   - Use proper secrets management
   - Set up monitoring

4. **Customize Prompts:**
   - Edit `src/devsecops_agent/prompts.py`
   - Adjust severity thresholds
   - Add custom rules

## Common Test Scenarios

### Scenario 1: First Time Setup
- Follow all steps in order
- Verify each step before proceeding
- Check logs at each stage

### Scenario 2: Already Setup, Testing Changes
- Just restart agent
- ngrok URL stays the same (unless restarted)
- No need to reconfigure webhook

### Scenario 3: Testing with RAG
- Index policies first
- Enable RAG in .env
- Restart agent
- Create PR - review will reference policies

### Scenario 4: Testing Different Code
- Use examples in `examples/test-pr-samples/`
- Create multiple PRs to test different scenarios
- Compare vulnerable vs secure code reviews

## Support

**Still having issues?**

1. Check `docs/LOCAL_TESTING.md` for detailed guide
2. Review logs: `docker-compose logs agent`
3. Test health: `curl http://localhost:8080/health`
4. Check GitHub webhook deliveries
5. Open GitHub issue with logs
