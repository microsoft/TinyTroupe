"""Regression test: ``check_assumptions`` must look metrics up inside the control
experiment, not at the top level of ``control_experiment_data``."""

import pytest

from tinytroupe.experimentation.statistical_tests import StatisticalTester


def _tester():
    return StatisticalTester(
        {"control_exp": {"metric1": [1.0, 2.0, 3.0, 2.5, 1.5]}},
        {"treatment1": {"metric1": [2.0, 3.0, 4.0, 3.5, 2.5]}},
    )


def test_check_assumptions_finds_the_control_metric():
    results = _tester().check_assumptions("metric1")

    assert set(results) == {"treatment1"}
    assert results["treatment1"]["control_normality"]["test"] == "Shapiro-Wilk"
    assert results["treatment1"]["treatment_normality"]["test"] == "Shapiro-Wilk"
    assert results["treatment1"]["variance_homogeneity"]["test"] == "Levene"
    assert results["treatment1"]["recommended_test"] in {
        "t_test",
        "welch_t_test",
        "mann_whitney",
    }


def test_check_assumptions_rejects_an_unknown_metric():
    with pytest.raises(ValueError, match="not found in control data"):
        _tester().check_assumptions("missing_metric")
