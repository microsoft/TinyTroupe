"""Offline tests for per-person action sampling temperature."""

import json
from unittest.mock import Mock, patch

import pytest

from tinytroupe.agent import TinyPerson
from tinytroupe.agent.action_generator import ActionGenerator


@pytest.fixture(autouse=True)
def clear_agents():
    TinyPerson.all_agents.clear()
    yield
    TinyPerson.all_agents.clear()


@pytest.mark.parametrize("reasoning", [False, True])
def test_action_uses_each_persons_temperature_and_preserves_global_fallback(reasoning):
    generator = ActionGenerator(
        enable_reasoning_step=reasoning,
        enable_multi_action_output=False,
    )
    response = {
        "role": "assistant",
        "content": json.dumps({"action": {"type": "DONE", "content": "", "target": ""}}),
    }
    fake_client = Mock()
    fake_client.send_message.return_value = response

    with patch("tinytroupe.agent.action_generator.client", return_value=fake_client):
        for name, temperature in [("Careful", 0.0), ("Creative", 1.2), ("Default", None)]:
            agent = TinyPerson(name, temperature=temperature)
            generator._generate_tentative_action(
                agent, [{"role": "user", "content": "Hello"}]
            )
            kwargs = fake_client.send_message.call_args.kwargs
            if temperature is None:
                assert "temperature" not in kwargs
            else:
                assert kwargs["temperature"] == temperature


def test_temperature_survives_specification_round_trip_and_old_specs():
    original = TinyPerson("Saved", temperature=0.4)
    specification = original.to_json(serialization_type_field_name="type")
    assert specification["temperature"] == 0.4

    TinyPerson.all_agents.clear()
    restored = TinyPerson.load_specification(specification)
    assert restored.temperature == 0.4

    TinyPerson.all_agents.clear()
    specification.pop("temperature")
    legacy = TinyPerson.load_specification(specification)
    assert legacy.temperature is None
