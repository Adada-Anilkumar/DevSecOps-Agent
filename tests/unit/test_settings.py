"""Test settings and configuration."""

from __future__ import annotations

import os

import pytest
from pydantic import ValidationError

from devsecops_agent.settings import Settings, get_settings, reset_settings


def test_settings_defaults():
    """Test default settings values."""
    os.environ["OPENAI_API_KEY"] = "test-key"
    settings = Settings()

    assert settings.openai_model == "gpt-4o-mini"
    assert settings.openai_embedding_model == "text-embedding-3-small"
    assert settings.port == 8080
    assert settings.webhook_use_rag is False
    assert settings.rate_limit_enabled is True


def test_settings_from_env():
    """Test settings loaded from environment."""
    os.environ["OPENAI_API_KEY"] = "custom-key"
    os.environ["OPENAI_MODEL"] = "gpt-4o"
    os.environ["PORT"] = "9000"

    settings = Settings()

    assert settings.openai_api_key == "custom-key"
    assert settings.openai_model == "gpt-4o"
    assert settings.port == 9000


def test_settings_validation_errors():
    """Test settings validation."""
    # Missing required field
    os.environ.pop("OPENAI_API_KEY", None)
    with pytest.raises(ValidationError):
        Settings()

    # Invalid port
    os.environ["OPENAI_API_KEY"] = "test"
    os.environ["PORT"] = "99999"
    with pytest.raises(ValidationError):
        Settings()


def test_settings_pr_actions_validation():
    """Test PR actions validation."""
    os.environ["OPENAI_API_KEY"] = "test"
    os.environ["WEBHOOK_PR_ACTIONS"] = "opened,invalid_action"

    with pytest.raises(ValidationError, match="Invalid PR actions"):
        Settings()


def test_get_pr_actions():
    """Test parsing PR actions."""
    os.environ["OPENAI_API_KEY"] = "test"
    os.environ["WEBHOOK_PR_ACTIONS"] = "opened, synchronize, reopened"

    settings = Settings()
    actions = settings.get_pr_actions()

    assert actions == {"opened", "synchronize", "reopened"}


def test_settings_singleton():
    """Test settings singleton pattern."""
    os.environ["OPENAI_API_KEY"] = "test"

    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2

    reset_settings()
    settings3 = get_settings()

    assert settings3 is not settings1
