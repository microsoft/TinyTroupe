import pytest

from tinytroupe import config_manager
from tinytroupe.clients.ollama_client import OllamaClient
from tinytroupe.clients.openai_client import LLMCacheBase


@pytest.fixture
def cache_configuration(tmp_path, monkeypatch):
    """Keep configuration changes and cache files local to each test."""
    monkeypatch.setattr(config_manager, "_config", config_manager._config.copy())
    cache_path = str(tmp_path / "api-cache.json")
    config_manager.update("cache_file_name", cache_path)
    config_manager.update("cache_api_calls", False)
    return cache_path


@pytest.mark.core
@pytest.mark.parametrize("call_style", ["omitted", "keyword", "positional"])
def test_cache_defaults_accept_all_argument_styles(cache_configuration, call_style):
    """The cache setter accepts positional None just like keyword None."""
    cache = LLMCacheBase()
    if call_style == "omitted":
        cache.set_api_cache(False)
    elif call_style == "keyword":
        cache.set_api_cache(False, cache_file_name=None)
    else:
        cache.set_api_cache(False, None)

    assert cache.cache_file_name == cache_configuration
    assert cache.cache_api_calls is False


@pytest.mark.core
def test_ollama_constructor_accepts_positional_defaults(cache_configuration):
    """Client construction resolves both positional defaults without an API call."""
    client = OllamaClient(None, None)
    assert client.cache_file_name == cache_configuration
    assert client.cache_api_calls is False


def test_config_defaults_preserve_explicit_values(cache_configuration):
    cache = LLMCacheBase()
    cache.set_api_cache(False, "explicit-cache.json")
    assert cache.cache_file_name == "explicit-cache.json"
    assert cache.cache_api_calls is False


def test_config_defaults_use_current_configuration(cache_configuration, tmp_path):
    cache = LLMCacheBase()
    cache.set_api_cache(False, None)
    assert cache.cache_file_name == cache_configuration

    updated_path = str(tmp_path / "updated-cache.json")
    config_manager.update("cache_file_name", updated_path)
    cache.set_api_cache(False, None)
    assert cache.cache_file_name == updated_path


def test_config_defaults_forward_parameter_kinds(cache_configuration):
    @config_manager.config_defaults(path="cache_file_name", enabled="cache_api_calls")
    def configured(path=None, /, *items, enabled=None, **metadata):
        return path, items, enabled, metadata

    assert configured(None, "first", "second", label="run") == (
        cache_configuration, ("first", "second"), False, {"label": "run"}
    )
    assert configured("explicit", enabled=True, label="run") == (
        "explicit", (), True, {"label": "run"}
    )


def test_config_defaults_keep_required_arguments(cache_configuration):
    @config_manager.config_defaults(path="cache_file_name")
    def configured(required, path=None):
        return required, path

    with pytest.raises(TypeError, match="required"):
        configured()
    assert configured("value", None) == ("value", cache_configuration)
