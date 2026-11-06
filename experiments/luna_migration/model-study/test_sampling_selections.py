"""Verify exact closed-vocabulary reconstruction and explicit rejection of invalid sampling plans."""

import json

import jsonschema
import pytest

from sampling_selections import indexed_request, reconstruct


def case(enforce=False):
    params = {"N": 2, "enforce_usage_of_all_dimensions": enforce,
              "max_quantity_per_sample_directive": 2,
              "sampling_dimensions": {"sampling_space_description": "Adults.",
                                      "dimensions": [
                                          {"name": "age", "range": [18, 30]},
                                          {"name": "place", "values": {"Full original option": 0.6,
                                                                       "Another full option": 0.4}}
                                      ]}}
    return {"phase": "sampling_plan", "request": {"messages": [{
        "role": "user", "content": "## Named parameters\n" + json.dumps(params)
    }]}}


def value():
    return {"sample_plan": [{"id": 1, "quantity": 2, "subpopulation_description": "Adults.",
                            "sampled_values": {"1": [18, 30], "2": 1}}]}


def test_indexed_plan_restores_exact_names_values_and_source_weights():
    original = case()
    before = json.dumps(original)
    messages, fmt = indexed_request(original, "Return JSON")
    payload = json.loads(messages[1]["content"].split("\n", 1)[1])
    assert payload["sampling_dimensions"]["dimensions"]["2"]["supplied_option_weights"] == {"1": 0.6, "2": 0.4}
    jsonschema.validate(value(), fmt["json_schema"]["schema"])
    restored = reconstruct(original, value())
    assert restored["sample_plan"][0]["sampled_values"] == {
        "age": [18, 30], "place": "Full original option"}
    assert json.dumps(original) == before


def test_optional_null_is_explicitly_removed_but_required_null_is_rejected():
    plan = value()
    plan["sample_plan"][0]["sampled_values"]["2"] = None
    assert reconstruct(case(), plan)["sample_plan"][0]["sampled_values"] == {"age": [18, 30]}
    with pytest.raises(ValueError, match="Required dimension"):
        reconstruct(case(True), plan)


@pytest.mark.parametrize("selection", [3, True, [1, 1], [1, 3]])
def test_invalid_or_duplicate_option_ids_are_not_silently_repaired(selection):
    plan = value()
    plan["sample_plan"][0]["sampled_values"]["2"] = selection
    with pytest.raises(ValueError):
        reconstruct(case(), plan)


@pytest.mark.parametrize("field,bad", [("quantity", 3), ("id", 2)])
def test_arithmetic_and_sequence_failures_are_reported(field, bad):
    plan = value()
    plan["sample_plan"][0][field] = bad
    with pytest.raises(ValueError):
        reconstruct(case(), plan)


@pytest.mark.parametrize("bad_range", [[30, 18], [18, 22, 30], [17, 30]])
def test_invalid_ranges_are_rejected(bad_range):
    plan = value()
    plan["sample_plan"][0]["sampled_values"]["1"] = bad_range
    with pytest.raises(ValueError):
        reconstruct(case(), plan)


def test_membership_encoding_cannot_repeat_an_option():
    plan = value()
    plan["sample_plan"][0]["sampled_values"]["2"] = {"1": True, "2": True}
    _, fmt = indexed_request(case(), "Return JSON", categorical_encoding="membership")
    jsonschema.validate(plan, fmt["json_schema"]["schema"])
    assert reconstruct(case(), plan)["sample_plan"][0]["sampled_values"]["place"] == [
        "Full original option", "Another full option"]


@pytest.mark.parametrize("selection", [
    {"1": False, "2": False}, {"1": True}, {"1": True, "2": 1},
    {"1": True, "2": False, "3": False},
])
def test_invalid_membership_is_rejected_without_repair(selection):
    plan = value()
    plan["sample_plan"][0]["sampled_values"]["2"] = selection
    with pytest.raises(ValueError):
        reconstruct(case(), plan)
