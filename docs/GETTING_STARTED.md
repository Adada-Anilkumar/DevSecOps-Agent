# Getting Started with DevSecOps Agent

Welcome! This guide will help you get started with the DevSecOps Agent.

## Choose Your Path

### 🚀 I Want to Test Locally (5 minutes)

**Best for:** First-time users, testing, development

**Follow:** [QUICKSTART.md](QUICKSTART.md)

**You'll need:**
- Python 3.10+
- OpenAI API key
- GitHub token
- ngrok (for local testing)

**Result:** Agent running locally, reviewing your test PRs

---

### 🐳 I Want to Deploy with Docker (10 minutes)

**Best for:** Quick production deployment, single server

**Follow:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#docker-on-vm)

**You'll need:**
- Docker & Docker Compose
- OpenAI API key
- GitHub token
- Public server or cloud VM

**Result:** Production-ready agent with monitoring

---

### ☸️ I Want to Deploy to Kubernetes (30 minutes)

**Best for:** Enterprise deployment, high availability

**Follow:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#kubernetes)

**You'll need:**
- Kubernetes cluster
- kubectl configured
- Container registry
- OpenAI API key
- GitHub token

**Result:** Scalable, highly available deployment

---

### ☁️ I Want to Deploy to Cloud (15 minutes)

**Best for:** Managed infrastructure, auto-scaling

**Options:**
- **Google Cloud Run:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#cloud-run-gcp)
- **Azure Container Apps:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md#azure-container-apps)
- **AWS ECS/Fargate:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

**Result:** Fully managed, auto-scaling deployment

---

## What You'll Build

```
┌─────────────┐
│   GitHub    │  PR created/updated
│     PR      │────────────────────┐
└─────────────┘                    │
                                   ▼
                          ┌─────────────────┐
                          │  DevSecOps      │
                          │  Agent          │
                          │  (Your Deploy)  │
                          └────────┬────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
              ┌──────────┐   ┌──────────┐  ┌──────────┐
              │ OpenAI   │   │ Vector   │  │ GitHub   │
              │ API      │   │ Store    │  │ API      │
              └──────────┘   └──────────┘  └──────────┘
                                                  │
                                                  ▼
                                          ┌─────────────┐
                                          │ Automated   │
                                          │ PR Comment  │
                                          └─────────────┘
```

## Key Concepts

### 1. Webhook Mode vs CLI Mode

**Webhook Mode** (Recommended for production)
- Automatic PR reviews
- GitHub integration
- Background processing
- Requires public endpoint

**CLI Mode** (Good for testing)
- Manual diff review
- No GitHub integration
- Immediate results
- Works offline

### 2. With RAG vs Without RAG

**Without RAG** (Simpler, faster)
- Uses only LLM knowledge
- No policy indexing needed
- Lower latency
- Good for general security

**With RAG** (Policy-aware)
- References your policies
- Requires policy indexing
- Slightly higher latency
- Better for org-specific rules

### 3. Local vs Production

**Local Testing**
- Use ngrok/smee.io
- Development mode
- Unsigned webhooks OK
- Single instance

**Production**
- Public HTTPS endpoint
- Signed webhooks
- Multiple instances
- Monitoring enabled

## Prerequisites Checklist

### Required

- [ ] Python 3.10 or higher
- [ ] OpenAI API key ([Get one](https://platform.openai.com/api-keys))
- [ ] GitHub account with repo access

### For Webhook Mode

- [ ] GitHub Personal Access Token ([Create](https://github.com/settings/tokens))
  - Scopes: `repo` (or `public_repo`), `write:discussion`
- [ ] Public endpoint (ngrok for testing, or production server)

### For Production

- [ ] Docker & Docker Compose (or Kubernetes)
- [ ] Domain name (optional but recommended)
- [ ] SSL certificate (or use Let's Encrypt)
- [ ] Monitoring setup (Prometheus/Grafana)

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/devsecops-agent.git
cd devsecops-agent
```

### 2. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your keys
nano .env  # or use your favorite editor
```

**Required variables:**
```bash
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=your-secret-here
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install
pip install -r requirements.txt
pip install -e .
```

### 4. Verify Installation

```bash
# Test configuration
python -c "from devsecops_agent.settings import get_settings; print('✅ Config OK')"

# Test health
python -m devsecops_agent.webhook.serve &
sleep 3
curl http://localhost:8080/health
# Should return: {"status":"ok"}
```

## First Test

### Option A: CLI Mode (Quickest)

```bash
# Create a test diff
echo "query = f'SELECT * FROM users WHERE id={user_id}'" > test.py
git add test.py
git diff --cached > test.diff

# Review it
python -m devsecops_agent --diff test.diff -l python

# You'll see a security review in your terminal!
```

### Option B: Webhook Mode (Full Experience)

Follow [QUICKSTART.md](QUICKSTART.md) for complete webhook setup.

## Common Issues

### "OPENAI_API_KEY not set"

**Solution:** Edit `.env` and add your OpenAI API key

### "GitHub token invalid"

**Solution:** 
1. Check token hasn't expired
2. Verify token has correct scopes
3. Test: `curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/user`

### "Webhook signature invalid"

**Solution:**
1. Verify secret matches in `.env` and GitHub webhook
2. For testing: Set `WEBHOOK_ALLOW_UNSIGNED=true` in `.env`

### "Port 8080 already in use"

**Solution:**
1. Change port in `.env`: `PORT=8081`
2. Or stop other service: `lsof -ti:8080 | xargs kill`

## Next Steps

### After First Successful Test

1. **Add Your Policies** (Optional)
   ```bash
   mkdir policies
   # Add your security policies as .md files
   python -m devsecops_agent --ingest policies --reset
   ```

2. **Enable RAG** (Optional)
   ```bash
   # In .env
   WEBHOOK_USE_RAG=true
   ```

3. **Deploy to Production**
   - See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

4. **Set Up Monitoring**
   ```bash
   docker-compose --profile monitoring up -d
   ```

5. **Customize Prompts**
   - Edit `src/devsecops_agent/prompts.py`

## Learning Resources

### Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup guide
- **[docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)** - Detailed testing guide
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - How it works
- **[docs/OPERATIONS.md](docs/OPERATIONS.md)** - Day-to-day operations

### Examples

- **[examples/test-pr-samples/](examples/test-pr-samples/)** - Test code samples
- **[examples/policies/](examples/policies/)** - Sample security policies

### Reference

- **[.env.example](.env.example)** - All configuration options
- **[Makefile](Makefile)** - Common commands
- **[IMPROVEMENTS.md](IMPROVEMENTS.md)** - What's been improved

## Getting Help

### Self-Service

1. **Check logs:**
   ```bash
   docker-compose logs agent
   ```

2. **Test health:**
   ```bash
   curl http://localhost:8080/health
   ```

3. **View metrics:**
   ```bash
   curl http://localhost:8080/metrics
   ```

4. **Check GitHub webhook deliveries:**
   - GitHub → Settings → Webhooks → Recent Deliveries

### Community Support

- **GitHub Issues:** Report bugs or ask questions
- **Documentation:** Check docs/ directory
- **Examples:** See examples/ directory

## Success Checklist

- [ ] Agent starts without errors
- [ ] Health check returns OK
- [ ] Test PR gets automated comment
- [ ] Metrics endpoint accessible
- [ ] Logs show successful processing
- [ ] Cost tracking working
- [ ] (Optional) RAG retrieval working
- [ ] (Optional) Monitoring dashboard accessible

## What's Next?

Once you have the basics working:

1. **Customize for your org:**
   - Add your security policies
   - Adjust severity thresholds
   - Customize output format

2. **Scale up:**
   - Deploy multiple instances
   - Add Redis queue
   - Set up load balancer

3. **Integrate:**
   - Add to CI/CD pipeline
   - Connect to Slack/Teams
   - Integrate with JIRA

4. **Monitor:**
   - Set up alerts
   - Track costs
   - Review metrics

---

**Ready to start?** → [QUICKSTART.md](QUICKSTART.md)

**Need help?** → Open a GitHub issue

**Want to contribute?** → See CONTRIBUTING.md
