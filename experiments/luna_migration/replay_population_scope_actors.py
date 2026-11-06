"""Distinguish metadata removal from new biography elaboration on frozen actor turns."""

import copy
import hashlib
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from model_case_study import decode_key
from tinytroupe import config_manager
from tinytroupe.agent import CognitiveActionsModel
from tinytroupe.clients import client, force_api_cache
from review_notebook_evidence import cost_for_run

output = ROOT / "population-scope-actor-replays"
output.mkdir()
cases = [json.loads((ROOT / "population-scope-trial" / name).read_text(encoding="utf-8"))
         for name in ["Diego.json", "Marco.json", "Gabriel.json"]]
expected = {case["name"]: case for case in cases}
current = json.loads((ROOT / "cf5-gaz" / "api.cache.json").read_text(encoding="utf-8"))
prior = json.loads((ROOT / "cf4-gaz" / "api.cache.json").read_text(encoding="utf-8"))
selected = {}
actor_counts = {}
corrected = []
for key, response in current.items():
    if key in prior:
        continue
    request, schema = decode_key(key)
    if schema != "tinytroupe.agent.CognitiveActionsModel":
        continue
    text = request["messages"][0]["content"].split("## Persona", 1)[1]
    persona = json.loads(re.search(r"```json\s*(.*?)```", text, re.S)[1])
    name = persona["name"]
    feedback = any("TENTATIVE ACTION GENERATION FAILED IN QUALITY CHECKS!" in m["content"]
                   for m in request["messages"])
    actor_counts[name] = actor_counts.get(name, 0) + 1
    if feedback:
        corrected.append({"name": name, "age": persona["age"]})
    if name not in expected or feedback:
        continue
    assert name not in selected
    assert all(persona.get(k) == v for k, v in expected[name]["before"].items())
    assert request["model"] == "gpt-6-luna" and request["reasoning_effort"] == "xhigh"
    selected[name] = (request, response, persona)
assert set(selected) == set(expected)
assert len(actor_counts) == 50 and len(corrected) == 3
assert all(row["age"] <= 1 for row in corrected)


def remove_catalog(name, original):
    cleaned = copy.deepcopy(original)
    paths = []
    if name.startswith("Diego"):
        paths.append("population_dimension_spectra")
        del cleaned["population_dimension_spectra"]
        assert cleaned["individual_dimension_profile"] == original["individual_dimension_profile"]
    else:
        key = "additional_dimensions" if name.startswith("Marco") else "population_dimension_catalog"
        del cleaned[key]["note"]
        paths.append(key + ".note")
        for dimension, value in cleaned[key].items():
            assert isinstance(value, dict) and len(value["values"]) == 10
            assert "selected_value" in value or "agent_value" in value
            del value["values"]
            paths.append(key + "." + dimension + ".values")
    return cleaned, paths


jobs = []
for name, case in expected.items():
    request, baseline, original = selected[name]
    cleaned, removed_paths = remove_catalog(name, original)
    for condition, persona in [("catalog_only_removed", cleaned), ("regenerated_biography", case["after"])]:
        messages = copy.deepcopy(request["messages"])
        system = messages[0]["content"]
        prefix, section = system.split("## Persona", 1)
        match = re.search(r"```json\s*(.*?)```", section, re.S)
        previous = match[1]
        assert previous.rstrip() == json.dumps(original, indent=4)
        trailing = previous[len(previous.rstrip()):]
        section = section[:match.start(1)] + json.dumps(persona, indent=4) + trailing + section[match.end(1):]
        messages[0]["content"] = prefix + "## Persona" + section
        assert messages[1:] == request["messages"][1:]
        jobs.append({
            "name": name, "condition": condition, "messages": messages,
            "max_completion_tokens": request.get("max_completion_tokens"),
            "baseline": json.loads(baseline["choices"][0]["message"]["content"]),
            "removed_paths": removed_paths if condition == "catalog_only_removed" else None,
        })
(output / "plan.json").write_text(json.dumps({
    "created_at": datetime.now(timezone.utc).isoformat(),
    "names": list(expected), "calls": len(jobs),
    "conditions": ["catalog_only_removed", "regenerated_biography"],
    "constants": "Captured full actor instructions, chronological stimuli, time, response schema, "
                 "model, effort, token limit and all non-persona messages.",
    "catalog_only": "Only identified alternative-value catalogs/notes are removed. Selected "
                    "individual descriptions and every other original persona field remain.",
    "new_biographies": "Same sampled characteristics, new elaborations from the scoped-generator candidate.",
    "acceptance": "Diagnostic only; no empirical calibration or population inference from six replays.",
    "quality_audit": {
        "actors": len(actor_counts), "actor_calls": sum(actor_counts.values()),
        "feedback_exposed": corrected,
        "finding": "Only three infants were regenerated. No adult rating was selected by a correction loop "
                   "in the complete CF5 run, so disabling correction is not a supported adult-rating remedy.",
    },
}, ensure_ascii=False, indent=2), encoding="utf-8")
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(output / "api.cache.json"))


def replay(job):
    answer = client().send_message(
        job["messages"], dedent_messages=False, response_format=CognitiveActionsModel,
        max_completion_tokens=job["max_completion_tokens"],
        frequency_penalty=0.0, presence_penalty=0.0,
    )
    if answer is None:
        raise RuntimeError(f"No actor response for {job['name']}/{job['condition']}.")
    result = json.loads(answer["content"])
    CognitiveActionsModel.model_validate(result)
    job["result"] = result
    public = lambda data: [a["content"] for a in data["actions"] if a["type"] == "TALK"]
    print(json.dumps({
        "name": job["name"], "condition": job["condition"],
        "baseline_public": public(job["baseline"]), "candidate_public": public(result),
    }, ensure_ascii=False), flush=True)
    return job


with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(replay, jobs))
(output / "results.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(encoding="utf-8"))["models"]["gpt-6-luna"]
cache = json.loads((output / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == len(jobs) == 6
usage = cost_for_run(output, {
    "started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(r["created"] for r in cache.values()) + 1,
}, prices)
(output / "receipt.json").write_text(json.dumps({
    "returned_responses": len(cache), "returned_usage_estimate": usage,
    "generator_template_sha256": hashlib.sha256(
        (REPO / "tinytroupe" / "factory" / "prompts" / "generate_person.mustache").read_bytes()
    ).hexdigest(),
    "scope": "Frozen first-turn actor replays, not full simulations or empirical validation. "
             "The historical full-run quality audit is in plan.json; these raw candidates "
             "have not been through the action-quality correction pipeline.",
}, indent=2), encoding="utf-8")
