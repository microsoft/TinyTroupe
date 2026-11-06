"""Verify that the full-input vocabulary replication changes only the declared instruction."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT / "model-study"))
from model_case_study import decode_key

OUTPUT = ROOT / "cf6-coherent-dimensions"
original = json.loads((ROOT / "cf6-dimension-request.json").read_text(encoding="utf-8"))
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == 1
key, response = next(iter(cache.items()))
request, schema = decode_key(key)
before = original["request"]
assert schema is None
assert request["messages"][1:] == before["messages"][1:]
assert {k: v for k, v in request.items() if k != "messages"} == {
    k: v for k, v in before.items() if k != "messages"
}
new_lines = [
    "- each categorical option must identify one coherent characteristic that can be selected for an individual.",
    'Keep opposing ends as separate options, not a single option such as "strongly rejects novelty OR adopts everything impulsively".',
    "A list can contain both ends; one selected option must not leave the person's position between incompatible alternatives unresolved.",
    "Related reasons for the same characteristic can share an option, but opposite behaviors require distinct options.",
]
system = request["messages"][0]["content"]
lines = system.splitlines(keepends=True)
removed = [line.strip() for line in lines if line.strip() in new_lines]
assert removed == new_lines
assert "".join(line for line in lines if line.strip() not in new_lines) == (
    before["messages"][0]["content"]
)
assert response["choices"][0]["finish_reason"] == "stop"
native = json.loads(response["choices"][0]["message"]["content"])
dimensions = json.loads((OUTPUT / "dimensions.json").read_text(encoding="utf-8"))
assert dimensions == native
by_name = {d["name"]: d for d in dimensions["dimensions"]}
adoption = list(by_name["attitude_toward_new_products"]["values"])
food = list(by_name["culinary_tastes"]["values"])
assert len(adoption) >= 10 and len(food) >= 10
assert "impulsive" in adoption[8].lower()
assert "strongly rejects" in adoption[9].lower()
result = {
    "status": "passed",
    "full_population_input_unchanged": True,
    "nonmessage_model_options_unchanged": True,
    "only_system_change": new_lines,
    "production_method_and_json_mode": True,
    "native_response_matches_saved_dimensions": True,
    "reviewed_dimension_options": {
        "attitude_toward_new_products": adoption, "culinary_tastes": food,
    },
    "semantic_review": "The original combined rejection-or-impulsivity option is replaced "
                       "by separately selectable impulsive-trend buying and strong rejection "
                       "options. Traditional food and unfamiliar-cuisine exploration also "
                       "remain separately selectable. These are coherent individual "
                       "characteristics, not assigned purchase scores.",
    "scope": "A single full-original-input dimension replication, not exhaustive joint "
             "dimension validation, a full new population survey, or proof of calibration.",
}
(OUTPUT / "audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print("Full-input replication request fidelity and opposing-option review passed.")
