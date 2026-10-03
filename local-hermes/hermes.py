#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import urllib.request

DEFAULTS = {
    "chat": "hermes-qwen3-chat",
    "plan": "hermes-qwen3-plan",
    "tools": "hermes-phi4-tools",
    "reason": "hermes-phi4-reasoning-alt",
}

MODEL_STATE_PATH = Path(__file__).with_name(".selected_model.json")


def load_selected_model() -> str | None:
    try:
        data = json.loads(MODEL_STATE_PATH.read_text())
    except Exception:
        return None
    model = str(data.get("model", "")).strip()
    return model or None


def save_selected_model(model: str) -> None:
    MODEL_STATE_PATH.write_text(json.dumps({"model": model}, indent=2) + "\n")


def list_ollama_models() -> list[str]:
    raw = run_command("ollama", "list")
    models: list[str] = []
    for line in raw.splitlines()[1:]:
        cols = line.split()
        if cols:
            models.append(cols[0])
    return models


def probe_ollama_chat_model(model: str) -> bool:
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Reply with OK."}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 1},
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        return bool((data.get("message") or {}).get("content") is not None)
    except Exception:
        return False


def filter_working_ollama_models(models: list[str]) -> list[str]:
    working: list[str] = []
    for model in models:
        # Skip embeddings and other non-chat-only artifacts.
        if model.startswith("nomic-embed-text"):
            continue
        if probe_ollama_chat_model(model):
            working.append(model)
    return working


def resolve_active_model(mode: str, explicit_model: str | None = None) -> str:
    if explicit_model:
        return explicit_model
    selected = load_selected_model()
    if selected and mode in {"auto", "chat", "plan"}:
        return selected
    return DEFAULTS.get(mode, DEFAULTS["chat"])

MATRIX_CORE = """\
You are Hermes, a local-only Mac assistant.
You are concise, pragmatic, and grounded in local evidence first.
Borrow the useful TinyTroupe patterns: structured persona, episodic/semantic memory, local grounding, iterative validation, and safe action gating.
Do not simulate emotions, social drama, or agent theater. Use the simplest reliable approach.
"""

TOOL_HINTS = (
    "run ", "execute", "tool", "terminal", "shell", "bash", "zsh",
    "file", "edit", "patch", "write", "delete", "remove", "create",
    "search", "find", "inspect", "open", "click", "browser", "curl",
    "install", "brew", "ollama", "launch", "start", "stop", "restart",
)
PLAN_HINTS = (
    "plan", "strategy", "architect", "design", "should we", "compare",
    "decide", "route", "orchestr", "workflow", "stack", "setup", "roadmap",
)
REASON_HINTS = (
    "why", "how do i", "what is the best", "tradeoff", "optimize",
    "analyze", "reason", "evaluate", "pros and cons", "pick one",
)


def choose_model(text: str) -> str:
    t = text.lower()
    if t.startswith("tool:"):
        return DEFAULTS["tools"]
    if t.startswith("plan:"):
        return DEFAULTS["plan"]
    if t.startswith("reason:"):
        return DEFAULTS["reason"]

    score_tools = sum(1 for hint in TOOL_HINTS if hint in t)
    score_plan = sum(1 for hint in PLAN_HINTS if hint in t)
    score_reason = sum(1 for hint in REASON_HINTS if hint in t)

    if score_tools >= 2 or re.search(r"\b(do|make|create|delete|edit|fix|run|install|build|test)\b", t):
        return DEFAULTS["tools"]
    if score_plan >= 2:
        return DEFAULTS["plan"]
    if score_reason >= 2:
        return DEFAULTS["reason"]
    return DEFAULTS["chat"]


def post_chat(model: str, prompt: str, system: str | None = None) -> str:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {"model": model, "messages": messages, "stream": False}
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode())
    return data["message"]["content"]


def run_command(*cmd: str) -> str:
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        err = completed.stderr.strip() or completed.stdout.strip() or f"command failed: {' '.join(cmd)}"
        raise RuntimeError(err)
    return completed.stdout.strip()


def summarize_ollama_list(raw: str) -> str:
    lines = [line for line in raw.splitlines() if line.strip()]
    if not lines:
        return "No Ollama models found."

    entries: list[tuple[str, str, str]] = []
    for line in lines[1:]:
        m = re.match(r"^(\S+)\s+(\S+)\s+([\d.]+\s+\S+)\s+(.+)$", line)
        if not m:
            continue
        name, _id, size, modified = m.groups()
        entries.append((name, size, modified))

    if not entries:
        return raw

    interesting = [
        e for e in entries
        if e[0].startswith("hermes-") or e[0].startswith("qwen3:") or e[0].startswith("phi4-")
    ]
    pool = interesting or entries
    out = ["Local Ollama models:"]
    for name, size, modified in pool:
        out.append(f"- {name} ({size}, {modified})")
    if interesting:
        out.append("")
        out.append("Hermes stack:")
        for name, size, _ in interesting:
            out.append(f"- {name} ({size})")
    return "\n".join(out)


def _wrap_screen_text(text: str, width: int = 18, max_lines: int = 4) -> list[str]:
    words = text.replace("\n", " ").split()
    if not words:
        return ["(empty)"]
    lines: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        projected = current_len + len(word) + (1 if current else 0)
        if projected > width:
            lines.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = projected
        if len(lines) >= max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(" ".join(current))
    return lines[:max_lines] or ["(empty)"]


def push_screen_update(mode: str, model: str | None, content: str, skipped: bool = False) -> None:
    payload = {
        "title": "Hermes Live",
        "subtitle": f"{mode} · {model or 'local'}",
        "mode": mode,
        "model": model,
        "accent": {
            "tools": "#6be7c8",
            "plan": "#7aa2ff",
            "reason": "#ffcd70",
            "chat": "#9ef0c4",
            "auto": "#a88cff",
        }.get(mode, "#7aa2ff"),
        "glyph": {
            "tools": "◫",
            "plan": "◌",
            "reason": "◈",
            "chat": "◉",
            "auto": "◍",
        }.get(mode, "◉"),
        "body_lines": _wrap_screen_text(content, width=18, max_lines=4),
        "footer": "local-only",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "skipped": skipped,
    }
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8787/api/screen",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=1.2) as _resp:
            _resp.read()
    except Exception:
        pass


def read_screen_state() -> str | None:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8787/api/screen", timeout=1.2) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return None
    frame = data.get("frame", data)
    lines = [
        f"TITLE: {frame.get('title', '')}",
        f"SUBTITLE: {frame.get('subtitle', '')}",
        f"MODE: {frame.get('mode', '')}",
        f"MODEL: {frame.get('model') or 'local'}",
        "BODY:",
    ]
    lines.extend(f"- {line}" for line in frame.get("body_lines", [])[:4])
    lines.append(f"UPDATED: {frame.get('updated_at', '')}")
    return "\n".join(lines)




def maybe_handle_builtin(prompt: str) -> str | None:
    raw = prompt.strip()
    t = raw.lower()

    if t.startswith("/model"):
        parts = raw.split(None, 1)
        arg = parts[1].strip() if len(parts) > 1 else ""
        if not arg or arg in {"list", "ls"}:
            models = filter_working_ollama_models(list_ollama_models())
            selected = load_selected_model()
            lines = ["Ollama models:"]
            for name in models:
                prefix = "*" if selected and name == selected else "-"
                lines.append(f"{prefix} {name}")
            if selected:
                lines.append("")
                lines.append(f"Selected: {selected}")
            return "\n".join(lines)
        if arg in {"current", "show"}:
            selected = load_selected_model()
            return f"Selected model: {selected or '(none)'}"
        if arg in {"clear", "reset", "default"}:
            try:
                MODEL_STATE_PATH.unlink(missing_ok=True)
            except Exception:
                pass
            return "Selected model cleared."
        if arg not in list_ollama_models():
            return f"Model not installed: {arg}"
        save_selected_model(arg)
        return f"Selected model set to {arg}"

    if re.search(r"\b(ollama list|installed models|available models|current local ollama models|what is installed|what's installed)\b", t):
        return summarize_ollama_list(run_command("ollama", "list"))
    if re.search(r"\b(screen state|show screen|show the screen|what is on the screen|what's on the screen|screen update)\b", t):
        return read_screen_state() or "Screen state unavailable."
    if m := re.search(r"ollama\s+show\s+([A-Za-z0-9:._-]+)", t):
        return run_command("ollama", "show", m.group(1))
    if t in {"pwd", "current directory", "where am i"}:
        return run_command("pwd")
    if t in {"uname", "os", "system info", "system information"}:
        return run_command("uname", "-a")
    return None


def build_system_prompt(model: str, mode: str, extra: str | None = None) -> str:
    lines = [MATRIX_CORE]
    if mode == "plan":
        lines.append("Planner mode: favor structure, tradeoffs, and next steps.")
    elif mode == "tools":
        lines.append("Tool mode: prefer exact actions, shell commands, and concise confirmations.")
    elif mode == "reason":
        lines.append("Reason mode: be careful, analytical, and explicit about uncertainty.")
    else:
        lines.append("Chat mode: answer directly and briefly.")

    if model == DEFAULTS["chat"]:
        lines.append("Do not provide hidden chain-of-thought or verbose deliberation.")
    if model == DEFAULTS["tools"]:
        lines.append("If a request is actionable, return the cleanest tool-oriented response.")
    if extra:
        lines.append(extra.strip())
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Local Hermes router for Ollama")
    parser.add_argument("prompt", nargs="*", help="Prompt text. If omitted, stdin is used.")
    parser.add_argument("--model", help="Force a specific Ollama model tag")
    parser.add_argument("--mode", choices=["auto", "chat", "plan", "tools", "reason"], default="auto")
    parser.add_argument("--system", help="Optional extra system prompt")
    args = parser.parse_args()

    prompt = " ".join(args.prompt).strip() if args.prompt else sys.stdin.read().strip()
    if not prompt:
        print("No prompt provided.", file=sys.stderr)
        return 2

    mode = args.mode
    model = resolve_active_model(mode, explicit_model=args.model)
    effective_mode = mode if mode != "auto" else (
        "tools" if model == DEFAULTS["tools"] else
        "plan" if model == DEFAULTS["plan"] else
        "reason" if model == DEFAULTS["reason"] else
        "chat"
    )
    system = build_system_prompt(model=model, mode=effective_mode, extra=args.system)

    builtin = maybe_handle_builtin(prompt)
    if builtin is not None:
        print(builtin.strip())
        push_screen_update(effective_mode, model, builtin, skipped=False)
        return 0

    output = post_chat(model, prompt, system=system)
    print(output.strip())
    push_screen_update(effective_mode, model, output, skipped=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
