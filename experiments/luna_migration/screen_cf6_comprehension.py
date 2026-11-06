"""Replay observed young-child failures through the full corrected action/extraction pipeline."""

import ast
import copy
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from run_notebook_comparison import library_fingerprint
from review_notebook_evidence import cost_for_run, public_actions
from tinytroupe import config_manager
from tinytroupe.agent import TinyPerson
from tinytroupe.clients import force_api_cache
from tinytroupe.environment import TinyWorld
from tinytroupe.extraction import ResultsExtractor

OUTPUT = ROOT / "cf6-comprehension-screen"
OUTPUT.mkdir()
people = json.loads((ROOT / "cf6-gaz-population-evidence.json").read_text(encoding="utf-8"))
selected = [p for p in people if p["age"] < 5]
selected += [next(p for p in people if p["name"] == name)
             for name in ["Terrence Calvin Booker", "Douglas Harlan Whitaker"]]
before = json.loads((ROOT / "cf6-gaz-public-evidence.json").read_text(encoding="utf-8"))
baseline = {p["name"]: p for p in before}
fingerprint = library_fingerprint(REPO / "tinytroupe")
(OUTPUT / "protocol.json").write_text(json.dumps({
    "library_sha256": fingerprint,
    "selection": "Every person younger than five in the fresh completed cohort, plus the "
                 "first two adults in the original response-table order as capability controls.",
    "selected_names": [p["name"] for p in selected],
    "constants": "Exact saved generated biographies, original gazpacho questionnaire, thought, "
                 "introduction, correction settings, extractor, model and xhigh effort.",
    "intervention": "Actor instructions distinguish demanded format from actual comprehension.",
    "scope": "Developmental-comprehension repair, not a calibration experiment or forced score.",
}, ensure_ascii=False, indent=2), encoding="utf-8")
for key, value in [("model", "gpt-6-luna"), ("reasoning_model", "gpt-6-luna"),
                   ("reasoning_effort", "xhigh"), ("timeout", 600)]:
    config_manager.update(key, value)
force_api_cache(True, str(OUTPUT / "api.cache.json"))
agents = []
for saved in selected:
    person = TinyPerson(saved["name"])
    for key, value in saved["persona"].items():
        person.define(key, copy.deepcopy(value))
    assert person._persona == saved["persona"]
    person.action_generator.enable_reasoning_step = False
    person.action_generator.enable_quality_checks = True
    person.action_generator.max_attempts = 5
    person.action_generator.enable_regeneration = True
    person.action_generator.quality_threshold = 5
    agents.append(person)
notebook = json.loads((REPO / "examples" /
    "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb").read_text(encoding="utf-8"))
namespace = {"ResultsExtractor": ResultsExtractor}
targets = {"interviewer_introduction", "interviewer_main_question", "inner_monologue",
           "results_extractor"}
for cell in notebook["cells"]:
    if cell["cell_type"] == "code":
        for node in ast.parse("".join(cell["source"])).body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id in targets for target in node.targets
            ):
                exec(compile(ast.Module(body=[node], type_ignores=[]), "<notebook>", "exec"), namespace)
started = time.monotonic()
world = TinyWorld("Developmental comprehension screen", agents, broadcast_if_no_target=False)
world.broadcast(namespace["interviewer_introduction"])
world.broadcast(namespace["interviewer_main_question"])
world.broadcast_thought(namespace["inner_monologue"])
world.run(1)
memories = {p.name: p.episodic_memory.retrieve_all() for p in agents}
(OUTPUT / "agents.json").write_text(
    json.dumps(memories, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
)
results = namespace["results_extractor"].extract_results_from_agents(agents)
talks = public_actions(memories)
review = [{
    "name": row["name"], "age": baseline[row["name"]]["age"],
    "baseline_response": baseline[row["name"]]["response"], "response": row["response"],
    "justification": row.get("justification"),
    "public": [a["text"] for a in talks[row["name"]]],
} for row in results]
(OUTPUT / "results.json").write_text(
    json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8"
)
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {"started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(r["created"] for r in cache.values()) + 1}, prices)
assert library_fingerprint(REPO / "tinytroupe") == fingerprint
(OUTPUT / "receipt.json").write_text(json.dumps({
    "elapsed_seconds": time.monotonic() - started,
    "returned_responses": len(cache), "returned_usage_estimate": usage,
    "library_unchanged": True, "manual_review": "Pending.",
}, indent=2), encoding="utf-8")
print(json.dumps(review, ensure_ascii=False), flush=True)
