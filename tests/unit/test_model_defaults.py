"""Regression coverage for model defaults and reasoning request parameters."""

import configparser
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic import BaseModel

from tinytroupe import ConfigManager, config_manager
from tinytroupe.clients import client
from tinytroupe.clients.openai_client import OpenAIClient


@pytest.mark.core
@pytest.mark.parametrize(
    "relative_path",
    [Path("tinytroupe") / "config.ini", Path("config.ini"), Path("examples") / "config.ini"],
)
def test_shipped_model_defaults(relative_path):
    """Active configs consistently select Luna at its highest API effort."""
    config = configparser.ConfigParser()
    config.read(Path(__file__).resolve().parents[2] / relative_path)
    assert config["OpenAI"]["MODEL"] == "gpt-6-luna"
    assert config["OpenAI"]["REASONING_MODEL"] == "gpt-6-luna"
    assert config["OpenAI"]["REASONING_EFFORT"] == "xhigh"


@pytest.mark.core
def test_model_config_fallbacks(monkeypatch):
    """Missing model settings use the same defaults as the shipped configs."""
    config = configparser.ConfigParser()
    config.read(Path(__file__).resolve().parents[2] / "tinytroupe" / "config.ini")
    for option in ("MODEL", "REASONING_MODEL", "REASONING_EFFORT"):
        config.remove_option("OpenAI", option)
    monkeypatch.setattr("tinytroupe.utils.read_config_file", lambda: config)
    manager = ConfigManager()
    assert manager.get("model") == "gpt-6-luna"
    assert manager.get("reasoning_model") == "gpt-6-luna"
    assert manager.get("reasoning_effort") == "xhigh"


@pytest.mark.core
@pytest.mark.parametrize("structured", [False, True])
@pytest.mark.parametrize("prepared_effort", [None, "high"])
def test_luna_request_parameters(monkeypatch, structured, prepared_effort):
    """Both completion routes pass effort and retain the output token limit."""
    api_client = OpenAIClient(cache_api_calls=False)
    api_client.client = Mock()
    monkeypatch.setitem(config_manager._config, "reasoning_effort", "xhigh")
    params = {
        "model": "gpt-6-luna",
        "messages": [{"role": "user", "content": "Say hello."}],
        "max_completion_tokens": 1024,
        "temperature": 0.5,
        "stream": False,
    }
    if structured:
        params["response_format"] = BaseModel
    if prepared_effort is not None:
        params["reasoning_effort"] = prepared_effort
    api_client._raw_model_call("gpt-6-luna", params)
    endpoint = (
        api_client.client.beta.chat.completions.parse
        if structured else api_client.client.chat.completions.create
    )
    sent = endpoint.call_args.kwargs
    assert sent["reasoning_effort"] == (prepared_effort or "xhigh")
    assert sent["max_completion_tokens"] == 1024
    assert "temperature" not in sent
    assert "stream" not in sent


@pytest.mark.core
@pytest.mark.parametrize("model", ["gpt-4.1-mini", "gpt-5-mini"])
def test_earlier_models_keep_sampling_parameters(model):
    """Existing non-o-series routes do not acquire Luna-specific parameters."""
    api_client = OpenAIClient(cache_api_calls=False)
    api_client.client = Mock()
    params = {
        "model": model,
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 1.0,
        "max_completion_tokens": 1024,
        "stream": False,
    }
    api_client._raw_model_call(model, params)
    sent = api_client.client.chat.completions.create.call_args.kwargs
    assert sent["temperature"] == 1.0
    assert sent["max_completion_tokens"] == 1024
    assert "reasoning_effort" not in sent


@pytest.mark.core
def test_luna_token_count():
    """An unfamiliar Luna tokenizer still yields an approximate token count."""
    api_client = OpenAIClient(cache_api_calls=False)
    count = api_client._count_tokens(
        [{"role": "user", "content": "Hello"}], "gpt-6-luna"
    )
    assert isinstance(count, int)
    assert count > 0


@pytest.mark.core
def test_reasoning_effort_separates_cache_entries(monkeypatch, tmp_path):
    """Changing effort must not reuse a response generated at a different effort."""
    api_client = OpenAIClient(
        cache_api_calls=True, cache_file_name=str(tmp_path / "cache.json")
    )
    monkeypatch.setattr(api_client, "_setup_from_config", lambda: None)
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message.to_dict.return_value = {"content": "Hello"}
    response.usage.prompt_tokens = 1
    response.usage.completion_tokens = 1
    response.usage.total_tokens = 2
    calls = []

    def capture_call(model, params):
        calls.append(params["reasoning_effort"])
        return response

    monkeypatch.setattr(api_client, "_raw_model_call", capture_call)
    monkeypatch.setattr(api_client, "_to_cacheable_format", lambda value: {})
    for effort in ("high", "xhigh"):
        monkeypatch.setitem(config_manager._config, "reasoning_effort", effort)
        result = api_client.send_message(
            [{"role": "user", "content": "Hello"}],
            model="gpt-6-luna", max_attempts=1, waiting_time=0,
        )
        assert result is not None
    assert calls == ["high", "xhigh"]
    assert len(api_client.api_cache) == 2


class Greeting(BaseModel):
    """Structured response used by the real API smoke test."""

    greeting: str


@pytest.mark.core
@pytest.mark.parametrize("structured", [False, True])
def test_luna_live_completion(monkeypatch, structured):
    """Exercise actual Luna completions with xhigh, including structured output."""
    monkeypatch.setitem(config_manager._config, "model", "gpt-6-luna")
    monkeypatch.setitem(config_manager._config, "reasoning_effort", "xhigh")
    response = client().send_message(
        [{"role": "user", "content": 'Say "Hello".'}],
        response_format=Greeting if structured else None,
        max_completion_tokens=4096,
        max_attempts=1,
    )
    assert response is not None
    if structured:
        assert response["parsed"]["greeting"].lower().startswith("hello")
    else:
        assert "hello" in response["content"].lower()
