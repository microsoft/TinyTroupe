"""Audit the completed real pipeline without reinterpreting private thoughts as responses."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key
from review_notebook_evidence import cost_for_run

folder = ROOT / "realized-coverage-pipeline"
load = lambda name: json.loads((folder / name).read_text(encoding="utf-8"))
protocol = load("protocol.json")
selected = load("selected-characteristics.json")
people = load("personas.json")
histories = load("agents.json")
results = {row["name"]: row for row in load("results.json")}
assert len(people) == len(results) == len(histories) == len(selected) == 6
assert set(people) == set(results) == set(histories) == {p["name"] for p in selected}
cache = load("api.cache.json")
assert len({response["id"] for response in cache.values()}) == len(cache)
generated = {}
for key, response in cache.items():
    request, schema = decode_key(key)
    assert request["model"] == "gpt-6-luna" and request["reasoning_effort"] == "xhigh"
    if request.get("response_format") == {"type": "json_object"}:
        body = json.loads(response["choices"][0]["message"]["content"])
        if isinstance(body, dict) and "name" in body and "age" in body:
            assert response["choices"][0]["finish_reason"] == "stop"
            generated[body["name"]] = body
assert set(generated) == set(people)
for name, raw in generated.items():
    assert all(people[name][key] == value for key, value in raw.items())
    assert {key: value for key, value in people[name].items() if key not in raw} == {
        "country_of_residence": None,
    }
rows = []
for chosen, role in zip(selected, protocol["roles"]):
    name = chosen["name"]
    assert people[name]["age"] == chosen["age"]
    public = []
    for event in histories[name]:
        content = event.get("content")
        if isinstance(content, dict):
            action = content.get("action", {})
            if action.get("type") == "TALK":
                public.append(action["content"])
    result = results[name]
    score = result["response"]
    if score != "N/A":
        assert score in {"1", "2", "3", "4", "5"} and public
        assert any(re.search(rf"\b{score}\b", speech) for speech in public)
        assert isinstance(result["justification"], str)
        assert any(result["justification"] in speech for speech in public)
    else:
        assert chosen["age"] == 1 and result["justification"] is None
    rows.append({
        "name": name, "age": chosen["age"], "preselected_role": role,
        "response": score, "justification": result["justification"],
        "last_public_speech": public[-1] if public else None,
        "generated_relevant_preferences": {
            key: value for key, value in people[name].get("preferences", {}).items()
            if any(word in key.lower() for word in ["culinar", "new_product"])
        },
    })
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(folder, {"started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(response["created"] for response in cache.values()) + 1}, prices)
summary = {
    "protocol_status": "passed",
    "people": 6, "returned_responses": len(cache),
    "generator_production_json_mode_verified": True,
    "persona_normalization": "All generated fields are unchanged; TinyPerson adds its "
                             "default country_of_residence=None field.",
    "names_and_ages_preserved": True,
    "adult_justifications_are_public_substrings": True,
    "infant_nonanswer_preserved": True,
    "returned_usage_estimate": usage,
    "rows": rows,
    "scope": "A preselected contrast integration screen; not an independent full survey "
             "rerun, representative panel or causal calibration estimate.",
}
(ROOT / "realized-coverage-pipeline-audit.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps({
    "protocol_status": summary["protocol_status"], "responses": len(cache),
    "returned_usage_usd": usage["usd"],
    "rows": [{"name": row["name"], "age": row["age"], "response": row["response"],
              "public": row["last_public_speech"]} for row in rows],
}, ensure_ascii=False, indent=2))
