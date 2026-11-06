"""Replay observed biography-generation failures with an explicit planning boundary."""

import copy
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
from tinytroupe.clients import client, force_api_cache

ADDITION = """
The population description may also include instructions for constructing a sampling
space, such as defining dimensions and their possible values. Those instructions
belong to population planning, not this person's biography. Use the sampled values
in Agent Particularities to describe this one person. Do not output population-wide
catalogs, alternative trait values, sampling plans, or demographic distributions as
persona fields. Preserve eligibility and the person's actual traits; the possible
values for other people are not additional traits of this person.
"""
MARKER = "Do not substitute someone who could answer hypothetically for an eligible member."
NAMES = ["Diego Andr\u00e9s Quintana", "Marco Antonio Salazar", "Gabriel Leon Sandoval"]
output = ROOT / "population-scope-trial"
output.mkdir(exist_ok=True)
people = json.loads(
    (ROOT / "cf5-gaz" / "population-generation-evidence.json").read_text(encoding="utf-8")
)
expected = {row["name"]: row for row in people if row["name"] in NAMES}
cache = json.loads((ROOT / "cf5-gaz" / "api.cache.json").read_text(encoding="utf-8"))
selected = {}
for key, response in cache.items():
    if "- Name, demographics and other characteristics:" not in key:
        continue
    request, schema = decode_key(key)
    if schema is not None:
        continue
    persona = json.loads(response["choices"][0]["message"]["content"])
    name = persona.get("name")
    if name not in expected:
        continue
    normalized = lambda p: {k: v for k, v in p.items() if v is not None}
    if normalized(persona) != normalized(expected[name]["persona"]):
        continue
    assert request["model"] == "gpt-6-luna"
    assert request["reasoning_effort"] == "xhigh"
    assert request["messages"][-1]["content"].count(MARKER) == 1
    selected[name] = (request, persona)
assert set(selected) == set(NAMES)
(output / "plan.json").write_text(json.dumps({
    "created_at": datetime.now(timezone.utc).isoformat(),
    "names": NAMES,
    "selection": "Three observed catalog-bearing biographies: food-adventurous early adopter, "
                 "traditional-food early adopter, and a novelty-resistant adult.",
    "intervention": ADDITION,
    "constants": "Original generator messages, individual sampled characteristics, eligibility, "
                 "model, effort and output-token limit; only the planning-boundary paragraph changes.",
    "outcomes": "Catalog removal and retained individual traits. Subsequent ratings, if tested, "
                "are not an acceptance criterion for this source-fidelity repair.",
    "scope": "New biography elaborations, not unchanged-persona actor comparisons or empirical validation.",
}, ensure_ascii=False, indent=2), encoding="utf-8")
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(output / "api.cache.json"))


def replay(name):
    request, before = selected[name]
    messages = copy.deepcopy(request["messages"])
    messages[-1]["content"] = messages[-1]["content"].replace(MARKER, MARKER + "\n\n" + ADDITION)
    reply = client().send_message(
        messages, dedent_messages=False, model=request["model"],
        max_completion_tokens=request.get("max_completion_tokens"),
        frequency_penalty=request.get("frequency_penalty", 0.0),
        presence_penalty=request.get("presence_penalty", 0.0),
    )
    if reply is None:
        raise RuntimeError(f"No returned generator response for {name}.")
    after = json.loads(reply["content"])
    assert after["name"] == name and after["age"] == before["age"], name
    result = {
        "name": name, "draws": expected[name]["draws"],
        "before": before, "after": after, "messages": messages,
        "before_chars": len(json.dumps(before)), "after_chars": len(json.dumps(after)),
        "before_dimension_fields": [k for k in before if re.search(r"dimension|sampling|catalog", k)],
        "after_dimension_fields": [k for k in after if re.search(r"dimension|sampling|catalog", k)],
    }
    (output / (name.split()[0] + ".json")).write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items()
                      if k not in {"draws", "before", "after", "messages"}}, ensure_ascii=False), flush=True)
    return result


with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(replay, NAMES))
assert all(not row["after_dimension_fields"] for row in results)
(output / "receipt.json").write_text(json.dumps({
    "status": "All three returned; identities/ages preserved and no dimension/catalog fields emitted.",
    "cases": len(results), "usage_snapshot": client().get_cost_stats(),
    "scope": "Individual biography content still requires manual semantic review.",
}, indent=2), encoding="utf-8")
