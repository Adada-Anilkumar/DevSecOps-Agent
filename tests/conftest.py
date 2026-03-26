"""Pytest configuration and fixtures."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing app
os.environ["OPENAI_API_KEY"] = "test-key-12345"
os.environ["GITHUB_TOKEN"] = "test-token"
os.environ["GITHUB_WEBHOOK_SECRET"] = "test-secret"
os.environ["WEBHOOK_ALLOW_UNSIGNED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["ENABLE_METRICS"] = "true"

from devsecops_agent.settings import reset_settings
from devsecops_agent.webhook.app import app


@pytest.fixture(autouse=True)
def reset_settings_fixture() -> Generator[None, None, None]:
    """Reset settings before each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_diff() -> str:
    """Sample git diff for testing."""
    return """diff --git a/api/auth.py b/api/auth.py
index 1234567..abcdefg 100644
--- a/api/auth.py
+++ b/api/auth.py
@@ -10,7 +10,7 @@ def login(username: str, password: str):
     # Authenticate user
-    query = f"SELECT * FROM users WHERE username='{username}'"
+    query = "SELECT * FROM users WHERE username=%s"
-    cursor.execute(query)
+    cursor.execute(query, (username,))
     user = cursor.fetchone()
"""


@pytest.fixture
def sample_pr_payload() -> dict:
    """Sample GitHub PR webhook payload."""
    return {
        "action": "opened",
        "number": 123,
        "pull_request": {
            "number": 123,
            "title": "Fix SQL injection",
            "head": {"sha": "abc123def456"},
            "base": {"ref": "main"},
        },
        "repository": {
            "full_name": "test-org/test-repo",
            "name": "test-repo",
            "owner": {"login": "test-org"},
        },
    }


@pytest.fixture
def temp_chroma_path(tmp_path: Path) -> Path:
    """Temporary Chroma directory."""
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    return chroma_dir
