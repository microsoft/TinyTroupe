"""Tests for OpenAIClient._setup_from_config base_url handling."""

import os
from unittest.mock import patch

import pytest

from tinytroupe import config_manager
from tinytroupe.clients.openai_client import OpenAIClient


@pytest.fixture
def openai_client():
    return OpenAIClient()


def test_setup_from_config_passes_base_url_from_config(openai_client):
    """BASE_URL from config.ini must be forwarded to the OpenAI client.

    Regression test: previously `_setup_from_config` built `OpenAI(...)` without
    `base_url`, so the `BASE_URL` config key was silently ignored and only the
    `OPENAI_BASE_URL` environment variable had any effect.
    """
    config_manager.update("base_url", "https://api.example.com/v1")

    with patch("tinytroupe.clients.openai_client.OpenAI") as mock_openai:
        openai_client._setup_from_config(timeout=10)

    mock_openai.assert_called_once()
    _, kwargs = mock_openai.call_args
    assert kwargs.get("base_url") == "https://api.example.com/v1"


def test_setup_from_config_omits_base_url_when_unset(openai_client):
    """When BASE_URL is not configured, base_url must be None (SDK default)."""
    config_manager.update("base_url", None)

    with patch("tinytroupe.clients.openai_client.OpenAI") as mock_openai:
        openai_client._setup_from_config(timeout=10)

    mock_openai.assert_called_once()
    _, kwargs = mock_openai.call_args
    assert kwargs.get("base_url") is None


def test_setup_from_config_still_sets_api_key(openai_client):
    """The fix must not regress the existing api_key wiring."""
    os.environ["OPENAI_API_KEY"] = "sk-test"

    with patch("tinytroupe.clients.openai_client.OpenAI") as mock_openai:
        openai_client._setup_from_config(timeout=10)

    _, kwargs = mock_openai.call_args
    assert kwargs.get("api_key") == "sk-test"
