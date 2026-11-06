"""Re-extract actual completed histories with the repaired production prompt, without rerunning actors."""

import ast
import copy
import csv
import hashlib
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import chevron

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study"), str(ROOT)]
from model_case_study import decode_key
from review_notebook_evidence import cost_for_run, public_actions
from run_notebook_comparison import library_fingerprint
from tinytroupe import config_manager
from tinytroupe.clients import client, force_api_cache
from tinytroupe.extraction import ResultsExtractor

output = ROOT / "cf5-reextraction"
output.mkdir()
template_path = REPO / "tinytroupe" / "extraction" / "prompts" / "interaction_results_extractor.mustache"
template = template_path.read_text(encoding="utf-8")
fingerprint = library_fingerprint(REPO / "tinytroupe")
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(output / "api.cache.json"))
started_at = datetime.now(timezone.utc).isoformat()
started = time.monotonic()
studies = {}


def extract(task):
    """Keep the original user/history message and change only the system extraction instructions."""
    name, request, baseline, system = task
    messages = copy.deepcopy(request["messages"])
    messages[0]["content"] = system
    answer = client().send_message(messages, frequency_penalty=0.0, presence_penalty=0.0)
    result = json.loads(answer["content"])
    if result["name"] != name or str(result["response"]) != str(baseline["response"]):
        raise ValueError(f"{name}: extracted identity or public response changed: {result}")
    return {
        "name": name, "baseline": baseline, "reextracted": result,
        "response_type_changed": type(result["response"]) is not type(baseline["response"]),
    }


for study, filename in [
    ("kids", "AI-enabled Children Story Telling Market Research 2.ipynb"),
    ("gaz", "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb"),
]:
    folder = ROOT / f"cf5-{study}"
    record = json.loads((folder / filename.replace(".ipynb", ".run.json")).read_text(encoding="utf-8"))
    assert record["status"] == "completed"
    begin = datetime.fromisoformat(record["started_at"]).timestamp()
    finish = begin + record["elapsed_seconds"]
    agents = json.loads((folder / filename.replace(".ipynb", ".agents.json")).read_text(encoding="utf-8"))
    talks = public_actions(agents)
    notebook = json.loads((REPO / "examples" / filename).read_text(encoding="utf-8"))
    namespace = {"ResultsExtractor": ResultsExtractor}
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "results_extractor"
                for target in node.targets
            ):
                exec(compile(ast.Module(body=[node], type_ignores=[]),
                             "<original-notebook-extractor>", "exec"), namespace)
    extractor = namespace["results_extractor"]
    system = chevron.render(template, {
        "fields": ", ".join(extractor.default_fields),
        "fields_hints": list(extractor.default_fields_hints.items()),
    })
    cache = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
    tasks = {}
    for key, response in cache.items():
        if not begin <= response["created"] <= finish:
            continue
        request, schema = decode_key(key)
        if schema is not None or not request["messages"][0]["content"].startswith("# Results filter"):
            continue
        baseline = json.loads(response["choices"][0]["message"]["content"])
        name = baseline.get("name")
        if name not in agents:
            continue
        if f"named {name}." not in request["messages"][-1]["content"]:
            continue
        assert name not in tasks, f"Ambiguous source extraction: {name}"
        tasks[name] = (name, request, baseline, system)
    assert set(tasks) == set(agents) and len(tasks) == 50
    with ThreadPoolExecutor(max_workers=8) as executor:
        rows = list(executor.map(extract, tasks.values()))
    for row in rows:
        justification = row["reextracted"]["justification"]
        speech = " ".join(action["text"] for action in talks[row["name"]])
        row["justification_is_public_substring"] = (
            justification is None or " ".join(justification.split()) in " ".join(speech.split())
        )
    studies[study] = rows
    (output / f"{study}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / f"{study}.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["name", "response", "justification"])
        writer.writeheader()
        writer.writerows(row["reextracted"] for row in rows)
    print(study, "responses unchanged", len(rows), "nonverbatim justifications",
          [row["name"] for row in rows if not row["justification_is_public_substring"]], flush=True)

assert library_fingerprint(REPO / "tinytroupe") == fingerprint
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))
receipt = {
    "started_at": started_at, "elapsed_seconds": time.monotonic() - started,
    "library_sha256": fingerprint,
    "template_sha256": hashlib.sha256(template_path.read_bytes()).hexdigest(),
    "model": "gpt-6-luna", "effort": "xhigh", "public_responses_semantically_unchanged": 100,
    "response_type_changes": [
        row["name"] for rows in studies.values() for row in rows if row["response_type_changed"]
    ],
    "scope": "Postprocessing replay of 100 real complete-study histories. Only extraction "
             "system instructions changed; original user/history messages and response schemas retained. "
             "This is not a new simulation rollout or a full notebook rerun under the later source hash.",
}
receipt["returned_usage_estimate"] = cost_for_run(output, receipt, prices["models"]["gpt-6-luna"])
(output / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print("RETURNED USAGE", receipt["returned_usage_estimate"]["usd"], flush=True)
