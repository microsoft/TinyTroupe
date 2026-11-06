"""Audit completed paired JSON-mode replays without inferring their semantic verdict."""

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key

folder = ROOT / "generator-example-ablation-json-mode"
plan = json.loads((folder / "plan.json").read_text(encoding="utf-8"))
receipt = json.loads((folder / "receipt.json").read_text(encoding="utf-8"))
assert receipt["generator_responses"] == receipt["generated_biographies"] == 6
assert receipt["actor_turns"] == 6 and receipt["observed_generation_failures"] == 0
assert receipt["production_template_unchanged"]
template = REPO / "tinytroupe" / "factory" / "prompts" / "generate_person.mustache"
assert hashlib.sha256(template.read_bytes()).hexdigest() == plan["production_template_sha256"]
assert hashlib.sha256((folder / "candidate.mustache").read_text(
    encoding="utf-8"
).encode("utf-8")).hexdigest() == plan["candidate_sha256"]
historical = {
    row["name"]: row for row in json.loads(
        (ROOT / "population-scope-actor-replays" / "results.json").read_text(encoding="utf-8")
    )
    if row["condition"] == "regenerated_biography"
}
cache = json.loads((folder / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == len({row["id"] for row in cache.values()}) == 12
generation_requests = {}
actor_requests = {}
for key, response in cache.items():
    request, schema = decode_key(key)
    assert request["model"] == "gpt-6-luna"
    assert request["reasoning_effort"] == "xhigh"
    assert response["choices"][0]["finish_reason"] == "stop"
    result = json.loads(response["choices"][0]["message"]["content"])
    if schema is None:
        assert request["response_format"] == {"type": "json_object"}
        condition = (
            "examples_retained_replication"
            if "## Examples" in request["messages"][-1]["content"]
            else "unrelated_examples_removed"
        )
        generation_requests[(result["name"], condition)] = (request, result)
    else:
        assert schema == "tinytroupe.agent.CognitiveActionsModel"
        actor_requests[json.dumps(request["messages"], sort_keys=True)] = result
assert len(generation_requests) == len(actor_requests) == 6

rows = []
for path in sorted(folder.glob("*-biography.json")):
    job = json.loads(path.read_text(encoding="utf-8"))
    request, persona = generation_requests[(job["name"], job["condition"])]
    assert request["messages"] == job["messages"] and persona == job["persona"]
    for key, value in job["generation_options"].items():
        assert request[key] == value
    expected = job["historical_scoped_persona"]
    assert persona["name"] == expected["name"] and persona["age"] == expected["age"]
    actor = json.loads(path.with_name(path.name.replace(
        "-biography.json", "-actor.json"
    )).read_text(encoding="utf-8"))
    captured = historical[job["name"]]
    assert actor["messages"][1:] == captured["messages"][1:]
    split_persona = lambda s: s.split("## Persona", 1)
    prefix, section = split_persona(actor["messages"][0]["content"])
    old_prefix, old_section = split_persona(captured["messages"][0]["content"])
    assert prefix == old_prefix
    match = re.search(r"```json\s*(.*?)```", section, re.S)
    old_match = re.search(r"```json\s*(.*?)```", old_section, re.S)
    assert json.loads(match[1]) == persona
    assert section[:match.start(1)] == old_section[:old_match.start(1)]
    assert section[match.end(1):] == old_section[old_match.end(1):]
    assert actor_requests[json.dumps(actor["messages"], sort_keys=True)] == actor["result"]
    rows.append({
        "name": job["name"], "condition": job["condition"],
        "sampled_culinary_traits": {
            key: value for key, value in job["sampled_characteristics"].items()
            if any(word in key.lower() for word in ["culinar", "new_product"])
        },
        "generated_culinary_preferences": {
            key: value for key, value in persona["preferences"].items()
            if any(word in key.lower() for word in ["culinar", "cuisine", "food"])
        } if isinstance(persona["preferences"], dict) else persona["preferences"],
        "public": [
            action["content"] for action in actor["result"]["actions"]
            if action["type"] == "TALK"
        ],
        "possible_planning_fields": [
            key for key in persona if re.search(r"dimension|sampling|catalog", key, re.I)
        ],
    })

for name in historical:
    retained = generation_requests[(name, "examples_retained_replication")][0]
    removed = generation_requests[(name, "unrelated_examples_removed")][0]
    assert {k: v for k, v in retained.items() if k != "messages"} == {
        k: v for k, v in removed.items() if k != "messages"
    }
    assert retained["messages"][:-1] == removed["messages"][:-1]
    expected = retained["messages"][-1]["content"].split("## Examples", 1)[0].replace(
        "The format for this JSON response is as described in the examples.",
        "The response is one JSON object with the fields listed below. Complex fields "
        "may use nested JSON objects, arrays, or descriptive strings, as appropriate.",
    ).rstrip() + "\n"
    assert expected == removed["messages"][-1]["content"]

summary = {
    "protocol_status": "Passed",
    "semantic_verdict": "Review public responses and sampled traits separately; protocol "
                        "fidelity does not establish empirical calibration.",
    "paired_people": 3,
    "generator_responses": 6,
    "actor_responses": 6,
    "production_json_mode_preserved": True,
    "production_template_sha256": plan["production_template_sha256"],
    "candidate_sha256": plan["candidate_sha256"],
    "candidate_hash_basis": "UTF-8 of newline-normalized candidate text; exact sent "
                            "messages are independently matched against saved requests.",
    "returned_usage_estimate": receipt["returned_usage_estimate"],
    "prior_out_of_contract_screen": {
        "folder": "generator-example-ablation",
        "generator_responses": 6, "valid_biographies": 5, "actor_responses": 5,
        "malformed_json": 1,
        "caveat": "The missing JSON-output flag means this syntax failure is not evidence "
                  "of a production regression. No replacement was drawn.",
        "returned_usage_estimate": json.loads(
            (ROOT / "generator-example-ablation" / "receipt.json").read_text(encoding="utf-8")
        )["returned_usage_estimate"],
    },
    "rows": rows,
}
(ROOT / "generator-example-ablation-audit.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps({
    "protocol_status": summary["protocol_status"],
    "responses": 12,
    "returned_usage_usd": receipt["returned_usage_estimate"]["usd"],
}, indent=2))
