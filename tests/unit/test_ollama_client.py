from unittest.mock import patch

import tinytroupe.clients as openai_utils
from tinytroupe.clients.ollama_client import OllamaClient


def test_ollama_client_selection():
    openai_utils.force_api_type("ollama")
    try:
        client = openai_utils.client()
        assert client.__class__.__name__ == "OllamaClient"
    finally:
        openai_utils.force_api_type("openai")


def test_ollama_host_pool_round_robin():
    """With multiple base URLs, _get_base_url() alternates round-robin."""
    with patch("tinytroupe.clients.ollama_client.config_manager") as cm:
        cm.get = lambda k, d=None: {
            "ollama_base_urls": ["http://host1:11434/v1", "http://host2:11435/v1"],
            "cache_api_calls": False,
            "cache_file_name": "test_cache.pkl",
        }.get(k, d)
        client = OllamaClient()

    assert len(client._base_urls) == 2
    urls = [client._get_base_url() for _ in range(4)]
    assert urls == [
        "http://host1:11434/v1",
        "http://host2:11435/v1",
        "http://host1:11434/v1",
        "http://host2:11435/v1",
    ]


def test_ollama_single_url_unchanged():
    """With one base URL, behavior matches legacy (no round-robin)."""
    with patch("tinytroupe.clients.ollama_client.config_manager") as cm:
        cm.get = lambda k, d=None: {
            "ollama_base_urls": ["http://localhost:11434/v1"],
            "cache_api_calls": False,
            "cache_file_name": "test_cache.pkl",
        }.get(k, d)
        client = OllamaClient()

    assert len(client._base_urls) == 1
    assert client.base_url == "http://localhost:11434/v1"
    for _ in range(3):
        assert client._get_base_url() == "http://localhost:11434/v1"

