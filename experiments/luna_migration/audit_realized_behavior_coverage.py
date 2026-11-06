"""Verify saved planner requests and structural coverage, separately from semantic review."""

import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent
REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(ROOT / "model-study")]
from model_case_study import decode_key
from tinytroupe.factory.sampling import restore_sampling_plan, sampling_plan_spec


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def comparable_options(request):
    """Absence of the nonstream flag is equivalent to its explicit false default."""
    assert "stream" not in request or request["stream"] is False
    return {k: v for k, v in request.items() if k not in {"messages", "stream"}}


original = ROOT / "realized-behavior-coverage"
baseline = load(original / "production_baseline_replication.json")
_, schema = sampling_plan_spec(baseline["parameters"])
baseline_request = None
response_ids = set()
rows = []
for folder in [original, ROOT / "realized-behavior-coverage-r2"]:
    protocol = load(folder / "plan.json")
    failure = load(folder / "failure.json") if (folder / "failure.json").exists() else None
    receipt = failure or load(folder / "receipt.json")
    cache = load(folder / "api.cache.json")
    assert len(cache) == receipt["returned_responses"] == len(protocol["conditions"])
    decoded = []
    for key, response in cache.items():
        request, model_schema = decode_key(key)
        assert model_schema is None
        assert request["model"] == "gpt-6-luna"
        assert request["reasoning_effort"] == "xhigh"
        assert request["response_format"] == schema
        assert response["choices"][0]["finish_reason"] == "stop"
        assert response["id"] not in response_ids
        response_ids.add(response["id"])
        decoded.append((request, response))
    for condition in protocol["conditions"]:
        if failure is not None:
            assert len(decoded) == 1
            request, response = decoded[0]
            assert request["messages"][1:] == baseline["messages"][1:]
            marker = "Population eligibility is mandatory in every directive"
            assert request["messages"][0]["content"] == baseline["messages"][0]["content"].replace(
                marker, protocol["candidate_paragraph"] + "\n" + marker
            )
            assert comparable_options(request) == comparable_options(baseline_request)
            returned = json.loads(response["choices"][0]["message"]["content"])
            try:
                restore_sampling_plan(baseline["parameters"], returned)
            except ValueError as error:
                assert str(error) == failure["rejection"]
            else:
                raise AssertionError("Invalid returned plan unexpectedly passed reconstruction.")
            rows.append({
                "condition": condition, "response_id": response["id"],
                "schema_and_exact_reconstruction": "rejected",
                "request_fidelity": "passed",
                "rejection": failure["rejection"],
                "empty_categorical_selections": failure["empty_categorical_selections"],
                "all_four_predefined_contrasts_guaranteed": None,
                "directives_with_unconstrained_or_incompatible_age_pairs": None,
                "semantic_review": "Invalid plan; no repaired-plan coverage is reported.",
                "transport_note": "The returned retry cache key omits stream=False; "
                                  "the API's default is nonstreaming. All other options match.",
            })
            continue
        result = load(folder / f"{condition}.json")
        audit = load(folder / f"{condition}-audit.json")
        assert result["parameters"] == baseline["parameters"]
        matches = [(request, response) for request, response in decoded
                   if request["messages"] == result["messages"]]
        assert len(matches) == 1
        request, response = matches[0]
        returned = json.loads(response["choices"][0]["message"]["content"])
        assert restore_sampling_plan(result["parameters"], returned)["sample_plan"] == result["sampling_plan"]
        if condition == "production_baseline_replication":
            baseline_request = request
        else:
            assert baseline_request is not None
            assert comparable_options(request) == comparable_options(baseline_request)
            assert result["messages"][1:] == baseline["messages"][1:]
            marker = "Population eligibility is mandatory in every directive"
            assert result["messages"][0]["content"] == baseline["messages"][0]["content"].replace(
                marker, protocol["candidate_paragraph"] + "\n" + marker
            )
        dimensions = {d["name"]: d for d in result["parameters"]["sampling_dimensions"]["dimensions"]}
        age_options = list(dimensions["age_distribution"]["values"])
        age_bands = [(0, 14), (15, 24), (25, 54), (55, 64), (65, 110)]
        age_errors = []
        guaranteed = {}
        for name, targets in protocol["targeted_options"].items():
            guaranteed[name] = {
                target: sum(d["quantity"] for d in result["sampling_plan"]
                            if d["sampled_values"].get(name) == target
                            or d["sampled_values"].get(name) == [target])
                for target in targets
            }
        for directive in result["sampling_plan"]:
            selected = directive["sampled_values"]
            if "age" not in selected or "age_distribution" not in selected:
                age_errors.append(directive["id"])
                continue
            numeric = selected["age"]
            bounds = numeric if isinstance(numeric, list) else [numeric, numeric]
            groups = selected["age_distribution"]
            groups = groups if isinstance(groups, list) else [groups]
            if any(not (age_bands[age_options.index(group)][0] <= bounds[0]
                        <= bounds[-1] <= age_bands[age_options.index(group)][1])
                   for group in groups):
                age_errors.append(directive["id"])
        rows.append({
            "condition": condition,
            "response_id": response["id"],
            "schema_and_exact_reconstruction": "passed",
            "non_message_options_match_baseline_after_nonstream_default_normalization": True,
            "only_prompt_change_is_recorded_paragraph": True,
            "production_template_sha256_at_execution": protocol["production_prompt_sha256"],
            "system_message_sha256": hashlib.sha256(
                result["messages"][0]["content"].encode("utf-8")
            ).hexdigest(),
            "directives": len(result["sampling_plan"]),
            "population": sum(d["quantity"] for d in result["sampling_plan"]),
            "guaranteed_predefined_contrasts": guaranteed,
            "all_four_predefined_contrasts_guaranteed": all(
                count > 0 for choices in guaranteed.values() for count in choices.values()
            ),
            "directives_with_unconstrained_or_incompatible_age_pairs": age_errors,
            "coverage_over_100_seeds": audit["targeted_coverage_over_100_seeds"],
            "demographic_allocations": {
                name: audit["categorical_allocations"][name]
                for name in ["age_distribution", "gender", "race_and_ethnicity",
                             "geographic_region", "settlement_type"]
            },
        })
compact_folder = ROOT / "realized-behavior-coverage-compact"
compact_protocol = load(compact_folder / "plan.json")
compact_cache = load(compact_folder / "api.cache.json")
assert len(compact_cache) == 1
key, response = next(iter(compact_cache.items()))
request, model_schema = decode_key(key)
assert model_schema is None
assert response["id"] not in response_ids
response_ids.add(response["id"])
assert response["choices"][0]["finish_reason"] == "stop"
assert request["messages"] == compact_protocol["messages"]
assert request["messages"][1:] == baseline["messages"][1:]
assert compact_protocol["parameters"] == baseline["parameters"]
paragraph = load(ROOT / "realized-behavior-coverage-r2" / "plan.json")["candidate_paragraph"]
expected_text = baseline["messages"][0]["content"].replace(
    "Population eligibility is mandatory in every directive",
    paragraph + "\nPopulation eligibility is mandatory in every directive",
)
for before, after in [
    ("- For a categorical dimension you constrain, return the schema's option-membership object. "
     "Every option has exactly one boolean slot: true means allowed; false means excluded. "
     "Select at least one option.",
     "- For a categorical dimension you constrain, return a nonempty list of its allowed "
     "option identifiers as integers. Select each identifier at most once."),
    (" Do not return an all-false object instead.", ""),
    ("Option membership and null are explicit intermediate representations.",
     "Option identifiers and null are explicit intermediate representations."),
]:
    assert expected_text.count(before) == 1
    expected_text = expected_text.replace(before, after)
assert request["messages"][0]["content"] == expected_text
baseline_options = comparable_options(baseline_request)
compact_options = comparable_options(request)
assert {k: v for k, v in baseline_options.items() if k != "response_format"} == {
    k: v for k, v in compact_options.items() if k != "response_format"
}
expected_schema = copy.deepcopy(schema)
properties = expected_schema["json_schema"]["schema"]["properties"]["sample_plan"]["items"][
    "properties"]["sampled_values"]["properties"]
for index, dimension in enumerate(baseline["parameters"]["sampling_dimensions"]["dimensions"], 1):
    if "values" in dimension:
        properties[str(index)]["anyOf"][0] = {
            "type": "array", "items": {"type": "integer",
                                      "enum": list(range(1, len(dimension["values"]) + 1))},
            "minItems": 1, "maxItems": len(dimension["values"]),
        }
assert request["response_format"] == compact_protocol["response_format"] == expected_schema
native = json.loads(response["choices"][0]["message"]["content"])
assert native == load(compact_folder / "native-response.json")
membership = copy.deepcopy(native)
for directive in membership["sample_plan"]:
    selections = directive["sampled_values"]
    for index, dimension in enumerate(baseline["parameters"]["sampling_dimensions"]["dimensions"], 1):
        chosen = selections[str(index)]
        if "values" in dimension and chosen is not None:
            assert isinstance(chosen, list) and chosen and len(set(chosen)) == len(chosen)
            assert all(type(v) is int and 1 <= v <= len(dimension["values"]) for v in chosen)
            selections[str(index)] = {
                str(v): v in chosen for v in range(1, len(dimension["values"]) + 1)
            }
assert restore_sampling_plan(baseline["parameters"], membership)["sample_plan"] == load(
    compact_folder / "sampling-plan.json"
)
compact_audit = load(compact_folder / "audit.json")
rows.append({
    "condition": "compact_identifier_lists_with_revision_2_instructions",
    "response_id": response["id"], "request_fidelity": "passed",
    "schema_and_exact_reconstruction": "passed",
    "all_four_predefined_contrasts_guaranteed": compact_audit[
        "all_four_predefined_contrasts_guaranteed"],
    "directives_with_unconstrained_or_incompatible_age_pairs": compact_audit[
        "directives_with_unconstrained_or_incompatible_age_pairs"],
    "guaranteed_predefined_contrasts": compact_audit["guaranteed_predefined_contrasts"],
    "coverage_over_100_seeds": compact_audit["coverage_over_100_seeds"],
    "semantic_review": "Candidate screen only; six-person integration is assessed separately.",
})
summary = {
    "protocol_status": "passed",
    "saved_returned_responses": len(response_ids),
    "rows": rows,
    "limitations": [
        "A protocol pass is not semantic acceptance, survey quality, or population calibration.",
        "One returned plan per prompt condition; sampling seeds are not independent model replications.",
        "The original frozen CF5 plan and the new baseline are distinct plans.",
        "No survey responses are generated or used by this experiment.",
    ],
}
(ROOT / "realized-behavior-coverage-audit.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(json.dumps({
    "protocol_status": summary["protocol_status"],
    "responses": len(response_ids),
    "conditions": [{
        "condition": row["condition"],
        "all_four_guaranteed": row["all_four_predefined_contrasts_guaranteed"],
        "age_errors": row["directives_with_unconstrained_or_incompatible_age_pairs"],
    } for row in rows],
}, indent=2))
