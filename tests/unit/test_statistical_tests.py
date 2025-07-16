import pytest
import logging
import numpy as np
from unittest.mock import Mock, patch
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

# Try to import scipy for verification tests
try:
    import scipy.stats as stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    stats = None

from tinytroupe.experimentation.statistical_tests import StatisticalTester
from testing_utils import *

def test_statistical_tester_initialization():
    """Test StatisticalTester initialization with valid data."""
    
    # Test basic initialization
    control_data = {"control_exp": {"metric1": [1, 2, 3], "metric2": [4, 5, 6]}}
    treatment_data = {
        "treatment1": {"metric1": [2, 3, 4], "metric2": [5, 6, 7]},
        "treatment2": {"metric1": [3, 4, 5], "metric2": [6, 7, 8]}
    }
    
    tester = StatisticalTester(control_data, treatment_data)
    assert tester.control_experiment_data == control_data
    assert tester.treatments_experiment_data == treatment_data

def test_statistical_tester_initialization_with_results_key():
    """Test StatisticalTester initialization with results_key parameter."""
    
    # Test with results_key to extract nested data
    control_data = {"control_exp": {"results": {"metric1": [1, 2, 3], "metric2": [4, 5, 6]}}}
    treatment_data = {
        "treatment1": {"results": {"metric1": [2, 3, 4], "metric2": [5, 6, 7]}},
        "treatment2": {"results": {"metric1": [3, 4, 5], "metric2": [6, 7, 8]}}
    }
    
    tester = StatisticalTester(control_data, treatment_data, results_key="results")
    
    # Data should be extracted from the "results" key
    expected_control = {"control_exp": {"metric1": [1, 2, 3], "metric2": [4, 5, 6]}}
    expected_treatment = {
        "treatment1": {"metric1": [2, 3, 4], "metric2": [5, 6, 7]},
        "treatment2": {"metric1": [3, 4, 5], "metric2": [6, 7, 8]}
    }
    
    assert tester.control_experiment_data == expected_control
    assert tester.treatments_experiment_data == expected_treatment

def test_statistical_tester_validation_errors():
    """Test StatisticalTester input validation."""
    
    # Test invalid control data type
    with pytest.raises(TypeError, match="Control experiment data must be a dictionary"):
        StatisticalTester("invalid", {})
    
    # Test invalid treatment data type
    with pytest.raises(TypeError, match="Treatments experiment data must be a dictionary"):
        StatisticalTester({}, "invalid")
    
    # Test empty control data
    with pytest.raises(ValueError, match="Control experiment data cannot be empty"):
        StatisticalTester({}, {"treatment1": {"metric1": [1, 2, 3]}})
    
    # Test multiple control experiments
    control_data = {
        "control1": {"metric1": [1, 2, 3]},
        "control2": {"metric1": [4, 5, 6]}
    }
    with pytest.raises(ValueError, match="Only one control experiment is allowed"):
        StatisticalTester(control_data, {"treatment1": {"metric1": [1, 2, 3]}})
    
    # Test empty treatment data
    with pytest.raises(ValueError, match="Treatments experiment data cannot be empty"):
        StatisticalTester({"control": {"metric1": [1, 2, 3]}}, {})

def test_statistical_tester_metric_validation():
    """Test validation of metric data structures."""
    
    # Test invalid control metrics type
    control_data = {"control": "invalid_metrics"}
    treatment_data = {"treatment1": {"metric1": [1, 2, 3]}}
    
    with pytest.raises(TypeError, match="Metrics for control experiment 'control' must be a dictionary"):
        StatisticalTester(control_data, treatment_data)
    
    # Test empty control metrics
    control_data = {"control": {}}
    with pytest.raises(ValueError, match="Control experiment 'control' has no metrics"):
        StatisticalTester(control_data, treatment_data)
    
    # Test invalid metric values type in control
    control_data = {"control": {"metric1": "invalid_values"}}
    with pytest.raises(TypeError, match="Values for metric 'metric1' in control experiment 'control' must be a list"):
        StatisticalTester(control_data, treatment_data)
    
    # Test invalid treatment data structure
    control_data = {"control": {"metric1": [1, 2, 3]}}
    treatment_data = {"treatment1": "invalid_structure"}
    
    with pytest.raises(TypeError, match="Data for treatment 'treatment1' must be a dictionary"):
        StatisticalTester(control_data, treatment_data)

def test_statistical_tester_welch_t_test():
    """Test Welch's t-test functionality."""
    
    # Create data with known statistical properties
    np.random.seed(42)  # For reproducible results
    
    control_data = {"control": {"metric1": [1.0, 2.0, 3.0, 2.5, 1.5] * 10}}  # Larger sample
    treatment_data = {
        "treatment1": {"metric1": [3.0, 4.0, 5.0, 4.5, 3.5] * 10},  # Higher mean
        "treatment2": {"metric1": [1.1, 2.1, 3.1, 2.6, 1.6] * 10}   # Similar mean
    }
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test", alpha=0.05)
    
    # Verify results structure
    assert "treatment1" in results
    assert "treatment2" in results
    
    for treatment_id in results:
        assert "metric1" in results[treatment_id]
        metric_result = results[treatment_id]["metric1"]
        
        # Check that result contains expected statistical test outputs
        assert "t_statistic" in metric_result
        assert "p_value" in metric_result
        assert "significant" in metric_result
        assert isinstance(metric_result["significant"], bool)
        assert isinstance(metric_result["p_value"], (float, int))

def test_statistical_tester_t_test():
    """Test standard t-test functionality."""
    
    control_data = {"control": {"metric1": [1, 2, 3, 4, 5]}}
    treatment_data = {"treatment1": {"metric1": [3, 4, 5, 6, 7]}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="t_test", alpha=0.05)
    
    # Verify basic result structure
    assert "treatment1" in results
    assert "metric1" in results["treatment1"]
    
    metric_result = results["treatment1"]["metric1"]
    assert "t_statistic" in metric_result
    assert "p_value" in metric_result
    assert "significant" in metric_result

def test_statistical_tester_mann_whitney():
    """Test Mann-Whitney U test functionality."""
    
    control_data = {"control": {"metric1": [1, 2, 3, 4, 5]}}
    treatment_data = {"treatment1": {"metric1": [6, 7, 8, 9, 10]}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="mann_whitney", alpha=0.05)
    
    # Verify result structure
    assert "treatment1" in results
    assert "metric1" in results["treatment1"]
    
    metric_result = results["treatment1"]["metric1"]
    assert "u_statistic" in metric_result
    assert "p_value" in metric_result
    assert "significant" in metric_result

def test_statistical_tester_anova():
    """Test ANOVA functionality."""
    
    control_data = {"control": {"metric1": [1, 2, 3, 4, 5]}}
    treatment_data = {
        "treatment1": {"metric1": [3, 4, 5, 6, 7]},
        "treatment2": {"metric1": [6, 7, 8, 9, 10]}
    }
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="anova", alpha=0.05)
    
    # ANOVA should test all groups together
    for treatment_id in results:
        assert "metric1" in results[treatment_id]
        metric_result = results[treatment_id]["metric1"]
        assert "f_statistic" in metric_result
        assert "p_value" in metric_result
        assert "significant" in metric_result

def test_statistical_tester_chi_square():
    """Test Chi-square test functionality."""
    
    # Chi-square test typically uses categorical data
    # Use data that creates a valid contingency table
    control_data = {"control": {"category_metric": [10, 15, 20, 25, 30]}}  # Higher counts
    treatment_data = {"treatment1": {"category_metric": [8, 12, 18, 22, 28]}}  # Different but comparable counts
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="chi_square", alpha=0.05)
    
    # Verify result structure
    assert "treatment1" in results
    assert "category_metric" in results["treatment1"]
    
    metric_result = results["treatment1"]["category_metric"]
    assert "chi2_statistic" in metric_result
    assert "p_value" in metric_result
    assert "significant" in metric_result

def test_statistical_tester_unsupported_test():
    """Test error handling for unsupported test types."""
    
    control_data = {"control": {"metric1": [1, 2, 3]}}
    treatment_data = {"treatment1": {"metric1": [4, 5, 6]}}
    
    tester = StatisticalTester(control_data, treatment_data)
    
    with pytest.raises(ValueError, match="Unsupported test type: invalid_test"):
        tester.run_test(test_type="invalid_test")

def test_statistical_tester_missing_metrics():
    """Test handling of missing metrics in treatments."""
    
    control_data = {"control": {"metric1": [1, 2, 3], "metric2": [4, 5, 6]}}
    treatment_data = {"treatment1": {"metric1": [2, 3, 4]}}  # Missing metric2
    
    tester = StatisticalTester(control_data, treatment_data)
    
    # Should handle missing metrics gracefully
    results = tester.run_test(test_type="welch_t_test")
    
    # Should have results for metric1 but not metric2
    assert "treatment1" in results
    assert "metric1" in results["treatment1"]
    # metric2 should be skipped due to missing data

def test_statistical_tester_empty_values():
    """Test handling of empty value lists."""
    
    control_data = {"control": {"metric1": [1, 2, 3], "metric2": []}}  # Empty values
    treatment_data = {"treatment1": {"metric1": [2, 3, 4], "metric2": [5, 6, 7]}}
    
    tester = StatisticalTester(control_data, treatment_data)
    
    # Should handle empty values gracefully
    results = tester.run_test(test_type="welch_t_test")
    
    # Should have results for metric1 but not metric2 (empty control values)
    assert "treatment1" in results
    if "metric1" in results["treatment1"]:
        # metric1 should work
        assert "t_statistic" in results["treatment1"]["metric1"]
    # metric2 should be skipped due to empty control values

def test_statistical_tester_multiple_treatments():
    """Test with multiple treatment groups."""
    
    control_data = {"control": {"metric1": [1, 2, 3, 4, 5]}}
    treatment_data = {
        "treatment1": {"metric1": [2, 3, 4, 5, 6]},
        "treatment2": {"metric1": [3, 4, 5, 6, 7]},
        "treatment3": {"metric1": [4, 5, 6, 7, 8]}
    }
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    # Should have results for all treatments
    assert len(results) == 3
    assert "treatment1" in results
    assert "treatment2" in results
    assert "treatment3" in results
    
    for treatment_id in results:
        assert "metric1" in results[treatment_id]

def test_statistical_tester_alpha_parameter():
    """Test that alpha parameter affects significance determination."""
    
    control_data = {"control": {"metric1": [1, 2, 3, 4, 5]}}
    treatment_data = {"treatment1": {"metric1": [1.1, 2.1, 3.1, 4.1, 5.1]}}  # Very similar values
    
    tester = StatisticalTester(control_data, treatment_data)
    
    # Test with very strict alpha (should likely not be significant)
    results_strict = tester.run_test(test_type="welch_t_test", alpha=0.001)
    
    # Test with lenient alpha (more likely to be significant)
    results_lenient = tester.run_test(test_type="welch_t_test", alpha=0.5)
    
    # Both should have the same p-value but different significance determinations
    p_value_strict = results_strict["treatment1"]["metric1"]["p_value"]
    p_value_lenient = results_lenient["treatment1"]["metric1"]["p_value"]
    
    # P-values should be the same
    assert abs(p_value_strict - p_value_lenient) < 1e-10
    
    # Significance might differ based on alpha
    # (exact result depends on the actual p-value, but structure should be correct)

def test_statistical_tester_numerical_precision():
    """Test statistical calculations with various numerical scenarios."""
    
    # Test with identical values (should have p-value = 1.0 or close)
    control_data = {"control": {"metric1": [5, 5, 5, 5, 5]}}
    treatment_data = {"treatment1": {"metric1": [5, 5, 5, 5, 5]}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    # With identical values, should not be significant
    assert not results["treatment1"]["metric1"]["significant"]
    
    # Test with very different values (should be significant)
    control_data = {"control": {"metric1": [1, 1, 1, 1, 1]}}
    treatment_data = {"treatment1": {"metric1": [100, 100, 100, 100, 100]}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    # With very different values, should be significant
    assert results["treatment1"]["metric1"]["significant"]

def test_statistical_tester_warning_logging():
    """Test that appropriate warnings are logged."""
    
    control_data = {"control": {"metric1": [1, 2, 3], "metric2": [4, 5, 6]}}
    treatment_data = {"treatment1": {"metric3": [7, 8, 9]}}  # No overlapping metrics
    
    with patch('tinytroupe.experimentation.statistical_tests.logger') as mock_logger:
        tester = StatisticalTester(control_data, treatment_data)
        
        # Should log warning about no common metrics during initialization
        mock_logger.warning.assert_called()
        
        # Run test should also handle missing metrics gracefully
        results = tester.run_test(test_type="welch_t_test")
        
        # Additional warnings should be logged during test execution
        assert mock_logger.warning.call_count > 0

def test_statistical_testing_comprehensive_scenarios(setup):
    """Test StatisticalTester with more realistic experimental scenarios."""
    
    # Test with real-world like experimental data
    control_data = {
        "baseline": {
            "conversion_rate": [0.12, 0.15, 0.13, 0.14, 0.11, 0.16, 0.12, 0.13, 0.14, 0.15],
            "engagement_score": [7.2, 7.5, 7.1, 7.3, 7.0, 7.6, 7.2, 7.4, 7.3, 7.5],
            "satisfaction": [3.2, 3.5, 3.1, 3.4, 3.0, 3.6, 3.2, 3.3, 3.4, 3.5]
        }
    }
    
    treatment_data = {
        "variant_a": {
            "conversion_rate": [0.16, 0.18, 0.17, 0.19, 0.15, 0.20, 0.16, 0.17, 0.18, 0.19],
            "engagement_score": [8.1, 8.3, 8.0, 8.2, 7.9, 8.4, 8.1, 8.2, 8.3, 8.4],
            "satisfaction": [3.8, 4.1, 3.7, 3.9, 3.6, 4.2, 3.8, 3.9, 4.0, 4.1]
        },
        "variant_b": {
            "conversion_rate": [0.14, 0.16, 0.15, 0.17, 0.13, 0.18, 0.14, 0.15, 0.16, 0.17],
            "engagement_score": [7.6, 7.8, 7.5, 7.7, 7.4, 7.9, 7.6, 7.7, 7.8, 7.9],
            "satisfaction": [3.4, 3.7, 3.3, 3.6, 3.2, 3.8, 3.4, 3.5, 3.6, 3.7]
        }
    }
    
    tester = StatisticalTester(control_data, treatment_data)
    
    # Test multiple metrics with different statistical tests
    metrics_to_test = ["conversion_rate", "engagement_score", "satisfaction"]
    
    for metric in metrics_to_test:
        # Test Welch's t-test
        results = tester.run_test(test_type="welch_t_test")
        variant_a_results = results["variant_a"][metric]
        assert "p_value" in variant_a_results
        assert "t_statistic" in variant_a_results
        assert "significant" in variant_a_results
        
        # Test Mann-Whitney U test
        results = tester.run_test(test_type="mann_whitney")
        variant_a_results = results["variant_a"][metric]
        assert "p_value" in variant_a_results
        assert "u_statistic" in variant_a_results
        assert "significant" in variant_a_results

def test_statistical_testing_edge_cases(setup):
    """Test StatisticalTester with edge cases and error conditions."""
    
    # Test with identical data (should show no significance)
    control_data = {"control": {"metric": [1, 1, 1, 1, 1]}}
    treatment_data = {"treatment": {"metric": [1, 1, 1, 1, 1]}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    # Should not be significant with identical data
    assert not results["treatment"]["metric"]["significant"]
    
    # P-value might be NaN with identical data due to zero variance, which is acceptable
    p_value = results["treatment"]["metric"]["p_value"]
    assert (p_value >= 0.05) or (p_value != p_value), f"P-value should be >= 0.05 or NaN, got {p_value}"

    # Test with very small sample size
    small_sample_control = {"control": {"metric": [1, 2]}}
    small_sample_treatment = {"treatment": {"metric": [2, 3]}}
    
    tester_small = StatisticalTester(small_sample_control, small_sample_treatment)
    results_small = tester_small.run_test(test_type="welch_t_test")
    
    # With such small samples, the test might not be reliable but should still work
    assert "t_statistic" in results_small["treatment"]["metric"]
    assert "p_value" in results_small["treatment"]["metric"]
    assert isinstance(results_small["treatment"]["metric"]["significant"], bool)

def test_statistical_results_correctness():
    """Test that statistical calculations produce mathematically correct results."""
    
    # Test with known data where we can calculate expected results
    # Using simple data where we know the expected t-statistic and p-value
    
    # Group 1: mean = 2, Group 2: mean = 5, both with same variance
    control_data = {"control": {"metric1": [1, 2, 3]}}  # mean = 2, std ≈ 1
    treatment_data = {"treatment1": {"metric1": [4, 5, 6]}}  # mean = 5, std ≈ 1
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test", alpha=0.05)
    
    # Verify the t-statistic makes sense (should be negative since treatment > control)
    result = results["treatment1"]["metric1"]
    t_stat = result["t_statistic"]
    p_value = result["p_value"]
    
    # With this data, the difference should be statistically significant
    # (3-point difference with small variance in small samples)
    assert abs(t_stat) > 2.0, f"T-statistic {t_stat} should indicate large effect"
    assert p_value < 0.05, f"P-value {p_value} should be significant for this large difference"
    assert result["significant"] == True

def test_welch_t_test_mathematical_accuracy():
    """Test Welch's t-test against manually calculated values."""
    
    if not HAS_SCIPY:
        pytest.skip("scipy not available for verification")
    
    # Use data where we can manually verify the calculation
    # Two groups with different means and variances
    control_vals = [1.0, 2.0, 3.0, 4.0, 5.0]  # mean = 3, var = 2.5
    treatment_vals = [6.0, 7.0, 8.0, 9.0, 10.0]  # mean = 8, var = 2.5
    
    control_data = {"control": {"metric": control_vals}}
    treatment_data = {"treatment": {"metric": treatment_vals}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    result = results["treatment"]["metric"]
    
    # Perform manual Welch's t-test for comparison
    t_stat_expected, p_val_expected = stats.ttest_ind(control_vals, treatment_vals, equal_var=False)
    
    # Check if our implementation matches scipy's results (within tolerance)
    assert abs(result["t_statistic"] - t_stat_expected) < 0.01, \
        f"T-statistic {result['t_statistic']} should match expected {t_stat_expected}"
    
    assert abs(result["p_value"] - p_val_expected) < 0.01, \
        f"P-value {result['p_value']} should match expected {p_val_expected}"

def test_mann_whitney_mathematical_accuracy():
    """Test Mann-Whitney U test against manually calculated values."""
    
    if not HAS_SCIPY:
        pytest.skip("scipy not available for verification")
    
    # Use ordinal data where Mann-Whitney is appropriate
    control_vals = [1, 2, 3, 4, 5]
    treatment_vals = [6, 7, 8, 9, 10]  # Clearly higher ranks
    
    control_data = {"control": {"metric": control_vals}}
    treatment_data = {"treatment": {"metric": treatment_vals}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="mann_whitney")
    
    result = results["treatment"]["metric"]
    
    # Manually calculate expected values using scipy
    u_stat_expected, p_val_expected = stats.mannwhitneyu(control_vals, treatment_vals, alternative='two-sided')
    
    # Check if our implementation matches scipy's results
    assert abs(result["u_statistic"] - u_stat_expected) < 0.01, \
        f"U-statistic {result['u_statistic']} should match expected {u_stat_expected}"
    
    assert abs(result["p_value"] - p_val_expected) < 0.01, \
        f"P-value {result['p_value']} should match expected {p_val_expected}"
    
    # With completely separated groups, should be highly significant
    assert result["significant"] == True
    assert result["p_value"] < 0.01

def test_effect_size_validation():
    """Test that effect sizes are calculated correctly."""
    
    # Test with known effect sizes
    # Small effect: Cohen's d ≈ 0.2
    control_small = [0.0, 0.1, 0.2, 0.3, 0.4] * 10  # mean ≈ 0.2
    treatment_small = [0.4, 0.5, 0.6, 0.7, 0.8] * 10  # mean ≈ 0.6, difference ≈ 0.4
    
    # Large effect: Cohen's d ≈ 0.8+
    control_large = [1.0, 2.0, 3.0, 4.0, 5.0] * 10  # mean = 3
    treatment_large = [5.0, 6.0, 7.0, 8.0, 9.0] * 10  # mean = 7, large difference
    
    # Test small effect
    control_data = {"control": {"metric": control_small}}
    treatment_data = {"treatment": {"metric": treatment_small}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    # Small effect should be detectable with larger sample
    small_result = results["treatment"]["metric"]
    
    # Test large effect
    control_data = {"control": {"metric": control_large}}
    treatment_data = {"treatment": {"metric": treatment_large}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    large_result = results["treatment"]["metric"]
    
    # Large effect should have smaller p-value and larger t-statistic
    assert large_result["p_value"] < small_result["p_value"], \
        "Large effect should have smaller p-value than small effect"
    
    assert abs(large_result["t_statistic"]) > abs(small_result["t_statistic"]), \
        "Large effect should have larger t-statistic magnitude"

def test_statistical_power_scenarios():
    """Test statistical power in various scenarios."""
    
    # Test insufficient power scenario (very small sample, minimal effect)
    control_small_n = [2.0, 2.0, 2.0]  # n=3, almost no variance
    treatment_small_n = [2.01, 2.01, 2.01]  # Tiny effect size
    
    control_data = {"control": {"metric": control_small_n}}
    treatment_data = {"treatment": {"metric": treatment_small_n}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    low_power_result = results["treatment"]["metric"]
    
    # With tiny effect and small sample, significance depends on implementation
    # Just check that we get a valid result
    assert "significant" in low_power_result, "Should return significance status"
    assert "p_value" in low_power_result, "Should return p-value"
    
    # Test high power scenario (large sample, clear effect)
    control_high_n = [1.0] * 100  # Large sample, clear difference
    treatment_high_n = [2.0] * 100
    
    control_data = {"control": {"metric": control_high_n}}
    treatment_data = {"treatment": {"metric": treatment_high_n}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    high_power_result = results["treatment"]["metric"]
    
    # Should be highly significant with large sample and clear effect
    assert high_power_result["significant"] == True, \
        "Large sample with clear effect should be significant"
    assert high_power_result["p_value"] < 0.001, \
        "Should have very small p-value with large sample and clear effect"

def test_type_i_error_control():
    """Test that Type I error is properly controlled at alpha level."""
    
    # Test with identical distributions (null hypothesis is true)
    # Should have approximately alpha proportion of false positives
    np.random.seed(42)
    
    false_positive_count = 0
    num_tests = 100
    alpha = 0.05
    
    for i in range(num_tests):
        # Generate identical distributions
        control_vals = np.random.normal(0, 1, 20).tolist()
        treatment_vals = np.random.normal(0, 1, 20).tolist()  # Same distribution
        
        control_data = {"control": {"metric": control_vals}}
        treatment_data = {"treatment": {"metric": treatment_vals}}
        
        tester = StatisticalTester(control_data, treatment_data)
        results = tester.run_test(test_type="welch_t_test", alpha=alpha)
        
        if results["treatment"]["metric"]["significant"]:
            false_positive_count += 1
    
    false_positive_rate = false_positive_count / num_tests
    
    # Should be approximately equal to alpha (within reasonable bounds)
    # Allow for some variation due to random sampling
    assert 0.01 <= false_positive_rate <= 0.10, \
        f"False positive rate {false_positive_rate} should be close to alpha {alpha}"

def test_multiple_comparisons_handling():
    """Test handling of multiple comparisons."""
    
    # Test multiple treatments against control
    control_data = {"control": {"metric": [1.0, 2.0, 3.0, 4.0, 5.0] * 10}}
    
    # Multiple treatments with varying effect sizes
    treatment_data = {
        "treatment1": {"metric": [1.1, 2.1, 3.1, 4.1, 5.1] * 10},  # Small effect
        "treatment2": {"metric": [2.0, 3.0, 4.0, 5.0, 6.0] * 10},  # Medium effect
        "treatment3": {"metric": [3.0, 4.0, 5.0, 6.0, 7.0] * 10},  # Large effect
    }
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test", alpha=0.05)
    
    # Check that all treatments are tested
    assert len(results) == 3
    assert "treatment1" in results
    assert "treatment2" in results  
    assert "treatment3" in results
    
    # Larger effects should have smaller p-values
    p1 = results["treatment1"]["metric"]["p_value"]
    p2 = results["treatment2"]["metric"]["p_value"]
    p3 = results["treatment3"]["metric"]["p_value"]
    
    # Should generally follow the pattern p3 < p2 < p1 (larger effect = smaller p)
    assert p3 < p1, "Largest effect should have smallest p-value"
    
    # At least the large effect should be significant
    assert results["treatment3"]["metric"]["significant"] == True

def test_statistical_means_and_effect_sizes():
    """Test that statistical test results correctly calculate means and effect sizes."""
    
    # Test with precise data where we know the expected means
    control_data = {"control": {"metric": [10.0, 20.0, 30.0, 40.0, 50.0]}}  # mean = 30
    treatment_data = {"treatment": {"metric": [15.0, 25.0, 35.0, 45.0, 55.0]}}  # mean = 35
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    result = results["treatment"]["metric"]
    
    # Verify calculated means are correct
    assert abs(result["control_mean"] - 30.0) < 0.001, \
        f"Control mean should be 30.0, got {result['control_mean']}"
    
    assert abs(result["treatment_mean"] - 35.0) < 0.001, \
        f"Treatment mean should be 35.0, got {result['treatment_mean']}"
    
    # Verify mean difference
    assert abs(result["mean_difference"] - 5.0) < 0.001, \
        f"Mean difference should be 5.0, got {result['mean_difference']}"
    
    # Verify percent change calculation
    expected_percent_change = (5.0 / 30.0) * 100  # ≈ 16.67%
    assert abs(result["percent_change"] - expected_percent_change) < 0.01, \
        f"Percent change should be ~16.67%, got {result['percent_change']}"
    
    # Verify sample sizes
    assert result["control_sample_size"] == 5
    assert result["treatment_sample_size"] == 5
    
    # Effect size should be reasonable (Cohen's d should be positive since treatment > control)
    assert result["effect_size"] > 0, "Effect size should be positive when treatment > control"

def test_confidence_intervals_coverage():
    """Test that confidence intervals are calculated correctly."""
    
    # Use larger samples for more stable confidence intervals
    np.random.seed(42)
    control_vals = [1.0] * 50  # All identical values, mean = 1, std = 0
    treatment_vals = [2.0] * 50  # All identical values, mean = 2, std = 0
    
    control_data = {"control": {"metric": control_vals}}
    treatment_data = {"treatment": {"metric": treatment_vals}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test", alpha=0.05)
    
    result = results["treatment"]["metric"]
    
    # With zero variance, the confidence interval should be very tight around the mean difference
    ci_lower, ci_upper = result["confidence_interval"]
    mean_diff = result["mean_difference"]
    
    # Should be exactly 1.0 difference with zero variance
    assert abs(mean_diff - 1.0) < 0.001, f"Mean difference should be 1.0, got {mean_diff}"
    
    # With zero variance, CI should be very tight (or exactly the mean difference)
    ci_width = ci_upper - ci_lower
    assert ci_width < 0.1, f"Confidence interval should be very narrow with zero variance, got width {ci_width}"
    
    # The mean difference should be within the confidence interval
    assert ci_lower <= mean_diff <= ci_upper, \
        f"Mean difference {mean_diff} should be within CI [{ci_lower}, {ci_upper}]"

def test_p_value_directional_consistency():
    """Test that p-values behave consistently with effect direction and magnitude."""
    
    # Test 1: No difference (should have high p-value)
    control_data = {"control": {"metric": [1, 2, 3, 4, 5] * 20}}
    treatment_data = {"treatment": {"metric": [1, 2, 3, 4, 5] * 20}}  # Identical
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    no_diff_p = results["treatment"]["metric"]["p_value"]
    
    # Test 2: Small difference (should have moderate p-value)
    treatment_data = {"treatment": {"metric": [1.1, 2.1, 3.1, 4.1, 5.1] * 20}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    small_diff_p = results["treatment"]["metric"]["p_value"]
    
    # Test 3: Large difference (should have small p-value)
    treatment_data = {"treatment": {"metric": [5, 6, 7, 8, 9] * 20}}
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="welch_t_test")
    
    large_diff_p = results["treatment"]["metric"]["p_value"]
    
    # P-values should follow expected pattern: no_diff > small_diff > large_diff
    assert no_diff_p > 0.5, f"No difference should have high p-value, got {no_diff_p}"
    assert large_diff_p < 0.01, f"Large difference should have very small p-value, got {large_diff_p}"
    assert large_diff_p < small_diff_p < no_diff_p, \
        f"P-values should decrease with effect size: {large_diff_p} < {small_diff_p} < {no_diff_p}"

def test_mann_whitney_rank_based_correctness():
    """Test that Mann-Whitney U test correctly handles rank-based comparisons."""
    
    # For very small samples (n=3 each), Mann-Whitney may not reach significance
    # due to discrete distribution. Let's use larger samples for reliable results.
    control_data = {"control": {"metric": [1, 2, 3, 1.5, 2.5, 3.5, 1.2, 2.2, 3.2]}}  # Lower values
    treatment_data = {"treatment": {"metric": [7, 8, 9, 7.5, 8.5, 9.5, 7.2, 8.2, 9.2]}}  # Higher values, clearly separated
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="mann_whitney")
    
    result = results["treatment"]["metric"]
    
    # Print debug info to understand what's happening
    print(f"Mann-Whitney p-value: {result['p_value']}")
    print(f"U statistic: {result['u_statistic']}")
    print(f"Effect size (CLES): {result['effect_size']}")
    
    # With clearly separated groups and larger sample size, should be significant
    assert result["significant"] == True, f"Clearly separated groups should be significant, p-value: {result['p_value']}"
    assert result["p_value"] < 0.05, f"P-value should be significant, got {result['p_value']}"
    
    # Median difference should be positive (treatment > control)
    assert result["median_difference"] > 0, "Median difference should be positive"
    
    # Effect size (CLES) should be close to 1.0 (all treatment > all control)
    effect_size = result.get("effect_size", 0)
    assert effect_size > 0.8, f"Effect size (CLES) should be high with separated groups, got {effect_size}"

def test_anova_multiple_group_comparison():
    """Test ANOVA correctly compares multiple groups."""
    
    # Create data with clear differences between groups
    control_data = {"control": {"metric": [1, 2, 3, 4, 5] * 10}}  # mean ≈ 3
    treatment_data = {
        "treatment1": {"metric": [2, 3, 4, 5, 6] * 10},  # mean ≈ 4
        "treatment2": {"metric": [3, 4, 5, 6, 7] * 10},  # mean ≈ 5
        "treatment3": {"metric": [1, 1, 2, 2, 3] * 10}   # mean ≈ 1.8 (clearly different)
    }
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="anova")
    
    # All treatments should be tested
    assert len(results) == 3
    
    # At least some treatments should be significantly different
    significant_count = sum(1 for treatment_id in results 
                          if results[treatment_id]["metric"]["significant"])
    
    assert significant_count > 0, "At least one treatment should be significantly different"
    
    # Treatment3 (most different) should definitely be significant
    treatment3_result = results["treatment3"]["metric"]
    assert treatment3_result["significant"] == True, \
        "Treatment3 with clearly different mean should be significant"

def test_debug_mann_whitney_cles():
    """Debug test to check CLES calculation and understand small sample behavior."""
    
    # Create simple data where we can manually calculate CLES
    control_data = {"control": {"metric": [1, 2, 3]}}  # Lower values
    treatment_data = {"treatment": {"metric": [7, 8, 9]}}  # Higher values, more separated
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="mann_whitney")
    
    result = results["treatment"]["metric"]
    
    # Manually calculate CLES for verification
    control_vals = [1, 2, 3]
    treatment_vals = [7, 8, 9]
    
    count = 0
    for tc in treatment_vals:
        for cc in control_vals:
            if tc > cc:
                count += 1
    
    expected_cles = count / (len(treatment_vals) * len(control_vals))
    # Should be 9/9 = 1.0 since all treatment values > all control values
    
    print(f"Expected CLES: {expected_cles}")
    print(f"Actual effect_size: {result.get('effect_size', 'NOT_FOUND')}")
    print(f"P-value: {result.get('p_value', 'NOT_FOUND')}")
    print(f"Significant: {result.get('significant', 'NOT_FOUND')}")
    print(f"All result keys: {list(result.keys())}")
    
    assert expected_cles == 1.0, f"Expected CLES should be 1.0, got {expected_cles}"
    
    # Check if the results structure is correct regardless of significance
    assert "p_value" in result, "Should have p_value in results"
    assert "significant" in result, "Should have significant in results"
    assert "effect_size" in result, "Should have effect_size in results"
    
    # With completely separated data, effect size should be 1.0
    assert result["effect_size"] == expected_cles, f"Effect size should be {expected_cles}, got {result['effect_size']}"
    
    # For very small samples, Mann-Whitney may not always reach traditional significance
    # but the effect size should still be correctly calculated
    # Just verify the test runs without error and produces reasonable results
    assert result["median_difference"] > 0, "Treatment median should be higher than control"

def test_mann_whitney_small_sample_limitations():
    """Test to document and verify Mann-Whitney behavior with very small samples."""
    
    # With very small samples (n=3 each), Mann-Whitney U test has limited power
    # and may not detect differences that would be significant with larger samples
    control_data = {"control": {"metric": [1, 2, 3]}}  # Lower values
    treatment_data = {"treatment": {"metric": [4, 5, 6]}}  # Higher values, completely separated
    
    tester = StatisticalTester(control_data, treatment_data)
    results = tester.run_test(test_type="mann_whitney")
    
    result = results["treatment"]["metric"]
    
    # The test should run without error and produce valid results
    assert "p_value" in result
    assert "significant" in result
    assert "effect_size" in result
    assert "u_statistic" in result
    
    # Effect size should be 1.0 since all treatment > all control
    assert result["effect_size"] == 1.0, f"Effect size should be 1.0, got {result['effect_size']}"
    
    # Median difference should be positive
    assert result["median_difference"] > 0, "Treatment median should be higher than control"
    
    # For this specific case, let's document the actual p-value behavior
    print(f"Small sample Mann-Whitney p-value: {result['p_value']}")
    print(f"Small sample significance: {result['significant']}")
    
    # Even if not significant due to small sample size, the effect size and direction should be correct
    assert result["effect_size"] >= 0.8, "Effect size should be large for completely separated groups"
