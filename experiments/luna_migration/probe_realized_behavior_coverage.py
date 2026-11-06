"""Compare illustrative contrast coverage without using any purchase responses."""

import ast
import argparse
import copy
import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from tinytroupe import config_manager, utils
from tinytroupe.clients import client, force_api_cache
from tinytroupe.factory import TinyPersonFactory
from tinytroupe.factory.sampling import sampling_plan_spec, restore_sampling_plan
from review_notebook_evidence import cost_for_run

ADDITION = """
Make explicitly requested behavioral contrasts survive the caller's random draws.
A long list of allowed alternatives does not guarantee that any particular contrast
will occur in a small realized sample. When eligibility and sample size permit,
reserve compatible directives that select just one value at each requested end of
the contrast, rather than allowing every relevant value only in mixed lists.
This is illustrative contrast coverage, not an estimate of those traits' prevalence.
Keep reported demographic proportions and eligibility constraints; do not force
rare demographic categories into equal shares or prescribe downstream decisions.
"""
MARKER = "Population eligibility is mandatory in every directive"
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--revision", type=int, choices=[1, 2], default=1)
args = parser.parse_args()
if args.revision == 2:
    ADDITION = """
Check realized contrast coverage before returning the plan. For each behavioral
family explicitly requested by the population specification, identify the opposing
ends in the supplied option meanings, including its stated extremes rather than
substituting only moderate alternatives.
When eligibility and sample size permit, give each requested end at least one
compatible directive that selects that option alone in that dimension. Quantities
can be one; other directives may retain mixed alternatives and supplied weights.
Count only these singleton allocations as guaranteed coverage. An extreme allowed
only in a mixed list can disappear when the caller draws the actual people.
Review the completed plan against those ends and revise missing allocations before
returning it, without overriding eligibility or reported demographic proportions.
This is illustrative contrast coverage, not an estimate of behavioral prevalence.
Do not equalize demographic categories or prescribe downstream decisions or scores.
"""
OUTPUT = ROOT / ("realized-behavior-coverage" if args.revision == 1
                 else "realized-behavior-coverage-r2")
OUTPUT.mkdir()

notebook = json.loads((ROOT / "cf5-gaz" /
    "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb"
).read_text(encoding="utf-8"))
displayed = {}
for cell in notebook["cells"]:
    source = "".join(cell["source"]).strip()
    if source in {"factory.sampling_dimensions", "factory.sampling_plan"}:
        for result in cell.get("outputs", []):
            text = "".join(result.get("data", {}).get("text/plain", []))
            if text:
                displayed[source] = ast.literal_eval(text)
dimensions = displayed["factory.sampling_dimensions"]
frozen_plan = displayed["factory.sampling_plan"]
if isinstance(frozen_plan, dict):
    frozen_plan = frozen_plan["sample_plan"]
dimension_by_name = {d["name"]: d for d in dimensions["dimensions"]}
cohort = json.loads((ROOT / "cf5-gaz" / "population-generation-evidence.json").read_text(
    encoding="utf-8"
))

namespace = {}
source_notebook = json.loads((REPO / "examples" /
    "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb"
).read_text(encoding="utf-8"))
for cell in source_notebook["cells"]:
    if cell["cell_type"] != "code":
        continue
    for node in ast.parse("".join(cell["source"])).body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "additional_demographic_specification"
            for target in node.targets
        ):
            exec(compile(ast.Module(body=[node], type_ignores=[]), "<notebook>", "exec"), namespace)
factory = TinyPersonFactory.create_factory_from_demography(
    str(REPO / "examples" / "information" / "populations" / "usa.json"),
    population_size=50,
    additional_demographic_specification=namespace["additional_demographic_specification"],
)
parameters = {
    "N": 50, "sampling_dimensions": dimensions,
    "max_quantity_per_sample_directive": 5, "min_sampling_directives": 10,
    "max_sampling_directives": 50, "enforce_usage_of_all_dimensions": False,
    "context": factory.context_text, "population_description": factory.sampling_space_description,
}
payload, schema = sampling_plan_spec(parameters)
messages = utils.compose_initial_LLM_messages_with_templates(
    "sampling_plan.system.mustache", "sampling_plan.user.mustache",
    base_module_folder="factory",
    rendering_configs={"parameters": json.dumps(payload, ensure_ascii=False)},
)
assert messages[0]["content"].count(MARKER) == 1
candidate = copy.deepcopy(messages)
candidate[0]["content"] = candidate[0]["content"].replace(MARKER, ADDITION + "\n" + MARKER)
assert candidate[1:] == messages[1:]
target_options = {
    "culinary_tastes": [dimension_by_name["culinary_tastes"]["values"][0],
                       dimension_by_name["culinary_tastes"]["values"][6]],
    "attitude_toward_new_products": [
        dimension_by_name["attitude_toward_new_products"]["values"][6],
        dimension_by_name["attitude_toward_new_products"]["values"][9],
    ],
}
assert "traditional" in target_options["culinary_tastes"][0]
assert "adventurous" in target_options["culinary_tastes"][1]
assert "strongly resistant" in target_options["attitude_toward_new_products"][0]
assert "extreme novelty" in target_options["attitude_toward_new_products"][1]


def allocations(plan, name):
    """Calculate expected categorical counts conditional on selected alternatives."""
    values = dimension_by_name[name]["values"]
    weights = values if isinstance(values, dict) else {value: 1 for value in values}
    expected, guaranteed = defaultdict(float), Counter()
    unconstrained = 0
    for directive in plan:
        selected = directive["sampled_values"].get(name)
        quantity = directive["quantity"]
        if selected is None:
            unconstrained += quantity
            continue
        allowed = selected if isinstance(selected, list) else [selected]
        total = sum(weights[value] for value in allowed)
        for value in allowed:
            expected[value] += quantity * weights[value] / total
        if len(allowed) == 1:
            guaranteed[allowed[0]] += quantity
    return {
        "unconstrained": unconstrained,
        "options": [
            {"value": value, "weight": weights[value], "expected": expected[value],
             "guaranteed": guaranteed[value]}
            for value in weights
        ],
    }


def review_plan(plan):
    """Measure coverage over fixed seeds, without looking at survey responses."""
    assert sum(d["quantity"] for d in plan) == 50
    coverage = {
        name: {value: [] for value in values} for name, values in target_options.items()
    }
    age_options = list(dimension_by_name["age_distribution"]["values"])
    age_bands = [(0, 14), (15, 24), (25, 54), (55, 64), (65, 120)]
    invalid_age_pairs = 0
    missing_age_pairs = 0
    for seed in range(100):
        factory.randomizer = random.Random(seed)
        samples = factory._flatten_sampling_plan(plan, sampling_dimensions=dimensions)
        for sample in samples:
            if "age" not in sample or "age_distribution" not in sample:
                missing_age_pairs += 1
                continue
            age = sample["age"]
            declared = sample["age_distribution"]
            lower, upper = age_bands[age_options.index(declared)]
            invalid_age_pairs += not lower <= age <= upper
        for name, choices in coverage.items():
            counts = Counter(sample.get(name) for sample in samples)
            for value in choices:
                choices[value].append(counts[value])
    return {
        "directives": len(plan),
        "categorical_allocations": {
            name: allocations(plan, name)
            for name in [
                "age_distribution", "gender", "race_and_ethnicity",
                "geographic_region", "settlement_type",
                "culinary_tastes", "attitude_toward_new_products",
            ]
        },
        "targeted_coverage_over_100_seeds": {
            name: {
                value: {"minimum": min(counts), "maximum": max(counts),
                        "seeds_without_value": counts.count(0)}
                for value, counts in choices.items()
            }
            for name, choices in coverage.items()
        },
        "inconsistent_numeric_age_vs_age_group": invalid_age_pairs,
        "unconstrained_numeric_age_or_age_group": missing_age_pairs,
        "scope": "A stratified illustrative coverage audit, not a population calibration. "
                 "A permitted option is not a guaranteed realized observation.",
    }


original_audit = review_plan(frozen_plan)
for name, data in original_audit["categorical_allocations"].items():
    actual = Counter(person["draws"].get(name) for person in cohort)
    for option in data["options"]:
        option["observed_cf5"] = actual[option["value"]]
(OUTPUT / "frozen-cohort-audit.json").write_text(
    json.dumps(original_audit, ensure_ascii=False, indent=2), encoding="utf-8"
)
(OUTPUT / "plan.json").write_text(json.dumps({
    "created_at": datetime.now(timezone.utc).isoformat(),
    "hypothesis": "Explicitly requested endpoints can disappear when only allowed "
                  "as members of multi-option lists; actual coverage needs compatible "
                  "singleton allocations, not a downstream rating target.",
    "conditions": (["production_baseline_replication", "concrete_contrast_coverage"]
                   if args.revision == 1 else ["concrete_contrast_coverage_v2"]),
    "revision": args.revision,
    "comparison": "Revision 2 retains the first experiment's baseline; no baseline redraw.",
    "constants": "Original 79 dimensions, original population description, sample size 50, "
                 "bounds/count limits, optional fields, strict closed-vocabulary schema, "
                 "model gpt-6-luna and effort xhigh.",
    "candidate_paragraph": ADDITION,
    "production_prompt_sha256": hashlib.sha256(
        (REPO / "tinytroupe" / "factory" / "prompts" / "sampling_plan.system.mustache").read_bytes()
    ).hexdigest(),
    "targeted_options": target_options,
    "acceptance": "Actual guaranteed coverage of the four predefined requested contrast ends; "
                  "valid counts and schema; preserved approximate supplied demographic "
                  "proportions; age/group compatibility and subsequent manual joint-eligibility "
                  "review. Do not select or redraw based on survey ratings.",
    "production_changed": False,
}, ensure_ascii=False, indent=2), encoding="utf-8")
config_manager.update("model", "gpt-6-luna")
config_manager.update("reasoning_model", "gpt-6-luna")
config_manager.update("reasoning_effort", "xhigh")
config_manager.update("timeout", 600)
force_api_cache(True, str(OUTPUT / "api.cache.json"))


def execute(condition, request_messages):
    response = client().send_message(
        request_messages, dedent_messages=False, response_format=schema,
    )
    if response is None:
        raise RuntimeError(f"No response for {condition}.")
    restored = restore_sampling_plan(parameters, json.loads(response["content"]))["sample_plan"]
    result = {
        "condition": condition, "messages": request_messages,
        "parameters": parameters, "sampling_plan": restored,
    }
    (OUTPUT / f"{condition}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return condition, restored


with ThreadPoolExecutor(max_workers=2) as executor:
    conditions = ([("production_baseline_replication", messages),
                   ("concrete_contrast_coverage", candidate)] if args.revision == 1
                  else [("concrete_contrast_coverage_v2", candidate)])
    futures = [executor.submit(execute, condition, request)
               for condition, request in conditions]
    results = [future.result() for future in futures]
for condition, restored in results:
    audit = review_plan(restored)
    (OUTPUT / f"{condition}-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({
        "condition": condition, "directives": audit["directives"],
        "coverage": audit["targeted_coverage_over_100_seeds"],
        "age_group_inconsistencies": audit["inconsistent_numeric_age_vs_age_group"],
    }, ensure_ascii=False), flush=True)
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == len(conditions)
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {
    "started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(row["created"] for row in cache.values()) + 1,
}, prices)
(OUTPUT / "receipt.json").write_text(json.dumps({
    "status": f"{len(results)} plans returned; coverage audited and semantic review still required.",
    "returned_responses": len(cache), "returned_usage_estimate": usage,
}, indent=2), encoding="utf-8")
