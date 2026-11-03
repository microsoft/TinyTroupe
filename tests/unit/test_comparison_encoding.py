"""Regression tests for comparable encodings in empirical validation."""

import pytest
from scipy.stats import ks_2samp

from tinytroupe.validation import (
    SimulationExperimentDataset,
    SimulationExperimentEmpiricalValidator,
    validate_simulation_experiment_empirically,
)


def dataset(values, data_type="categorical"):
    return SimulationExperimentDataset(
        key_results={"response": values}, data_types={"response": data_type}
    )


def compare(control, treatment, output_format="values"):
    return SimulationExperimentEmpiricalValidator().validate(
        control, treatment, validation_types=["statistical"],
        statistical_test_type="ks_test", output_format=output_format,
    )


@pytest.mark.parametrize("control,treatment,expected", [
    (["apple"] * 10, ["pear"] * 10, 1.0),
    (["apple", "pear"] * 5, ["pear"] * 10, 0.5),
    (["pear"] * 10, ["apple", "pear"] * 5, 0.5),
    (["apple", "pear"] * 5, ["pear", "apple"] * 5, 0.0),
    ([None, "apple", "pear"], ["pear", None, "pear"], 0.5),
    ("apple", "pear", 1.0),
])
def test_categorical_comparison_uses_shared_label_identity(control, treatment, expected):
    control_data, treatment_data = dataset(control), dataset(treatment)
    before = (control_data.model_dump(), treatment_data.model_dump())
    result = compare(control_data, treatment_data)
    metric = result.statistical_results["test_results"]["treatment"]["response"]
    assert metric["ks_statistic"] == pytest.approx(expected)
    assert result.statistical_results["comparison_mappings"]["response"] == {
        "apple": 0, "pear": 1
    }
    assert (control_data.model_dump(), treatment_data.model_dump()) == before
    repeated = compare(control_data, treatment_data).statistical_results
    assert repeated["comparison_mappings"] == result.statistical_results["comparison_mappings"]
    assert repeated["test_results"]["treatment"]["response"]["ks_statistic"] == pytest.approx(expected)


def test_ordinal_comparison_keeps_meaningful_order():
    control = dataset(["low", "medium"] * 5, "ordinal")
    treatment = dataset(["medium", "high"] * 5, "ordinal")
    result = compare(control, treatment).statistical_results
    assert result["comparison_mappings"]["response"] == {"low": 0, "medium": 1, "high": 2}
    assert result["test_results"]["treatment"]["response"]["ks_statistic"] == pytest.approx(0.5)


def test_serialized_datasets_keep_category_identity():
    result = validate_simulation_experiment_empirically(
        control_data=dataset(["apple"] * 10).model_dump(),
        treatment_data=dataset(["pear"] * 10).model_dump(),
        validation_types=["statistical"], statistical_test_type="ks_test",
    )
    assert result.statistical_results["test_results"]["treatment"]["response"]["ks_statistic"] == 1


def test_numeric_data_remains_unchanged():
    control, treatment = [1.2, 2.4, 3.6], [2.5, 3.7, 4.9]
    result = compare(dataset(control, "numeric"), dataset(treatment, "numeric")).statistical_results
    metric = result["test_results"]["treatment"]["response"]
    expected = ks_2samp(control, treatment)
    assert metric["ks_statistic"] == expected.statistic
    assert metric["p_value"] == expected.pvalue
    assert not result.get("comparison_mappings")


@pytest.mark.parametrize("other", [
    {"values": [0, 1], "data_type": "numeric"},
    {"values": ["apple", "pear"], "data_type": "ordinal"},
])
def test_incompatible_label_encodings_report_error(other):
    result = compare(dataset(["apple", "pear"]), dataset(**other))
    assert "incompatible" in result.statistical_results["error"].lower()


def test_report_preserves_original_label_distributions():
    control, treatment = dataset(["apple"] * 10), dataset(["pear"] * 10)
    report = compare(control, treatment, output_format="report")
    assert "apple" in report
    assert "pear" in report
    assert control.categorical_mappings["response"] == {"apple": 0}
    assert treatment.categorical_mappings["response"] == {"pear": 0}


def test_numeric_ordinal_data_is_not_treated_as_label_mapping():
    control, treatment = dataset([1, 2, 3], "ordinal"), dataset([2, 3, 4], "ordinal")
    result = compare(control, treatment).statistical_results
    metric = result["test_results"]["treatment"]["response"]
    assert metric["ks_statistic"] == pytest.approx(1 / 3)
    assert "comparison_mappings" not in result


def test_serialized_string_ordinals_retain_their_labels():
    control = dataset(["low", "medium"] * 5, "ordinal")
    treatment = dataset(["medium", "high"] * 5, "ordinal")
    expected = compare(control, treatment).statistical_results
    result = validate_simulation_experiment_empirically(
        control_data=control.model_dump(), treatment_data=treatment.model_dump(),
        validation_types=["statistical"], statistical_test_type="ks_test",
    )
    assert result.statistical_results == expected


def encoded_ordinal(values, mapping):
    return SimulationExperimentDataset(
        key_results={"response": values}, data_types={"response": "ordinal"},
        ordinal_mappings={"response": mapping},
    )


def test_explicit_ordinal_order_is_preserved():
    mapping = {"bronze": 0, "silver": 1, "gold": 2}
    result = compare(encoded_ordinal([1] * 10, mapping),
                     encoded_ordinal([2] * 10, mapping)).statistical_results
    assert result["comparison_mappings"]["response"] == mapping
    metric = result["test_results"]["treatment"]["response"]
    assert metric["control_mean"] < metric["treatment_mean"]


def test_compatible_partial_ordinal_orders_are_merged():
    control = encoded_ordinal([0, 1] * 5, {"bronze": 0, "silver": 1})
    treatment = encoded_ordinal([0, 1] * 5, {"silver": 0, "gold": 1})
    result = compare(control, treatment).statistical_results
    assert result["comparison_mappings"]["response"] == {"bronze": 0, "silver": 1, "gold": 2}
    assert result["test_results"]["treatment"]["response"]["ks_statistic"] == pytest.approx(0.5)


def test_conflicting_ordinal_orders_report_error():
    control = encoded_ordinal([0] * 10, {"bronze": 0, "gold": 1})
    treatment = encoded_ordinal([0] * 10, {"gold": 0, "bronze": 1})
    result = compare(control, treatment).statistical_results
    assert "incompatible" in result["error"].lower()
