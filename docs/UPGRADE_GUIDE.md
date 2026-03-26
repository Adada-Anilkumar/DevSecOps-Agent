# Upgrade Guide: v0.1.0 → v0.3.0

This guide helps you upgrade from the basic version to the production-ready version.

## Breaking Changes

### Configuration

**Old (v0.1.0):**
```python
# Direct environment variable access
os.environ.get("OPENAI_API_KEY")
```

**New (v0.3.0):**
```python
# Pydantic settings with validation
from devsecops_agent.settings import get_settings
settings = get_settings()
settings.openai_api_key
```

### Import Changes

**Old:**
```python
from devsecops_agent.config import chat_model
```

**New:**
```python
from devsecops_agent.settings import get_settings
settings = get_settings()
model = settings.openai_model
```

## New Features

### 1. Structured Logging

```python
from devsecops_agent.utils import get_logger

logger = get_logger(__name__)
logger.info("Processing review", pr_number=123, repo="org/repo")
```

### 2. Cost Tracking

```python
from devsecops_agent.utils import get_cost_tracker

tracker = get_cost_tracker()
cost = tracker.track_usage("gpt-4o-mini", 1000, 500)
summary = tracker.get_summary()
```

### 3. Retry Logic

```python
from devsecops_agent.utils import retry_with_backoff

@retry_with_backoff(max_attempts=3)
def api_call():
    # Your code here
    pass
```

### 4. Metrics

Access at `http://localhost:8080/metrics`

## Migration Steps

### Step 1: Update Dependencies

```bash
pip install -r requirements.txt --upgrade
```

### Step 2: Update Environment Variables

Copy new `.env.example` and update your `.env`:

```bash
cp .env.example .env.new
# Merge your existing values
```

New required variables:
- None (all backward compatible)

New optional variables:
- `RATE_LIMIT_ENABLED`
- `ENABLE_METRICS`
- `REDIS_URL`
- `SENTRY_DSN`

### Step 3: Update Docker Configuration

```bash
# Rebuild image
docker-compose down
docker-compose build
docker-compose up -d
```

### Step 4: Test Migration

```bash
# Run health check
curl http://localhost:8080/health

# Run tests
make test

# Check metrics
curl http://localhost:8080/metrics
```

## Rollback Plan

If issues occur:

```bash
# Stop new version
docker-compose down

# Checkout old version
git checkout v0.1.0

# Restore old .env
cp .env.backup .env

# Start old version
docker-compose up -d
```

## Post-Migration

### Enable Monitoring

```bash
# Start with monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000
```

### Configure Alerts

See [docs/DEPLOYMENT.md](DEPLOYMENT.md#alerting) for alert configuration.

### Review Logs

```bash
# Check for any errors
docker-compose logs agent | grep ERROR
```

## Support

If you encounter issues:
1. Check logs: `docker-compose logs agent`
2. Verify configuration: `make health-check`
3. Review [docs/DEPLOYMENT.md](DEPLOYMENT.md)
4. Open GitHub issue with logs
