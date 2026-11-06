"""Screen a compact closed-vocabulary representation with unchanged semantic requirements."""

import copy
import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from tinytroupe import config_manager
from tinytroupe.clients import client, force_api_cache
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.factory.sampling import sampling_plan_spec, restore_sampling_plan
from review_notebook_evidence import cost_for_run

OUTPUT = ROOT / "realized-behavior-coverage-compact"
OUTPUT.mkdir()
original = json.loads((ROOT / "realized-behavior-coverage" /
    "production_baseline_replication.json").read_text(encoding="utf-8"))
revision = json.loads((ROOT / "realized-behavior-coverage-r2" /
    "plan.json").read_text(encoding="utf-8"))
parameters = original["parameters"]
dimensions = parameters["sampling_dimensions"]["dimensions"]
_, schema = sampling_plan_spec(parameters)
schema = copy.deepcopy(schema)
properties = schema["json_schema"]["schema"]["properties"]["sample_plan"]["items"][
    "properties"]["sampled_values"]["properties"]
for index, dimension in enumerate(dimensions, 1):
    if "values" in dimension:
        properties[str(index)]["anyOf"][0] = {
            "type": "array", "items": {"type": "integer",
                                      "enum": list(range(1, len(dimension["values"]) + 1))},
            "minItems": 1, "maxItems": len(dimension["values"]),
        }
messages = copy.deepcopy(original["messages"])
marker = "Population eligibility is mandatory in every directive"
text = messages[0]["content"].replace(marker, revision["candidate_paragraph"] + "\n" + marker)
changes = [
    ("- For a categorical dimension you constrain, return the schema's option-membership object. "
     "Every option has exactly one boolean slot: true means allowed; false means excluded. "
     "Select at least one option.",
     "- For a categorical dimension you constrain, return a nonempty list of its allowed "
     "option identifiers as integers. Select each identifier at most once."),
    (" Do not return an all-false object instead.", ""),
    ("Option membership and null are explicit intermediate representations.",
     "Option identifiers and null are explicit intermediate representations."),
]
for before, after in changes:
    assert text.count(before) == 1
    text = text.replace(before, after)
messages[0]["content"] = text
(OUTPUT / "plan.json").write_text(json.dumps({
    "hypothesis": "Full repeated boolean membership slots may distract from global coverage "
                  "constraints; compact identifier lists reduce output bureaucracy without "
                  "changing categorical meanings, counts, eligibility or output effort.",
    "parameters": parameters, "messages": messages, "response_format": schema,
    "comparison": "Revision 2 semantic instructions and original input; only the structured "
                  "selection representation and its necessary instructions differ.",
    "targeted_options": revision["targeted_options"],
    "acceptance": revision["acceptance"],
    "production_changed": False,
    "production_prompt_sha256": revision["production_prompt_sha256"],
    "system_message_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
}, ensure_ascii=False, indent=2), encoding="utf-8")
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(OUTPUT / "api.cache.json"))
response = client().send_message(messages, dedent_messages=False, response_format=schema)
if response is None:
    raise RuntimeError("Compact plan returned no response.")
value = json.loads(response["content"])
(OUTPUT / "native-response.json").write_text(
    json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
)
membership = copy.deepcopy(value)
for directive in membership["sample_plan"]:
    selections = directive["sampled_values"]
    for index, dimension in enumerate(dimensions, 1):
        selected = selections[str(index)]
        if "values" not in dimension or selected is None:
            continue
        if (not isinstance(selected, list) or not selected
                or any(type(option) is not int or not 1 <= option <= len(dimension["values"])
                       for option in selected)
                or len(set(selected)) != len(selected)):
            raise ValueError(f"Invalid categorical identifiers in directive {directive['id']}, "
                             f"dimension {index}: {selected}")
        selections[str(index)] = {
            str(option): option in selected for option in range(1, len(dimension["values"]) + 1)
        }
plan = restore_sampling_plan(parameters, membership)["sample_plan"]
(OUTPUT / "sampling-plan.json").write_text(
    json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
)
guaranteed = {
    name: {target: sum(d["quantity"] for d in plan
                      if d["sampled_values"].get(name) in (target, [target]))
           for target in targets}
    for name, targets in revision["targeted_options"].items()
}
factory = TinyPersonFactory()
coverage = {name: {target: [] for target in targets}
            for name, targets in revision["targeted_options"].items()}
dimension_by_name = {d["name"]: d for d in dimensions}
age_options = list(dimension_by_name["age_distribution"]["values"])
age_bounds = [(0, 14), (15, 24), (25, 54), (55, 64), (65, 110)]
age_errors = []
for directive in plan:
    selected = directive["sampled_values"]
    if "age" not in selected or "age_distribution" not in selected:
        age_errors.append(directive["id"])
        continue
    age = selected["age"]
    bounds = age if isinstance(age, list) else [age, age]
    groups = selected["age_distribution"]
    groups = groups if isinstance(groups, list) else [groups]
    if any(not (age_bounds[age_options.index(group)][0] <= bounds[0]
                <= bounds[-1] <= age_bounds[age_options.index(group)][1])
           for group in groups):
        age_errors.append(directive["id"])
for seed in range(100):
    factory.randomizer = random.Random(seed)
    samples = factory._flatten_sampling_plan(plan, sampling_dimensions=parameters["sampling_dimensions"])
    for name, targets in coverage.items():
        counts = Counter(sample.get(name) for sample in samples)
        for target in targets:
            targets[target].append(counts[target])
audit = {
    "directives": len(plan), "population": sum(d["quantity"] for d in plan),
    "guaranteed_predefined_contrasts": guaranteed,
    "all_four_predefined_contrasts_guaranteed": all(
        count > 0 for choices in guaranteed.values() for count in choices.values()
    ),
    "directives_with_unconstrained_or_incompatible_age_pairs": age_errors,
    "coverage_over_100_seeds": {
        name: {target: {"minimum": min(counts), "maximum": max(counts),
                        "seeds_without_value": counts.count(0)}
               for target, counts in targets.items()}
        for name, targets in coverage.items()
    },
    "semantic_review": "Pending; structural validity is not semantic acceptance or calibration.",
}
(OUTPUT / "audit.json").write_text(
    json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
)
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == 1
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {"started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(row["created"] for row in cache.values()) + 1}, prices)
(OUTPUT / "receipt.json").write_text(json.dumps({
    "returned_responses": len(cache), "returned_usage_estimate": usage,
    "scope": "One experimental identifier-list plan; no production changes or survey responses.",
}, indent=2), encoding="utf-8")
print(json.dumps(audit, ensure_ascii=False), flush=True)
