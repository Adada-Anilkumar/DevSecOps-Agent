"""Integration tests for webhook endpoint."""

from __future__ import annotations

import hashlib
import hmac
import json

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics_endpoint(client: TestClient):
    """Test metrics endpoint."""
    response = client.get("/metrics")

    assert response.status_code == 200
    assert b"devsecops" in response.content


def test_webhook_invalid_signature(client: TestClient, sample_pr_payload: dict):
    """Test webhook with invalid signature."""
    payload = json.dumps(sample_pr_payload).encode()

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": "sha256=invalid",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 401


def test_webhook_valid_signature(client: TestClient, sample_pr_payload: dict):
    """Test webhook with valid signature."""
    secret = "test-secret"
    payload = json.dumps(sample_pr_payload).encode()

    # Generate valid signature
    signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


def test_webhook_non_pr_event(client: TestClient):
    """Test webhook ignores non-PR events."""
    secret = "test-secret"
    payload = json.dumps({"action": "created"}).encode()

    signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-GitHub-Event": "issue_comment",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_webhook_invalid_json(client: TestClient):
    """Test webhook with invalid JSON."""
    secret = "test-secret"
    payload = b"not json"

    signature = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/webhook",
        content=payload,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 400


def test_webhook_payload_too_large(client: TestClient):
    """Test webhook rejects oversized payloads."""
    secret = "test-secret"
    # Create 11MB payload
    large_payload = json.dumps({"data": "x" * 11_000_000}).encode()

    signature = hmac.new(
        secret.encode(), large_payload, hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/webhook",
        content=large_payload,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": f"sha256={signature}",
            "Content-Type": "application/json",
        },
    )

    assert response.status_code == 413
