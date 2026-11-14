"""Tests for the FastAPI dashboard helper."""
from fastapi.testclient import TestClient

from tinytroupe.ui.api_dashboard import (
    AgentCreateRequest,
    MessageRequest,
    TinyTroupeDashboard,
    create_dashboard_app,
)


class _DummyMemory:
    def __init__(self) -> None:
        self._count = 0

    def count(self) -> int:  # pragma: no cover - trivial
        return self._count


class _DummyAgent:
    def __init__(self, name: str) -> None:
        self.name = name
        self._persona = {"name": name, "occupation": "Tester"}
        self.episodic_memory = _DummyMemory()
        self.semantic_memory = _DummyMemory()
        self._last_message = ""

    def listen(self, message: str, **_kwargs) -> None:  # pragma: no cover - trivial
        self._last_message = message

    def act(self, **_kwargs):  # pragma: no cover - deterministic stub
        return [
            {
                "action": {
                    "type": "SPEAK",
                    "content": f"Echo: {self._last_message}",
                    "target": "user",
                }
            }
        ]


def _loader(**kwargs):  # pragma: no cover - helper for dependency injection
    name = kwargs.get("name") or "Stub"
    return _DummyAgent(name)


def test_dashboard_create_and_converse():
    dashboard = TinyTroupeDashboard(agent_loader=_loader)
    request = AgentCreateRequest(name="Ada", specification={"name": "Ada"})
    agent = dashboard.create_agent(request)

    assert agent["name"] == "Ada"
    assert dashboard.list_agents()[0]["name"] == "Ada"

    reply = dashboard.send_message("Ada", "Hello!")
    assert "Echo: Hello!" in reply["response"]

    history = dashboard.get_conversation("Ada")
    assert len(history) == 2  # user + agent


class _StubManager:
    def __init__(self) -> None:
        self.agents = {}

    def list_agents(self):
        return [{"name": "Stub", "persona": {}, "memory": {}, "conversation_length": 0}]

    def create_agent(self, payload):
        self.agents[payload.name] = payload.name
        return {"name": payload.name, "persona": {}, "memory": {}, "conversation_length": 0}

    def load_example_agents(self, _folder=None):
        return (["Stub"], [])

    def delete_agent(self, name):
        self.agents.pop(name, None)

    def get_persona(self, _name):
        return {"name": "Stub"}

    def get_conversation(self, _name):
        return []

    def send_message(self, name, message):
        if name not in self.agents:
            raise KeyError
        return {"response": message.upper(), "actions": []}


def test_fastapi_routes_expose_manager():
    app = create_dashboard_app(manager=_StubManager())
    client = TestClient(app)

    assert client.get("/health").json()["status"] == "ok"

    response = client.post(
        "/api/agents",
        json={"name": "beta", "specification": {"name": "beta"}},
    )
    assert response.status_code == 200

    response = client.post(
        "/api/agents/beta/message",
        json=MessageRequest(message="ping").model_dump(),
    )
    assert response.status_code == 200
    assert response.json()["response"] == "PING"
