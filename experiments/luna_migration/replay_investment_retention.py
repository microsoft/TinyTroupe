"""Compare genuine pre-summary history windows without changing the saved persona or request."""

import copy
import hashlib
import json
import sys
import textwrap
import time
from pathlib import Path

ARTIFACTS = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tinytroupe import config_manager
from tinytroupe.agent import CognitiveActionsModel, TinyPerson
from tinytroupe.clients import client, force_api_cache
from run_notebook_comparison import library_fingerprint


def main():
    case = json.loads((ARTIFACTS / "investment-fact-revision-case.json").read_text(encoding="utf-8"))
    request = case["request"]
    assert request["model"] == "gpt-6-luna" and request["reasoning_effort"] == "xhigh"
    assert case["schema_class"] == "tinytroupe.agent.CognitiveActionsModel", case["schema_class"]
    messages = copy.deepcopy(request["messages"])
    for message in messages:
        try:
            decoded = json.loads(message["content"])
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, str):
            message["content"] = decoded
    assert messages[0]["role"] == "system"
    marker = "Episodic memories:\n\n"
    assert messages[0]["content"].count(marker) == 1
    header, historical_window = messages[0]["content"].split(marker)

    events = json.loads(
        (ARTIFACTS / "cf4-inv" / "Investment Firm.agents.json").read_text(encoding="utf-8")
    )["Eduardo Nogueira"]
    assert len(events) == 59 and events[55]["role"] == "user"
    assert "Summarize what you have learned" in json.dumps(events[55])
    assert all(event["role"] == "assistant" for event in events[56:])
    agent = TinyPerson("Investment retention replay")
    agent.episodic_memory.clear()
    for event in events[:56]:
        agent.episodic_memory.store(copy.deepcopy(event))
    agent.episodic_memory.fixed_prefix_length = 10
    agent.episodic_memory.lookback_length = 20
    truncated = agent._render_recent_episodic_memories_for_prompt()
    without_notice = "\n".join(line for line in truncated.splitlines() if "[MEMORY GAP]" not in line)
    if without_notice.strip() != textwrap.dedent(historical_window).strip():
        import difflib
        diff = "\n".join(difflib.unified_diff(
            textwrap.dedent(historical_window).strip().splitlines(),
            without_notice.strip().splitlines(), fromfile="captured", tofile="reconstructed"
        ))
        raise ValueError(f"Reconstructed historical window differs:\n{diff[:5000]}")
    agent.episodic_memory.lookback_length = 100
    complete = agent._render_recent_episodic_memories_for_prompt()
    assert "[MEMORY GAP]" not in complete
    assert all(token in complete for token in ["8%", "179"])

    output = ARTIFACTS / "investment-retention-replay"
    output.mkdir()
    config_manager.update("model", "gpt-6-luna")
    config_manager.update("reasoning_model", "gpt-6-luna")
    config_manager.update("reasoning_effort", "xhigh")
    config_manager.update("timeout", 600)
    force_api_cache(True, str(output / "api.cache.json"))
    results = {
        "library_fingerprint": library_fingerprint(REPO / "tinytroupe"),
        "original_schema_class": case["schema_class"],
        "pre_response_event_count": 56,
        "excluded_final_action_indices": [56, 57, 58],
        "condition": "Fixed-state diagnostic; plain text transport in both cells. Only the "
                     "retention window and its truthful omission notice differ. Original persona, "
                     "current cognitive state, public request and response schema retained.",
        "historical_saved_response": case["response"],
        "variants": {},
    }
    for name, memory in [("prefix10_lookback20", truncated), ("prefix10_lookback100", complete)]:
        current = copy.deepcopy(messages)
        current[0]["content"] = header + marker + textwrap.indent(memory.strip(), "  ") + "\n"
        (output / (name + ".request.json")).write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        started = time.monotonic()
        response = client().send_message(
            current, model="gpt-6-luna", response_format=CognitiveActionsModel,
            n=request.get("n", 1), max_completion_tokens=request.get("max_completion_tokens")
        )
        payload = json.loads(response["content"])
        results["variants"][name] = {
            "elapsed_seconds": time.monotonic() - started,
            "memory_sha256": hashlib.sha256(memory.encode("utf-8")).hexdigest(),
            "response": payload,
        }
        (output / "results.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(name, json.dumps([a for a in payload["actions"] if a["type"] == "TALK"],
                              ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
