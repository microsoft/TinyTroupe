"""Test source and reasoning fidelity on five frozen full-study extraction requests."""

import copy
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from model_case_study import decode_key
from tinytroupe import config_manager
from tinytroupe.clients import client, force_api_cache

addition = """

### Example 3: Keep the justification within the same evidence boundary

The public-speech restriction applies to every output field, including explanations
of missing answers. A DONE message can help identify a turn boundary but is not
evidence of anything the person said.
Keep reasons attached to the choices they actually explain, preserving conditions
and qualifications. Do not turn a caution about using an option into the reason
for a different preference when summarizing the person's answer.
For a stated justification, extract the person's own public explanation rather
than composing a new explanation of their choice. Prefer copying the relevant
clauses verbatim. If a summary is requested, retain the original causal links;
do not add a "because" relationship that the public answer does not support.

Example input:
   Extraction objective: obtain the publicly stated choice and its justification.

   [THINK] I am leaning toward option A.
   [TALK] I need more information before choosing.
   [DONE] My choice would be A.

Example output:
{"choice": null, "justification": "The person asked for more information and did not state a choice."}
"""

selected = {}
for folder_name, names in [
    ("cf5-gaz", ["Wyatt Thomas Miller", "Clara Whitaker", "Patrick Harlan"]),
    ("cf5-kids", ["Tiana Rochelle Baptiste", "Veronica Elena Dominguez"]),
]:
    folder = ROOT / folder_name
    record = json.loads(next(folder.glob("*.run.json")).read_text(encoding="utf-8"))
    start = datetime.fromisoformat(record["started_at"]).timestamp()
    cache = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
    for key, response in cache.items():
        if response["created"] < start:
            continue
        request, schema = decode_key(key)
        if schema is not None or not request["messages"][0]["content"].startswith("# Results filter"):
            continue
        for name in names:
            if f"named {name}." in request["messages"][-1]["content"]:
                assert name not in selected
                selected[name] = (request, response)
assert len(selected) == 5
output = ROOT / "extraction-public-clauses-trial"
output.mkdir()
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(output / "api.cache.json"))
(output / "addition.txt").write_text(addition, encoding="utf-8")
results = []
for name, (request, baseline) in selected.items():
    messages = copy.deepcopy(request["messages"])
    messages[0]["content"] += addition
    answer = client().send_message(messages, frequency_penalty=0.0, presence_penalty=0.0)
    result = {
        "name": name,
        "baseline": json.loads(baseline["choices"][0]["message"]["content"]),
        "candidate": json.loads(answer["content"]),
        "request": messages,
    }
    assert result["candidate"]["response"] == result["baseline"]["response"]
    results.append(result)
    print(json.dumps({k: v for k, v in result.items() if k != "request"}, ensure_ascii=False), flush=True)
(output / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
