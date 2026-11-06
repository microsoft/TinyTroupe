"""Audit a fresh production plan without repairing or redrawing its selections."""

import argparse
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from model_case_study import decode_key
from run_notebook_comparison import library_fingerprint
from tinytroupe import utils
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.factory.sampling import restore_sampling_plan, sampling_plan_spec

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--folder", default="integrated-coverage-plan")
args = parser.parse_args()
OUTPUT = ROOT / args.folder


def load(name):
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


protocol = load("protocol.json")
parameters = protocol["parameters"]
assert library_fingerprint(REPO / "tinytroupe") == protocol["library_sha256"]
payload, schema = sampling_plan_spec(parameters)
messages = utils.compose_initial_LLM_messages_with_templates(
    "sampling_plan.system.mustache", "sampling_plan.user.mustache",
    base_module_folder="factory",
    rendering_configs={"parameters": json.dumps(payload, ensure_ascii=False)},
)
if "candidate_paragraph" in protocol:
    marker = "Quantities must be positive integers summing to exactly N."
    assert messages[0]["content"].count(marker) == 1
    messages[0]["content"] = messages[0]["content"].replace(
        marker, protocol["candidate_paragraph"] + "\n" + marker
    )
    assert messages == protocol["messages"]
for message in messages:
    if isinstance(message.get("content"), str):
        message["content"] = utils.dedent(message["content"])
cache = load("api.cache.json")
assert len(cache) == 1
key, response = next(iter(cache.items()))
request, extra_schema = decode_key(key)
assert extra_schema is None
assert request["model"] == "gpt-6-luna"
assert request["reasoning_effort"] == "xhigh"
assert request["messages"] == messages
assert request["response_format"] == schema
assert response["choices"][0]["finish_reason"] == "stop"
native = json.loads(response["choices"][0]["message"]["content"])
plan = restore_sampling_plan(parameters, native)["sample_plan"]
assert plan == load("sampling-plan.json")

dimensions = {d["name"]: d for d in parameters["sampling_dimensions"]["dimensions"]}
age_options = list(dimensions["age_distribution"]["values"])
age_bands = [(0, 14), (15, 24), (25, 54), (55, 64), (65, 110)]
age_errors, eligibility_errors, covered_ages = [], [], set()
age_allocations = Counter()
condensed = []
for directive in plan:
    selected = directive["sampled_values"]
    numeric = selected.get("age")
    bounds = numeric if isinstance(numeric, list) else [numeric, numeric]
    groups = selected.get("age_distribution")
    groups = groups if isinstance(groups, list) else [groups]
    if (numeric is None or None in groups or any(
        not age_bands[age_options.index(group)][0]
        <= bounds[0] <= bounds[-1] <= age_bands[age_options.index(group)][1]
        for group in groups
    )):
        age_errors.append(directive["id"])
    else:
        covered_ages.update(range(int(bounds[0]), int(bounds[-1]) + 1))
    if len(groups) == 1 and groups[0] is not None:
        age_allocations[groups[0]] += directive["quantity"]
    if selected.get("country_of_residence") != dimensions["country_of_residence"]["values"][0]:
        eligibility_errors.append(directive["id"])
    full_vocabularies = {
        name for name, value in selected.items()
        if isinstance(value, list) and "values" in dimensions[name]
        and value == list(dimensions[name]["values"])
    }
    condensed.append({
        "id": directive["id"], "quantity": directive["quantity"],
        "description": directive["subpopulation_description"],
        "selected": {name: value for name, value in selected.items()
                     if name not in {"age_distribution", "country_of_residence"}
                     and name not in full_vocabularies},
        "independently_drawn_full_vocabularies": sorted(full_vocabularies),
    })

factory = TinyPersonFactory(context=parameters["context"])
draw_issues, demographics = [], {}
for seed in range(100):
    factory.randomizer = random.Random(seed)
    samples = factory._flatten_sampling_plan(
        plan, sampling_dimensions=parameters["sampling_dimensions"]
    )
    assert len(samples) == parameters["N"]
    for sample in samples:
        if not any(low <= sample.get("age", -1) <= high
                   and sample.get("age_distribution") == group
                   for group, (low, high) in zip(age_options, age_bands)):
            draw_issues.append({"seed": seed, "sample": sample})
    for name in ["age_distribution", "gender", "race_and_ethnicity",
                 "geographic_region", "settlement_type"]:
        counts = Counter(sample.get(name, "<unconstrained>") for sample in samples)
        values = set(dimensions[name]["values"]) | {"<unconstrained>"}
        for value in values:
            demographics.setdefault(name, {}).setdefault(value, []).append(counts[value])

result = {
    "request_and_exact_reconstruction": "passed",
    "response_id": response["id"], "library_sha256": protocol["library_sha256"],
    "population": sum(d["quantity"] for d in plan), "directives": len(plan),
    "incompatible_or_unconstrained_age_directives": age_errors,
    "uncovered_integer_ages": sorted(set(range(111)) - covered_ages),
    "missing_explicit_residence_directives": eligibility_errors,
    "incompatible_age_draws_over_100_seeds": draw_issues,
    "singleton_age_allocations": age_allocations,
    "demographic_draw_counts_over_100_seeds": {
        name: {value: {"minimum": min(counts), "maximum": max(counts),
                       "mean": sum(counts) / len(counts)}
               for value, counts in values.items() if max(counts)}
        for name, values in demographics.items()
    },
    "scope": "One fresh plan and 100 fixed drawing seeds, not 100 model replications "
             "or proof of demographic representativeness. Joint semantic review is separate.",
    "request_normalization": "Expected template messages receive exactly the production "
                             "client's utils.dedent preprocessing before wire comparison.",
}
(OUTPUT / "structural-audit.json").write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
)
(OUTPUT / "condensed-plan.json").write_text(
    json.dumps(condensed, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps(result, ensure_ascii=False, indent=2))
