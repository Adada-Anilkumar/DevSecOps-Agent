"""Prometheus metrics for monitoring."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Review metrics
review_requests_total = Counter(
    "devsecops_review_requests_total",
    "Total number of review requests",
    ["status", "use_rag"],
)

review_duration_seconds = Histogram(
    "devsecops_review_duration_seconds",
    "Time spent processing reviews",
    ["use_rag"],
    buckets=(1, 5, 10, 30, 60, 120, 300),
)

review_errors_total = Counter(
    "devsecops_review_errors_total",
    "Total number of review errors",
    ["error_type"],
)

# API metrics
api_calls_total = Counter(
    "devsecops_api_calls_total",
    "Total API calls to external services",
    ["service", "status"],
)

api_duration_seconds = Histogram(
    "devsecops_api_duration_seconds",
    "API call duration",
    ["service"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30),
)

# Token usage metrics
tokens_used_total = Counter(
    "devsecops_tokens_used_total",
    "Total tokens consumed",
    ["model", "type"],  # type: prompt, completion
)

estimated_cost_usd = Counter(
    "devsecops_estimated_cost_usd_total",
    "Estimated API cost in USD",
    ["model"],
)

# Webhook metrics
webhook_requests_total = Counter(
    "devsecops_webhook_requests_total",
    "Total webhook requests received",
    ["event", "action", "status"],
)

webhook_queue_size = Gauge(
    "devsecops_webhook_queue_size",
    "Current webhook processing queue size",
)

# RAG metrics
rag_retrievals_total = Counter(
    "devsecops_rag_retrievals_total",
    "Total RAG retrieval operations",
    ["status"],
)

rag_chunks_retrieved = Histogram(
    "devsecops_rag_chunks_retrieved",
    "Number of chunks retrieved per query",
    buckets=(0, 1, 3, 5, 10, 20),
)


def get_metrics() -> bytes:
    """Generate Prometheus metrics in text format."""
    return generate_latest()
