import types
from unittest.mock import patch

import tinytroupe.openai_utils as openai_utils


class _StubResponsesClient:
    def __init__(self):
        self.last_params = None

    class _Responses:
        def __init__(self, outer):
            self._outer = outer

        def create(self, **kwargs):
            # Capture params for assertions
            self._outer.last_params = kwargs

            # Return minimal object with output_text like the SDK does
            return types.SimpleNamespace(output_text="ok")

    @property
    def responses(self):
        return _StubResponsesClient._Responses(self)


def test_send_message_uses_responses_api_when_api_mode_is_responses():
    stub = _StubResponsesClient()

    # Patch setup to force responses mode and inject stub client
    original_setup = openai_utils.OpenAIClient._setup_from_config

    def _setup_with_responses(self):
        self.client = stub
        self.api_mode = "responses"

    try:
        openai_utils.OpenAIClient._setup_from_config = _setup_with_responses

        client = openai_utils.OpenAIClient()

        messages = [
            {"role": "system", "content": "You are terse."},
            {"role": "user", "content": "Say ok."},
        ]

        result = client.send_message(
            current_messages=messages,
            model="gpt-4.1-mini",
            temperature=0.2,
            max_tokens=128,
        )

        # Verify mapping to Responses API
        assert stub.last_params is not None
        assert stub.last_params.get("model") == "gpt-4.1-mini"
        assert stub.last_params.get("temperature") == 0.2
        assert stub.last_params.get("max_output_tokens") == 128

        input_msgs = stub.last_params.get("input")
        assert isinstance(input_msgs, list) and len(input_msgs) == 2
        assert input_msgs[0]["role"] == "system"
        assert input_msgs[1]["role"] == "user"
        assert input_msgs[1]["content"][0]["text"] == "Say ok."

        # Verify extractor returns assistant content
        assert result["content"].lower().startswith("ok")

    finally:
        openai_utils.OpenAIClient._setup_from_config = original_setup


