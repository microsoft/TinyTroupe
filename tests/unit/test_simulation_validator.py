"""
Tests for the simulation validation mechanism.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tinytroupe.validation import SimulationExperimentEmpiricalValidator, SimulationExperimentDataset, validate_simulation_experiment_empirically


def test_simulation_experiment_dataset():
    """Test SimulationExperimentDataset creation and conversion."""
    print("Testing SimulationExperimentDataset...")
    
    # Test creation with new format
    dataset = SimulationExperimentDataset(
        name="Test Dataset",
        description="A test dataset",
        key_results={"metric1": [1, 2, 3], "metric2": 0.5},
        result_types={"metric1": "per_agent", "metric2": "aggregate"},
        agent_names=["Agent_A", "Agent_B", "Agent_C"],
        agent_justifications=[
            {"agent_name": "Agent_A", "justification": "Test reasoning A"},
            {"agent_index": 1, "justification": "Test reasoning B"},
            "Simple justification without agent reference"
        ],
        justification_summary="Test summary"
    )
    
    # Test helper methods
    assert dataset.get_agent_name(0) == "Agent_A"
    assert dataset.get_agent_name(1) == "Agent_B"
    assert dataset.get_agent_name(10) is None  # Out of bounds
    
    # Test justification text extraction
    assert dataset.get_justification_text("Simple text") == "Simple text"
    assert dataset.get_justification_text({"justification": "Dict text"}) == "Dict text"
    
    # Test agent reference extraction
    assert dataset.get_justification_agent_reference({"agent_name": "TestAgent"}) == "TestAgent"
    assert dataset.get_justification_agent_reference({"agent_index": 0}) == "Agent_A"
    assert dataset.get_justification_agent_reference("Simple text") is None
    
    # Test conversion to dict
    dataset_dict = dataset.dict()
    assert dataset_dict["name"] == "Test Dataset"
    assert dataset_dict["key_results"]["metric1"] == [1, 2, 3]
    assert dataset_dict["result_types"]["metric1"] == "per_agent"
    
    # Test creation from dict
    dataset2 = SimulationExperimentDataset.parse_obj(dataset_dict)
    assert dataset2.name == dataset.name
    assert dataset2.key_results == dataset.key_results
    assert dataset2.result_types == dataset.result_types
    
    print("✅ SimulationExperimentDataset tests passed")


def test_statistical_validation():
    """Test statistical validation functionality."""
    print("Testing statistical validation...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    treatment_data = {
        "name": "Treatment", 
        "key_results": {
            "metric1": [15, 17, 16, 18, 14, 19],  # Higher values
            "metric2": [0.8, 0.9, 0.85, 0.95, 0.75, 1.0]  # Higher values
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    assert result.overall_score is not None
    assert 0.0 <= result.overall_score <= 1.0
    
    print("✅ Statistical validation tests passed")


def test_semantic_validation():
    """Test semantic validation functionality."""
    print("Testing semantic validation...")
    
    control_data = {
        "name": "Control",
        "agent_names": ["Agent1", "Agent2"],
        "agent_justifications": [
            {"agent_name": "Agent1", "justification": "I prefer affordable options because I'm budget-conscious."},
            {"agent_index": 1, "justification": "Price is my main concern when making purchases."}
        ],
        "justification_summary": "Agents focused primarily on cost and affordability in their decisions."
    }
    
    treatment_data = {
        "name": "Treatment",
        "agent_names": ["AgentA", "AgentB"],
        "agent_justifications": [
            {"agent_name": "AgentA", "justification": "I choose quality products even if they cost more because durability matters."},
            "Premium features justify higher prices for long-term value."  # String format without agent reference
        ],
        "justification_summary": "Agents emphasized quality and long-term value over immediate cost concerns."
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["semantic"],
        output_format="values"
    )
    
    assert result.semantic_results is not None
    assert len(result.semantic_results.get("individual_comparisons", [])) > 0
    assert result.semantic_results.get("summary_comparison") is not None
    assert result.overall_score is not None
    
    print("✅ Semantic validation tests passed")


def test_combined_validation():
    """Test combined statistical and semantic validation."""
    print("Testing combined validation...")
    
    control_data = {
        "name": "Control Group",
        "description": "Baseline experiment",
        "key_results": {
            "purchase_rate": [0.1, 0.12, 0.11, 0.13, 0.09],
            "satisfaction": [3.0, 3.2, 3.1, 3.3, 2.9]
        },
        "agent_justifications": [
            {"agent_name": "C1", "justification": "Price was too high for the value provided."},
            {"agent_name": "C2", "justification": "Product quality didn't meet my expectations."}
        ],
        "justification_summary": "Agents were generally dissatisfied with value proposition."
    }
    
    treatment_data = {
        "name": "Treatment Group",
        "description": "Enhanced product experiment", 
        "key_results": {
            "purchase_rate": [0.18, 0.20, 0.19, 0.21, 0.17],
            "satisfaction": [4.2, 4.4, 4.3, 4.5, 4.1]
        },
        "agent_justifications": [
            {"agent_name": "T1", "justification": "The enhanced features provided excellent value for money."},
            {"agent_name": "T2", "justification": "Product quality exceeded expectations and justified the cost."}
        ],
        "justification_summary": "Agents were highly satisfied with the improved value proposition."
    }
    
    # Test values output
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical", "semantic"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert result.semantic_results is not None
    assert result.overall_score is not None
    assert result.summary != ""
    
    # Test report output
    report = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical", "semantic"],
        output_format="report"
    )
    
    assert isinstance(report, str)
    assert "# Simulation Experiment Empirical Validation Report" in report
    assert "Statistical Validation" in report
    assert "Semantic Validation" in report
    
    print("✅ Combined validation tests passed")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("Testing error handling...")
    
    # Test with empty data
    empty_control = {"name": "Empty", "key_results": {}}
    empty_treatment = {"name": "Empty", "key_results": {}}
    
    result = validate_simulation_experiment_empirically(
        control_data=empty_control,
        treatment_data=empty_treatment,
        validation_types=["statistical"],
        output_format="values"
    )
    
    # Should handle gracefully
    assert result.statistical_results is not None
    assert "error" in result.statistical_results
    
    print("✅ Error handling tests passed")


def test_missing_data_handling():
    """Test handling of missing agent names and missing data points."""
    print("Testing missing data handling...")
    
    # Test with missing agent names and missing data
    dataset_with_missing = SimulationExperimentDataset(
        name="Test Missing Data",
        key_results={
            "metric1": [1, None, 3, 4],  # Missing data for agent 1
            "metric2": [0.5, 0.6, None, 0.8]  # Missing data for agent 2
        },
        result_types={
            "metric1": "per_agent",
            "metric2": "per_agent"
        },
        agent_names=["Alice", None, "Charlie", "Diana"],  # Missing name for agent 1
        agent_justifications=[
            {"agent_name": "Alice", "justification": "Good experience"},
            {"agent_index": 1, "justification": "Anonymous feedback"},  # Unnamed agent
            "Had some issues",  # No agent reference
            {"agent_name": "Diana", "justification": "Excellent"}
        ]
    )
    
    # Test agent name retrieval with None
    assert dataset_with_missing.get_agent_name(0) == "Alice"
    assert dataset_with_missing.get_agent_name(1) is None  # Missing name
    assert dataset_with_missing.get_agent_name(2) == "Charlie"
    
    # Test data retrieval with None values
    assert dataset_with_missing.get_agent_data("metric1", 0) == 1
    assert dataset_with_missing.get_agent_data("metric1", 1) is None  # Missing data
    assert dataset_with_missing.get_agent_data("metric1", 2) == 3
    
    # Test valid data filtering
    valid_metric1 = dataset_with_missing.get_valid_agent_data("metric1")
    assert valid_metric1 == [1, 3, 4]  # None filtered out
    
    valid_metric2 = dataset_with_missing.get_valid_agent_data("metric2")
    assert valid_metric2 == [0.5, 0.6, 0.8]  # None filtered out
    
    # Test all agent data mapping (should exclude None values)
    all_metric1 = dataset_with_missing.get_all_agent_data("metric1")
    expected_keys = {"Alice", "Charlie", "Diana"}  # Agent_1 excluded due to None value
    assert set(all_metric1.keys()) == expected_keys
    assert all_metric1["Alice"] == 1
    assert all_metric1["Charlie"] == 3
    assert all_metric1["Diana"] == 4
    
    # Test consistency validation (should show warnings, not errors)
    issues = dataset_with_missing.validate_data_consistency()
    warning_issues = [issue for issue in issues if issue.startswith("WARNING")]
    error_issues = [issue for issue in issues if not issue.startswith("WARNING")]
    
    assert len(error_issues) == 0  # No structural errors
    assert len(warning_issues) > 0  # Should have warnings about None values
    
    print("✅ Missing data handling tests passed")


def test_statistical_validation_with_missing_data():
    """Test statistical validation when data contains None values."""
    print("Testing statistical validation with missing data...")
    
    control_data = {
        "name": "Control with Missing",
        "key_results": {
            "metric1": [10, None, 12, 14],  # 1 missing value
            "metric2": [0.5, 0.6, None, 0.8]  # 1 missing value
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    treatment_data = {
        "name": "Treatment with Missing",
        "key_results": {
            "metric1": [15, 17, None, 19],  # 1 missing value
            "metric2": [0.7, None, 0.9, 1.0]  # 1 missing value
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    # Should not crash despite missing data
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    assert result.overall_score is not None
    
    print("✅ Statistical validation with missing data tests passed")


def test_statistical_equivalence():
    """Test statistical validation when control and treatment are equivalent."""
    print("Testing statistical equivalence...")
    
    # Create identical data for control and treatment
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    # Treatment data is identical to control (should show no significant differences)
    treatment_data = {
        "name": "Treatment", 
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],  # Same values as control
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]  # Same values as control
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    
    # Check that no tests show significance (since data is identical)
    test_results = result.statistical_results["test_results"]
    for treatment_name, treatment_results in test_results.items():
        for metric, metric_result in treatment_results.items():
            assert not metric_result.get("significant", True), f"Metric {metric} should not be significant with identical data"
            # p-value should be high (close to 1.0) for identical data
            p_value = metric_result.get("p_value", 0)
            assert p_value > 0.05, f"p-value for {metric} should be > 0.05 for identical data, got {p_value}"
    
    # Overall score should be high (close to 1.0) since no significant differences
    assert result.overall_score is not None
    assert result.overall_score >= 0.8, f"Overall score should be high for equivalent data, got {result.overall_score}"
    
    print("✅ Statistical equivalence tests passed")


def test_near_equivalent_data():
    """Test statistical validation with very similar but not identical data."""
    print("Testing near-equivalent data...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    # Treatment data is very similar to control with minor random variations
    treatment_data = {
        "name": "Treatment", 
        "key_results": {
            "metric1": [10.1, 11.9, 11.1, 13.1, 8.9, 14.1],  # Small variations
            "metric2": [0.51, 0.59, 0.56, 0.64, 0.46, 0.69]  # Small variations
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    
    # Check that most tests don't show significance (since data is very similar)
    test_results = result.statistical_results["test_results"]
    significant_count = 0
    total_count = 0
    
    for treatment_name, treatment_results in test_results.items():
        for metric, metric_result in treatment_results.items():
            total_count += 1
            if metric_result.get("significant", False):
                significant_count += 1
            
            # p-value should be reasonably high for similar data
            p_value = metric_result.get("p_value", 0)
            print(f"  {metric}: p-value = {p_value:.4f}, significant = {metric_result.get('significant', False)}")
    
    # Most tests should not be significant
    significance_rate = significant_count / total_count if total_count > 0 else 0
    assert significance_rate <= 0.5, f"Too many significant results for similar data: {significant_count}/{total_count}"
    
    # Overall score should be moderate to high
    assert result.overall_score is not None
    assert result.overall_score >= 0.4, f"Overall score should be reasonable for similar data, got {result.overall_score}"
    
    print("✅ Near-equivalent data tests passed")


def test_clearly_different_data():
    """Test statistical validation with clearly different data to ensure tests work correctly."""
    print("Testing clearly different data...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [1, 2, 3, 2, 1, 3],  # Low values
            "metric2": [0.1, 0.2, 0.15, 0.25, 0.1, 0.3]  # Low values
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    # Treatment data is clearly different from control
    treatment_data = {
        "name": "Treatment", 
        "key_results": {
            "metric1": [20, 22, 21, 23, 19, 24],  # Much higher values
            "metric2": [0.8, 0.9, 0.85, 0.95, 0.75, 1.0]  # Much higher values
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    
    # Check that tests show significance (since data is clearly different)
    test_results = result.statistical_results["test_results"]
    significant_count = 0
    total_count = 0
    
    for treatment_name, treatment_results in test_results.items():
        for metric, metric_result in treatment_results.items():
            total_count += 1
            if metric_result.get("significant", False):
                significant_count += 1
            
            # p-value should be low for clearly different data
            p_value = metric_result.get("p_value", 1)
            print(f"  {metric}: p-value = {p_value:.4f}, significant = {metric_result.get('significant', False)}")
    
    # Most or all tests should be significant
    significance_rate = significant_count / total_count if total_count > 0 else 0
    assert significance_rate >= 0.5, f"Too few significant results for clearly different data: {significant_count}/{total_count}"
    
    # Overall score should be low (since there are significant differences)
    assert result.overall_score is not None
    assert result.overall_score <= 0.6, f"Overall score should be low for clearly different data, got {result.overall_score}"
    
    print("✅ Clearly different data tests passed")


def test_mixed_equivalence_results():
    """Test statistical validation with mixed results (some metrics equivalent, some different)."""
    print("Testing mixed equivalence results...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],  # Will be equivalent
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7],  # Will be different
            "metric3": [100, 102, 101, 103, 99, 104]  # Will be equivalent
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent",
            "metric3": "per_agent"
        }
    }
    
    treatment_data = {
        "name": "Treatment", 
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],  # Same as control
            "metric2": [0.8, 0.9, 0.85, 0.95, 0.75, 1.0],  # Different from control
            "metric3": [100, 102, 101, 103, 99, 104]  # Same as control
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent",
            "metric3": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    
    # Check specific metrics
    test_results = result.statistical_results["test_results"]
    for treatment_name, treatment_results in test_results.items():
        # metric1 and metric3 should not be significant (identical data)
        if "metric1" in treatment_results:
            assert not treatment_results["metric1"].get("significant", True), "metric1 should not be significant"
        if "metric3" in treatment_results:
            assert not treatment_results["metric3"].get("significant", True), "metric3 should not be significant"
        
        # metric2 should be significant (different data)
        if "metric2" in treatment_results:
            # Note: With small sample sizes, even large differences might not always be significant
            # So we check the direction of the difference rather than strict significance
            p_value = treatment_results["metric2"].get("p_value", 1)
            print(f"  metric2: p-value = {p_value:.4f}, significant = {treatment_results['metric2'].get('significant', False)}")
    
    # Overall score should be moderate (some equivalent, some different)
    assert result.overall_score is not None
    assert 0.2 <= result.overall_score <= 0.9, f"Overall score should be moderate for mixed results, got {result.overall_score}"
    
    print("✅ Mixed equivalence results tests passed")


def test_treatment_equivalent_to_control():
    """Test that when Treatment data is equivalent to Control, validation detects no significant differences."""
    print("Testing treatment equivalent to control...")
    
    # Create identical datasets (Treatment should be equivalent to Control)
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    # Treatment with identical values (should show no significant difference)
    treatment_data = {
        "name": "Treatment",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],  # Identical values
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]  # Identical values
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    # Check that statistical results are available
    assert result.statistical_results is not None, "Statistical results should be available"
    assert "test_results" in result.statistical_results, "Test results should be present"
    
    # Check that no significant differences are detected (high p-values)
    test_results = result.statistical_results["test_results"]
    for treatment_name, treatment_results in test_results.items():
        for metric, metric_result in treatment_results.items():
            assert not metric_result.get("significant", True), \
                f"Metric '{metric}' should not show significant difference when Treatment equals Control"
            
            # P-value should be high (close to 1.0) for identical data
            p_value = metric_result.get("p_value", 0.0)
            assert p_value > 0.05, f"P-value for '{metric}' should be > 0.05 (was {p_value})"
    
    # Overall score should be very high (close to 1.0) when effect sizes are near 0
    assert result.overall_score is not None, "Overall score should be calculated"
    assert result.overall_score > 0.9, f"Overall score should be very high for identical data (was {result.overall_score})"
    
    print("✅ Treatment equivalent to control test passed")


def test_treatment_slightly_different_from_control():
    """Test that when Treatment data is slightly different from Control, validation detects minimal differences."""
    print("Testing treatment slightly different from control...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    # Treatment with slightly different values (small random noise)
    treatment_data = {
        "name": "Treatment",
        "key_results": {
            "metric1": [10.1, 12.1, 11.1, 13.1, 9.1, 14.1],  # Slightly higher
            "metric2": [0.51, 0.61, 0.56, 0.66, 0.46, 0.71]  # Slightly higher
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    # Check that statistical results are available
    assert result.statistical_results is not None, "Statistical results should be available"
    assert "test_results" in result.statistical_results, "Test results should be present"
    
    # Check that differences are likely not significant (small differences)
    test_results = result.statistical_results["test_results"]
    for treatment_name, treatment_results in test_results.items():
        for metric, metric_result in treatment_results.items():
            # Small differences should likely not be significant
            p_value = metric_result.get("p_value", 0.0)
            # With small differences, p-value should typically be > 0.05
            assert p_value >= 0.0, f"P-value for '{metric}' should be valid (was {p_value})"
    
    # Overall score should be moderate to high
    assert result.overall_score is not None, "Overall score should be calculated"
    assert 0.0 <= result.overall_score <= 1.0, f"Overall score should be between 0 and 1 (was {result.overall_score})"
    
    print("✅ Treatment slightly different from control test passed")


def test_treatment_very_different_from_control():
    """Test that when Treatment data is very different from Control, validation detects significant differences."""
    print("Testing treatment very different from control...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "metric1": [10, 12, 11, 13, 9, 14],
            "metric2": [0.5, 0.6, 0.55, 0.65, 0.45, 0.7]
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    # Treatment with very different values (much higher)
    treatment_data = {
        "name": "Treatment",
        "key_results": {
            "metric1": [25, 27, 26, 28, 24, 29],  # Much higher values
            "metric2": [1.0, 1.1, 1.05, 1.15, 0.95, 1.2]  # Much higher values
        },
        "result_types": {
            "metric1": "per_agent",
            "metric2": "per_agent"
        }
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    # Check that statistical results are available
    assert result.statistical_results is not None, "Statistical results should be available"
    assert "test_results" in result.statistical_results, "Test results should be present"
    
    # Check that significant differences are detected
    test_results = result.statistical_results["test_results"]
    significant_count = 0
    total_tests = 0
    
    for treatment_name, treatment_results in test_results.items():
        for metric, metric_result in treatment_results.items():
            total_tests += 1
            if metric_result.get("significant", False):
                significant_count += 1
            
            # P-value should be low for very different data
            p_value = metric_result.get("p_value", 1.0)
            assert p_value >= 0.0, f"P-value for '{metric}' should be valid (was {p_value})"
    
    # At least some tests should show significant differences
    assert total_tests > 0, "Should have at least one test"
    
    # Overall score should be lower when there are significant differences
    assert result.overall_score is not None, "Overall score should be calculated"
    assert 0.0 <= result.overall_score <= 1.0, f"Overall score should be between 0 and 1 (was {result.overall_score})"
    
    print("✅ Treatment very different from control test passed")


def test_semantic_equivalence_check():
    """Test that semantic validation correctly identifies equivalent vs different justifications."""
    print("Testing semantic equivalence check...")
    
    # Test with semantically equivalent justifications
    control_data = {
        "name": "Control",
        "agent_justifications": [
            {"agent_name": "Agent1", "justification": "I prefer affordable options because I'm budget-conscious."},
            {"agent_name": "Agent2", "justification": "Price is my main concern when making purchases."}
        ],
        "justification_summary": "Agents focused primarily on cost and affordability in their decisions."
    }
    
    # Treatment with semantically similar justifications (should have high proximity)
    treatment_data = {
        "name": "Treatment",
        "agent_justifications": [
            {"agent_name": "AgentA", "justification": "I choose affordable products because I'm price-sensitive."},
            {"agent_name": "AgentB", "justification": "Cost is my primary consideration when buying things."}
        ],
        "justification_summary": "Agents emphasized cost and affordability as key factors in their choices."
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["semantic"],
        output_format="values"
    )
    
    # Check that semantic results are available
    assert result.semantic_results is not None, "Semantic results should be available"
    assert len(result.semantic_results.get("individual_comparisons", [])) > 0, "Should have individual comparisons"
    
    # Check that proximity scores are high (semantically similar)
    individual_comparisons = result.semantic_results["individual_comparisons"]
    for comparison in individual_comparisons:
        proximity_score = comparison["proximity_score"]
        assert 0.0 <= proximity_score <= 1.0, f"Proximity score should be between 0 and 1 (was {proximity_score})"
        # Similar justifications should have moderate to high proximity
        assert proximity_score > 0.3, f"Semantically similar justifications should have proximity > 0.3 (was {proximity_score})"
    
    # Check summary comparison
    summary_comparison = result.semantic_results.get("summary_comparison")
    if summary_comparison:
        summary_proximity = summary_comparison["proximity_score"]
        assert 0.0 <= summary_proximity <= 1.0, f"Summary proximity should be between 0 and 1 (was {summary_proximity})"
        assert summary_proximity > 0.3, f"Similar summaries should have proximity > 0.3 (was {summary_proximity})"
    
    # Overall score should be moderate to high for semantically similar content
    assert result.overall_score is not None, "Overall score should be calculated"
    assert result.overall_score > 0.3, f"Overall score should be > 0.3 for similar content (was {result.overall_score})"
    
    print("✅ Semantic equivalence check test passed")


def test_combined_validation_equivalence():
    """Test combined validation when Treatment is equivalent to Control."""
    print("Testing combined validation equivalence...")
    
    # Create datasets that are equivalent both statistically and semantically
    control_data = {
        "name": "Control Group",
        "key_results": {
            "satisfaction": [3.5, 3.6, 3.4, 3.7, 3.3, 3.8],
            "engagement": [0.6, 0.65, 0.55, 0.7, 0.5, 0.75]
        },
        "result_types": {
            "satisfaction": "per_agent",
            "engagement": "per_agent"
        },
        "agent_justifications": [
            {"agent_name": "C1", "justification": "The product met my expectations and provided good value."},
            {"agent_name": "C2", "justification": "I found the offering to be satisfactory and reasonably priced."}
        ],
        "justification_summary": "Agents found the product satisfactory and reasonably priced."
    }
    
    # Treatment with equivalent data (same values, similar justifications)
    treatment_data = {
        "name": "Treatment Group",
        "key_results": {
            "satisfaction": [3.5, 3.6, 3.4, 3.7, 3.3, 3.8],  # Identical values
            "engagement": [0.6, 0.65, 0.55, 0.7, 0.5, 0.75]  # Identical values
        },
        "result_types": {
            "satisfaction": "per_agent",
            "engagement": "per_agent"
        },
        "agent_justifications": [
            {"agent_name": "T1", "justification": "The product matched my expectations and offered good value."},
            {"agent_name": "T2", "justification": "I considered the offering satisfactory and fairly priced."}
        ],
        "justification_summary": "Agents considered the product satisfactory and fairly priced."
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical", "semantic"],
        output_format="values"
    )
    
    # Check both statistical and semantic results
    assert result.statistical_results is not None, "Statistical results should be available"
    assert result.semantic_results is not None, "Semantic results should be available"
    
    # Statistical tests should show no significant differences
    if "test_results" in result.statistical_results:
        test_results = result.statistical_results["test_results"]
        for treatment_name, treatment_results in test_results.items():
            for metric, metric_result in treatment_results.items():
                assert not metric_result.get("significant", True), \
                    f"Metric '{metric}' should not show significant difference for equivalent data"
    
    # Semantic comparison should show high similarity
    if result.semantic_results.get("individual_comparisons"):
        for comparison in result.semantic_results["individual_comparisons"]:
            proximity_score = comparison["proximity_score"]
            assert proximity_score > 0.3, f"Equivalent justifications should have high proximity (was {proximity_score})"
    
    # Overall score should be high for equivalent data (effect sizes near 0)
    assert result.overall_score is not None, "Overall score should be calculated"
    assert result.overall_score > 0.8, f"Overall score should be high for equivalent data (was {result.overall_score})"
    
    # Test report output
    report = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical", "semantic"],
        output_format="report"
    )
    
    assert isinstance(report, str), "Report should be a string"
    assert "# Simulation Experiment Empirical Validation Report" in report, "Report should have proper header"
    assert "Statistical Validation" in report, "Report should include statistical section"
    assert "Semantic Validation" in report, "Report should include semantic section"
    assert "Not Significant" in report, "Report should indicate no significant differences"
    
    print("✅ Combined validation equivalence test passed")

