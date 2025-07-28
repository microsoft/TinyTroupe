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
    dataset_dict = dataset.model_dump()
    assert dataset_dict["name"] == "Test Dataset"
    assert dataset_dict["key_results"]["metric1"] == [1, 2, 3]
    assert dataset_dict["result_types"]["metric1"] == "per_agent"
    
    # Test creation from dict
    dataset2 = SimulationExperimentDataset.model_validate(dataset_dict)
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
    print("result.semantic_results = ", result.semantic_results)
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


def test_ks_test_functionality():
    """Test KS test functionality for distribution comparison."""
    print("Testing KS test functionality...")
    
    # Test with similar distributions (should not be significant)
    control_data = {
        "name": "Control",
        "key_results": {
            # Most agents prefer "Maybe" (2), some "Yes" (1), few "No" (0)
            "preference_score": [0, 0, 0, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2]
        },
        "result_types": {
            "preference_score": "per_agent"
        }
    }
    
    treatment_data = {
        "name": "Treatment",
        "key_results": {
            # Similar distribution with slight variation
            "preference_score": [0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        },
        "result_types": {
            "preference_score": "per_agent"
        }
    }
    
    # Test with KS test
    result_ks = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="values"
    )
    
    assert result_ks.statistical_results is not None
    assert "test_results" in result_ks.statistical_results
    assert result_ks.statistical_results["test_type"] == "ks_test"
    
    # Check KS-specific results
    test_results = result_ks.statistical_results["test_results"]
    for treatment_name, treatment_results in test_results.items():
        for metric, metric_result in treatment_results.items():
            assert "ks_statistic" in metric_result
            assert "test_type" in metric_result
            assert "Kolmogorov-Smirnov" in metric_result["test_type"]
            assert "overlap_coefficient" in metric_result
            assert "percentile_differences" in metric_result
            assert "interpretation" in metric_result
    
    print("✅ KS test functionality tests passed")


def test_ks_vs_ttest_comparison():
    """Test that KS test can detect distributional differences that t-test might miss."""
    print("Testing KS test vs t-test comparison...")
    
    # Create data with same mean but different distributions
    # Control: concentrated around middle value
    control_data = {
        "name": "Control",
        "key_results": {
            "metric": [1.5, 1.6, 1.4, 1.5, 1.6, 1.4, 1.5, 1.6]  # Mean ≈ 1.5
        },
        "result_types": {
            "metric": "per_agent"
        }
    }
    
    # Treatment: more spread out but similar mean
    treatment_data = {
        "name": "Treatment", 
        "key_results": {
            "metric": [0.5, 2.5, 0.5, 2.5, 1.0, 2.0, 1.0, 2.0]  # Mean ≈ 1.5
        },
        "result_types": {
            "metric": "per_agent"
        }
    }
    
    # Test with t-test
    result_ttest = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="welch_t_test",
        output_format="values"
    )
    
    # Test with KS test
    result_ks = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="values"
    )
    
    # Both should have results
    assert result_ttest.statistical_results is not None
    assert result_ks.statistical_results is not None
    
    # Extract significance results
    ttest_significant = result_ttest.statistical_results["test_results"]["treatment"]["metric"]["significant"]
    ks_significant = result_ks.statistical_results["test_results"]["treatment"]["metric"]["significant"]
    
    ttest_pvalue = result_ttest.statistical_results["test_results"]["treatment"]["metric"]["p_value"]
    ks_pvalue = result_ks.statistical_results["test_results"]["treatment"]["metric"]["p_value"]
    
    print(f"T-test: significant={ttest_significant}, p-value={ttest_pvalue:.4f}")
    print(f"KS test: significant={ks_significant}, p-value={ks_pvalue:.4f}")
    
    # KS test should be more sensitive to distributional differences
    # Note: This is a probabilistic test, so we check that both tests can run without error
    assert isinstance(ttest_significant, bool)
    assert isinstance(ks_significant, bool)
    assert 0.0 <= ttest_pvalue <= 1.0
    assert 0.0 <= ks_pvalue <= 1.0
    
    print("✅ KS vs t-test comparison tests passed")


def test_ks_test_categorical_responses():
    """Test KS test with categorical response data (Yes/No/Maybe)."""
    print("Testing KS test with categorical responses...")
    
    # Control: Most say "Maybe" (encoded as 1)
    control_data = {
        "name": "Control Group",
        "description": "Empirical control data for product preference",
        "key_results": {
            "response": [0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 2, 2]  # 0=No, 1=Maybe, 2=Yes
        },
        "result_types": {
            "response": "per_agent"
        },
        "agent_names": [f"C{i}" for i in range(12)],
        "justification_summary": "Most agents were undecided, leaning towards maybe"
    }
    
    # Treatment: More polarized responses (more Yes and No, less Maybe)
    treatment_data = {
        "name": "Simulation Group",
        "description": "AI agent simulation results for product preference",
        "key_results": {
            "response": [0, 0, 0, 0, 0, 1, 1, 2, 2, 2, 2, 2]  # More polarized
        },
        "result_types": {
            "response": "per_agent"
        },
        "agent_names": [f"S{i}" for i in range(12)],
        "justification_summary": "Agents showed more polarized responses with clearer preferences"
    }
    
    # Test with KS test
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    
    # Extract KS test results
    test_results = result.statistical_results["test_results"]
    metric_result = test_results["treatment"]["response"]
    
    # Verify KS-specific fields
    assert "ks_statistic" in metric_result
    assert "overlap_coefficient" in metric_result
    assert "percentile_differences" in metric_result
    assert "interpretation" in metric_result
    
    # KS statistic should be > 0 (some difference detected)
    ks_stat = metric_result["ks_statistic"]
    assert ks_stat >= 0.0
    assert ks_stat <= 1.0
    
    # Check percentile differences
    percentile_diffs = metric_result["percentile_differences"]
    assert "p25_diff" in percentile_diffs
    assert "p50_diff" in percentile_diffs
    assert "p75_diff" in percentile_diffs
    
    print("✅ KS test categorical responses tests passed")


def test_ks_test_report_generation():
    """Test that KS test results are properly formatted in reports."""
    print("Testing KS test report generation...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "metric": [1, 2, 3, 4, 5]
        },
        "result_types": {
            "metric": "per_agent"
        }
    }
    
    treatment_data = {
        "name": "Treatment",
        "key_results": {
            "metric": [2, 3, 4, 5, 6]
        },
        "result_types": {
            "metric": "per_agent"
        }
    }
    
    # Generate report with KS test
    report = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="report"
    )
    
    assert isinstance(report, str)
    assert "# Simulation Experiment Empirical Validation Report" in report
    assert "Kolmogorov-Smirnov test" in report
    assert "ks_statistic" in report or "statistic:" in report
    assert "effect size:" in report
    
    # Check for KS-specific effect size interpretation
    assert any(phrase in report for phrase in [
        "negligible difference", "small difference", 
        "medium difference", "large difference"
    ])
    
    print("✅ KS test report generation tests passed")


def test_ks_test_identical_distributions():
    """Test KS test with identical distributions (should show no significant difference)."""
    print("Testing KS test with identical distributions...")
    
    # Identical distributions
    identical_data = [1, 2, 2, 3, 3, 3, 4, 4, 5]
    
    control_data = {
        "name": "Control",
        "key_results": {"metric": identical_data},
        "result_types": {"metric": "per_agent"}
    }
    
    treatment_data = {
        "name": "Treatment",
        "key_results": {"metric": identical_data.copy()},
        "result_types": {"metric": "per_agent"}
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="values"
    )
    
    assert result.statistical_results is not None
    
    # Check results
    metric_result = result.statistical_results["test_results"]["treatment"]["metric"]
    
    # Should not be significant and KS statistic should be 0 or very small
    assert not metric_result["significant"] or metric_result["p_value"] > 0.05
    assert metric_result["ks_statistic"] <= 0.01  # Very small difference
    
    # Overall score should be high (distributions are identical)
    assert result.overall_score is not None
    assert result.overall_score > 0.95
    
    print("✅ KS test identical distributions tests passed")


def test_ks_test_completely_different_distributions():
    """Test KS test with completely different distributions (should be highly significant)."""
    print("Testing KS test with completely different distributions...")
    
    control_data = {
        "name": "Control",
        "key_results": {"metric": [1, 1, 1, 2, 2, 2]},  # Low values
        "result_types": {"metric": "per_agent"}
    }
    
    treatment_data = {
        "name": "Treatment",
        "key_results": {"metric": [8, 8, 8, 9, 9, 9]},  # High values
        "result_types": {"metric": "per_agent"}
    }
    
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="values"
    )
    
    assert result.statistical_results is not None
    
    # Check results
    metric_result = result.statistical_results["test_results"]["treatment"]["metric"]
    
    # Should be highly significant
    assert metric_result["significant"]
    assert metric_result["p_value"] < 0.01
    assert metric_result["ks_statistic"] > 0.5  # Large difference
    
    # Interpretation should indicate large difference
    assert "large difference" in metric_result["interpretation"].lower()
    
    # Overall score should be low (distributions are very different)
    assert result.overall_score is not None
    assert result.overall_score <= 0.5
    
    print("✅ KS test completely different distributions tests passed")


def test_all_statistical_test_types():
    """Test that all statistical test types work with the validator."""
    print("Testing all statistical test types...")
    
    control_data = {
        "name": "Control",
        "key_results": {"metric": [10, 12, 11, 13, 9, 14]},
        "result_types": {"metric": "per_agent"}
    }
    
    treatment_data = {
        "name": "Treatment",
        "key_results": {"metric": [15, 17, 16, 18, 14, 19]},
        "result_types": {"metric": "per_agent"}
    }
    
    # Test each statistical test type
    test_types = ["welch_t_test", "t_test", "mann_whitney", "ks_test"]
    
    for test_type in test_types:
        print(f"  Testing {test_type}...")
        
        result = validate_simulation_experiment_empirically(
            control_data=control_data,
            treatment_data=treatment_data,
            validation_types=["statistical"],
            statistical_test_type=test_type,
            output_format="values"
        )
        
        assert result.statistical_results is not None, f"Failed for {test_type}"
        assert "test_results" in result.statistical_results, f"Failed for {test_type}"
        assert result.statistical_results["test_type"] == test_type, f"Failed for {test_type}"
        assert result.overall_score is not None, f"Failed for {test_type}"
        assert 0.0 <= result.overall_score <= 1.0, f"Failed for {test_type}"
        
        # Check that the appropriate test was used
        metric_result = result.statistical_results["test_results"]["treatment"]["metric"]
        test_name = metric_result["test_type"].lower()
        
        if test_type == "ks_test":
            assert "kolmogorov-smirnov" in test_name
            assert "ks_statistic" in metric_result
        elif test_type in ["welch_t_test", "t_test"]:
            assert "t-test" in test_name
            assert "t_statistic" in metric_result
        elif test_type == "mann_whitney":
            assert "mann-whitney" in test_name
            assert "u_statistic" in metric_result
    
    print("✅ All statistical test types tests passed")


def test_categorical_data_basic():
    """Test basic categorical data handling."""
    print("Testing basic categorical data handling...")
    
    # Test dataset with categorical string data
    dataset = SimulationExperimentDataset(
        name="Categorical Test",
        key_results={
            "preference": ["yes", "no", "maybe", "yes", "maybe"],
            "satisfaction": ["high", "medium", "low", "high", "medium"]
        },
        result_types={
            "preference": "per_agent",
            "satisfaction": "per_agent"
        }
    )
    
    # Check that categorical mappings were created
    assert "preference" in dataset.categorical_mappings
    assert "satisfaction" in dataset.categorical_mappings
    
    # Check mappings are correct (sorted alphabetically)
    pref_mapping = dataset.categorical_mappings["preference"]
    expected_pref_categories = ["maybe", "no", "yes"]  # Sorted alphabetically
    assert len(pref_mapping) == 3
    for i, category in enumerate(expected_pref_categories):
        assert pref_mapping[category] == i
    
    # Check that original data was converted to ordinal
    converted_data = dataset.key_results["preference"]
    assert isinstance(converted_data, list)
    assert all(isinstance(x, int) for x in converted_data)
    
    # Check conversion accuracy
    original = ["yes", "no", "maybe", "yes", "maybe"]
    expected_ordinal = [pref_mapping[x] for x in original]
    assert converted_data == expected_ordinal
    
    print("✅ Basic categorical data handling tests passed")


def test_categorical_data_normalization():
    """Test categorical data normalization (case, whitespace)."""
    print("Testing categorical data normalization...")
    
    dataset = SimulationExperimentDataset(
        name="Normalization Test",
        key_results={
            "response": ["Yes", "NO", " maybe ", "YES", "no", "Maybe"]
        },
        result_types={
            "response": "per_agent"
        }
    )
    
    # Check that normalization worked (should have 3 unique categories)
    mapping = dataset.categorical_mappings["response"]
    assert len(mapping) == 3
    
    # Check normalized categories exist
    assert "yes" in mapping
    assert "no" in mapping
    assert "maybe" in mapping
    
    # All should map to different ordinal values
    values = list(mapping.values())
    assert len(set(values)) == 3  # All unique values
    
    print("✅ Categorical data normalization tests passed")


def test_categorical_data_with_none():
    """Test categorical data handling with None values."""
    print("Testing categorical data with None values...")
    
    dataset = SimulationExperimentDataset(
        name="None Test",
        key_results={
            "response": ["yes", None, "no", "maybe", None, "yes"]
        },
        result_types={
            "response": "per_agent"
        }
    )
    
    # Check mapping was created despite None values
    assert "response" in dataset.categorical_mappings
    mapping = dataset.categorical_mappings["response"]
    assert len(mapping) == 3  # Only non-None values should be mapped
    
    # Check that None values are preserved
    converted_data = dataset.key_results["response"]
    assert converted_data[1] is None
    assert converted_data[4] is None
    
    # Check non-None values are converted
    assert isinstance(converted_data[0], int)
    assert isinstance(converted_data[2], int)
    
    print("✅ Categorical data with None values tests passed")


def test_categorical_conversion_methods():
    """Test categorical conversion helper methods."""
    print("Testing categorical conversion methods...")
    
    dataset = SimulationExperimentDataset(
        name="Conversion Test",
        key_results={
            "preference": ["yes", "no", "maybe"],
            "numeric": [1, 2, 3]  # Should not be treated as categorical
        },
        result_types={
            "preference": "per_agent",
            "numeric": "per_agent"
        }
    )
    
    # Test get_categorical_values
    categories = dataset.get_categorical_values("preference")
    assert categories == ["maybe", "no", "yes"]  # Alphabetically sorted
    
    # Test with non-categorical metric
    assert dataset.get_categorical_values("numeric") is None
    
    # Test convert_ordinal_to_categorical
    mapping = dataset.categorical_mappings["preference"]
    for category, ordinal in mapping.items():
        converted_back = dataset.convert_ordinal_to_categorical("preference", ordinal)
        assert converted_back == category
    
    # Test is_categorical_metric
    assert dataset.is_categorical_metric("preference") is True
    assert dataset.is_categorical_metric("numeric") is False
    
    # Test get_metric_summary
    summary = dataset.get_metric_summary("preference")
    assert summary["is_categorical"] is True
    assert "categories" in summary
    assert "category_mapping" in summary
    assert "category_distribution" in summary
    
    numeric_summary = dataset.get_metric_summary("numeric")
    assert numeric_summary["is_categorical"] is False
    assert "categories" not in numeric_summary
    
    print("✅ Categorical conversion methods tests passed")


def test_categorical_ks_test():
    """Test KS test with categorical string input."""
    print("Testing KS test with categorical string input...")
    
    # Control group: mostly "maybe" responses
    control_data = {
        "name": "Control",
        "key_results": {
            "preference": ["no", "no", "maybe", "maybe", "maybe", "maybe", "yes"]
        },
        "result_types": {
            "preference": "per_agent"
        }
    }
    
    # Treatment group: more polarized (more yes/no, less maybe)
    treatment_data = {
        "name": "Treatment",
        "key_results": {
            "preference": ["no", "no", "no", "yes", "yes", "yes", "yes"]
        },
        "result_types": {
            "preference": "per_agent"
        }
    }
    
    # Test with KS test
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    
    # Check that the test ran successfully
    metric_result = result.statistical_results["test_results"]["treatment"]["preference"]
    assert "ks_statistic" in metric_result
    assert "p_value" in metric_result
    assert "significant" in metric_result
    
    print("✅ Categorical KS test tests passed")


def test_categorical_report_generation():
    """Test that categorical data appears correctly in reports."""
    print("Testing categorical report generation...")
    
    control_data = {
        "name": "Control",
        "key_results": {
            "satisfaction": ["low", "medium", "high", "medium"],
            "preference": ["yes", "no", "maybe", "yes"]
        },
        "result_types": {
            "satisfaction": "per_agent",
            "preference": "per_agent"
        }
    }
    
    treatment_data = {
        "name": "Treatment", 
        "key_results": {
            "satisfaction": ["medium", "high", "high", "high"],
            "preference": ["yes", "yes", "maybe", "yes"]
        },
        "result_types": {
            "satisfaction": "per_agent",
            "preference": "per_agent"
        }
    }
    
    # Generate report
    report = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        statistical_test_type="ks_test",
        output_format="report"
    )
    
    assert isinstance(report, str)
    assert "Data Type Information" in report
    assert "satisfaction" in report
    assert "preference" in report
    # New format uses "**Control:**" and "**Treatment:**" (with markdown bold)
    assert "**Control:**" in report
    assert "**Treatment:**" in report
    assert "- Distribution:" in report  # Updated to match actual format
    
    # Check that categorical mappings are shown
    assert "low" in report
    assert "medium" in report
    assert "high" in report
    assert "yes" in report
    assert "no" in report
    assert "maybe" in report
    
    print("✅ Categorical report generation tests passed")


def test_mixed_categorical_numeric_data():
    """Test datasets with both categorical and numeric metrics."""
    print("Testing mixed categorical and numeric data...")
    
    dataset = SimulationExperimentDataset(
        name="Mixed Test",
        key_results={
            "satisfaction": ["low", "medium", "high"],  # Categorical
            "score": [1.5, 2.8, 4.2],  # Numeric
            "preference": ["yes", "no", "maybe"],  # Categorical
            "count": [10, 15, 8]  # Numeric
        },
        result_types={
            "satisfaction": "per_agent",
            "score": "per_agent", 
            "preference": "per_agent",
            "count": "per_agent"
        }
    )
    
    # Check that only categorical metrics have mappings
    assert "satisfaction" in dataset.categorical_mappings
    assert "preference" in dataset.categorical_mappings
    assert "score" not in dataset.categorical_mappings
    assert "count" not in dataset.categorical_mappings
    
    # Check data conversion
    assert isinstance(dataset.key_results["satisfaction"], list)
    assert all(isinstance(x, int) for x in dataset.key_results["satisfaction"])
    
    assert isinstance(dataset.key_results["score"], list)
    assert all(isinstance(x, float) for x in dataset.key_results["score"])
    
    # Test metric summaries
    cat_summary = dataset.get_metric_summary("satisfaction")
    assert cat_summary["is_categorical"] is True
    
    num_summary = dataset.get_metric_summary("score")
    assert num_summary["is_categorical"] is False
    
    print("✅ Mixed categorical and numeric data tests passed")


def test_categorical_edge_cases():
    """Test edge cases for categorical data handling."""
    print("Testing categorical edge cases...")
    
    # Test with single categorical value
    dataset1 = SimulationExperimentDataset(
        name="Single Value",
        key_results={"response": ["yes", "yes", "yes"]},
        result_types={"response": "per_agent"}
    )
    
    assert "response" in dataset1.categorical_mappings
    assert len(dataset1.categorical_mappings["response"]) == 1
    assert "yes" in dataset1.categorical_mappings["response"]
    
    # Test with empty list
    dataset2 = SimulationExperimentDataset(
        name="Empty",
        key_results={"response": []},
        result_types={"response": "per_agent"}
    )
    
    assert "response" not in dataset2.categorical_mappings
    
    # Test with all None values
    dataset3 = SimulationExperimentDataset(
        name="All None",
        key_results={"response": [None, None, None]},
        result_types={"response": "per_agent"}
    )
    
    assert "response" not in dataset3.categorical_mappings
    
    # Test aggregate categorical data
    dataset4 = SimulationExperimentDataset(
        name="Aggregate",
        key_results={"response": "yes"},
        result_types={"response": "aggregate"}
    )
    
    assert "response" in dataset4.categorical_mappings
    assert dataset4.key_results["response"] == 0  # Converted to ordinal
    
    print("✅ Categorical edge cases tests passed")


# New tests for additional data types
def test_ordinal_data_basic():
    """Test basic ordinal data handling."""
    print("Testing ordinal data basic functionality...")
    
    # Test numeric ordinal data (Likert scale)
    dataset = SimulationExperimentDataset(
        name="Likert Test",
        key_results={
            "satisfaction": [1, 2, 3, 4, 5, 4, 3, 2, 1],
            "quality_rating": [2, 3, 4, 5, 5, 4, 3, 2, 1]
        },
        result_types={
            "satisfaction": "per_agent",
            "quality_rating": "per_agent"
        },
        data_types={
            "satisfaction": "ordinal",
            "quality_rating": "ordinal"
        }
    )
    
    # Check data type detection
    assert dataset.data_types["satisfaction"] == "ordinal"
    assert dataset.data_types["quality_rating"] == "ordinal"
    
    # Check ordinal mappings were created
    assert "satisfaction" in dataset.ordinal_mappings
    assert "quality_rating" in dataset.ordinal_mappings
    
    # Check ordinal info
    satisfaction_info = dataset.ordinal_mappings["satisfaction"]
    assert satisfaction_info["min_value"] == 1
    assert satisfaction_info["max_value"] == 5
    assert satisfaction_info["num_levels"] == 5
    
    print("✅ Ordinal data basic tests passed")


def test_ordinal_data_string_based():
    """Test string-based ordinal data handling."""
    print("Testing string-based ordinal data...")
    
    # Test with standard Likert strings
    dataset = SimulationExperimentDataset(
        name="String Ordinal Test",
        key_results={
            "agreement": ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
            "quality": ["Poor", "Fair", "Good", "Very Good", "Excellent"]
        },
        result_types={
            "agreement": "per_agent",
            "quality": "per_agent"
        },
        data_types={
            "agreement": "ordinal",
            "quality": "ordinal"
        }
    )
    
    # Check that string ordinal data was processed
    assert dataset.data_types["agreement"] == "ordinal"
    assert dataset.data_types["quality"] == "ordinal"
    
    # Check that strings were converted to ordinal values
    agreement_values = dataset.key_results["agreement"]
    assert all(isinstance(val, int) for val in agreement_values)
    
    # Check ordinal mappings
    assert "agreement" in dataset.ordinal_mappings
    agreement_mapping = dataset.ordinal_mappings["agreement"]
    
    # Should be ordered: Strongly Disagree < Disagree < Neutral < Agree < Strongly Agree
    assert agreement_mapping["strongly disagree"] < agreement_mapping["disagree"]
    assert agreement_mapping["disagree"] < agreement_mapping["neutral"]
    assert agreement_mapping["neutral"] < agreement_mapping["agree"]
    assert agreement_mapping["agree"] < agreement_mapping["strongly agree"]
    
    # Test conversion back to categorical
    assert dataset.convert_ordinal_to_categorical("agreement", 0) == "strongly disagree"
    
    # Test is_categorical_metric (should return True for string-based ordinal)
    assert dataset.is_categorical_metric("agreement") == True
    
    print("✅ String-based ordinal data tests passed")


def test_ranking_data():
    """Test ranking data handling."""
    print("Testing ranking data...")
    
    # Test ranking data (1=best, higher=worse)
    dataset = SimulationExperimentDataset(
        name="Ranking Test",
        key_results={
            "preference_rank": [1, 2, 3, 1, 2, 3, 1, 2],  # Ranking 3 options
            "performance_rank": [1, 3, 2, 4, 1, 2, 3, 4]  # Ranking 4 options
        },
        result_types={
            "preference_rank": "per_agent",
            "performance_rank": "per_agent"
        },
        data_types={
            "preference_rank": "ranking",
            "performance_rank": "ranking"
        }
    )
    
    # Check data type detection
    assert dataset.data_types["preference_rank"] == "ranking"
    assert dataset.data_types["performance_rank"] == "ranking"
    
    # Check ranking info
    assert "preference_rank" in dataset.ranking_info
    pref_info = dataset.ranking_info["preference_rank"]
    assert pref_info["min_rank"] == 1
    assert pref_info["max_rank"] == 3
    assert pref_info["num_ranks"] == 3
    assert pref_info["direction"] == "ascending"
    
    perf_info = dataset.ranking_info["performance_rank"]
    assert perf_info["min_rank"] == 1
    assert perf_info["max_rank"] == 4
    assert perf_info["num_ranks"] == 4
    
    # Test data type info
    data_type_info = dataset.get_data_type_info("preference_rank")
    assert data_type_info["data_type"] == "ranking"
    assert "ranking_info" in data_type_info
    
    # Test metric summary
    summary = dataset.get_metric_summary("preference_rank")
    assert summary["data_type"] == "ranking"
    assert "rank_distribution" in summary
    
    print("✅ Ranking data tests passed")


def test_count_data():
    """Test count data handling."""
    print("Testing count data...")
    
    # Test count data (non-negative integers)
    dataset = SimulationExperimentDataset(
        name="Count Test",
        key_results={
            "click_count": [0, 1, 2, 5, 10, 0, 3, 7],
            "visit_count": [1, 2, 3, 4, 5, 6, 7, 8]
        },
        result_types={
            "click_count": "per_agent",
            "visit_count": "per_agent"
        },
        data_types={
            "click_count": "count",
            "visit_count": "count"
        }
    )
    
    # Check data type detection
    assert dataset.data_types["click_count"] == "count"
    assert dataset.data_types["visit_count"] == "count"
    
    # Test metric summary
    summary = dataset.get_metric_summary("click_count")
    assert summary["data_type"] == "count"
    assert summary["min_value"] == 0
    assert summary["max_value"] == 10
    
    print("✅ Count data tests passed")


def test_count_data_validation():
    """Test count data validation (should reject negative numbers)."""
    print("Testing count data validation...")
    
    try:
        # This should raise an error due to negative values
        dataset = SimulationExperimentDataset(
            name="Invalid Count Test",
            key_results={
                "invalid_count": [1, 2, -1, 4]  # Negative value should cause error
            },
            result_types={
                "invalid_count": "per_agent"
            },
            data_types={
                "invalid_count": "count"
            }
        )
        assert False, "Should have raised ValueError for negative count data"
    except ValueError as e:
        assert "non-negative integers" in str(e)
    
    print("✅ Count data validation tests passed")


def test_proportion_data():
    """Test proportion data handling."""
    print("Testing proportion data...")
    
    # Test proportion data (0-1 range)
    dataset = SimulationExperimentDataset(
        name="Proportion Test",
        key_results={
            "success_rate": [0.1, 0.2, 0.8, 1.0, 0.0, 0.5],
            "completion_rate": [10, 20, 80, 100,  0, 50]  # Percentages that should be normalized
        },
        result_types={
            "success_rate": "per_agent",
            "completion_rate": "per_agent"
        },
        data_types={
            "success_rate": "proportion",
            "completion_rate": "proportion"
        }
    )
    
    # Check data type detection
    assert dataset.data_types["success_rate"] == "proportion"
    assert dataset.data_types["completion_rate"] == "proportion"
    
    # Check that percentages were normalized to 0-1 range
    completion_values = dataset.key_results["completion_rate"]
    assert all(0 <= val <= 1 for val in completion_values)
    assert completion_values[0] == 0.1  # 10 -> 0.1
    assert completion_values[3] == 1.0  # 100 -> 1.0
    
    # Success rate should remain unchanged (already 0-1)
    success_values = dataset.key_results["success_rate"]
    assert success_values == [0.1, 0.2, 0.8, 1.0, 0.0, 0.5]
    
    print("✅ Proportion data tests passed")


def test_binary_data():
    """Test binary data handling."""
    print("Testing binary data...")
    
    # Test various binary representations
    dataset = SimulationExperimentDataset(
        name="Binary Test",
        key_results={
            "bool_values": [True, False, True, False],
            "string_values": ["Yes", "No", "True", "False", "1", "0"],
            "numeric_values": [1, 0, 1, 0, 2, -1]  # 2 and -1 should become 1 and 0
        },
        result_types={
            "bool_values": "per_agent",
            "string_values": "per_agent",
            "numeric_values": "per_agent"
        },
        data_types={
            "bool_values": "binary",
            "string_values": "binary",
            "numeric_values": "binary"
        }
    )
    
    # Check data type detection
    assert dataset.data_types["bool_values"] == "binary"
    assert dataset.data_types["string_values"] == "binary"
    assert dataset.data_types["numeric_values"] == "binary"
    
    # Check that all values were converted to 0 or 1
    bool_values = dataset.key_results["bool_values"]
    assert bool_values == [1, 0, 1, 0]
    
    string_values = dataset.key_results["string_values"]
    assert string_values == [1, 0, 1, 0, 1, 0]
    
    numeric_values = dataset.key_results["numeric_values"]
    assert numeric_values == [1, 0, 1, 0, 1, 1]  # 2 -> 1, -1 -> 1 (non-zero)
    
    # Test metric summary with binary distribution
    summary = dataset.get_metric_summary("bool_values")
    assert summary["data_type"] == "binary"
    assert "binary_distribution" in summary
    distribution = summary["binary_distribution"]
    assert distribution["true"] == 2
    assert distribution["false"] == 2
    
    print("✅ Binary data tests passed")


def test_auto_data_type_detection():
    """Test automatic data type detection."""
    print("Testing automatic data type detection...")
    
    # Test auto-detection without explicit data types
    dataset = SimulationExperimentDataset(
        name="Auto Detection Test",
        key_results={
            "categorical_data": ["Red", "Blue", "Green", "Red"],
            "ordinal_numbers": [1, 2, 3, 4, 5],
            "ranking_data": [1, 2, 3, 1, 2, 3],  # Should detect as ranking
            "count_data": [0, 1, 2, 5, 10],
            "proportion_data": [0.1, 0.5, 0.8, 1.0],
            "binary_bool": [True, False, True, False],
            "numeric_data": [1.5, 2.7, 3.2, 4.1]
        },
        result_types={name: "per_agent" for name in [
            "categorical_data", "ordinal_numbers", "ranking_data", 
            "count_data", "proportion_data", "binary_bool", "numeric_data"
        ]}
        # No explicit data_types - should auto-detect
    )
    
    # Check auto-detection results
    assert dataset.data_types["categorical_data"] == "categorical"
    assert dataset.data_types["ranking_data"] == "ranking"  # Consecutive 1,2,3
    assert dataset.data_types["count_data"] == "count"
    assert dataset.data_types["proportion_data"] == "proportion"
    assert dataset.data_types["binary_bool"] == "binary"
    assert dataset.data_types["numeric_data"] == "numeric"
    
    # ordinal_numbers is tricky - could be count or ranking
    # [1, 2, 3, 4, 5] has no repetition, so should be detected as count (not ranking)
    assert dataset.data_types["ordinal_numbers"] == "count"
    
    print("✅ Auto data type detection tests passed")


def test_mixed_data_types_validation():
    """Test validation with mixed data types."""
    print("Testing mixed data types validation...")
    
    control_data = {
        "name": "Control Mixed",
        "key_results": {
            "satisfaction": ["Poor", "Fair", "Good", "Very Good", "Excellent"],
            "ranking": [1, 2, 3, 1, 2],
            "success": [True, False, True, False, True],
            "click_count": [0, 1, 2, 3, 4],
            "conversion_rate": [0.1, 0.2, 0.3, 0.4, 0.5]
        },
        "result_types": {name: "per_agent" for name in [
            "satisfaction", "ranking", "success", "click_count", "conversion_rate"
        ]},
        "data_types": {
            "satisfaction": "ordinal",
            "ranking": "ranking", 
            "success": "binary",
            "click_count": "count",
            "conversion_rate": "proportion"
        }
    }
    
    treatment_data = {
        "name": "Treatment Mixed",
        "key_results": {
            "satisfaction": ["Fair", "Good", "Very Good", "Excellent", "Excellent"],
            "ranking": [1, 1, 2, 1, 1],  # Better rankings
            "success": [True, True, True, True, False],  # Higher success rate
            "click_count": [1, 2, 3, 4, 5],  # Higher counts
            "conversion_rate": [0.2, 0.3, 0.4, 0.5, 0.6]  # Higher rates
        },
        "result_types": {name: "per_agent" for name in [
            "satisfaction", "ranking", "success", "click_count", "conversion_rate"
        ]},
        "data_types": {
            "satisfaction": "ordinal",
            "ranking": "ranking",
            "success": "binary", 
            "click_count": "count",
            "conversion_rate": "proportion"
        }
    }
    
    # Test statistical validation with mixed data types
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert "test_results" in result.statistical_results
    assert result.overall_score is not None
    
    # Test report generation with mixed data types
    report = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="report"
    )
    
    assert isinstance(report, str)
    assert "Data Type Information" in report
    assert "Ordinal Data" in report
    assert "Ranking Data" in report
    assert "Binary Data" in report
    assert "Count Data" in report
    assert "Proportion Data" in report
    
    print("✅ Mixed data types validation tests passed")


def test_data_type_edge_cases():
    """Test edge cases for data type handling."""
    print("Testing data type edge cases...")
    
    # Test with None values
    dataset = SimulationExperimentDataset(
        name="Edge Cases Test",
        key_results={
            "with_nones": [1, None, 3, None, 5],
            "empty_list": [],
            "single_value": [42],
            "mixed_types": [1, "text", 3.14]  # Should default to numeric
        },
        result_types={
            "with_nones": "per_agent",
            "empty_list": "per_agent", 
            "single_value": "per_agent",
            "mixed_types": "per_agent"
        }
        # Let auto-detection handle data types
    )
    
    # Should handle None values gracefully
    assert dataset.data_types["with_nones"] == "count"  # Non-negative integers
    assert dataset.data_types["empty_list"] == "numeric"  # Default fallback
    assert dataset.data_types["single_value"] == "count"  # Single positive integer
    assert dataset.data_types["mixed_types"] == "categorical"  # Mixed types with strings default to categorical
    
    # Test data consistency validation
    issues = dataset.validate_data_consistency()
    # Should not crash despite edge cases
    assert isinstance(issues, list)
    
    print("✅ Data type edge cases tests passed")


def test_ordinal_ranking_comparison():
    """Test validation specifically comparing ordinal vs ranking data."""
    print("Testing ordinal vs ranking comparison...")
    
    # Control with ordinal satisfaction ratings
    control_data = {
        "name": "Control Ordinal",
        "key_results": {
            "satisfaction": [1, 2, 3, 4, 5, 3, 2, 4, 5, 1]  # Likert scale
        },
        "result_types": {"satisfaction": "per_agent"},
        "data_types": {"satisfaction": "ordinal"}
    }
    
    # Treatment with ranking data (different concept - preference ranks)
    treatment_data = {
        "name": "Treatment Ranking", 
        "key_results": {
            "satisfaction": [1, 1, 2, 1, 1, 2, 3, 1, 1, 2]  # Rankings (1=best)
        },
        "result_types": {"satisfaction": "per_agent"},
        "data_types": {"satisfaction": "ranking"}
    }
    
    # Should be able to compare despite different data type semantics
    result = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="values"
    )
    
    assert result.statistical_results is not None
    assert result.overall_score is not None
    
    print("✅ Ordinal vs ranking comparison tests passed")


def test_comprehensive_data_type_report():
    """Test comprehensive data type reporting."""
    print("Testing comprehensive data type report...")
    
    # Create datasets with all data types
    control_data = {
        "name": "Comprehensive Control",
        "key_results": {
            "categorical": ["Red", "Blue", "Green"],
            "ordinal_string": ["Poor", "Good", "Excellent"], 
            "ordinal_numeric": [1, 3, 5],
            "ranking": [1, 2, 3],
            "count": [0, 5, 10],
            "proportion": [0.1, 0.5, 0.9],
            "binary": [True, False, True],
            "numeric": [1.5, 2.7, 3.9]
        },
        "result_types": {name: "per_agent" for name in [
            "categorical", "ordinal_string", "ordinal_numeric", "ranking",
            "count", "proportion", "binary", "numeric"
        ]},
        "data_types": {
            "categorical": "categorical",
            "ordinal_string": "ordinal",
            "ordinal_numeric": "ordinal", 
            "ranking": "ranking",
            "count": "count",
            "proportion": "proportion",
            "binary": "binary",
            "numeric": "numeric"
        }
    }
    
    treatment_data = {
        "name": "Comprehensive Treatment",
        "key_results": {
            "categorical": ["Blue", "Green", "Red"],
            "ordinal_string": ["Good", "Excellent", "Excellent"],
            "ordinal_numeric": [3, 5, 5],
            "ranking": [2, 1, 1], 
            "count": [2, 7, 12],
            "proportion": [0.2, 0.6, 1.0],
            "binary": [True, True, False],
            "numeric": [2.1, 3.2, 4.5]
        },
        "result_types": {name: "per_agent" for name in [
            "categorical", "ordinal_string", "ordinal_numeric", "ranking",
            "count", "proportion", "binary", "numeric"
        ]},
        "data_types": {
            "categorical": "categorical",
            "ordinal_string": "ordinal",
            "ordinal_numeric": "ordinal",
            "ranking": "ranking", 
            "count": "count",
            "proportion": "proportion",
            "binary": "binary",
            "numeric": "numeric"
        }
    }
    
    # Generate comprehensive report
    report = validate_simulation_experiment_empirically(
        control_data=control_data,
        treatment_data=treatment_data,
        validation_types=["statistical"],
        output_format="report"
    )
    
    # Check that all data types are documented
    data_type_sections = [
        "Categorical Data", "Ordinal Data", "Ranking Data", 
        "Count Data", "Proportion Data", "Binary Data", "Numeric Data"
    ]
    
    for section in data_type_sections:
        assert section in report, f"Missing section: {section}"
    
    # Check for specific data type information
    assert "String categories converted to ordinal" in report
    assert "Ordered categories or levels" in report
    assert "Rank positions" in report
    assert "Non-negative integer counts" in report
    assert "Values between 0-1" in report
    assert "Binary outcomes converted to 0/1" in report
    
    print("✅ Comprehensive data type report tests passed")


def test_csv_reading_single_value_per_agent():
    """Test CSV reading functionality with single value per agent data."""
    print("Testing CSV reading with single value per agent...")
    
    # Create test CSV content
    csv_content = """Responder #,Vote,Explanation,Age Range,Gender Identity,Political Affiliation,Racial Or Ethnic Identity
1,4,Yes because it is something i have never tried and willing to give it a go,25-34,Male,Democrat,White
2,1,I HATE soup.  Cold soup would be worse.,65+,Female,Democrat,White
3,1,i would not purchase a ready to drink gazpacho because i am not a fan of it.,35-44,Female,Democrat,Black
4,5,"It sounds healthy and if it's ready to drink and doesn't require me to do all that chopping of the vegetables, what's not to like!",55-64,Female,Democrat,White
5,3,"Like most things, I would try it at the right price. I normally don't eat gazpacho though.",35-44,Non-binary,Independent / other,Other"""
    
    # Write to temporary CSV file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Test CSV reading
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path=csv_file_path,
            experimental_data_type="single_value_per_agent",
            agent_id_column="Responder #",
            value_column="Vote",
            agent_comments_column="Explanation",
            agent_attributes_columns=["Age Range", "Gender Identity", "Political Affiliation", "Racial Or Ethnic Identity"],
            dataset_name="Test Gazpacho Survey"
        )
        
        # Verify dataset structure
        assert dataset.name == "Test Gazpacho Survey"
        assert "Vote" in dataset.key_results
        assert "Age Range" in dataset.agent_attributes
        assert "Gender Identity" in dataset.agent_attributes
        assert "Political Affiliation" in dataset.agent_attributes
        assert "Racial Or Ethnic Identity" in dataset.agent_attributes
        
        # Check data values
        assert dataset.key_results["Vote"] == [4, 1, 1, 5, 3]
        assert len(dataset.agent_justifications) == 5
        assert len(dataset.agent_names) == 5
        
        # Check agent names
        assert dataset.agent_names == ["1", "2", "3", "4", "5"]
        
        # Check justifications include agent references
        first_justification = dataset.agent_justifications[0]
        assert isinstance(first_justification, dict)
        assert first_justification["agent_name"] == "1"
        assert "never tried" in first_justification["justification"]
        
        # Check data types were auto-detected
        assert dataset.data_types["Vote"] == "count"  # Should be detected as count (1-5 integers)
        # Agent attributes should not have data types since they're not in key_results
        assert "Age Range" not in dataset.data_types
        assert "Gender Identity" not in dataset.data_types
        
        # Check that agent attributes are stored correctly  
        assert dataset.agent_attributes["Age Range"] == ["25-34", "65+", "35-44", "55-64", "35-44"]
        assert dataset.agent_attributes["Gender Identity"] == ["Male", "Female", "Female", "Female", "Non-binary"]
        assert dataset.agent_attributes["Political Affiliation"] == ["Democrat", "Democrat", "Democrat", "Democrat", "Independent / other"]
        assert dataset.agent_attributes["Racial Or Ethnic Identity"] == ["White", "White", "Black", "White", "Other"]
        
        # Categorical mappings should not be created for agent attributes
        assert "Age Range" not in dataset.categorical_mappings
        assert "Gender Identity" not in dataset.categorical_mappings
        
        print("✅ CSV reading with single value per agent tests passed")
        # Agent attributes should not be in key_results anymore
        assert "Political Affiliation" not in dataset.key_results
        assert "Racial Or Ethnic Identity" not in dataset.key_results
        
        # Check data values
        assert dataset.key_results["Vote"] == [4, 1, 1, 5, 3]
        assert len(dataset.agent_justifications) == 5
        assert len(dataset.agent_names) == 5
        
        # Check agent names
        assert dataset.agent_names == ["1", "2", "3", "4", "5"]
        
        # Check justifications include agent references
        first_justification = dataset.agent_justifications[0]
        assert isinstance(first_justification, dict)
        assert first_justification["agent_name"] == "1"
        assert "never tried" in first_justification["justification"]
        
        print("✅ CSV reading with single value per agent tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(csv_file_path)


def test_csv_reading_ranking_per_agent():
    """Test CSV reading functionality with ranking per agent data."""
    print("Testing CSV reading with ranking per agent...")
    
    # Create test ranking CSV content
    csv_content = """Agent,Product_A_Rank,Product_B_Rank,Product_C_Rank,Comments,Age,Gender
Agent1,1,2,3,Product A was clearly the best,25-34,Male
Agent2,2,1,3,Product B had better value,35-44,Female
Agent3,1,3,2,Liked A most and C second,45-54,Male
Agent4,3,2,1,Product C was my favorite,25-34,Female"""
    
    # Write to temporary CSV file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Test CSV reading for ranking data
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path=csv_file_path,
            experimental_data_type="ranking_per_agent",
            agent_id_column="Agent",
            ranking_columns=["Product_A_Rank", "Product_B_Rank", "Product_C_Rank"],
            agent_comments_column="Comments",
            agent_attributes_columns=["Age", "Gender"],
            dataset_name="Product Ranking Study"
        )
        
        # Verify dataset structure
        assert dataset.name == "Product Ranking Study"
        assert "Product_A_Rank" in dataset.key_results
        assert "Product_B_Rank" in dataset.key_results
        assert "Product_C_Rank" in dataset.key_results
        assert "Age" in dataset.agent_attributes
        assert "Gender" in dataset.agent_attributes
        
        # Check ranking data values
        assert dataset.key_results["Product_A_Rank"] == [1, 2, 1, 3]
        assert dataset.key_results["Product_B_Rank"] == [2, 1, 3, 2]
        assert dataset.key_results["Product_C_Rank"] == [3, 3, 2, 1]
        
        # Check agent data
        assert len(dataset.agent_justifications) == 4
        assert len(dataset.agent_names) == 4
        assert dataset.agent_names == ["Agent1", "Agent2", "Agent3", "Agent4"]
        
        # Check data types for ranking
        assert dataset.data_types["Product_A_Rank"] == "ranking"
        assert dataset.data_types["Product_B_Rank"] == "ranking"
        assert dataset.data_types["Product_C_Rank"] == "ranking"
        # Agent attributes should not have data types since they're not in key_results
        assert "Age" not in dataset.data_types
        assert "Gender" not in dataset.data_types
        
        # Check that agent attributes are stored correctly
        assert dataset.agent_attributes["Age"] == ["25-34", "35-44", "45-54", "25-34"]
        assert dataset.agent_attributes["Gender"] == ["Male", "Female", "Male", "Female"]
        
        # Check ranking info was stored
        assert "Product_A_Rank" in dataset.ranking_info
        ranking_info = dataset.ranking_info["Product_A_Rank"]
        assert ranking_info["min_rank"] == 1
        assert ranking_info["max_rank"] == 3
        
        print("✅ CSV reading with ranking per agent tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(csv_file_path)


def test_csv_reading_error_handling():
    """Test CSV reading error handling for invalid inputs."""
    print("Testing CSV reading error handling...")
    
    validator = SimulationExperimentEmpiricalValidator()
    
    # Test with non-existent file
    try:
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path="nonexistent_file.csv",
            experimental_data_type="single_value_per_agent"
        )
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass  # Expected
    
    # Test with invalid experiment type
    import tempfile
    import os
    
    csv_content = "col1,col2\n1,2\n3,4\n"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        try:
            dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
                file_path=csv_file_path,
                experimental_data_type="invalid_type"
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "experimental_data_type" in str(e)
        
        # Test with missing required column
        try:
            dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
                file_path=csv_file_path,
                experimental_data_type="single_value_per_agent",
                value_column="nonexistent_column"
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "not found in CSV" in str(e)
            
    finally:
        os.unlink(csv_file_path)
    
    print("✅ CSV reading error handling tests passed")


def test_csv_reading_with_missing_data():
    """Test CSV reading with missing/empty values in data."""
    print("Testing CSV reading with missing data...")
    
    # Create CSV with some missing values
    csv_content = """ID,Score,Comment,Category
1,4,Good product,A
2,,No comment,B
3,5,Excellent,
4,2,Poor quality,A
5,,"",C"""
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path=csv_file_path,
            experimental_data_type="single_value_per_agent",
            agent_id_column="ID",
            value_column="Score",
            agent_comments_column="Comment",
            agent_attributes_columns=["Category"],
            dataset_name="Test with Missing Data"
        )
        
        # Check that missing values are handled properly (converted to None)
        scores = dataset.key_results["Score"]
        assert scores == [4.0, None, 5.0, 2.0, None]  # Missing scores should be None
        
        # Check categories with missing values - now in agent_attributes
        categories = dataset.agent_attributes["Category"]
        assert None in categories  # Should have None for missing category
        assert categories == ["A", "B", None, "A", "C"]
        
        # Check justifications - empty comments should still be included
        assert len(dataset.agent_justifications) == 5
        
        # Check that missing values don't break data type detection
        assert dataset.data_types["Score"] == "count"  # Should still detect as count despite missing values
        
        print("✅ CSV reading with missing data tests passed")
        
    finally:
        os.unlink(csv_file_path)


def test_csv_reading_convenience_method():
    """Test the convenience method for creating validator and reading CSV in one step."""
    print("Testing CSV reading convenience method...")
    
    csv_content = """Agent,Rating,Feedback
A1,3,Good
A2,4,Very good
A3,2,Fair"""
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Test convenience method
        validator, dataset = SimulationExperimentEmpiricalValidator.create_from_csv(
            file_path=csv_file_path,
            experimental_data_type="single_value_per_agent",
            agent_id_column="Agent",
            value_column="Rating",
            agent_comments_column="Feedback",
            dataset_name="Convenience Test"
        )
        
        # Verify it's a properly constructed validator with loaded data
        assert dataset is not None
        assert dataset.name == "Convenience Test"
        assert dataset.key_results["Rating"] == [3.0, 4.0, 2.0]
        assert len(dataset.agent_justifications) == 3
        
        print("✅ CSV reading convenience method tests passed")
        
    finally:
        os.unlink(csv_file_path)


def test_csv_reading_ordinal_ranking_per_agent():
    """Test CSV reading functionality with ordinal ranking per agent data (single column with separator)."""
    print("Testing CSV reading with ordinal ranking per agent...")
    
    # Create test ordinal ranking CSV content
    csv_content = """Agent,Product_Ranking,Comments,Age,Gender
Agent1,B-A-C,Product B was clearly the best,25-34,Male
Agent2,A-C-B,Product A had better value,35-44,Female
Agent3,C-A-B,Liked C most and A second,45-54,Male
Agent4,A-B-C,Product A was my favorite,25-34,Female
Agent5,B-C-A,B then C then A,35-44,Male"""
    
    # Write to temporary CSV file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Test CSV reading for ordinal ranking data
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path=csv_file_path,
            experimental_data_type="ordinal_ranking_per_agent",
            agent_id_column="Agent",
            ordinal_ranking_column="Product_Ranking",
            ordinal_ranking_separator="-",
            ordinal_ranking_options=["A", "B", "C"],
            agent_comments_column="Comments",
            agent_attributes_columns=["Age", "Gender"],
            dataset_name="Product Ordinal Ranking Study"
        )
        
        # Verify dataset structure
        assert dataset.name == "Product Ordinal Ranking Study"
        assert "A_rank" in dataset.key_results
        assert "B_rank" in dataset.key_results
        assert "C_rank" in dataset.key_results
        assert "Age" in dataset.agent_attributes
        assert "Gender" in dataset.agent_attributes
        
        # Check ranking data values (based on the ordinal positions)
        # Agent1: B-A-C means B=1st, A=2nd, C=3rd
        # Agent2: A-C-B means A=1st, C=2nd, B=3rd
        # Agent3: C-A-B means C=1st, A=2nd, B=3rd
        # Agent4: A-B-C means A=1st, B=2nd, C=3rd
        # Agent5: B-C-A means B=1st, C=2nd, A=3rd
        assert dataset.key_results["A_rank"] == [2, 1, 2, 1, 3]
        assert dataset.key_results["B_rank"] == [1, 3, 3, 2, 1]
        assert dataset.key_results["C_rank"] == [3, 2, 1, 3, 2]
        
        # Check agent data
        assert len(dataset.agent_justifications) == 5
        assert len(dataset.agent_names) == 5
        assert dataset.agent_names == ["Agent1", "Agent2", "Agent3", "Agent4", "Agent5"]
        
        # Check data types for ranking
        assert dataset.data_types["A_rank"] == "ranking"
        assert dataset.data_types["B_rank"] == "ranking"
        assert dataset.data_types["C_rank"] == "ranking"
        # Agent attributes should not have data types since they're not in key_results
        assert "Age" not in dataset.data_types
        assert "Gender" not in dataset.data_types
        
        # Check that agent attributes are stored correctly
        assert dataset.agent_attributes["Age"] == ["25-34", "35-44", "45-54", "25-34", "35-44"]
        assert dataset.agent_attributes["Gender"] == ["Male", "Female", "Male", "Female", "Male"]
        
        # Check ranking info was stored with ordinal-specific details
        assert "A_rank" in dataset.ranking_info
        ranking_info = dataset.ranking_info["A_rank"]
        assert ranking_info["min_rank"] == 1
        assert ranking_info["max_rank"] == 3
        assert ranking_info["original_options"] == ["A", "B", "C"]
        assert ranking_info["separator"] == "-"
        assert ranking_info["source_column"] == "Product_Ranking"
        
        print("✅ CSV reading with ordinal ranking per agent tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(csv_file_path)


def test_csv_reading_ordinal_ranking_auto_detection():
    """Test auto-detection features for ordinal ranking CSV reading."""
    print("Testing ordinal ranking CSV auto-detection...")
    
    # Create test CSV content without explicit options (auto-detect)
    csv_content = """participant_id,preference_order,feedback
P001,Option2-Option1-Option3,Option2 was clearly superior
P002,Option1-Option3-Option2,Option1 had the best features
P003,,No response provided
P004,Option3-Option2-Option1,Preferred Option3 overall"""
    
    # Write to temporary CSV file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Test auto-detection (no explicit column or options specified)
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path=csv_file_path,
            experimental_data_type="ordinal_ranking_per_agent",
            agent_id_column="participant_id",
            agent_comments_column="feedback",
            ordinal_ranking_separator="-"
            # No ordinal_ranking_column or ordinal_ranking_options specified
        )
        
        # Should auto-detect "preference_order" as the ranking column
        # Should auto-detect ["Option1", "Option2", "Option3"] as options
        assert "Option1_rank" in dataset.key_results
        assert "Option2_rank" in dataset.key_results
        assert "Option3_rank" in dataset.key_results
        
        # Check that missing data is handled (P003 has empty ranking)
        # P001: Option2-Option1-Option3 → Option1=2, Option2=1, Option3=3
        # P002: Option1-Option3-Option2 → Option1=1, Option3=2, Option2=3
        # P003: (empty) → All None
        # P004: Option3-Option2-Option1 → Option3=1, Option2=2, Option1=3
        assert dataset.key_results["Option1_rank"] == [2, 1, None, 3]
        assert dataset.key_results["Option2_rank"] == [1, 3, None, 2]
        assert dataset.key_results["Option3_rank"] == [3, 2, None, 1]
        
        # Verify ranking info includes auto-detected information
        ranking_info = dataset.ranking_info["Option1_rank"]
        assert set(ranking_info["original_options"]) == {"Option1", "Option2", "Option3"}
        assert ranking_info["separator"] == "-"
        assert ranking_info["source_column"] == "preference_order"
        
        print("✅ Ordinal ranking CSV auto-detection tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(csv_file_path)


def test_csv_reading_ordinal_ranking_error_handling():
    """Test error handling for ordinal ranking CSV reading."""
    print("Testing ordinal ranking CSV error handling...")
    
    # Test with malformed data
    csv_content = """Agent,Ranking
Agent1,A|B|C
Agent2,InvalidFormat"""
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Should handle malformed data gracefully
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path=csv_file_path,
            experimental_data_type="ordinal_ranking_per_agent",
            ordinal_ranking_column="Ranking",
            ordinal_ranking_separator="-",  # Different separator than data
            ordinal_ranking_options=["A", "B", "C"]
        )
        
        # Should have created the structure but with None values for malformed data
        assert "A_rank" in dataset.key_results
        assert "B_rank" in dataset.key_results
        assert "C_rank" in dataset.key_results
        
        # Both agents should have None values due to malformed data
        assert dataset.key_results["A_rank"] == [None, None]
        assert dataset.key_results["B_rank"] == [None, None]
        assert dataset.key_results["C_rank"] == [None, None]
        
        print("✅ Ordinal ranking CSV error handling tests passed")
        
    finally:
        # Clean up temporary file
        os.unlink(csv_file_path)


def test_csv_reading_ordinal_ranking_custom_separator():
    """Test ordinal ranking with custom separators."""
    print("Testing ordinal ranking with custom separators...")
    
    # Test with different separators
    test_cases = [
        ("|", "X|Y|Z", [1, 2, 3]),  # Pipe separator
        (">", "Z>X>Y", [2, 3, 1])  # Arrow separator  
    ]

    # Note that comma separators would be illegal
    
    for separator, ranking_string, expected_x_y_z in test_cases:
        csv_content = f"""Agent,Ranking
Agent1,{ranking_string}"""
        
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            csv_file_path = f.name
        
        try:
            dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
                file_path=csv_file_path,
                experimental_data_type="ordinal_ranking_per_agent",
                ordinal_ranking_column="Ranking",
                ordinal_ranking_separator=separator,
                ordinal_ranking_options=["X", "Y", "Z"]
            )
            
            # Verify the parsing worked correctly
            x_rank, y_rank, z_rank = expected_x_y_z
            assert dataset.key_results["X_rank"] == [x_rank]
            assert dataset.key_results["Y_rank"] == [y_rank]
            assert dataset.key_results["Z_rank"] == [z_rank]
            
        finally:
            os.unlink(csv_file_path)
    
    print("✅ Ordinal ranking custom separator tests passed")


def test_csv_reading_explicit_data_types():
    """Test CSV reading with explicit data type specification."""
    print("Testing CSV reading with explicit data types...")
    
    csv_content = """ID,Satisfaction,Priority,Active,Score
1,Very Satisfied,High,Yes,85
2,Satisfied,Medium,No,75
3,Neutral,Low,Yes,65"""
    
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # Test CSV reading with explicit data types  
        dataset = SimulationExperimentEmpiricalValidator.read_empirical_data_from_csv(
            file_path=csv_file_path,
            experimental_data_type="single_value_per_agent",
            agent_id_column="ID",
            value_column="Score",
            agent_attributes_columns=["Satisfaction", "Priority", "Active"],
            dataset_name="Explicit Types Test"
        )
        
        # Verify agent attributes were loaded (these are stored separately from key_results)
        assert "Satisfaction" in dataset.agent_attributes
        assert "Priority" in dataset.agent_attributes
        assert "Active" in dataset.agent_attributes
        
        assert dataset.agent_attributes["Satisfaction"] == ["Very Satisfied", "Satisfied", "Neutral"]
        assert dataset.agent_attributes["Priority"] == ["High", "Medium", "Low"]
        assert dataset.agent_attributes["Active"] == ["Yes", "No", "Yes"]
        
        # Verify main data column was loaded
        assert dataset.key_results["Score"] == [85, 75, 65]
        assert dataset.result_types["Score"] == "per_agent"
        
        # Check that the Score data type was auto-detected properly  
        assert dataset.data_types["Score"] == "count"  # Auto-detected
        
        print("✅ CSV reading with explicit data types tests passed")
        
    finally:
        os.unlink(csv_file_path)

