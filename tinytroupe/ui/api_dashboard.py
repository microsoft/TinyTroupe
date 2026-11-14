"""TinyTroupe API Dashboard.

This module exposes a lightweight FastAPI application that allows users to
manage TinyTroupe agents through a browser-based GUI while simultaneously
providing a JSON API.  It is meant to make it easier to explore the library
without writing Python code and to serve as an integration surface for other
systems.

Typical usage::

    python -m tinytroupe.ui.api_dashboard

The command above starts an HTTP server (powered by FastAPI/Uvicorn) that can
be accessed with a browser.  From there you can load the example personas,
inspect their persona metadata, and send prompts to them.  All the underlying
operations are also available through REST endpoints, so the dashboard can be
used to orchestrate experiments from external tools.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from tinytroupe.agent import TinyPerson

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_EXAMPLES_DIR = ROOT_DIR / "examples" / "agents"
logger = logging.getLogger("tinytroupe.ui.dashboard")


class AgentCreateRequest(BaseModel):
    """Request payload for creating a new agent."""

    name: str = Field(..., description="Human-friendly agent name")
    specification_path: Optional[str] = Field(
        None,
        description=(
            "Path to a JSON specification.  Relative paths are resolved "
            "against the repository root."
        ),
    )
    specification: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "A TinyPerson specification represented as a dictionary.  "
            "If both specification and specification_path are provided, "
            "the path takes precedence."
        ),
    )
    auto_rename_agent: bool = Field(
        False,
        description=(
            "Whether to automatically rename agents when there is a "
            "conflict between the provided name and the specification."
        ),
    )


class MessageRequest(BaseModel):
    """Payload for exchanging a message with an agent."""

    message: str = Field(..., description="The text that should be delivered to the agent.")


class LoadExamplesRequest(BaseModel):
    """Payload for loading bundled example agents."""

    folder: Optional[str] = Field(
        None,
        description="Optional override for the folder that contains *.agent.json files.",
    )


def _sanitize(value: Any) -> Any:
    """Recursively convert TinyTroupe objects into JSON-serialisable data."""

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {key: _sanitize(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, (set, tuple)):
        return [_sanitize(item) for item in value]
    return str(value)


class TinyTroupeDashboard:
    """In-memory manager behind the API dashboard."""

    def __init__(
        self,
        agent_loader: Optional[Callable[..., Any]] = None,
        response_generator: Optional[Callable[[Any, str], Dict[str, Any]]] = None,
        examples_dir: Path = DEFAULT_EXAMPLES_DIR,
    ) -> None:
        self.agent_loader = agent_loader or self._load_agent_from_spec
        self.response_generator = response_generator or self._generate_agent_response
        self.examples_dir = Path(examples_dir)
        self.agents: Dict[str, Any] = {}
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}

    # ----------------------------------------------------------------------------------
    # Agent management helpers
    # ----------------------------------------------------------------------------------
    def _resolve_path(self, path: str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = ROOT_DIR / candidate
        return candidate

    def _load_agent_from_spec(
        self,
        specification_path: Optional[str] = None,
        specification: Optional[Dict[str, Any]] = None,
        name: Optional[str] = None,
        auto_rename_agent: bool = False,
    ) -> TinyPerson:
        if specification_path:
            resolved = self._resolve_path(specification_path)
            if not resolved.exists():
                raise FileNotFoundError(f"Specification not found: {resolved}")
            agent = TinyPerson.load_specification(
                str(resolved),
                auto_rename_agent=auto_rename_agent,
                new_agent_name=name,
            )
        elif specification is not None:
            agent = TinyPerson.load_specification(
                specification,
                auto_rename_agent=auto_rename_agent,
                new_agent_name=name,
            )
        else:
            raise ValueError("Either specification_path or specification must be provided.")

        # Avoid flooding stdout in server scenarios.
        TinyPerson.communication_display = False
        return agent

    def _generate_agent_response(self, agent: TinyPerson, message: str) -> Dict[str, Any]:
        agent.listen(message, source="dashboard", communication_display=False)
        actions = agent.act(
            until_done=False,
            n=1,
            return_actions=True,
            communication_display=False,
        ) or []

        response_text = ""
        if actions:
            last_action = actions[-1]
            response_text = last_action.get("action", {}).get("content", "")

        return {"response": response_text, "actions": actions}

    def _log_message(self, agent_name: str, role: str, content: str) -> None:
        if not content:
            return
        self.conversations.setdefault(agent_name, []).append(
            {
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
        )

    def create_agent(self, payload: AgentCreateRequest) -> Dict[str, Any]:
        if payload.name in self.agents:
            raise ValueError(f"Agent '{payload.name}' already exists.")

        agent = self.agent_loader(
            specification_path=payload.specification_path,
            specification=payload.specification,
            name=payload.name,
            auto_rename_agent=payload.auto_rename_agent,
        )
        self.agents[agent.name] = agent
        self.conversations.setdefault(agent.name, [])
        return self._serialize_agent(agent)

    def load_example_agents(self, folder: Optional[str] = None) -> Tuple[List[str], List[str]]:
        directory = Path(folder).expanduser() if folder else self.examples_dir
        if not directory.exists():
            raise FileNotFoundError(f"Examples folder '{directory}' does not exist.")

        created: List[str] = []
        errors: List[str] = []
        for spec_file in sorted(directory.glob("*.agent.json")):
            try:
                agent = self.agent_loader(specification_path=str(spec_file))
            except Exception as exc:  # pragma: no cover - defensive logging hook
                message = f"Failed to load example {spec_file}: {exc}"
                logger.warning(message)
                errors.append(message)
                continue

            if agent.name in self.agents:
                continue

            self.agents[agent.name] = agent
            self.conversations.setdefault(agent.name, [])
            created.append(agent.name)

        if not created and errors:
            raise RuntimeError("Unable to load example agents. " + " | ".join(errors))

        return created, errors

    def list_agents(self) -> List[Dict[str, Any]]:
        return [self._serialize_agent(agent) for agent in self.agents.values()]

    def delete_agent(self, name: str) -> None:
        if name not in self.agents:
            raise KeyError(name)
        del self.agents[name]
        self.conversations.pop(name, None)

    def get_persona(self, name: str) -> Dict[str, Any]:
        agent = self._get_agent(name)
        persona = getattr(agent, "_persona", getattr(agent, "persona", {}))
        return _sanitize(persona)

    def get_conversation(self, name: str) -> List[Dict[str, Any]]:
        if name not in self.conversations:
            raise KeyError(name)
        return list(self.conversations[name])

    def send_message(self, name: str, message: str) -> Dict[str, Any]:
        agent = self._get_agent(name)
        self._log_message(name, "user", message)
        payload = self.response_generator(agent, message)
        response_text = payload.get("response", "")
        self._log_message(name, agent.name, response_text)
        return {"response": response_text, "actions": payload.get("actions", [])}

    def _serialize_agent(self, agent: Any) -> Dict[str, Any]:
        persona = getattr(agent, "_persona", getattr(agent, "persona", {}))
        memory = {
            "episodic_entries": self._memory_count(getattr(agent, "episodic_memory", None)),
            "semantic_entries": self._memory_count(getattr(agent, "semantic_memory", None)),
        }

        return {
            "name": agent.name,
            "persona": _sanitize(persona),
            "memory": memory,
            "conversation_length": len(self.conversations.get(agent.name, [])),
        }

    def _get_agent(self, name: str) -> Any:
        try:
            return self.agents[name]
        except KeyError as exc:
            raise KeyError(f"Agent '{name}' not found.") from exc

    @staticmethod
    def _memory_count(memory_obj: Any) -> int:
        if memory_obj is None:
            return 0
        counter = getattr(memory_obj, "count", None)
        if callable(counter):
            try:
                return int(counter())
            except Exception:  # pragma: no cover - defensive
                return 0
        values = getattr(memory_obj, "memory", None)
        if isinstance(values, list):
            return len(values)
        return 0


def create_dashboard_app(manager: Optional[TinyTroupeDashboard] = None) -> FastAPI:
    """Factory that builds the FastAPI application."""

    dashboard = manager or TinyTroupeDashboard()
    app = FastAPI(title="TinyTroupe API Dashboard", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    async def root() -> HTMLResponse:
        return HTMLResponse(DASHBOARD_HTML)

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        return {"status": "ok", "agents": len(dashboard.agents)}

    @app.get("/api/agents")
    async def list_agents() -> Dict[str, Any]:
        return {"agents": dashboard.list_agents()}

    @app.post("/api/agents")
    async def create_agent(payload: AgentCreateRequest) -> Dict[str, Any]:
        if not payload.specification_path and payload.specification is None:
            raise HTTPException(status_code=400, detail="Missing specification information.")
        try:
            agent = dashboard.create_agent(payload)
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"agent": agent}

    @app.post("/api/agents/load_examples")
    async def load_examples(payload: LoadExamplesRequest) -> Dict[str, Any]:
        try:
            created, errors = dashboard.load_example_agents(payload.folder)
        except (FileNotFoundError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"loaded": created, "errors": errors}

    @app.delete("/api/agents/{agent_name}")
    async def delete_agent(agent_name: str) -> Dict[str, Any]:
        try:
            dashboard.delete_agent(agent_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"deleted": agent_name}

    @app.get("/api/agents/{agent_name}/persona")
    async def get_persona(agent_name: str) -> Dict[str, Any]:
        try:
            persona = dashboard.get_persona(agent_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"persona": persona}

    @app.get("/api/agents/{agent_name}/conversation")
    async def get_conversation(agent_name: str) -> Dict[str, Any]:
        try:
            history = dashboard.get_conversation(agent_name)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"history": history}

    @app.post("/api/agents/{agent_name}/message")
    async def send_message(agent_name: str, payload: MessageRequest) -> Dict[str, Any]:
        try:
            response = dashboard.send_message(agent_name, payload.message)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return response

    return app


def run_dashboard(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Launch the dashboard using uvicorn."""

    import uvicorn  # Imported lazily to keep import time low.

    app = create_dashboard_app()
    uvicorn.run(app, host=host, port=port)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>TinyTroupe API Dashboard</title>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; background: #f5f6fa; color: #222; }
    header { background: #2b2d42; color: #fff; padding: 20px; }
    header h1 { margin: 0; font-size: 1.8rem; }
    header p { margin: 4px 0 0; color: #d9e4ff; }
    main { padding: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
    section { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); }
    h2 { margin-top: 0; }
    label { display: block; font-size: 0.9rem; margin-bottom: 4px; font-weight: 600; }
    input, textarea, select, button { width: 100%; margin-bottom: 12px; padding: 8px; border-radius: 4px; border: 1px solid #ccc; font-family: inherit; }
    textarea { min-height: 120px; }
    button { background: #2b2d42; color: #fff; border: none; cursor: pointer; font-weight: 600; }
    button.secondary { background: #8d99ae; }
    .agents-list { max-height: 320px; overflow-y: auto; }
    .agent-card { border: 1px solid #e0e0e0; border-radius: 6px; padding: 10px; margin-bottom: 10px; }
    .agent-card h3 { margin: 0 0 4px; }
    .pill { display: inline-block; padding: 2px 6px; border-radius: 10px; background: #edf2f4; margin-right: 4px; font-size: 0.75rem; }
    #conversation-log { max-height: 360px; overflow-y: auto; background: #0d1b2a; color: #edf2f4; padding: 12px; border-radius: 8px; }
    .message { margin-bottom: 12px; }
    .message strong { color: #5ac8fa; }
    .status { margin: 0 0 12px; font-size: 0.9rem; color: #2b2d42; }
    .error { color: #d90429; }
  </style>
</head>
<body>
  <header>
    <h1>TinyTroupe API Dashboard</h1>
    <p>Manage agents and interact with them via a friendly GUI. All actions are backed by REST APIs.</p>
  </header>
  <main>
    <section>
      <h2>Load Agents</h2>
      <p class=\"status\" id=\"load-status\"></p>
      <button id=\"load-examples\">Load bundled examples</button>
      <form id=\"create-agent-form\">
        <label for=\"agent-name\">Agent name</label>
        <input id=\"agent-name\" name=\"name\" placeholder=\"e.g., CustomPersona\" required>
        <label for=\"spec-path\">Specification path</label>
        <input id=\"spec-path\" name=\"specification_path\" placeholder=\"examples/agents/Oscar.agent.json\">
        <label for=\"spec-json\">Specification JSON (optional)</label>
        <textarea id=\"spec-json\" name=\"specification\" placeholder=\"{\n  \"name\": \"CustomPersona\"\n}\"></textarea>
        <label><input type=\"checkbox\" id=\"auto-rename\"> Auto rename on conflict</label>
        <button type=\"submit\">Create agent</button>
      </form>
    </section>
    <section>
      <h2>Agents</h2>
      <div class=\"agents-list\" id=\"agents-list\"></div>
      <button class=\"secondary\" id=\"refresh-agents\">Refresh list</button>
    </section>
    <section>
      <h2>Conversation</h2>
      <label for=\"agent-selector\">Select agent</label>
      <select id=\"agent-selector\"></select>
      <div id=\"conversation-log\"></div>
      <form id=\"message-form\">
        <label for=\"message-input\">Message</label>
        <textarea id=\"message-input\" placeholder=\"Ask something...\" required></textarea>
        <button type=\"submit\">Send</button>
      </form>
      <p class=\"status\" id=\"message-status\"></p>
    </section>
  </main>
  <script>
    const agentsList = document.getElementById('agents-list');
    const agentSelector = document.getElementById('agent-selector');
    const conversationLog = document.getElementById('conversation-log');
    const loadStatus = document.getElementById('load-status');
    const messageStatus = document.getElementById('message-status');

    async function fetchJSON(url, options = {}) {
      const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
      if (!response.ok) {
        const details = await response.json().catch(() => ({}));
        throw new Error(details.detail || response.statusText);
      }
      return response.json();
    }

    function renderAgents(agents) {
      agentsList.innerHTML = '';
      agentSelector.innerHTML = '';
      agents.forEach(agent => {
        const wrapper = document.createElement('div');
        wrapper.className = 'agent-card';
        wrapper.innerHTML = `
          <h3>${agent.name}</h3>
          <p><strong>Memories:</strong> Episodic ${agent.memory.episodic_entries}, Semantic ${agent.memory.semantic_entries}</p>
          <div>${Object.entries(agent.persona || {}).map(([k, v]) => `<span class=\"pill\">${k}: ${v}</span>`).join(' ')}</div>
        `;
        agentsList.appendChild(wrapper);

        const option = document.createElement('option');
        option.value = agent.name;
        option.textContent = agent.name;
        agentSelector.appendChild(option);
      });
    }

    function renderConversation(history) {
      if (!history.length) {
        conversationLog.innerHTML = '<p>No messages yet.</p>';
        return;
      }
      conversationLog.innerHTML = history.map(entry => `
        <div class=\"message\"><strong>${entry.role}</strong> <small>${entry.timestamp}</small><br>${entry.content}</div>
      `).join('');
    }

    async function refreshAgents() {
      try {
        const { agents } = await fetchJSON('/api/agents');
        renderAgents(agents);
        if (agents.length) {
          agentSelector.value = agents[0].name;
          refreshConversation();
        } else {
          conversationLog.innerHTML = '<p>Load or create an agent to start chatting.</p>';
        }
      } catch (error) {
        agentsList.innerHTML = `<p class='error'>${error.message}</p>`;
      }
    }

    async function refreshConversation() {
      const selected = agentSelector.value;
      if (!selected) return;
      try {
        const { history } = await fetchJSON(`/api/agents/${encodeURIComponent(selected)}/conversation`);
        renderConversation(history);
      } catch (error) {
        conversationLog.innerHTML = `<p class='error'>${error.message}</p>`;
      }
    }

    document.getElementById('refresh-agents').addEventListener('click', async () => {
      try {
        await refreshAgents();
      } catch (error) {
        loadStatus.textContent = error.message;
        loadStatus.classList.add('error');
      }
    });

    document.getElementById('load-examples').addEventListener('click', async () => {
      loadStatus.textContent = 'Loading examples...';
      try {
        const data = await fetchJSON('/api/agents/load_examples', { method: 'POST', body: JSON.stringify({}) });
        loadStatus.textContent = `Loaded ${data.loaded.length} agents.`;
        if (data.errors && data.errors.length) {
          loadStatus.textContent += ` ${data.errors.length} file(s) skipped.`;
        }
        loadStatus.classList.remove('error');
        await refreshAgents();
      } catch (error) {
        loadStatus.textContent = error.message;
        loadStatus.classList.add('error');
      }
    });

    document.getElementById('create-agent-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const form = event.target;
      let specification = null;
      if (form.specification.value) {
        try {
          specification = JSON.parse(form.specification.value);
        } catch (error) {
          loadStatus.textContent = 'Invalid JSON specification.';
          loadStatus.classList.add('error');
          return;
        }
      }
      const payload = {
        name: form.name.value,
        specification_path: form.specification_path.value || null,
        specification,
        auto_rename_agent: document.getElementById('auto-rename').checked,
      };
      loadStatus.textContent = 'Creating agent...';
      try {
        await fetchJSON('/api/agents', { method: 'POST', body: JSON.stringify(payload) });
        loadStatus.textContent = 'Agent created.';
        loadStatus.classList.remove('error');
        form.reset();
        await refreshAgents();
      } catch (error) {
        loadStatus.textContent = error.message;
        loadStatus.classList.add('error');
      }
    });

    agentSelector.addEventListener('change', refreshConversation);

    document.getElementById('message-form').addEventListener('submit', async (event) => {
      event.preventDefault();
      const message = document.getElementById('message-input').value;
      const agentName = agentSelector.value;
      if (!agentName) {
        messageStatus.textContent = 'Select an agent first.';
        messageStatus.classList.add('error');
        return;
      }
      messageStatus.textContent = 'Sending message...';
      try {
        await fetchJSON(`/api/agents/${encodeURIComponent(agentName)}/message`, {
          method: 'POST',
          body: JSON.stringify({ message })
        });
        document.getElementById('message-input').value = '';
        messageStatus.textContent = 'Response received.';
        messageStatus.classList.remove('error');
        await refreshConversation();
      } catch (error) {
        messageStatus.textContent = error.message;
        messageStatus.classList.add('error');
      }
    });

    refreshAgents();
  </script>
</body>
</html>
"""


if __name__ == "__main__":  # pragma: no cover - convenience entry point
    run_dashboard()
