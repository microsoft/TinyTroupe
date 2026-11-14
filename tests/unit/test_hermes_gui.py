"""Tests for the Hermes visual conversation layer."""
import asyncio
import time

from fastapi.testclient import TestClient

import tinytroupe.ui.hermes_gui as hermes_gui
from tinytroupe.ui.hermes_gui import (
    HermesChatRequest,
    _build_prompt,
    _expressive_focus_lines,
    _run_hermes_with_screen_updates,
    create_hermes_gui_app,
)


class _FakeCompleted:
    def __init__(self, stdout: str = "ok", returncode: int = 0, stderr: str = "") -> None:
        self.stdout = stdout
        self.returncode = returncode
        self.stderr = stderr


def test_hermes_gui_endpoints(monkeypatch):
    def fake_run(cmd, capture_output, text, check):  # pragma: no cover - test stub
        return _FakeCompleted(stdout="hi from hermes")

    monkeypatch.setattr("subprocess.run", fake_run)

    app = create_hermes_gui_app()
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    matrix = client.get("/api/matrix")
    assert matrix.status_code == 200
    assert "Hermes" in matrix.text or len(matrix.text) > 0

    screen = client.get("/api/screen")
    assert screen.status_code == 200
    screen_payload = screen.json()
    assert screen_payload["frame"]["title"]
    assert screen_payload["revision"] == 0

    set_screen = client.post(
        "/api/screen",
        json={"title": "Updated", "subtitle": "test", "body_lines": ["one", "two"]},
    )
    assert set_screen.status_code == 200
    updated = set_screen.json()
    assert updated["frame"]["title"] == "Updated"
    assert updated["revision"] == 1

    followup = client.get("/api/screen")
    assert followup.json()["revision"] == 1

    reply = client.post(
        "/api/chat",
        json={
            "message": "hello",
            "mode": "chat",
            "conversation": [{"role": "user", "content": "Earlier message"}],
        },
    )
    assert reply.status_code == 200
    payload = reply.json()
    assert payload["response"] == "hi from hermes"
    assert payload["mode"] == "chat"


def test_visual_plane_filters_process_language():
    lines = _expressive_focus_lines(
        "Here is the plan: do three things\nActual signal arrives\nNext steps: more process",
        "auto",
    )
    assert lines == ["Actual signal arrives"]

    fallback = _expressive_focus_lines("Plan:\nTODO:\nPOST /api/screen", "tools")
    assert fallback == ["moving through it", "hands steady"]


def test_chat_prompt_prefers_finished_content():
    prompt = _build_prompt("improve it", [])
    assert "Answer directly with finished user-facing content" in prompt
    assert "planning/process invisible" in prompt
    assert "Reply to the latest user message in the selected mode" not in prompt


def test_turn_runner_pushes_live_screen_updates(monkeypatch):
    frames = []

    def fake_post(frame):
        frames.append(frame)

    def slow_run(prompt, mode, model, system):
        time.sleep(0.04)
        return "finished answer"

    monkeypatch.setattr(hermes_gui, "_post_screen_update", fake_post)
    monkeypatch.setattr(hermes_gui, "_run_hermes", slow_run)

    payload = HermesChatRequest(message="hello", mode="chat")
    result = asyncio.run(_run_hermes_with_screen_updates("prompt", payload, interval=0.01))

    assert result == "finished answer"
    assert len(frames) >= 2
    assert frames[0]["title"] == "Listening"
    assert any(frame["title"] in {"In motion", "Thinking", "Shaping"} for frame in frames[1:])
