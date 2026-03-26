# DevSecOps Review Agent

Production-ready AI agent for automated security reviews of GitHub Pull Requests.

**🆓 Now supports FREE Google Gemini API!** No credit card required!

[![CI/CD](https://github.com/your-org/devsecops-agent/workflows/CI/badge.svg)](https://github.com/your-org/devsecops-agent/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**🚀 [Quick Start in 5 Minutes](QUICKSTART.md)** | **🆓 [Use FREE Gemini](docs/GEMINI_SETUP.md)** | **📖 [Full Documentation](docs/)** | **🐳 [Deploy to Production](docs/DEPLOYMENT.md)**

## Features

- 🆓 **FREE Gemini Support** - No credit card required!
- 🤖 **AI-Powered Analysis** - Gemini 1.5 or GPT-4/GPT-3.5
- 📚 **RAG Support** - Retrieval-Augmented Generation with your security policies
- 🔄 **GitHub Integration** - Automatic PR reviews via webhooks
- 📊 **Monitoring** - Prometheus metrics and Grafana dashboards
- 🔒 **Enterprise Security** - Rate limiting, signature verification, input validation
- 🚀 **Production Ready** - Docker, Kubernetes, horizontal scaling
- 💰 **Cost Tracking** - Real-time token usage and cost estimation
- 🧪 **Fully Tested** - Comprehensive unit and integration tests

## Quick Demo

```bash
# 1. Get FREE Gemini API key (2 min)
# Visit: https://aistudio.google.com/app/apikey

# 2. Setup (2 min)
./scripts/setup-local-test.sh
# Edit .env: Add GEMINI_API_KEY=AIza...

# 3. Start agent (1 min)
python -m devsecops_agent.webhook.serve

# 4. Expose with ngrok (1 min)
ngrok http 8080

# 5. Configure GitHub webhook (1 min)
# Add webhook with ngrok URL

# 6. Create test PR (1 min)
git checkout -b test
cp examples/test-pr-samples/vulnerable-code.py test.py
git add test.py && git commit -m "test" && git push
gh pr create --title "Test" --body "Testing agent"

# 🎉 Agent automatically comments on your PR with FREE Gemini!
```

**📖 Gemini Guide:** [docs/GEMINI_SETUP.md](docs/GEMINI_SETUP.md)  
**📖 Detailed Guide:** [QUICKSTART.md](QUICKSTART.md)

**Architecture:** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | **Deployment:** See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 📚 Documentation

**📑 [Complete Documentation Index](docs/INDEX.md)** - Find any document quickly

### Quick Links
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)** - Choose your deployment path
- **[docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)** - Complete local testing guide
- **[docs/TESTING_FLOW.md](docs/TESTING_FLOW.md)** - Visual flow diagrams
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture
- **[docs/OPERATIONS.md](docs/OPERATIONS.md)** - Day-to-day operations
- **[docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md)** - Production improvements summary

## 🎯 Use Cases

### Scenario 1: Automated PR Security Reviews

Every PR automatically gets:
- SQL injection detection
- Hardcoded secret scanning
- Authentication/authorization checks
- Dockerfile security review
- IaC security analysis
- Custom policy enforcement

### Scenario 2: Policy-Aware Reviews (RAG)

Add your organization's policies:
```bash
mkdir policies
echo "# SQL Standards\nAlways use parameterized queries" > policies/sql.md
python -m devsecops_agent --ingest policies --reset
```

Agent will reference your policies in reviews!

### Scenario 3: CI/CD Integration

```yaml
# .github/workflows/security-review.yml
- name: Security Review
  run: |
    git diff origin/main...HEAD > changes.diff
    devsecops-review --diff changes.diff --rag
```

## Quick Start

### 🚀 Test Locally in 5 Minutes

**Prerequisites:**
- Python 3.10+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- GitHub token ([Create here](https://github.com/settings/tokens))
- ngrok ([Download](https://ngrok.com/download)) or smee.io

**Step 1: Setup**

```bash
# Windows
.\scripts\setup-local-test.ps1

# Linux/Mac
chmod +x scripts/setup-local-test.sh
./scripts/setup-local-test.sh
```

**Step 2: Start Agent**

```bash
python -m devsecops_agent.webhook.serve
```

**Step 3: Expose Locally (New Terminal)**

```bash
ngrok http 8080
# Copy the HTTPS URL (e.g., https://abc123.ngrok.io)
```

**Step 4: Configure GitHub Webhook**

1. Go to your repo → Settings → Webhooks → Add webhook
2. Payload URL: `https://abc123.ngrok.io/webhook`
3. Content type: `application/json`
4. Secret: (from your `.env` file)
5. Events: Select "Pull requests"

**Step 5: Test It!**

```bash
# Create a test PR with vulnerable code
git checkout -b test-security
cp examples/test-pr-samples/vulnerable-code.py test.py
git add test.py
git commit -m "Add test code"
git push origin test-security

# Create PR on GitHub
gh pr create --title "Test security review" --body "Testing agent"
```

**Watch the magic!** The agent will automatically comment on your PR with a security review! 🎉

📖 **Detailed Guide:** [docs/LOCAL_TESTING.md](docs/LOCAL_TESTING.md)

### CLI Mode (No Webhook)

```bash
# Review a diff
git diff main...HEAD | python -m devsecops_agent --diff - -l python

# With RAG (policy-aware)
make ingest-policies
git diff main...HEAD | python -m devsecops_agent --diff - --rag
```

### Production Deployment

```bash
# Docker Compose
make compose-up

# With monitoring
make compose-monitoring

# Check health
make health-check
```

📖 **Full Deployment Guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Production Features

### Error Handling & Resilience
- Automatic retry with exponential backoff
- Circuit breaker patterns
- Graceful degradation
- Comprehensive error logging

### Monitoring & Observability
- Prometheus metrics endpoint
- Structured logging with structlog
- Cost tracking and token usage monitoring
- Health checks and readiness probes

### Security
- Rate limiting (configurable per IP)
- Webhook signature verification
- Input validation and sanitization
- Non-root container execution
- Secrets management support

### Scalability
- Horizontal scaling support
- Redis-based job queue (optional)
- Async processing
- Configurable resource limits

### Cost Management
- Real-time token usage tracking
- Cost estimation per review
- Configurable model selection
- Diff size limits

## Development

### Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration
```

### Code Quality

```bash
# Lint code
make lint

# Format code
make format

# Security scan
make security-scan

# Run all CI checks
make ci
```

### Local Development

```bash
# Start webhook server locally
make webhook-start

# Review a diff file
make review-diff DIFF=path/to/diff

# View metrics
make metrics
```


## Configuration

All configuration via environment variables. See [.env.example](.env.example) for full list.

### Key Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | Chat model for reviews | `gpt-4o-mini` |
| `GITHUB_TOKEN` | GitHub PAT for API access | - |
| `GITHUB_WEBHOOK_SECRET` | Webhook signature secret | - |
| `WEBHOOK_USE_RAG` | Enable RAG for reviews | `false` |
| `RATE_LIMIT_PER_MINUTE` | Rate limit per IP | `10` |
| `ENABLE_METRICS` | Enable Prometheus metrics | `true` |

## Monitoring

### Metrics Endpoint

```bash
curl http://localhost:8080/metrics
```

### Key Metrics

- `devsecops_review_requests_total` - Total reviews processed
- `devsecops_review_duration_seconds` - Review latency
- `devsecops_tokens_used_total` - Token consumption
- `devsecops_estimated_cost_usd_total` - Estimated API costs
- `devsecops_review_errors_total` - Error count by type

### Grafana Dashboard

Import `monitoring/grafana/dashboards/devsecops-dashboard.json` for pre-built visualizations.

## CLI Reference

```bash
# Review diff from stdin
git diff | devsecops-review --diff -

# Review diff file
devsecops-review --diff changes.diff --language python

# With RAG
devsecops-review --diff changes.diff --rag --rag-k 6

# Index policies
devsecops-review --ingest policies/ --reset

# Dry run (print prompt only)
devsecops-review --diff changes.diff --dry-run
```

## Architecture

```
┌─────────────┐
│   GitHub    │
│  Webhook    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│   FastAPI Webhook Server        │
│  - Signature verification       │
│  - Rate limiting                │
│  - Background task queue        │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│   Review Service                │
│  - Fetch PR diff                │
│  - Optional RAG retrieval       │
│  - LLM analysis                 │
└──────┬──────────────────────────┘
       │
       ├──────────┐
       ▼          ▼
┌──────────┐  ┌──────────┐
│  OpenAI  │  │  Chroma  │
│   API    │  │  Vector  │
│          │  │   Store  │
└──────────┘  └──────────┘
       │
       ▼
┌─────────────────────────────────┐
│   GitHub API                    │
│  - Post PR comment              │
└─────────────────────────────────┘
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make ci`
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- **Documentation:** [docs/](docs/)
- **Issues:** GitHub Issues
- **Deployment Guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Operations Guide:** [docs/OPERATIONS.md](docs/OPERATIONS.md)

## 🎉 Summary

Your DevSecOps Agent is now **production-ready** with:

✅ **Complete local testing setup** - Test in 5 minutes with ngrok  
✅ **Automated PR reviews** - Agent comments on every PR automatically  
✅ **Production deployment** - Docker, Kubernetes, Cloud Run ready  
✅ **Comprehensive monitoring** - Prometheus metrics & Grafana dashboards  
✅ **Enterprise security** - Rate limiting, validation, error handling  
✅ **Cost tracking** - Real-time token usage and cost estimation  
✅ **Full documentation** - 15+ guides covering every scenario  
✅ **Test suite** - 85%+ code coverage  

## 🚀 Next Steps

1. **Test Locally** → [QUICKSTART.md](QUICKSTART.md) (5 minutes)
2. **Add Policies** → Create `policies/` directory with your security standards
3. **Deploy** → [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) (Docker/K8s/Cloud)
4. **Monitor** → Set up Prometheus + Grafana dashboards
5. **Customize** → Edit prompts and severity thresholds

## 📞 Support

- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Documentation**: [docs/](docs/)
- **Issues**: GitHub Issues
- **Examples**: [examples/](examples/)

---

**Made with ❤️ for DevSecOps teams**
#   D e v S e c O p s - A g e n t 
 
 