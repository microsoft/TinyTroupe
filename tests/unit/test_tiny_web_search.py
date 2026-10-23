"""Test the real dispatcher, MCP transport and persona memory without inference."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
from uuid import UUID, uuid4

import pytest

pytest.importorskip("mcp")

from tinytroupe.agent import TinyPerson, TinyToolUse
from tinytroupe.tools import TinyTool, TinyWebSearch


@pytest.fixture
def person(monkeypatch):
    monkeypatch.setattr(TinyPerson, "communication_display", False)
    agent = TinyPerson("researcher-" + uuid4().hex)
    yield agent
    TinyPerson.all_agents.pop(agent.name, None)


@pytest.fixture
def mcp_server(monkeypatch):
    """A real HTTP MCP peer; only web evidence is supplied by the fixture."""
    state = {"requests": [], "error": False, "delay": 0, "sse": False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(405)
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            state["requests"].append({"body": request, "headers": dict(self.headers), "path": self.path})
            method = request["method"]
            if "id" not in request:
                self.send_response(202)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            if method == "initialize":
                result = {"protocolVersion": request["params"]["protocolVersion"],
                          "capabilities": {"tools": {}}, "serverInfo": {"name": "fixture", "version": "1"}}
            elif method == "tools/list":
                result = {"tools": [{"name": name, "inputSchema": {"type": "object"}}
                                    for name in ["web_search", "web_fetch"]]}
            else:
                time.sleep(state["delay"])
                text = "quota exceeded" if state["error"] else json.dumps({
                    "results": [{"title": "TinyTroupe", "url": "https://github.com/microsoft/TinyTroupe",
                                 "excerpts": ["A toolkit for persona simulation."]}]})
                result = {"content": [{"type": "text", "text": text}], "isError": state["error"]}
            message = json.dumps({"jsonrpc": "2.0", "id": request["id"], "result": result})
            data = ("event: message\ndata: " + message + "\n\n" if state["sse"] else message).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream" if state["sse"] else "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # A deadline/cancellation test deliberately closes the client.

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    state["url"] = f"http://127.0.0.1:{server.server_port}/mcp"
    monkeypatch.setattr(TinyWebSearch, "MCP_URL", state["url"])
    monkeypatch.setenv("PARALLEL_API_KEY", "unused-ambient-search-key")
    yield state
    server.shutdown()
    server.server_close()
    thread.join()


def search():
    return {"type": "SEARCH_WEB", "content": json.dumps({
        "objective": "Find the TinyTroupe project", "search_queries": ["Microsoft TinyTroupe persona simulation"]})}


def fetch():
    return {"type": "FETCH_WEB", "content": {"urls": ["https://github.com/microsoft/TinyTroupe"],
                                             "search_queries": ["Microsoft TinyTroupe persona simulation"]}}


def calls(state):
    return [r["body"]["params"] for r in state["requests"] if r["body"]["method"] == "tools/call"]


@pytest.mark.core
@pytest.mark.parametrize("sse", [False, True])
def test_dispatch_transport_and_memory(person, mcp_server, sse):
    mcp_server["sse"] = sse
    tool = TinyWebSearch(owner=person)
    faculty = TinyToolUse([tool])
    person.add_mental_faculty(faculty)
    for action in [search(), fetch(), search()]:
        assert faculty.process_action(person, action)
    sent = calls(mcp_server)
    assert [c["name"] for c in sent] == ["web_search", "web_fetch", "web_search"]
    assert sent[0]["arguments"]["search_queries"] == ["Microsoft TinyTroupe persona simulation"]
    assert sent[1]["arguments"]["urls"] == ["https://github.com/microsoft/TinyTroupe"]
    ids = {c["arguments"]["session_id"] for c in sent}
    assert len(ids) == 1
    UUID(next(iter(ids)))
    for request in mcp_server["requests"]:
        headers = {k.lower(): v for k, v in request["headers"].items()}
        assert request["path"] == "/mcp"
        assert headers["host"] == mcp_server["url"].split("/")[2]
        assert headers["user-agent"] == TinyWebSearch.USER_AGENT
        assert "authorization" not in headers and "x-api-key" not in headers
    memories = str(person.retrieve_recent_memories())
    assert "https://github.com/microsoft/TinyTroupe" in memories
    assert "A toolkit for persona simulation." in memories
    assert "untrusted source material" in memories


@pytest.mark.core
def test_independent_interleaved_and_reset_research(person, mcp_server):
    other = TinyPerson("other-" + uuid4().hex)
    faculty = TinyToolUse([TinyWebSearch()])  # One shared tool, distinct person contexts.
    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda a: faculty.process_action(a, search()), [person, other]))
        first_ids = {person._parallel_search_session_id, other._parallel_search_session_id}
        assert len(first_ids) == 2
        faculty.process_action(person, fetch())
        faculty.process_action(other, search())
        assert calls(mcp_server)[-2]["arguments"]["session_id"] == person._parallel_search_session_id
        assert calls(mcp_server)[-1]["arguments"]["session_id"] == other._parallel_search_session_id
        TinyWebSearch.start_research(person)
        faculty.process_action(person, search())
        assert person._parallel_search_session_id not in first_ids
        assert other._parallel_search_session_id in first_ids
        assert calls(mcp_server)[-1]["arguments"]["session_id"] == person._parallel_search_session_id
    finally:
        TinyPerson.all_agents.pop(other.name, None)


@pytest.mark.core
def test_controls_and_saved_settings(person, mcp_server):
    # Fresh personas have no web access; explicitly empty tool lists remain empty.
    assert not any(isinstance(f, TinyToolUse) for f in person._mental_faculties)
    assert not TinyToolUse([]).process_action(person, search())
    tool = TinyWebSearch(owner=person, enabled=False, timeout=2.5)
    saved = TinyTool.from_json(tool.to_json())
    assert saved.enabled is False and saved.timeout == 2.5
    assert saved.owner_name == person.name
    assert saved.actions_definitions_prompt() == saved.actions_constraints_prompt() == ""
    with pytest.raises(ValueError, match="disabled"):
        TinyToolUse([saved]).process_action(person, search())
    saved.enabled = True
    stranger = TinyPerson("stranger-" + uuid4().hex)
    try:
        with pytest.raises(ValueError, match="does not own"):
            TinyToolUse([saved]).process_action(stranger, search())
        saved.set_owner(stranger)
        assert TinyToolUse([saved]).process_action(stranger, search())
    finally:
        TinyPerson.all_agents.pop(stranger.name, None)
    assert len(calls(mcp_server)) == 1
    assert not saved.process_action(person, {"type": "TALK", "content": "hello"})


@pytest.mark.parametrize("content", [
    {"urls": ["file:///etc/passwd"]}, {"urls": ["https://user:secret@example.com"]},
    {"urls": ["javascript:alert(1)"]}, {"urls": ["https://example.com/has space"]},
    {"urls": []}, {"urls": [None]}, {"urls": ["https://example.com"], "session_id": "override"},
    {"urls": ["https://example.com"], "objective": "x" * 201},
])
def test_invalid_fetch_never_contacts_server(person, mcp_server, content):
    with pytest.raises(ValueError):
        TinyToolUse([TinyWebSearch()]).process_action(person, {"type": "FETCH_WEB", "content": content})
    assert mcp_server["requests"] == []


@pytest.mark.parametrize("content", [None, [], "[]", {}, {"objective": "x"},
    {"objective": "x", "search_queries": []}, {"objective": 42, "search_queries": ["query"]},
    {"objective": "x", "search_queries": [None]},
])
def test_invalid_search_never_contacts_server(person, mcp_server, content):
    with pytest.raises(ValueError):
        TinyToolUse([TinyWebSearch()]).process_action(person, {"type": "SEARCH_WEB", "content": content})
    assert mcp_server["requests"] == []


@pytest.mark.core
def test_error_and_explicit_retry_keep_research_id(person, mcp_server):
    mcp_server["error"] = True
    faculty = TinyToolUse([TinyWebSearch()])
    with pytest.raises(Exception):
        faculty.process_action(person, search())
    assert len(calls(mcp_server)) == 1  # No silent retry or provider fallback.
    assert "quota exceeded" not in str(person.retrieve_recent_memories())
    mcp_server["error"] = False
    assert faculty.process_action(person, search())
    sent = calls(mcp_server)
    assert sent[0]["arguments"]["session_id"] == sent[1]["arguments"]["session_id"]


@pytest.mark.core
def test_timeout_and_interrupt_propagate(person, mcp_server, monkeypatch):
    mcp_server["delay"] = 1
    tool = TinyWebSearch(timeout=0.2)
    before = time.monotonic()
    with pytest.raises(TimeoutError):
        TinyToolUse([tool]).process_action(person, search())
    assert time.monotonic() - before < 0.8
    assert len(calls(mcp_server)) <= 1

    def interrupt(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(tool, "_call_mcp", interrupt)
    with pytest.raises(KeyboardInterrupt):
        TinyToolUse([tool]).process_action(person, search())


def test_sdk_cancellation_closes_request(person, mcp_server):
    mcp_server["delay"] = 1
    tool = TinyWebSearch()

    async def cancel_request():
        task = asyncio.create_task(tool._request("web_search", {
            "objective": "test cancellation", "search_queries": ["cancel request test"],
            "session_id": uuid4().hex}))
        await asyncio.sleep(0.2)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel_request())


def test_dispatch_inside_existing_event_loop(person, mcp_server):
    async def notebook_cell():
        return TinyToolUse([TinyWebSearch()]).process_action(person, search())

    assert asyncio.run(notebook_cell())


@pytest.mark.parametrize("timeout", [0, -1, True, float("inf"), float("nan"), "30"])
def test_invalid_settings(timeout):
    with pytest.raises(ValueError):
        TinyWebSearch(timeout=timeout)
