import pytest

from tinytroupe.agent.action_generator import ActionGenerator, ActionRefusedException
from tinytroupe.agent import TinyPerson, CognitiveActionModel


class FakeClient:
    def __init__(self, message):
        self._message = message

    def send_message(self, *args, **kwargs):
        return self._message


def test_prefers_parsed_payload(monkeypatch):
    TinyPerson.clear_agents()
    # Build a parsed payload consistent with CognitiveActionModel
    parsed = {
        "action": {"type": "THINK", "content": "test content", "target": ""},
        "cognitive_state": {
            "goals": "g",
            "context": ["c"],
            "attention": "a",
            "emotions": "e",
        },
    }

    message = {"role": "assistant", "content": "{\"action\":{}}", "parsed": parsed}

    # Patch client used by action generator to return our fake message
    from tinytroupe import openai_utils

    monkeypatch.setattr(openai_utils, "client", lambda: FakeClient(message))

    agent = TinyPerson(name="Tester")
    ag = ActionGenerator()

    action, role, content = ag._generate_tentative_action(agent, agent.current_messages)[0:3]

    assert content == parsed
    assert action == parsed["action"]
    assert role == "assistant"


def test_refusal_raises(monkeypatch):
    TinyPerson.clear_agents()
    message = {"role": "assistant", "content": "{}", "refusal": "safety refusal"}

    from tinytroupe import openai_utils

    monkeypatch.setattr(openai_utils, "client", lambda: FakeClient(message))

    agent = TinyPerson(name="Tester")
    ag = ActionGenerator()

    with pytest.raises(ActionRefusedException):
        ag._generate_tentative_action(agent, agent.current_messages)
