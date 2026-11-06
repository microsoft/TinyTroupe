"""Offline invariants for the indexed semantic-grouping adapter."""

import copy

import jsonschema
import pytest

from normalization_assignments import indexed_request, reconstruct, source_items


def case():
    return {"request": {"messages": [
        {"role": "system", "content": "Original contract"},
        {"role": "user", "content": "Produce UP TO 2 categories.\nINPUT ELEMENTS:\n  - duplicate\n  - second\n  - duplicate\n"}
    ]}}


def test_indexed_contract_preserves_every_original_occurrence():
    original = case()
    saved = copy.deepcopy(original)
    messages, fmt = indexed_request(original, "Return JSON")
    assert original == saved
    import json
    assert list(json.loads(messages[1]["content"])["items"].values()) == ["duplicate", "second", "duplicate"]
    value = {"labels": {"1": "Repeated", "2": "Other"}, "assignments": {"1": 1, "2": 2, "3": 1}}
    jsonschema.validate(value, fmt["json_schema"]["schema"])
    assert reconstruct(original, value) == {"Repeated": ["duplicate", "duplicate"], "Other": ["second"]}


@pytest.mark.parametrize("assignments", [{"1": 1, "2": 2}, {"1": 1, "2": 3, "3": 1},
                                        {"1": True, "2": 2, "3": 1}])
def test_missing_invalid_or_boolean_assignment_is_rejected(assignments):
    with pytest.raises(ValueError):
        reconstruct(case(), {"labels": {"1": "First", "2": "Second"}, "assignments": assignments})


def test_empty_duplicate_and_overlength_labels_are_rejected():
    for labels in [{"1": "Same", "2": "Same"}, {"1": "x"*41, "2": "Other"}, {"1": "", "2": "Other"}]:
        with pytest.raises(ValueError):
            reconstruct(case(), {"labels": labels, "assignments": {"1": 1, "2": 2, "3": 1}})
    with pytest.raises(ValueError, match="Empty categories"):
        reconstruct(case(), {"labels": {"1": "First", "2": "Second"},
                             "assignments": {"1": 1, "2": 1, "3": 1}})


def test_malformed_source_is_not_silently_normalized():
    original = case()
    original["request"]["messages"][1]["content"] = "No source list"
    with pytest.raises(ValueError):
        source_items(original)
