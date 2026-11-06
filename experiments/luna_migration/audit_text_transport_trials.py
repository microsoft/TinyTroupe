"""Verify the actual captured actor request encoding and price the two retention replays."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key
from review_notebook_evidence import cost_for_run

report = {"transport": {}}
for name, expected in [
    ("fixed-persona-gaz-text-transport", 8),
    ("fixed-persona-gaz-text-controls", 2),
    ("fixed-persona-gaz-situated-decisions", 8),
    ("fixed-persona-gaz-holdout-text", 8),
    ("fixed-persona-gaz-holdout-situated", 8),
    ("fixed-persona-gaz-situated-controls", 2),
    ("fixed-persona-gaz-minimal-actor", 8),
    ("fixed-persona-gaz-minimal-controls", 2),
    ("fixed-persona-gaz-low-effort", 8),
]:
    folder = ROOT / name
    if not (folder / "receipt.json").exists():
        report["transport"][name] = {"status": "Pending"}
        continue
    cache = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
    actors = []
    for key in cache:
        request, schema = decode_key(key)
        if schema != "tinytroupe.agent.CognitiveActionsModel":
            continue
        assert request["model"] == "gpt-6-luna"
        expected_effort = "low" if name == "fixed-persona-gaz-low-effort" else "xhigh"
        assert request["reasoning_effort"] == expected_effort
        system = request["messages"][0]
        assert system["role"] == "system" and system["content"].startswith("# Agent specification\n")
        for message in request["messages"]:
            content = message["content"]
            if not isinstance(content, str):
                raise ValueError(f"{name}: unexpected non-text input in this text-only diagnostic.")
            try:
                decoded = json.loads(content)
            except json.JSONDecodeError:
                continue
            assert not isinstance(decoded, str), f"{name}: JSON-string-wrapped actor content remains."
        actors.append(request)
    assert len(actors) >= expected, (name, len(actors), expected)
    report["transport"][name] = {
        "status": "Passed",
        "actor_requests": len(actors),
        "plain_system_and_control_strings": True,
        "actual_model_and_effort": f"gpt-6-luna/{expected_effort}",
        "original_response_schema": "tinytroupe.agent.CognitiveActionsModel",
    }

prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))
report["investment_retention_replay_returned_usage"] = cost_for_run(
    ROOT / "investment-retention-replay",
    {"started_at": "1970-01-01T00:00:00+00:00",
     "elapsed_seconds": datetime.now(timezone.utc).timestamp()},
    prices["models"]["gpt-6-luna"],
)
(ROOT / "text-transport-trial-audit.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(report, ensure_ascii=False, indent=2))
