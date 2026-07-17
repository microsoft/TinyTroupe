import json
import sys
import types
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

sys.path.insert(0, "..")
sys.path.insert(0, "../../")


def _make_mock_response(content="Test response", role="assistant", finish_reason="stop"):
    """Build a mock litellm.ModelResponse-like object."""
    response = MagicMock()
    response.model_dump.return_value = {
        "choices": [
            {
                "message": {"role": role, "content": content},
                "finish_reason": finish_reason,
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }
    return response


def _make_empty_response():
    """Build a response with null content."""
    response = MagicMock()
    response.model_dump.return_value = {
        "choices": [
            {
                "message": {"role": "assistant", "content": None},
                "finish_reason": "stop",
            }
        ],
    }
    return response


def _make_malformed_response():
    """Build a response with missing choices."""
    response = MagicMock()
    response.model_dump.return_value = {"choices": []}
    return response


class TestLiteLLMClient:

    @pytest.mark.core
    def test_basic_completion(self):
        """Test that a normal completion call dispatches correctly and returns parsed content."""
        import litellm
        with patch.object(litellm, "completion", return_value=_make_mock_response("Hello!")) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "Say hello"}],
                model="openai/gpt-4o-mini",
                max_attempts=1,
                waiting_time=0,
            )
            assert result is not None
            assert result["content"] == "Hello!"
            assert result["role"] == "assistant"
            mock_comp.assert_called_once()
            call_kwargs = mock_comp.call_args[1]
            assert call_kwargs["model"] == "openai/gpt-4o-mini"
            assert call_kwargs["stream"] is False

    @pytest.mark.core
    def test_drop_params_default_true(self):
        """Verify drop_params=True is always sent by default."""
        import litellm
        with patch.object(litellm, "completion", return_value=_make_mock_response()) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            client.send_message(
                [{"role": "user", "content": "test"}],
                model="anthropic/claude-haiku-4-5",
                max_attempts=1,
                waiting_time=0,
            )
            call_kwargs = mock_comp.call_args[1]
            assert call_kwargs.get("drop_params") is True

    @pytest.mark.core
    def test_auth_error_no_retry(self):
        """AuthenticationError should NOT trigger retry - fail immediately."""
        import litellm
        with patch.object(
            litellm, "completion",
            side_effect=litellm.AuthenticationError(
                message="Invalid API key", model="test", llm_provider="openai"
            ),
        ) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/gpt-4o-mini",
                max_attempts=3,
                waiting_time=0,
            )
            assert result is None
            assert mock_comp.call_count == 1

    @pytest.mark.core
    def test_bad_request_no_retry(self):
        """BadRequestError should NOT trigger retry."""
        import litellm
        with patch.object(
            litellm, "completion",
            side_effect=litellm.BadRequestError(
                message="Invalid model", model="test", llm_provider="openai"
            ),
        ) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="nonexistent/model",
                max_attempts=3,
                waiting_time=0,
            )
            assert result is None
            assert mock_comp.call_count == 1

    @pytest.mark.core
    def test_model_not_found_no_retry(self):
        """NotFoundError should NOT trigger retry."""
        import litellm
        with patch.object(
            litellm, "completion",
            side_effect=litellm.NotFoundError(
                message="Model not found", model="test", llm_provider="openai"
            ),
        ) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/nonexistent-model",
                max_attempts=3,
                waiting_time=0,
            )
            assert result is None
            assert mock_comp.call_count == 1

    @pytest.mark.core
    def test_rate_limit_retries(self):
        """RateLimitError should trigger retry with backoff."""
        import litellm
        rate_err = litellm.RateLimitError(
            message="Rate limit", model="test", llm_provider="openai"
        )
        with patch.object(
            litellm, "completion",
            side_effect=[rate_err, _make_mock_response("recovered")],
        ) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/gpt-4o-mini",
                max_attempts=3,
                waiting_time=0,
            )
            assert result is not None
            assert result["content"] == "recovered"
            assert mock_comp.call_count == 2

    @pytest.mark.core
    def test_timeout_retries(self):
        """Timeout should trigger retry."""
        import litellm
        timeout_err = litellm.Timeout(
            message="Request timed out", model="test", llm_provider="openai"
        )
        with patch.object(
            litellm, "completion",
            side_effect=[timeout_err, _make_mock_response("ok")],
        ) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/gpt-4o-mini",
                max_attempts=3,
                waiting_time=0,
            )
            assert result is not None
            assert mock_comp.call_count == 2

    @pytest.mark.core
    def test_empty_response_retries(self):
        """Empty/null response content should trigger retry."""
        import litellm
        with patch.object(
            litellm, "completion",
            side_effect=[_make_empty_response(), _make_mock_response("valid")],
        ) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/gpt-4o-mini",
                max_attempts=3,
                waiting_time=0,
            )
            assert result is not None
            assert result["content"] == "valid"
            assert mock_comp.call_count == 2

    @pytest.mark.core
    def test_malformed_response_returns_none(self):
        """Malformed response (empty choices) should not crash."""
        import litellm
        with patch.object(
            litellm, "completion",
            return_value=_make_malformed_response(),
        ):
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/gpt-4o-mini",
                max_attempts=1,
                waiting_time=0,
            )
            assert result is None

    @pytest.mark.core
    def test_all_retries_exhausted(self):
        """When all retries fail, should return None."""
        import litellm
        with patch.object(
            litellm, "completion",
            side_effect=litellm.APIConnectionError(
                message="Connection refused", model="test", llm_provider="openai"
            ),
        ) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            result = client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/gpt-4o-mini",
                max_attempts=2,
                waiting_time=0,
            )
            assert result is None
            assert mock_comp.call_count == 2

    @pytest.mark.core
    def test_messages_forwarded_correctly(self):
        """Verify messages list is passed through to litellm.completion."""
        import litellm
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
        ]
        with patch.object(litellm, "completion", return_value=_make_mock_response()) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            client.send_message(
                messages,
                model="openai/gpt-4o-mini",
                max_attempts=1,
                waiting_time=0,
                dedent_messages=False,
            )
            call_kwargs = mock_comp.call_args[1]
            assert call_kwargs["messages"] == messages

    @pytest.mark.core
    def test_none_params_stripped(self):
        """Verify None-valued params are excluded from the API call."""
        import litellm
        with patch.object(litellm, "completion", return_value=_make_mock_response()) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            client.send_message(
                [{"role": "user", "content": "test"}],
                model="openai/gpt-4o-mini",
                temperature=None,
                top_p=None,
                frequency_penalty=None,
                presence_penalty=None,
                max_attempts=1,
                waiting_time=0,
            )
            call_kwargs = mock_comp.call_args[1]
            assert "temperature" not in call_kwargs
            assert "top_p" not in call_kwargs
            assert "frequency_penalty" not in call_kwargs
            assert "presence_penalty" not in call_kwargs

    @pytest.mark.core
    def test_token_counter(self):
        """Verify token counting delegates to litellm."""
        import litellm
        with patch.object(litellm, "token_counter", return_value=42) as mock_tc:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            count = client._count_tokens(
                [{"role": "user", "content": "hello"}],
                "openai/gpt-4o-mini",
            )
            assert count == 42
            mock_tc.assert_called_once()

    @pytest.mark.core
    def test_import_error_message(self):
        """Verify clear error when litellm not installed."""
        import importlib
        from tinytroupe.clients import litellm_client

        original_import = __builtins__.__import__ if hasattr(__builtins__, '__import__') else __import__

        def mock_import(name, *args, **kwargs):
            if name == "litellm":
                raise ImportError("No module named 'litellm'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            importlib.reload(litellm_client)
            client = litellm_client.LiteLLMClient()
            with pytest.raises(ImportError, match="pip install"):
                client.send_message(
                    [{"role": "user", "content": "test"}],
                    model="openai/gpt-4o-mini",
                    max_attempts=1,
                    waiting_time=0,
                )

        importlib.reload(litellm_client)

    @pytest.mark.core
    def test_client_registered_in_registry(self):
        """Verify litellm client is registered and retrievable."""
        from tinytroupe.clients import _get_client_for_api_type
        client = _get_client_for_api_type("litellm")
        assert client.__class__.__name__ == "LiteLLMClient"

    @pytest.mark.core
    def test_caching_stores_and_retrieves(self):
        """Verify response caching works."""
        import litellm
        mock_resp = _make_mock_response("cached answer")
        with patch.object(litellm, "completion", return_value=mock_resp) as mock_comp:
            from tinytroupe.clients.litellm_client import LiteLLMClient
            client = LiteLLMClient()
            client.cache_api_calls = True
            client.api_cache = {}
            client.cache_file_name = "/dev/null"

            result1 = client.send_message(
                [{"role": "user", "content": "cache test"}],
                model="openai/gpt-4o-mini",
                max_attempts=1,
                waiting_time=0,
                dedent_messages=False,
            )
            result2 = client.send_message(
                [{"role": "user", "content": "cache test"}],
                model="openai/gpt-4o-mini",
                max_attempts=1,
                waiting_time=0,
                dedent_messages=False,
            )
            assert result1["content"] == "cached answer"
            assert result2["content"] == "cached answer"
            assert mock_comp.call_count == 1
