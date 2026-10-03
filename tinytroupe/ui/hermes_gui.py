"""Hermes visual conversation layer.

This module exposes a lightweight local-only web UI that talks to the root
`hermes` launcher and gives you a second, more visual communication layer.

Usage:
    python -m tinytroupe.ui.hermes_gui

The app is intentionally simple: it keeps the conversation in the browser,
formats the transcript into a prompt, and sends it to the local Hermes CLI.
"""
from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

ROOT_DIR = Path(__file__).resolve().parents[2]
HERMES_CLI = ROOT_DIR / "hermes"
MATRIX_PATH = ROOT_DIR / "local-hermes" / "personality-matrix.md"
LOCAL_HERMES_DIR = ROOT_DIR / "local-hermes"
logger = logging.getLogger("tinytroupe.ui.hermes_gui")

MODES: List[Literal["auto", "chat", "plan", "tools", "reason"]] = [
    "auto",
    "chat",
    "plan",
    "tools",
    "reason",
]


class HermesTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class HermesChatRequest(BaseModel):
    message: str = Field(..., description="Latest user message")
    mode: Literal["auto", "chat", "plan", "tools", "reason"] = "auto"
    model: Optional[str] = Field(
        None,
        description="Optional explicit Ollama model tag. Usually leave blank.",
    )
    system: Optional[str] = Field(
        None,
        description="Optional extra system instructions added to the Hermes matrix.",
    )
    conversation: List[HermesTurn] = Field(
        default_factory=list,
        description="Conversation history that the UI maintains in the browser.",
    )


class HermesChatResponse(BaseModel):
    response: str
    mode: str
    model: Optional[str] = None
    prompt_preview: str


class HermesScreenFrame(BaseModel):
    title: str = "Hermes Screen"
    subtitle: str = "idle"
    mode: str = "auto"
    model: Optional[str] = None
    accent: str = "#7aa2ff"
    glyph: str = "◉"
    expression: str = "attentive"
    scene: str = "presence"
    situation: str = ""
    anchor: str = ""
    pressure: str = ""
    objective: str = "holding the thread"
    implication: str = "keeping the useful part visible"
    next_step: str = "ready for the next signal"
    need_from_user: str = "say what matters most"
    body_lines: List[str] = Field(default_factory=list)
    cards: List[Dict[str, str]] = Field(default_factory=list)
    image_url: Optional[str] = None
    image_alt: str = ""
    footer: str = "local-only"
    updated_at: str = ""
    skipped: bool = False


DEFAULT_SCREEN_FRAME = HermesScreenFrame(
    title="With you",
    subtitle="11:07 PM · refactor open · left: companion / right: stage",
    mode="auto",
    accent="#7aa2ff",
    glyph="✦",
    expression="attentive",
    scene="presence",
    situation="Mac Studio M2 Max · TinyTroupe refactor",
    anchor="the current line is still moving",
    pressure="the wording keeps drifting toward brochure-clean",
    objective="cut the exact fake phrase",
    implication="keep the machine, repo, and wording in contact",
    next_step="show me the line that slips",
    need_from_user="point at the dead phrase",
    body_lines=[
        "The editor is open on the Mac Studio, and the line in front of us keeps reaching for the safe word instead of the exact one.",
        "TinyTroupe is open, the live GUI is open, and the problem is the copy going smooth where it should bite.",
        "If the sentence cannot point to the snag, it is still hiding behind glass.",
    ],
    cards=[
        {"label": "room", "value": "Mac Studio M2 Max · live GUI"},
        {"label": "snag", "value": "brochure-clean phrasing"},
        {"label": "contact", "value": "the line loses the thing"},
        {"label": "cut", "value": "point at the dead phrase"},
    ],
    footer="live",
)

_SCREEN_FRAME = DEFAULT_SCREEN_FRAME.model_dump()
_SCREEN_REVISION = 0
_SCREEN_SUBSCRIBERS: set[asyncio.Queue[str]] = set()
_SCREEN_WEBSOCKETS: set[WebSocket] = set()
PAGE_VERSION = "2026-05-10-ws2"


@dataclass
class HermesStatus:
    launcher_exists: bool
    matrix_exists: bool
    local_hermes_dir_exists: bool


def _read_matrix_excerpt(limit: int = 1600) -> str:
    if not MATRIX_PATH.exists():
        return "TinyTroupe-inspired matrix not found."
    text = MATRIX_PATH.read_text(encoding="utf-8")
    return text[:limit].strip()


def _build_prompt(message: str, conversation: List[HermesTurn]) -> str:
    lines = [
        "Conversation rules:",
        "- Answer directly with finished user-facing content.",
        "- Answer like a real person with a point of view, not a customer-support bot with a checklist.",
        "- Replace abstractions with concrete nouns, actions, textures, failures, or named things from the user's wording.",
        "- Lead with the situation: what is happening right now in the room, the code, or the machine.",
        "- Do not summarize the vibe when you can name the object, the snag, the movement, or the line that changed.",
        "- Connect the pieces: who, where, what changed, and what the consequence is should feel tied together in the same sentence flow.",
        "- Prefer words with weight: burr, seam, hinge, drag, residue, scar, knot, notch, crack, splice, grit.",
        "- Do not use boilerplate such as 'I understand', 'certainly', 'here is the plan', 'next steps', or generic filler about being helpful.",
        "- Keep the answer sharp enough that a third party can picture the scene, the snag, or the object being discussed.",
        "- Use uneven, human sentence rhythm when it fits; avoid every line sounding like it came from the same mold.",
        "- Stay concise unless the user asks for detail.",
        "- Use local grounding when the request is about this machine or repo.",
        "",
        "Conversation so far:",
    ]

    for turn in conversation[-20:]:
        label = "User" if turn.role == "user" else "Hermes"
        lines.append(f"{label}: {turn.content}")

    lines.extend([
        "",
        "Latest user message:",
        message,
        "",
        "Reply directly. Put substance first; keep planning/process invisible unless explicitly requested.",
    ])
    return "\n".join(lines)


def _mode_visual(mode: str) -> Dict[str, Any]:
    visuals = {
        "tools": {
            "title": "Hands on it",
            "subtitle": "the machine is moving",
            "accent": "#6be7c8",
            "glyph": "✦",
            "expression": "working",
            "scene": "operating",
            "card": "doing the cut",
            "body": ["tool in hand", "result under tension"],
            "brief": "what changed, what remains",
        },
        "plan": {
            "title": "Tracing the ridge",
            "subtitle": "where this gets real",
            "accent": "#7aa2ff",
            "glyph": "◇",
            "expression": "thinking",
            "scene": "shaping",
            "card": "finding the ridge",
            "body": ["path in view", "decision still open"],
            "brief": "shape the next move",
        },
        "reason": {
            "title": "Working the grain",
            "subtitle": "pulling signal from clutter",
            "accent": "#ffcd70",
            "glyph": "◈",
            "expression": "thinking",
            "scene": "focusing",
            "card": "cutting through noise",
            "body": ["signal under load", "noise getting sorted"],
            "brief": "separate the inference from the theater",
        },
        "chat": {
            "title": "Cutting to the nerve",
            "subtitle": "speaking to you, not at you",
            "accent": "#9ef0c4",
            "glyph": "●",
            "expression": "attentive",
            "scene": "listening",
            "card": "speaking plain",
            "body": ["hold your meaning", "answer without varnish"],
            "brief": "speak like a person who means it",
        },
        "auto": {
            "title": "Holding the room",
            "subtitle": "listening for friction",
            "accent": "#a88cff",
            "glyph": "✧",
            "expression": "attentive",
            "scene": "present",
            "card": "staying close",
            "body": ["close enough to catch the snag", "quiet enough to hear the edge"],
            "brief": "stay near the useful roughness",
        },
    }
    return visuals.get(mode, visuals["auto"])


def _screen_frame_for_turn(
    *,
    mode: str,
    model: Optional[str],
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    body_lines: Optional[List[str]] = None,
    cards: Optional[List[Dict[str, str]]] = None,
    expression: Optional[str] = None,
    glyph: Optional[str] = None,
    scene: Optional[str] = None,
    accent: Optional[str] = None,
    objective: Optional[str] = None,
    implication: Optional[str] = None,
    next_step: Optional[str] = None,
    need_from_user: Optional[str] = None,
) -> Dict[str, Any]:
    visual = _mode_visual(mode)
    return {
        "title": title or visual["title"],
        "subtitle": subtitle or visual["subtitle"],
        "mode": mode,
        "model": model,
        "accent": accent or visual["accent"],
        "glyph": glyph or visual["glyph"],
        "expression": expression or visual["expression"],
        "scene": scene or visual["scene"],
        "objective": objective or "keep the rough edge visible",
        "implication": implication or "don’t sand the meaning flat",
        "next_step": next_step or "point at the part that feels dead",
        "need_from_user": need_from_user or "show me the knot, not the wallpaper",
        "body_lines": body_lines or ["I’m listening for the place where the words start to snag.", "If it goes soft or generic, I should cut closer to the nerve."],
        "cards": cards or [
            {"label": "grain", "value": "keep the scratch"},
            {"label": "pressure", "value": "don’t polish away the friction"},
            {"label": "ask", "value": "show me the knot"},
        ],
        "footer": "live",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "skipped": False,
    }


def _dense_screen_pack(
    *,
    mode: str,
    model: Optional[str],
    title: str,
    subtitle: str,
    body: str,
    response_text: Optional[str] = None,
    user_text: Optional[str] = None,
    signal: Optional[str] = None,
    footer: str = "live",
    accent: Optional[str] = None,
    glyph: Optional[str] = None,
    expression: Optional[str] = None,
    scene: Optional[str] = None,
) -> Dict[str, Any]:
    visual = _mode_visual(mode)
    body_lines = [line.strip() for line in body.split("\n") if line.strip()][:4]
    user_excerpt = (user_text or "").strip()
    response_excerpt = (response_text or "").strip()
    objective = {
        "tools": "apply the tool, then report the useful result",
        "plan": "shape a clear path without fog",
        "reason": "separate signal from noise",
        "chat": "hold the thread and answer cleanly",
        "auto": "stay with you and keep the thread alive",
    }.get(mode, "stay with you and keep the thread alive")
    implication = {
        "tools": "you get a concrete artifact or action",
        "plan": "you can see the structure before committing",
        "reason": "you get the inference, not the theater",
        "chat": "the reply should feel direct and human",
        "auto": "the surface stays alive while work happens",
    }.get(mode, "the surface stays alive while work happens")
    next_step = response_excerpt[:64] or "I’m still shaping the reply"
    need_from_user = user_excerpt[:64] or "say what matters most"
    cards = [
        {"label": "signal", "value": signal or visual["card"]},
        {"label": "you said", "value": user_excerpt[:52] or "—"},
        {"label": "I answered", "value": response_excerpt[:52] or "—"},
    ]
    return _screen_frame_for_turn(
        mode=mode,
        model=model,
        title=title,
        subtitle=subtitle,
        body_lines=body_lines,
        cards=cards,
        expression=expression or visual["expression"],
        glyph=glyph or visual["glyph"],
        scene=scene or visual["scene"],
        accent=accent or visual["accent"],
        objective=objective,
        implication=implication,
        next_step=next_step,
        need_from_user=need_from_user,
    )


_TURN_PULSES = [
    ("Listening", "open channel", ["your words landed", "holding focus"], ["open", "awake", "near"], "attentive", "●"),
    ("In motion", "quiet current", ["signal gathered", "the thread stays warm"], ["moving", "steady", "near"], "working", "✦"),
    ("Thinking", "deep focus", ["connections forming", "noise falling away"], ["focusing", "clear", "awake"], "thinking", "◈"),
    ("Shaping", "almost there", ["the answer is taking shape", "attention stays with you"], ["shaping", "steady", "near"], "working", "◇"),
]


async def _run_hermes_with_screen_updates(
    prompt: str,
    payload: HermesChatRequest,
    interval: float = 1.15,
) -> str:
    task = asyncio.create_task(asyncio.to_thread(_run_hermes, prompt, payload.mode, payload.model, payload.system))

    _post_screen_update(
        _dense_screen_pack(
            mode=payload.mode,
            model=payload.model,
            title="Listening",
            subtitle="open channel",
            body=f"your words landed\nholding focus\n{payload.message[:72]}",
            user_text=payload.message,
            signal="open",
            expression="attentive",
            glyph="●",
            scene="presence",
        )
    )

    pulse_index = 0
    while not task.done():
        await asyncio.sleep(interval)
        if task.done():
            break
        title, subtitle, body_lines, card_values, expression, glyph = _TURN_PULSES[pulse_index % len(_TURN_PULSES)]
        _post_screen_update(
            _dense_screen_pack(
                mode=payload.mode,
                model=payload.model,
                title=title,
                subtitle=subtitle,
                body="\n".join(body_lines),
                signal=card_values[0],
                response_text=" / ".join(card_values[1:]),
                user_text=payload.message,
                expression=expression,
                glyph=glyph,
                scene="working through the turn",
            )
        )
        pulse_index += 1

    response_text = await task
    final_summary = _expressive_focus_lines(response_text, payload.mode, max_lines=3)
    _post_screen_update(
        _dense_screen_pack(
            mode=payload.mode,
            model=payload.model,
            title=_mode_visual(payload.mode)["title"],
            subtitle="complete",
            body="\n".join(final_summary),
            response_text=response_text,
            user_text=payload.message,
            signal="done",
            expression="happy done",
            glyph="✓",
            scene="answer delivered",
        )
    )
    return response_text




def _screen_defaults() -> Dict[str, Any]:
    return DEFAULT_SCREEN_FRAME.model_dump()


def _screen_from_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    frame = _screen_defaults()
    frame.update({k: v for k, v in payload.items() if k in frame})
    if not isinstance(frame.get("body_lines"), list):
        frame["body_lines"] = [str(frame.get("body_lines", ""))]
    frame["body_lines"] = [str(line)[:160] for line in frame["body_lines"][:10]]

    cards = frame.get("cards", [])
    if not isinstance(cards, list):
        cards = []
    cleaned_cards: List[Dict[str, str]] = []
    for card in cards[:6]:
        if isinstance(card, dict):
            cleaned_cards.append({
                "label": str(card.get("label", ""))[:28],
                "value": str(card.get("value", ""))[:90],
            })
        else:
            cleaned_cards.append({"label": "note", "value": str(card)[:90]})
    frame["cards"] = cleaned_cards

    frame["subtitle"] = str(frame.get("subtitle", ""))[:64]
    frame["title"] = str(frame.get("title", ""))[:64]
    frame["footer"] = str(frame.get("footer", ""))[:64]
    frame["glyph"] = str(frame.get("glyph", "◉"))[:4]
    frame["expression"] = str(frame.get("expression", "attentive"))[:32]
    frame["scene"] = str(frame.get("scene", "presence"))[:32]
    frame["objective"] = str(frame.get("objective", "holding the thread"))[:72]
    frame["implication"] = str(frame.get("implication", "keeping the useful part visible"))[:96]
    frame["next_step"] = str(frame.get("next_step", "ready for the next signal"))[:96]
    frame["need_from_user"] = str(frame.get("need_from_user", "say what matters most"))[:96]
    frame["image_alt"] = str(frame.get("image_alt", ""))[:120]
    image_url = frame.get("image_url")
    frame["image_url"] = str(image_url)[:2000] if image_url else None
    frame["mode"] = str(frame.get("mode", "auto"))
    frame["updated_at"] = str(frame.get("updated_at", ""))
    frame["accent"] = str(frame.get("accent", "#7aa2ff"))
    frame["model"] = frame.get("model") or None
    frame["skipped"] = bool(frame.get("skipped", False))
    return frame


def _summarize_for_screen(text: str, width: int = 18, max_lines: int = 4) -> List[str]:
    words = text.replace("\n", " ").split()
    if not words:
        return ["(empty)"]
    lines: List[str] = []
    current: List[str] = []
    current_len = 0
    for word in words:
        if current_len + len(word) + (1 if current else 0) > width:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += len(word) + (1 if current_len else 0)
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(" ".join(current))
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    return lines or ["(empty)"]



_META_PREFIXES = (
    "i will ",
    "i'll ",
    "here is the plan",
    "here's the plan",
    "next steps",
    "plan:",
    "approach:",
    "analysis:",
    "thinking:",
    "todo:",
    "checklist:",
    "step ",
)


def _expressive_focus_lines(text: str, mode: str, max_lines: int = 2) -> List[str]:
    """Extract compact, user-facing screen text without exposing plans/process."""
    cleaned: List[str] = []
    for raw_line in text.replace("\r", "\n").split("\n"):
        line = raw_line.strip(" -*#\t")
        if not line:
            continue
        lower = line.lower()
        if any(lower.startswith(prefix) for prefix in _META_PREFIXES):
            continue
        if " /api/" in lower or "post /" in lower or "debug" in lower:
            continue
        cleaned.append(line)
        if len(cleaned) >= max_lines:
            break

    if cleaned:
        return [line[:96] for line in cleaned]

    fallback = {
        "tools": ["moving through it", "hands steady"],
        "plan": ["shape emerging", "the path is clean"],
        "reason": ["focus deepens", "signal over noise"],
        "chat": ["listening", "the thread is held"],
        "auto": ["with you", "quiet attention"],
    }.get(mode, ["with you", "quiet attention"])
    return fallback[:max_lines]


def _post_screen_update(frame: Dict[str, Any]) -> None:
    global _SCREEN_FRAME, _SCREEN_REVISION
    _SCREEN_FRAME = _screen_from_payload(frame)
    _SCREEN_REVISION += 1
    _broadcast_screen_update()


def _screen_payload() -> Dict[str, Any]:
    return {"frame": _SCREEN_FRAME, "revision": _SCREEN_REVISION}


def _screen_event(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def _push_screen_update(payload: Dict[str, Any]) -> None:
    message = json.dumps(payload, ensure_ascii=False)
    stale: List[WebSocket] = []
    for websocket in list(_SCREEN_WEBSOCKETS):
        try:
            await websocket.send_text(message)
        except Exception:
            stale.append(websocket)
    for websocket in stale:
        _SCREEN_WEBSOCKETS.discard(websocket)


def _broadcast_screen_update() -> None:
    payload = _screen_payload()
    payload_json = json.dumps(payload, ensure_ascii=False)
    sse_payload = f"data: {payload_json}\n\n"
    for queue in list(_SCREEN_SUBSCRIBERS):
        try:
            queue.put_nowait(sse_payload)
        except asyncio.QueueFull:
            continue

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return

    loop.create_task(_push_screen_update(payload))


def _hermes_command(prompt: str, mode: str, model: Optional[str], system: Optional[str]) -> List[str]:
    cli = HERMES_CLI if HERMES_CLI.exists() else (LOCAL_HERMES_DIR / "hermes")
    if not cli.exists():
        raise FileNotFoundError(f"Hermes launcher not found at {cli}")

    command = [str(cli)]
    if mode and mode != "auto":
        command.extend(["--mode", mode])
    if model:
        command.extend(["--model", model])
    if system:
        command.extend(["--system", system])
    command.append(prompt)
    return command


def _run_hermes(prompt: str, mode: str, model: Optional[str], system: Optional[str]) -> str:
    command = _hermes_command(prompt, mode, model, system)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        detail = stderr or stdout or f"Hermes CLI failed with exit code {completed.returncode}"
        raise RuntimeError(detail)
    return completed.stdout.strip()


def _run_hermes_streaming(prompt: str, mode: str, model: Optional[str], system: Optional[str]):
    command = _hermes_command(prompt, mode, model, system)
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []
    assert proc.stdout is not None
    assert proc.stderr is not None

    while True:
        line = proc.stdout.readline()
        if line:
            stdout_lines.append(line)
            yield "stdout", line.rstrip("\n")
        elif proc.poll() is not None:
            break
        else:
            time.sleep(0.05)

    stderr_text = proc.stderr.read() or ""
    if stderr_text:
        stderr_lines.append(stderr_text)
        yield "stderr", stderr_text.strip()

    returncode = proc.wait()
    stdout_text = "".join(stdout_lines).strip()
    stderr_text = "".join(stderr_lines).strip()
    if returncode != 0:
        raise RuntimeError(stderr_text or stdout_text or f"Hermes CLI failed with exit code {returncode}")
    yield "final", stdout_text


def _status() -> HermesStatus:
    return HermesStatus(
        launcher_exists=HERMES_CLI.exists(),
        matrix_exists=MATRIX_PATH.exists(),
        local_hermes_dir_exists=LOCAL_HERMES_DIR.exists(),
    )


def _screen_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hermes Companion</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #020309;
      --ink: #f4f7ff;
      --muted: rgba(244,247,255,.62);
      --accent: #7aa2ff;
      --accent-2: #6be7c8;
      --accent-3: #ffcf73;
      --accent-4: #ff7aa8;
      --line: rgba(255,255,255,.08);
    }
    * { box-sizing: border-box; }
    html, body { margin: 0; min-height: 100%; }
    body {
      min-height: 100vh;
      overflow: hidden;
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 50% 40%, rgba(122,162,255,.13), transparent 23%),
        radial-gradient(circle at 78% 18%, rgba(107,231,200,.10), transparent 16%),
        radial-gradient(circle at 22% 78%, rgba(255,207,115,.08), transparent 16%),
        radial-gradient(circle at 58% 70%, rgba(255,122,168,.07), transparent 16%),
        linear-gradient(180deg, #050713 0%, #020309 55%, #010205 100%);
    }
    .scene {
      position: relative;
      min-height: 100vh;
      width: 100vw;
      overflow: hidden;
    }
    .grain {
      position: absolute;
      inset: 0;
      pointer-events: none;
      opacity: .12;
      background-image:
        linear-gradient(rgba(255,255,255,.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.015) 1px, transparent 1px);
      background-size: 100% 22px, 22px 100%;
      mask-image: linear-gradient(180deg, rgba(0,0,0,.9), transparent 8%, transparent 92%, rgba(0,0,0,.9));
      mix-blend-mode: screen;
    }
    .frame {
      position: absolute;
      inset: 16px;
      border-radius: 36px;
      border: 1px solid rgba(255,255,255,.07);
      background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.00));
      box-shadow: inset 0 1px 0 rgba(255,255,255,.03), 0 26px 80px rgba(0,0,0,.42);
      overflow: hidden;
    }
    .mist {
      position: absolute;
      inset: 0;
      background:
        radial-gradient(circle at 50% 50%, rgba(122,162,255,.04), transparent 38%),
        radial-gradient(circle at 30% 30%, rgba(107,231,200,.05), transparent 20%),
        radial-gradient(circle at 70% 70%, rgba(255,122,168,.04), transparent 18%);
      mix-blend-mode: screen;
      opacity: .9;
    }
    .core {
      position: absolute;
      left: 50%;
      top: 52%;
      transform: translate(-50%, -50%);
      width: min(58vh, 54vw);
      aspect-ratio: 1;
      border-radius: 50%;
      background:
        radial-gradient(circle at 36% 30%, rgba(255,255,255,.98), rgba(255,255,255,.30) 7%, rgba(122,162,255,.24) 18%, rgba(122,162,255,.14) 30%, rgba(18,25,47,.10) 48%, rgba(2,3,8,.94) 82%),
        radial-gradient(circle at 50% 50%, rgba(107,231,200,.18), transparent 46%);
      box-shadow:
        0 0 0 1px rgba(255,255,255,.08) inset,
        0 0 0 20px rgba(122,162,255,.03),
        0 0 110px rgba(122,162,255,.18),
        0 30px 120px rgba(0,0,0,.42);
      overflow: hidden;
      animation: breathe 5.2s ease-in-out infinite;
    }
    .core::before {
      content: "";
      position: absolute;
      inset: 8%;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,.10);
      box-shadow: inset 0 0 120px rgba(255,255,255,.03);
    }
    .core::after {
      content: "";
      position: absolute;
      inset: 22% 27% 28% 27%;
      border-radius: 44% 44% 54% 54%;
      background:
        radial-gradient(circle at 34% 42%, #fff 0 5%, transparent 6%),
        radial-gradient(circle at 66% 42%, #fff 0 5%, transparent 6%),
        radial-gradient(circle at 50% 67%, rgba(255,255,255,.84) 0 4%, transparent 5%);
      opacity: .82;
      mix-blend-mode: screen;
      filter: blur(.25px);
    }
    .halo {
      position: absolute;
      inset: -11%;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,.08);
      box-shadow: 0 0 120px rgba(122,162,255,.16), inset 0 0 0 42px rgba(122,162,255,.02);
      animation: halo 8s linear infinite;
    }
    .veil {
      position: absolute;
      inset: auto 12% 5% 12%;
      height: 14%;
      border-radius: 50%;
      background: radial-gradient(circle at 50% 50%, rgba(122,162,255,.34), transparent 68%);
      filter: blur(20px);
      opacity: .82;
    }
    .orbit {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .ring {
      position: absolute;
      left: 50%;
      top: 50%;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,.10);
      transform: translate(-50%, -50%);
      box-shadow: 0 0 30px rgba(122,162,255,.08);
    }
    .r1 { width: min(72vh, 68vw); height: min(72vh, 68vw); opacity: .9; }
    .r2 { width: min(82vh, 78vw); height: min(82vh, 78vw); opacity: .65; }
    .r3 { width: min(92vh, 88vw); height: min(92vh, 88vw); opacity: .42; }
    .strand {
      position: absolute;
      left: 50%;
      top: 50%;
      width: min(82vh, 76vw);
      height: 2px;
      transform-origin: center;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.75), rgba(122,162,255,.58), transparent);
      box-shadow: 0 0 16px rgba(122,162,255,.4);
      border-radius: 999px;
      opacity: .72;
    }
    .s1 { transform: translate(-50%, -50%) rotate(17deg); }
    .s2 { transform: translate(-50%, -50%) rotate(-31deg); background: linear-gradient(90deg, transparent, rgba(107,231,200,.7), rgba(255,255,255,.6), transparent); }
    .s3 { transform: translate(-50%, -50%) rotate(63deg); background: linear-gradient(90deg, transparent, rgba(255,207,115,.72), rgba(255,255,255,.62), transparent); }
    .s4 { transform: translate(-50%, -50%) rotate(-74deg); background: linear-gradient(90deg, transparent, rgba(255,122,168,.7), rgba(255,255,255,.62), transparent); }
    .spark {
      position: absolute;
      width: 12px; height: 12px; border-radius: 50%;
      background: radial-gradient(circle at 35% 35%, #fff, var(--accent-2) 42%, rgba(107,231,200,.12) 72%);
      box-shadow: 0 0 18px rgba(107,231,200,.58);
      animation: bob 4.8s ease-in-out infinite;
    }
    .p1 { left: 18%; top: 20%; }
    .p2 { right: 20%; top: 22%; background: radial-gradient(circle at 35% 35%, #fff, var(--accent-3) 42%, rgba(255,207,115,.12) 72%); animation-delay: -1.1s; }
    .p3 { left: 24%; bottom: 22%; background: radial-gradient(circle at 35% 35%, #fff, var(--accent-4) 42%, rgba(255,122,168,.12) 72%); animation-delay: -2.3s; }
    .p4 { right: 24%; bottom: 22%; animation-delay: -3.4s; }
    .vignette {
      position: absolute;
      inset: 0;
      background:
        linear-gradient(180deg, rgba(0,0,0,.12), transparent 20%, transparent 78%, rgba(0,0,0,.18)),
        radial-gradient(circle at center, transparent 28%, rgba(0,0,0,.06) 68%, rgba(0,0,0,.35) 100%);
      pointer-events: none;
    }
    .micro {
      position: absolute;
      left: 50%;
      bottom: 24px;
      transform: translateX(-50%);
      z-index: 4;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .24em;
      font-size: 10px;
      pointer-events: none;
    }
    .micro .bar {
      display: inline-block;
      width: 120px;
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,.55), transparent);
      vertical-align: middle;
      margin: 0 10px;
      opacity: .8;
    }
    .edge-note {
      position: absolute;
      top: 50%;
      transform: translateY(-50%);
      z-index: 4;
      color: rgba(243,247,255,.54);
      text-transform: uppercase;
      letter-spacing: .22em;
      font-size: 9px;
      writing-mode: vertical-rl;
      pointer-events: none;
    }
    .edge-note.left { left: 18px; }
    .edge-note.right { right: 18px; }
    @keyframes pulse { 0%,100% { transform: scale(1); opacity: .82; } 50% { transform: scale(1.16); opacity: 1; } }
    @keyframes bob { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
    @keyframes breathe { 0%,100% { transform: translate(-50%, -50%) scale(1); } 50% { transform: translate(-50%, -50%) scale(1.02); } }
    @keyframes halo { 0% { transform: rotate(0deg) scale(1); } 50% { transform: rotate(180deg) scale(1.015); } 100% { transform: rotate(360deg) scale(1); } }
    @media (max-width: 720px) {
      .core { width: min(74vw, 58vh); }
      .r1 { width: min(84vw, 72vh); height: min(84vw, 72vh); }
      .r2 { width: min(94vw, 80vh); height: min(94vw, 80vh); }
      .r3 { width: min(104vw, 88vh); height: min(104vw, 88vh); }
      .micro { bottom: 28px; max-width: 90vw; text-align: center; }
      .edge-note { font-size: 8px; }
    }
  </style>
</head>
<body>
  <main class="scene" id="scene">
    <div class="grain"></div>
    <div class="frame">
      <div class="mist"></div>
      <div class="edge-note left" id="edge-left">listen</div>
      <div class="edge-note right" id="edge-right">hold</div>
      <div class="core" id="orb">
        <div class="halo"></div>
        <div class="veil"></div>
        <div class="orbit">
          <div class="ring r1"></div>
          <div class="ring r2"></div>
          <div class="ring r3"></div>
          <div class="strand s1"></div>
          <div class="strand s2"></div>
          <div class="strand s3"></div>
          <div class="strand s4"></div>
          <div class="spark p1"></div>
          <div class="spark p2"></div>
          <div class="spark p3"></div>
          <div class="spark p4"></div>
        </div>
      </div>
      <div class="vignette"></div>
    </div>
    <div class="micro" id="micro"><span id="top-left">hermes</span><span class="bar"></span><span id="top-right">mac studio m2 max · refactor open</span></div>
  </main>

  <script>
    window.__HERMES_INITIAL_FRAME__ = __INITIAL_FRAME__;
    const $ = id => document.getElementById(id);
    let socket = null;
    let reconnectMs = 300;
    function safe(v){ return String(v ?? ''); }
    function short(v, fallback){ const s = safe(v).trim(); return s ? s : fallback; }
    function renderFrame(frame){
      frame = frame || {};
      const accent = frame.accent || '#7aa2ff';
      document.documentElement.style.setProperty('--accent', accent);
      $('top-left').textContent = short(frame.title || 'hermes', 'hermes');
      $('top-right').textContent = short(frame.context || 'mac studio m2 max · refactor open', 'mac studio m2 max · refactor open');
      $('edge-left').textContent = short(frame.anchor || 'listen', 'listen');
      $('edge-right').textContent = short(frame.need_from_user || 'hold', 'hold');
      $('micro').style.opacity = frame.expression && String(frame.expression).toLowerCase().includes('alert') ? '.98' : '.85';
      const orb = $('orb');
      if (orb) {
        orb.style.boxShadow = frame.expression && String(frame.expression).toLowerCase().includes('alert')
          ? '0 0 0 1px rgba(255,255,255,.08) inset, 0 0 0 20px rgba(255,122,168,.03), 0 0 110px rgba(255,122,168,.18), 0 30px 120px rgba(0,0,0,.42)'
          : '0 0 0 1px rgba(255,255,255,.08) inset, 0 0 0 20px rgba(122,162,255,.03), 0 0 110px rgba(122,162,255,.18), 0 30px 120px rgba(0,0,0,.42)';
      }
    }
    async function loadInitialFrame(){
      try {
        const resp = await fetch(`/api/screen?ts=${Date.now()}`, { cache: 'no-store' });
        const data = await resp.json();
        renderFrame(data.frame || data);
      } catch (e) { console.warn(e); }
    }
    function connect(){
      if (socket) socket.close();
      const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
      socket = new WebSocket(`${protocol}://${location.host}/api/screen/ws`);
      socket.onmessage = event => { try { const data = JSON.parse(event.data); renderFrame(data.frame || data); } catch (e) { console.warn(e); } };
      socket.onopen = () => { reconnectMs = 300; };
      socket.onclose = () => setTimeout(connect, reconnectMs = Math.min(reconnectMs * 1.6, 5000));
      socket.onerror = () => { try { socket.close(); } catch (_) {} };
    }
    const initialFrame = window.__HERMES_INITIAL_FRAME__ || null;
    if (initialFrame) renderFrame(initialFrame.frame || initialFrame);
    loadInitialFrame();
    connect();
    setInterval(loadInitialFrame, 15000);
    document.addEventListener('visibilitychange', () => { if (!document.hidden) loadInitialFrame(); });
  </script>
</body>
</html>""".replace("__PAGE_VERSION__", PAGE_VERSION)

HERMES_HTML = _screen_html()


def create_hermes_gui_app() -> FastAPI:
    app = FastAPI(title="Hermes Companion", version=PAGE_VERSION)

    @app.get("/")
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/screen")

    @app.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/matrix")
    async def matrix() -> HTMLResponse:
        excerpt = _read_matrix_excerpt()
        return HTMLResponse(f"<pre>{excerpt}</pre>")

    @app.get("/api/screen")
    async def get_screen() -> Dict[str, Any]:
        return _screen_payload()

    @app.post("/api/screen")
    async def set_screen(payload: Dict[str, Any]) -> Dict[str, Any]:
        _post_screen_update(payload)
        return _screen_payload()

    @app.get("/screen", response_class=HTMLResponse)
    async def screen() -> HTMLResponse:
        return HTMLResponse(HERMES_HTML)

    @app.get("/live", response_class=HTMLResponse)
    async def live() -> HTMLResponse:
        return HTMLResponse(HERMES_HTML)

    @app.websocket("/api/screen/ws")
    async def screen_ws(websocket: WebSocket) -> None:
        await websocket.accept()
        _SCREEN_WEBSOCKETS.add(websocket)
        try:
            await websocket.send_text(json.dumps(_screen_payload(), ensure_ascii=False))
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
        finally:
            _SCREEN_WEBSOCKETS.discard(websocket)

    @app.post("/api/chat", response_model=HermesChatResponse)
    async def chat(payload: HermesChatRequest) -> HermesChatResponse:
        if not payload.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        prompt = _build_prompt(payload.message, payload.conversation)
        try:
            response = await _run_hermes_with_screen_updates(prompt, payload)
        except Exception as exc:
            _post_screen_update(
                _screen_frame_for_turn(
                    mode=payload.mode,
                    model=payload.model,
                    title="Interrupted",
                    subtitle="needs attention",
                    body_lines=["something snagged", "the thread is still here"],
                    cards=[
                        {"label": "alert", "value": "something snagged"},
                        {"label": "thread", "value": "still here"},
                        {"label": "need", "value": "say what matters most"},
                    ],
                    expression="alert",
                    glyph="!",
                )
            )
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        response_text = response
        _post_screen_update(
            _screen_frame_for_turn(
                mode=payload.mode,
                model=payload.model,
                title=_mode_visual(payload.mode)["title"],
                subtitle="complete",
                body_lines=_expressive_focus_lines(response_text, payload.mode, max_lines=3),
                cards=[
                    {"label": "done", "value": "signal delivered"},
                    {"label": "awake", "value": "thread held"},
                    {"label": "need", "value": "say what matters most"},
                ],
                expression="happy done",
                glyph="✓",
            )
        )

        return HermesChatResponse(
            response=response_text,
            mode=payload.mode,
            model=payload.model,
            prompt_preview=prompt[:500],
        )

    return app


app = create_hermes_gui_app()


def run_hermes_gui(host: str = "127.0.0.1", port: int = 8787) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Launch the Hermes visual conversation UI")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8787, help="Bind port (default: 8787)")
    args = parser.parse_args()
    run_hermes_gui(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
