"""Test prompt building."""

from __future__ import annotations

from devsecops_agent.prompts import SYSTEM_PROMPT, build_user_message


def test_system_prompt_structure():
    """Test system prompt contains required sections."""
    assert "DevSecOps" in SYSTEM_PROMPT
    assert "Critical Issues" in SYSTEM_PROMPT
    assert "High Priority Issues" in SYSTEM_PROMPT
    assert "Medium Issues" in SYSTEM_PROMPT
    assert "Suggestions" in SYSTEM_PROMPT


def test_build_user_message_basic():
    """Test basic user message building."""
    diff = "diff --git a/test.py b/test.py\n+print('hello')"

    message = build_user_message(diff)

    assert "BEGIN DIFF" in message
    assert "END DIFF" in message
    assert "print('hello')" in message


def test_build_user_message_with_language():
    """Test user message with language hint."""
    diff = "diff --git a/test.py b/test.py"

    message = build_user_message(diff, language="Python 3.11")

    assert "Python 3.11" in message


def test_build_user_message_with_context():
    """Test user message with extra context."""
    diff = "diff --git a/test.py b/test.py"

    message = build_user_message(diff, extra_context="Production API")

    assert "Production API" in message


def test_build_user_message_complete():
    """Test user message with all parameters."""
    diff = "diff --git a/test.py b/test.py"

    message = build_user_message(
        diff, language="Python", extra_context="Critical service"
    )

    assert "BEGIN DIFF" in message
    assert "Python" in message
    assert "Critical service" in message
