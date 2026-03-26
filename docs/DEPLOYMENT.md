# Deployment Guide

This guide covers deploying the DevSecOps Agent to production environments.

## Prerequisites

- Docker and Docker Compose
- GitHub repository with webhook access
- OpenAI API key
- (Optional) Redis for job queue
- (Optional) Prometheus/Grafana for monitoring

## Quick Start with Docker Compose

### 1. Clone and Configure

```bash
git clone <repository-url>
cd devsecops-agent
cp .env.example .env
```

### 2. Edit .env File

```bash
# Required
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=your-secret-here

# Optional - Production Settings
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
ENABLE_METRICS=true
RATE_LIMIT_ENABLED=true
WEBHOOK_USE_RAG=true
```

### 3. Build and Start

```bash
# Basic deployment
docker-compose up -d

# With monitoring stack
docker-compose --profile monitoring up -d
```

### 4. Verify Deployment

```bash
# Check health
curl http://localhost:8080/health

# Check metrics
curl http://localhost:8080/metrics

# View logs
docker-compose logs -f agent
```

## Production Deployment Options

### Option 1: Docker on VM/EC2

```bash
# Build image
docker build -t devsecops-agent:latest .

# Run container
docker run -d \
  --name devsecops-agent \
  -p 8080:8080 \
  --env-file .env \
  -v $(pwd)/data/chroma:/app/.devsecops/chroma \
  --restart unless-stopped \
  devsecops-agent:latest
```

### Option 2: Kubernetes

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: devsecops-agent
  labels:
    app: devsecops-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: devsecops-agent
  template:
    metadata:
      labels:
        app: devsecops-agent
    spec:
      containers:
      - name: agent
        image: your-registry/devsecops-agent:latest
        ports:
        - containerPort: 8080
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: devsecops-secrets
              key: openai-api-key
        - name: GITHUB_TOKEN
          valueFrom:
            secretKeyRef:
              name: devsecops-secrets
              key: github-token
        - name: GITHUB_WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: devsecops-secrets
              key: webhook-secret
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: devsecops-agent
spec:
  selector:
    app: devsecops-agent
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
```

Deploy:

```bash
# Create secrets
kubectl create secret generic devsecops-secrets \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=github-token=$GITHUB_TOKEN \
  --from-literal=webhook-secret=$GITHUB_WEBHOOK_SECRET

# Deploy
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods -l app=devsecops-agent
kubectl logs -f deployment/devsecops-agent
```

### Option 3: Cloud Run (GCP)

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/devsecops-agent

# Deploy
gcloud run deploy devsecops-agent \
  --image gcr.io/PROJECT_ID/devsecops-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars OPENAI_API_KEY=$OPENAI_API_KEY \
  --set-env-vars GITHUB_TOKEN=$GITHUB_TOKEN \
  --set-env-vars GITHUB_WEBHOOK_SECRET=$GITHUB_WEBHOOK_SECRET \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

### Option 4: Azure Container Apps

```bash
# Create resource group
az group create --name devsecops-rg --location eastus

# Create container app
az containerapp create \
  --name devsecops-agent \
  --resource-group devsecops-rg \
  --image your-registry/devsecops-agent:latest \
  --target-port 8080 \
  --ingress external \
  --secrets \
    openai-key=$OPENAI_API_KEY \
    github-token=$GITHUB_TOKEN \
    webhook-secret=$GITHUB_WEBHOOK_SECRET \
  --env-vars \
    OPENAI_API_KEY=secretref:openai-key \
    GITHUB_TOKEN=secretref:github-token \
    GITHUB_WEBHOOK_SECRET=secretref:webhook-secret \
  --cpu 1.0 \
  --memory 2.0Gi
```

## GitHub Webhook Configuration

### 1. Get Your Deployment URL

- Docker: `https://your-domain.com/webhook`
- Kubernetes: `https://your-loadbalancer-ip/webhook`
- Cloud Run: `https://devsecops-agent-xxx.run.app/webhook`

### 2. Configure Webhook in GitHub

1. Go to repository Settings → Webhooks → Add webhook
2. Payload URL: Your deployment URL
3. Content type: `application/json`
4. Secret: Same value as `GITHUB_WEBHOOK_SECRET` in .env
5. Events: Select "Pull requests"
6. Active: ✓

### 3. Test Webhook

Create a test PR and check:
- Webhook delivery in GitHub (Settings → Webhooks → Recent Deliveries)
- Agent logs: `docker-compose logs -f agent`
- PR comment appears automatically

## RAG Setup (Optional)

If using RAG for policy-aware reviews:

### 1. Prepare Policy Documents

```bash
mkdir -p policies
# Add your .md/.txt policy files
```

### 2. Build Index

```bash
# Using Docker
docker-compose exec agent devsecops-review --ingest /app/policies --reset

# Or locally
python -m devsecops_agent --ingest policies --reset
```

### 3. Enable RAG in Webhook

```bash
# In .env
WEBHOOK_USE_RAG=true
WEBHOOK_RAG_K=6
```

### 4. Restart Service

```bash
docker-compose restart agent
```

## Monitoring Setup

### Prometheus + Grafana

```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000
# Login: admin / admin (change on first login)

# Import dashboard
# Use monitoring/grafana/dashboards/devsecops-dashboard.json
```

### Metrics Available

- `devsecops_review_requests_total` - Total reviews
- `devsecops_review_duration_seconds` - Review latency
- `devsecops_tokens_used_total` - Token consumption
- `devsecops_estimated_cost_usd_total` - API costs
- `devsecops_webhook_requests_total` - Webhook traffic

### Alerting

Create `monitoring/alerting_rules.yml`:

```yaml
groups:
  - name: devsecops_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(devsecops_review_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: HighAPIcost
        expr: increase(devsecops_estimated_cost_usd_total[1h]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "API costs exceeding $10/hour"
```

## Security Hardening

### 1. Use Secrets Management

```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name devsecops/openai-key \
  --secret-string $OPENAI_API_KEY

# Retrieve in app
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id devsecops/openai-key \
  --query SecretString \
  --output text)
```

### 2. Enable HTTPS

Use reverse proxy (nginx, Caddy) or cloud load balancer:

```nginx
server {
    listen 443 ssl http2;
    server_name devsecops.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Network Isolation

```yaml
# docker-compose.yml
networks:
  devsecops-network:
    driver: bridge
    internal: true  # No external access except via proxy
```

### 4. Rate Limiting

Already enabled by default. Adjust in .env:

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=10
```

## Scaling Considerations

### Horizontal Scaling

For multiple instances:

1. Use external Redis for job queue:
   ```bash
   REDIS_URL=redis://your-redis:6379/0
   USE_BACKGROUND_QUEUE=true
   ```

2. Use managed vector DB (Pinecone, Weaviate) instead of local Chroma

3. Deploy behind load balancer

### Vertical Scaling

Adjust resources based on load:

```yaml
# docker-compose.yml
services:
  agent:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
```

## Troubleshooting

### Check Logs

```bash
# Docker Compose
docker-compose logs -f agent

# Kubernetes
kubectl logs -f deployment/devsecops-agent

# Docker
docker logs -f devsecops-agent
```

### Common Issues

**Webhook not receiving events:**
- Check GitHub webhook delivery status
- Verify HTTPS and public accessibility
- Check signature validation

**High latency:**
- Enable RAG caching
- Increase replicas
- Use faster OpenAI model

**Out of memory:**
- Reduce `WEBHOOK_MAX_DIFF_CHARS`
- Increase container memory
- Enable diff truncation

### Health Checks

```bash
# Application health
curl http://localhost:8080/health

# Metrics
curl http://localhost:8080/metrics | grep devsecops

# Redis connection (if using)
docker-compose exec redis redis-cli ping
```

## Backup and Recovery

### Backup Chroma Index

```bash
# Backup
tar -czf chroma-backup-$(date +%Y%m%d).tar.gz data/chroma/

# Restore
tar -xzf chroma-backup-20240101.tar.gz -C data/
```

### Backup Configuration

```bash
# Backup secrets
cp .env .env.backup

# Store securely (never commit)
```

## Cost Optimization

### 1. Monitor Token Usage

```bash
# Check metrics
curl http://localhost:8080/metrics | grep tokens_used

# View cost estimates
curl http://localhost:8080/metrics | grep estimated_cost
```

### 2. Optimize Settings

```bash
# Use cheaper model
OPENAI_MODEL=gpt-4o-mini

# Reduce diff size
WEBHOOK_MAX_DIFF_CHARS=100000

# Limit RAG chunks
WEBHOOK_RAG_K=3
```

### 3. Set Budget Alerts

Configure alerts when costs exceed thresholds (see Monitoring section).

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: docs/
- Logs: Check application logs for detailed error messages
