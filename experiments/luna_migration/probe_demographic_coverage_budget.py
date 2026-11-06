"""Test marginal-budget accounting without tuning any downstream survey rating."""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from run_notebook_comparison import library_fingerprint
from tinytroupe import config_manager, utils
from tinytroupe.clients import client, force_api_cache
from tinytroupe.factory.sampling import restore_sampling_plan, sampling_plan_spec
from review_notebook_evidence import cost_for_run

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--revision", type=int, choices=[1, 2, 3, 4], default=1)
args = parser.parse_args()
OUTPUT = ROOT / ("demographic-coverage-budget" if args.revision == 1
                 else f"demographic-coverage-budget-r{args.revision}")
OUTPUT.mkdir()
baseline = json.loads((ROOT / "integrated-coverage-plan" / "protocol.json").read_text(
    encoding="utf-8"
))
parameters = baseline["parameters"]
payload, schema = sampling_plan_spec(parameters)
messages = utils.compose_initial_LLM_messages_with_templates(
    "sampling_plan.system.mustache", "sampling_plan.user.mustache",
    base_module_folder="factory",
    rendering_configs={"parameters": json.dumps(payload, ensure_ascii=False)},
)
paragraph = """
## Account for fixed allocations before filling demographic budgets

Illustrative behavioral coverage must fit inside the demographic sample, not be
added on top of it. For each supplied demographic marginal, review the finished
plan's expected count for every option. A singleton contributes its full quantity.
A mixed list contributes its quantity times that option's supplied weight divided
by the sum of the weights in that list; without supplied weights, use equal shares.
Include both kinds of contribution. Giving a rare demographic category a fixed
allocation and then offering it at its original weight throughout the remaining
directives can overrepresent it.

Allocate approximately N times each supplied demographic proportion, allowing
integer rounding. Introduce relevant behavioral and cultural contrasts within
those allocations. When a cultural background fixes a demographic category,
account for that quantity in the remaining demographic budget. Do not change
the supplied weights or invent joint demographic frequencies.

Likewise, a supplied education marginal does not say that all older adults have
the same qualification. Preserve compatible educational variation across adult
age bands rather than assigning every member of one band the same attainment
solely to make a compact plan. Eligibility can exclude incompatible options;
it does not establish unreported correlations between age, schooling, ethnicity,
income, politics, or personal preferences.
"""
if args.revision == 2:
    paragraph += """
An illustration: in a sample of ten with a supplied category share of 20%, the
category's total budget is two people. Reserving one person for a compatible
cultural profile leaves one, not another 20% of the nine remaining people.
Removing one fully allocated category from a mixed list also renormalizes every
remaining weight; it does not automatically make their residual budgets correct.
Review all categories after such exclusions, not only the category removed.
When residual mixed-list arithmetic is difficult to represent, use explicit
singleton demographic allocations with rounded quantities instead. Allocate
behavioral contrasts within those budgets, without prescribing their decisions.

Nominal categories such as ethnic or cultural backgrounds have no ordinal
extremes. Relevant cultural variety does not require equal quotas for every
background or a new guaranteed person for every supplied label. Preserve the
population's demographic proportions rather than treating nominal labels like
opposing ends of an attitude scale.
"""
if args.revision in {3, 4}:
    paragraph = """
## Preserve weighted demographic choices when defining behavioral contrasts

When only marginal proportions are supplied, a behavioral contrast does not
establish a different demographic distribution. Within a directive, retain
the complete supplied weighted option set for each compatible nominal
demographic dimension rather than selecting one category to make the profile
distinctive. The caller can then draw from those original proportions in every
behavioral group. Restrict a demographic option set only for a stated eligibility
condition, an explicitly requested demographic stratum, or a genuine compatibility
constraint; do not invent that restriction from a personality or taste.

For example, contrasting adventurous and traditional tastes does not require
assigning different races, genders or regions to those two groups. Each group can
allow all supplied options with their original weights. This preserves expected
marginal proportions without requiring residual demographic arithmetic after each
behavioral allocation. It does not guarantee every rare demographic category
appears in a small realized sample or establish measured joint prevalence.

Where two optional dimensions encode the same demographic fact at different levels
of detail, retain one weighted description and leave the redundant dimension
unconstrained if independent draws would conflict. A full race list combined with
independently drawn race-specific cultural profiles is not coherent. Do not fix a
rare race merely to showcase a cultural profile. Cultural influences that do not
imply a particular race can still be varied. Apply the same compatibility check
to region and state, and to educational attainment and learning profiles.

Keep required age strata and supplied age proportions. Within eligible adult
bands, allow the supplied range of educational attainment unless another explicit
restriction genuinely excludes an option. Do not assign everyone in an older band
advanced education merely to produce a compact profile. An optional learning
profile can remain unconstrained rather than contradicting an allowed attainment.
Retain the requested behavioral singleton contrasts within these demographic
choices; neither a demographic label nor a survey rating is a behavioral contrast.
"""
if args.revision == 4:
    paragraph += """
Compatibility still takes precedence over retaining full option sets. A job that
requires a particular qualification cannot be drawn independently of attainment
options that exclude that qualification. If the job dimension is optional, leave
it unconstrained rather than assigning everyone a degree to accommodate a possible
job. If both dimensions are required, use mutually compatible alternatives or
separate compatible directives while respecting the supplied marginal budgets.
"""
marker = "Quantities must be positive integers summing to exactly N."
assert messages[0]["content"].count(marker) == 1
messages[0]["content"] = messages[0]["content"].replace(marker, paragraph + "\n" + marker)
protocol = {
    "library_sha256": library_fingerprint(REPO / "tinytroupe"),
    "parameters": parameters, "messages": messages, "response_format": schema,
    "candidate_paragraph": paragraph,
    "baseline": "integrated-coverage-plan/sampling-plan.json",
    "hypothesis": (
        "Preserving full compatible weighted demographic alternatives inside behavioral "
        "directives avoids residual-budget arithmetic and unsupported demographic "
        "stereotypes; omit redundant optional descriptions that cannot be drawn coherently."
        if args.revision in {3, 4} else
        "Fixed cultural/behavioral allocations are not deducted from remaining "
        "demographic budgets; explicit expected-count accounting may preserve "
        "contrasts without this marginal distortion or age-education collapse."
    ),
    "acceptance": {
        "exact_original_size_and_validity": True,
        "all_four_predefined_singleton_endpoints": True,
        "race_gender_region_settlement_expected_total_variation_people_at_most": 1.0,
        "age_totals": [9, 7, 20, 6, 8],
        "adult_age_bands_55_64_and_65_plus_education_support": "At least two compatible "
            "attainment options permitted in each band; no empirical joint prevalence inferred.",
    },
    "scope": "One prospective prompt test against the frozen fresh baseline; no rating "
             "data, model substitution, source edit, repaired response, or baseline redraw.",
}
(OUTPUT / "protocol.json").write_text(
    json.dumps(protocol, ensure_ascii=False, indent=2), encoding="utf-8"
)
for key, value in [("model", "gpt-6-luna"), ("reasoning_model", "gpt-6-luna"),
                   ("reasoning_effort", "xhigh"), ("timeout", 600)]:
    config_manager.update(key, value)
force_api_cache(True, str(OUTPUT / "api.cache.json"))
response = client().send_message(messages, response_format=schema)
if not response or not response.get("content"):
    raise RuntimeError("Demographic-budget candidate returned no content.")
native = json.loads(response["content"])
(OUTPUT / "native-response.json").write_text(
    json.dumps(native, ensure_ascii=False, indent=2), encoding="utf-8"
)
cache = json.loads((OUTPUT / "api.cache.json").read_text(encoding="utf-8"))
assert len(cache) == 1
prices = json.loads((ROOT / "model-study" / "study-prices.json").read_text(
    encoding="utf-8"
))["models"]["gpt-6-luna"]
usage = cost_for_run(OUTPUT, {
    "started_at": "1970-01-01T00:00:00+00:00",
    "elapsed_seconds": max(r["created"] for r in cache.values()) + 1,
}, prices)
(OUTPUT / "receipt.json").write_text(json.dumps({
    "returned_responses": 1, "returned_usage_estimate": usage,
    "unknown_unreturned_charges": "Excluded; estimate is not an invoice.",
}, indent=2), encoding="utf-8")
plan = restore_sampling_plan(parameters, native)["sample_plan"]
(OUTPUT / "sampling-plan.json").write_text(
    json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8"
)

dimensions = {d["name"]: d for d in parameters["sampling_dimensions"]["dimensions"]}


def measure(candidate):
    """Use exact conditional weights, not a favorable realized sampling seed."""
    marginal_errors = {}
    for name in ["race_and_ethnicity", "gender", "geographic_region", "settlement_type"]:
        weights = dimensions[name]["values"]
        expected = Counter()
        omitted = 0
        for directive in candidate:
            value = directive["sampled_values"].get(name)
            if value is None:
                omitted += directive["quantity"]
                continue
            values = value if isinstance(value, list) else [value]
            denominator = sum(weights[v] for v in values)
            for option in values:
                expected[option] += directive["quantity"] * weights[option] / denominator
        marginal_errors[name] = {
            "omitted_people": omitted,
            "expected_counts": dict(expected),
            "expected_total_variation_people": sum(
                abs(expected[option] - parameters["N"] * weight / sum(weights.values()))
                for option, weight in weights.items()
            ) / 2,
        }
    age_options = list(dimensions["age_distribution"]["values"])
    age_counts = Counter()
    education_support = {age: set() for age in age_options[-2:]}
    for directive in candidate:
        selected = directive["sampled_values"]
        group = selected.get("age_distribution")
        if isinstance(group, str):
            age_counts[group] += directive["quantity"]
            if group in education_support:
                attained = selected.get("education_attainment")
                if attained is not None:
                    education_support[group].update(
                        attained if isinstance(attained, list) else [attained]
                    )
    guaranteed = {
        name: {target: sum(d["quantity"] for d in candidate
                          if d["sampled_values"].get(name) == target)
               for target in targets}
        for name, targets in baseline["targeted_options"].items()
    }
    checks = {
        "marginal_expected_counts": all(
            not row["omitted_people"] and row["expected_total_variation_people"] <= 1.0 + 1e-9
            for row in marginal_errors.values()
        ),
        "age_totals": [age_counts[age] for age in age_options] == [9, 7, 20, 6, 8],
        "older_education_support": all(len(support) >= 2 for support in education_support.values()),
        "all_four_predefined_singletons": all(
            count > 0 for targets in guaranteed.values() for count in targets.values()
        ),
    }
    return {
        "marginals": marginal_errors, "age_counts": age_counts,
        "older_education_support": {age: sorted(support)
                                   for age, support in education_support.items()},
        "guaranteed_contrasts": guaranteed, "checks": checks,
        "passed_numerical_screen": all(checks.values()),
        "joint_semantic_review": "Pending; numerical screening alone is not adoption.",
    }


old_plan = json.loads((ROOT / "integrated-coverage-plan" / "sampling-plan.json").read_text(
    encoding="utf-8"
))
results = {"baseline": measure(old_plan), "candidate": measure(plan)}
(OUTPUT / "numerical-screen.json").write_text(
    json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps({condition: result["checks"] for condition, result in results.items()}))
