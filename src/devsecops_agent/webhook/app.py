"""
GitHub webhook endpoint.

Flow: GitHub → POST /webhook → verify signature → queue background job →
fetch PR diff → Security Agent → POST issue comment.

GitHub expects a 2xx within ~10s; long LLM work runs in BackgroundTasks after 202.
"""

from __future__ import annotations

import json
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

from devsecops_agent.settings import get_settings
from devsecops_agent.utils.logging_config import configure_logging, get_logger
from devsecops_agent.utils.metrics import get_metrics, webhook_requests_total
from devsecops_agent.webhook.github_client import verify_webhook_signature
from devsecops_agent.webhook.handlers import process_pull_request_event

# Initialize settings and logging
settings = get_settings()
configure_logging(settings.log_level, enable_json=False)
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting DevSecOps Agent", version="0.3.0")
    yield
    logger.info("Shutting down DevSecOps Agent")


app = FastAPI(
    title="DevSecOps Agent Webhook",
    version="0.3.0",
    description="AI-powered security review agent for GitHub PRs",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware (configure as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.3.0"}


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    if not settings.enable_metrics:
        raise HTTPException(status_code=404, detail="Metrics disabled")
    return Response(content=get_metrics(), media_type="text/plain")


@app.post("/webhook")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def github_webhook(
    request: Request, background_tasks: BackgroundTasks
) -> dict[str, str]:
    """
    GitHub webhook endpoint for PR events.

    Validates signature, queues background processing, returns 202.
    """
    raw = await request.body()

    # Validate payload size
    if len(raw) > 10_000_000:  # 10MB limit
        logger.warning("Webhook payload too large", size=len(raw))
        webhook_requests_total.labels(
            event="unknown", action="unknown", status="rejected_size"
        ).inc()
        raise HTTPException(status_code=413, detail="Payload too large")

    # Verify signature
    sig = request.headers.get("X-Hub-Signature-256")

    if settings.github_webhook_secret:
        if not verify_webhook_signature(settings.github_webhook_secret, raw, sig):
            logger.warning("Invalid webhook signature", ip=get_remote_address(request))
            webhook_requests_total.labels(
                event="unknown", action="unknown", status="invalid_signature"
            ).inc()
            raise HTTPException(status_code=401, detail="Invalid signature")
    elif not settings.webhook_allow_unsigned:
        logger.warning("Webhook secret not configured")
        webhook_requests_total.labels(
            event="unknown", action="unknown", status="no_secret"
        ).inc()
        raise HTTPException(status_code=503, detail="Webhook secret not configured")

    # Parse payload
    try:
        payload: dict[str, Any] = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON payload", error=str(e))
        webhook_requests_total.labels(
            event="unknown", action="unknown", status="invalid_json"
        ).inc()
        raise HTTPException(status_code=400, detail="Invalid JSON") from e

    # Check event type
    event = request.headers.get("X-GitHub-Event", "")
    action = payload.get("action", "unknown")

    if event != "pull_request":
        logger.info("Ignoring non-PR event", event_type=event)
        webhook_requests_total.labels(
            event=event, action=action, status="ignored"
        ).inc()
        return {"status": "ignored", "reason": f"event={event}"}

    # Queue background processing
    logger.info("Webhook received", event_type=event, action=action)
    webhook_requests_total.labels(event=event, action=action, status="accepted").inc()

    background_tasks.add_task(process_pull_request_event, payload)

    return {"status": "accepted", "event": "pull_request", "action": action}
