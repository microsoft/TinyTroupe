"""Tests for OpenAIClient._setup_from_config base_url handling."""

import pytest

from tinytroupe import config_manager
from tinytroupe.clients.openai_client import OpenAIClient

pytestmark = pytest.mark.core


@pytest.fixture
def openai_client(monkeypatch):
    """Keep the client's configuration and credentials local to each test."""
    previous_base_url = config_manager.get("base_url")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-unit-test")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    client = OpenAIClient(cache_api_calls=False)
    try:
        yield client
    finally:
        config_manager.update("base_url", previous_base_url)
        if hasattr(client, "client"):
            client.client.close()


@pytest.mark.parametrize(
    "environment_url", [None, "https://environment.example.test/v1"]
)
def test_setup_from_config_passes_base_url_from_config(
    openai_client, monkeypatch, environment_url
):
    """An explicit configuration URL takes precedence over the SDK environment."""
    config_manager.update("base_url", "https://configured.example.test/v1")
    if environment_url is not None:
        monkeypatch.setenv("OPENAI_BASE_URL", environment_url)

    openai_client._setup_from_config(timeout=10)
    assert str(openai_client.client.base_url) == "https://configured.example.test/v1/"


@pytest.mark.parametrize(
    "environment_url, expected_url",
    [
        (None, "https://api.openai.com/v1/"),
        ("https://environment.example.test/v1", "https://environment.example.test/v1/"),
    ],
)
def test_setup_from_config_uses_sdk_defaults_when_unset(
    openai_client, monkeypatch, environment_url, expected_url
):
    """An unset configuration preserves the SDK's default and environment fallback."""
    config_manager.update("base_url", None)
    if environment_url is not None:
        monkeypatch.setenv("OPENAI_BASE_URL", environment_url)

    openai_client._setup_from_config(timeout=10)
    assert str(openai_client.client.base_url) == expected_url


def test_setup_from_config_still_sets_api_key(openai_client, monkeypatch):
    """The fix must not regress the existing api_key wiring."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-client-test")
    openai_client._setup_from_config(timeout=10)
    assert openai_client.client.api_key == "sk-client-test"
