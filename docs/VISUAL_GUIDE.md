# Visual Guide - DevSecOps Agent

## 🎯 What It Does

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Developer creates PR  →  Agent reviews  →  Posts comment  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Complete Flow

```
Developer                    GitHub                    Agent                    OpenAI
    │                          │                         │                        │
    │  1. Create PR            │                         │                        │
    ├─────────────────────────>│                         │                        │
    │                          │                         │                        │
    │                          │  2. Webhook Event       │                        │
    │                          ├────────────────────────>│                        │
    │                          │                         │                        │
    │                          │  3. 202 Accepted        │                        │
    │                          │<────────────────────────┤                        │
    │                          │                         │                        │
    │                          │  4. Fetch PR Diff       │                        │
    │                          │<────────────────────────┤                        │
    │                          │                         │                        │
    │                          │  5. Return Diff         │                        │
    │                          ├────────────────────────>│                        │
    │                          │                         │                        │
    │                          │                         │  6. Analyze Code       │
    │                          │                         ├───────────────────────>│
    │                          │                         │                        │
    │                          │                         │  7. Security Review    │
    │                          │                         │<───────────────────────┤
    │                          │                         │                        │
    │                          │  8. Post Comment        │                        │
    │                          │<────────────────────────┤                        │
    │                          │                         │                        │
    │  9. See Review Comment   │                         │                        │
    │<─────────────────────────┤                         │                        │
    │                          │                         │                        │
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Repository                           │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │   PR 1   │  │   PR 2   │  │   PR 3   │  │   PR 4   │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
│       │             │             │             │                  │
└───────┼─────────────┼─────────────┼─────────────┼──────────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │    Webhook Endpoint         │
        │    (FastAPI Server)         │
        │                             │
        │  • Signature Verification   │
        │  • Rate Limiting            │
        │  • Input Validation         │
        └─────────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │   Background Queue          │
        │   (FastAPI / Redis)         │
        └─────────────┬───────────────┘
                      │
                      ▼
        ┌─────────────────────────────┐
        │   Review Service            │
        │                             │
        │  ┌─────────────────────┐   │
        │  │  Fetch PR Diff      │   │
        │  └──────────┬──────────┘   │
        │             ▼               │
        │  ┌─────────────────────┐   │
        │  │  RAG Retrieval      │   │
        │  │  (Optional)         │   │
        │  └──────────┬──────────┘   │
        │             ▼               │
        │  ┌─────────────────────┐   │
        │  │  LLM Analysis       │   │
        │  └──────────┬──────────┘   │
        │             ▼               │
        │  ┌─────────────────────┐   │
        │  │  Format Comment     │   │
        │  └──────────┬──────────┘   │
        │             ▼               │
        │  ┌─────────────────────┐   │
        │  │  Post to GitHub     │   │
        │  └─────────────────────┘   │
        └─────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ OpenAI   │  │  Chroma  │  │ GitHub   │
│   API    │  │  Vector  │  │   API    │
│          │  │  Store   │  │          │
└──────────┘  └──────────┘  └──────────┘
```

## 🔐 Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                    Incoming Request                     │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Rate Limiting         │  ← 10 req/min per IP
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Signature Verify      │  ← HMAC-SHA256
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Payload Size Check    │  ← Max 10MB
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  JSON Validation       │  ← Schema check
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Event Type Filter     │  ← Only PR events
            └────────────┬───────────┘
                         │
                         ▼
            ┌────────────────────────┐
            │  Process Request       │
            └────────────────────────┘
```

## 📊 Monitoring Stack

```
┌─────────────────────────────────────────────────────────┐
│                    Application                          │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Webhook    │  │   Review     │  │   GitHub     │ │
│  │   Handler    │  │   Service    │  │   Client     │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│         └─────────────────┴─────────────────┘          │
│                           │                            │
└───────────────────────────┼────────────────────────────┘
                            │
                            │ Metrics
                            ▼
                ┌───────────────────────┐
                │   Prometheus          │
                │   (Metrics Storage)   │
                └───────────┬───────────┘
                            │
                            │ Query
                            ▼
                ┌───────────────────────┐
                │   Grafana             │
                │   (Visualization)     │
                └───────────────────────┘
                            │
                            │ Alerts
                            ▼
                ┌───────────────────────┐
                │   Alertmanager        │
                │   (Notifications)     │
                └───────────────────────┘
```

## 💰 Cost Flow

```
Request → Token Estimation → API Call → Usage Tracking → Metrics

┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Diff    │───>│ Estimate │───>│ OpenAI   │───>│  Track   │
│  Input   │    │  Tokens  │    │   API    │    │  Cost    │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │  Prometheus  │
                                              │   Metrics    │
                                              └──────────────┘
```

## 🧪 Testing Setup

```
Local Machine                    Internet                    GitHub
     │                              │                           │
     │                              │                           │
┌────┴────┐                   ┌────┴────┐                 ┌────┴────┐
│  Agent  │                   │  ngrok  │                 │ Webhook │
│  :8080  │<──────────────────│  Tunnel │<────────────────│ Config  │
└─────────┘                   └─────────┘                 └─────────┘
     │                              │                           │
     │  http://localhost:8080       │  https://abc.ngrok.io     │
     │                              │                           │
     └──────────────────────────────┴───────────────────────────┘
                    Webhook Flow
```

## 🚀 Deployment Options

### Option 1: Docker Compose (Simple)

```
┌─────────────────────────────────────────┐
│           Docker Host                   │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │  Agent   │  │  Redis   │           │
│  │  :8080   │  │  :6379   │           │
│  └──────────┘  └──────────┘           │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │Prometheus│  │ Grafana  │           │
│  │  :9090   │  │  :3000   │           │
│  └──────────┘  └──────────┘           │
└─────────────────────────────────────────┘
```

### Option 2: Kubernetes (Scalable)

```
┌─────────────────────────────────────────────────────────┐
│                  Kubernetes Cluster                     │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Load Balancer                      │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                 │
│         ┌─────────────┼─────────────┐                  │
│         ▼             ▼             ▼                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │  Agent   │  │  Agent   │  │  Agent   │            │
│  │  Pod 1   │  │  Pod 2   │  │  Pod 3   │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│         │             │             │                  │
│         └─────────────┼─────────────┘                  │
│                       │                                 │
│                       ▼                                 │
│              ┌─────────────────┐                       │
│              │  Redis Service  │                       │
│              └─────────────────┘                       │
└─────────────────────────────────────────────────────────┘
```

### Option 3: Cloud Run (Serverless)

```
┌─────────────────────────────────────────┐
│         Google Cloud Run                │
│                                         │
│  Auto-scaling: 0 → N instances          │
│                                         │
│  ┌──────────┐  ┌──────────┐           │
│  │ Instance │  │ Instance │  ...       │
│  │    1     │  │    2     │           │
│  └──────────┘  └──────────┘           │
│                                         │
│  Pay per request                        │
└─────────────────────────────────────────┘
```

## 📈 Scaling Strategy

```
Traffic Level          Deployment Strategy
─────────────────────────────────────────────────────────
Low (< 10 PRs/day)    → Single Docker container
                        No Redis needed
                        
Medium (10-100/day)   → Docker Compose
                        Redis queue
                        2-3 instances
                        
High (100-1000/day)   → Kubernetes
                        Redis cluster
                        5-10 pods
                        Auto-scaling
                        
Very High (1000+/day) → Cloud Run / ECS
                        Managed Redis
                        Auto-scaling
                        CDN for static assets
```

## 🔍 Troubleshooting Decision Tree

```
Issue: Agent not working
         │
         ▼
    Can access /health?
         │
    ┌────┴────┐
    │         │
   Yes       No
    │         │
    │         └──> Check: Agent running?
    │                     Port correct?
    │                     Firewall?
    │
    ▼
Webhook received?
    │
┌───┴───┐
│       │
Yes    No
│       │
│       └──> Check: GitHub webhook config
│                   ngrok running?
│                   URL correct?
│
▼
Comment posted?
│
┌───┴───┐
│       │
Yes    No
│       │
│       └──> Check: GitHub token valid?
│                   Token permissions?
│                   API rate limit?
│
▼
✅ Working!
```

## 📚 Quick Reference

### Ports

- `8080` - Agent webhook endpoint
- `9090` - Prometheus metrics
- `3000` - Grafana dashboard
- `6379` - Redis (if used)
- `4040` - ngrok dashboard

### Endpoints

- `GET /health` - Health check
- `POST /webhook` - GitHub webhook
- `GET /metrics` - Prometheus metrics

### Key Files

- `.env` - Configuration
- `docker-compose.yml` - Docker setup
- `Dockerfile` - Container image
- `src/devsecops_agent/prompts.py` - Review prompts
- `policies/` - Security policies (RAG)

### Common Commands

```bash
# Start
make compose-up

# Stop
make compose-down

# Logs
make compose-logs

# Health
make health-check

# Metrics
make metrics

# Test
make test
```
