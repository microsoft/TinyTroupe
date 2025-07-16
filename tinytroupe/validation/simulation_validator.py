"""
Simulation experiment empirical validation mechanisms for TinyTroupe.

This module provides tools to validate simulation experiment results against empirical control data,
supporting both statistical hypothesis testing and semantic validation approaches.
This is distinct from LLM-based evaluations, focusing on data-driven validation
against known empirical benchmarks.
"""

from typing import Dict, List, Optional, Union, Any
import json
from datetime import datetime
from pydantic import BaseModel, Field

from tinytroupe.experimentation.statistical_tests import StatisticalTester
from tinytroupe.utils.semantics import compute_semantic_proximity

# TODO Work-in-Progress below

class SimulationExperimentDataset(BaseModel):
    """
    Represents a dataset from a simulation experiment or empirical study.
    
    This contains data that can be used for validation, including quantitative metrics 
    and qualitative agent justifications from simulation experiments or empirical studies.
    
    Attributes:
        name: Optional name for the dataset
        description: Optional description of the dataset
        key_results: Map from result names to their values (numbers, proportions, booleans, etc.)
        result_types: Map indicating whether each result is "aggregate" or "per_agent"
        agent_names: Optional list of agent names (can be referenced by index in results)
        agent_justifications: List of justifications (with optional agent references)
        justification_summary: Optional summary of all agent justifications
    """
    name: Optional[str] = None
    description: Optional[str] = None
    key_results: Dict[str, Union[float, int, bool, List[Union[float, int, bool, None]], None]] = Field(default_factory=dict)
    result_types: Dict[str, str] = Field(default_factory=dict, description="Map from result name to 'aggregate' or 'per_agent'")
    agent_names: Optional[List[Optional[str]]] = Field(None, description="Optional list of agent names for reference (can contain None for unnamed agents)")
    agent_justifications: List[Union[str, Dict[str, Union[str, int]]]] = Field(
        default_factory=list, 
        description="List of justifications as strings or dicts with optional 'agent_name'/'agent_index' and 'justification'"
    )
    justification_summary: Optional[str] = None

    class Config:
        """Pydantic configuration."""
        extra = "forbid"  # Prevent accidental extra fields
        validate_assignment = True  # Validate on assignment after creation
    
    def get_agent_name(self, index: int) -> Optional[str]:
        """Get agent name by index, if available."""
        if self.agent_names and 0 <= index < len(self.agent_names):
            agent_name = self.agent_names[index]
            return agent_name if agent_name is not None else None
        return None
    
    def get_agent_data(self, metric_name: str, agent_index: int) -> Optional[Union[float, int, bool]]:
        """Get a specific agent's data for a given metric. Returns None for missing data."""
        if metric_name not in self.key_results:
            return None
            
        metric_data = self.key_results[metric_name]
        
        # Check if it's per-agent data
        if self.result_types.get(metric_name) == "per_agent" and isinstance(metric_data, list):
            if 0 <= agent_index < len(metric_data):
                return metric_data[agent_index]  # This can be None for missing data
        
        return None
    
    def get_all_agent_data(self, metric_name: str) -> Dict[str, Union[float, int, bool]]:
        """Get all agents' data for a given metric as a dictionary mapping agent names/indices to values."""
        if metric_name not in self.key_results:
            return {}
            
        metric_data = self.key_results[metric_name]
        result = {}
        
        # For per-agent data, create mapping
        if self.result_types.get(metric_name) == "per_agent" and isinstance(metric_data, list):
            for i, value in enumerate(metric_data):
                agent_name = self.get_agent_name(i) or f"Agent_{i}"
                # Only include non-None values in the result
                if value is not None:
                    result[agent_name] = value
        
        # For aggregate data, return single value  
        elif self.result_types.get(metric_name) == "aggregate":
            result["aggregate"] = metric_data
            
        return result
    
    def get_valid_agent_data(self, metric_name: str) -> List[Union[float, int, bool]]:
        """Get only valid (non-None) values for a per-agent metric."""
        if metric_name not in self.key_results:
            return []
            
        metric_data = self.key_results[metric_name]
        
        if self.result_types.get(metric_name) == "per_agent" and isinstance(metric_data, list):
            return [value for value in metric_data if value is not None]
        
        return []
    
    def validate_data_consistency(self) -> List[str]:
        """Validate that per-agent data is consistent across metrics and with agent names."""
        errors = []
        warnings = []
        
        # Check per-agent metrics have consistent lengths
        per_agent_lengths = []
        per_agent_metrics = []
        
        for metric_name, result_type in self.result_types.items():
            if result_type == "per_agent" and metric_name in self.key_results:
                metric_data = self.key_results[metric_name]
                if isinstance(metric_data, list):
                    per_agent_lengths.append(len(metric_data))
                    per_agent_metrics.append(metric_name)
                else:
                    errors.append(f"Metric '{metric_name}' marked as per_agent but is not a list")
        
        # Check all per-agent metrics have same length
        if per_agent_lengths and len(set(per_agent_lengths)) > 1:
            errors.append(f"Per-agent metrics have inconsistent lengths: {dict(zip(per_agent_metrics, per_agent_lengths))}")
        
        # Check agent_names length matches per-agent data length
        if self.agent_names and per_agent_lengths:
            agent_count = len(self.agent_names)
            data_length = per_agent_lengths[0] if per_agent_lengths else 0
            if agent_count != data_length:
                errors.append(f"agent_names length ({agent_count}) doesn't match per-agent data length ({data_length})")
        
        # Check for None values in agent_names and provide warnings
        if self.agent_names:
            none_indices = [i for i, name in enumerate(self.agent_names) if name is None]
            if none_indices:
                warnings.append(f"agent_names contains None values at indices: {none_indices}")
        
        # Check for None values in per-agent data and provide info
        for metric_name in per_agent_metrics:
            if metric_name in self.key_results:
                metric_data = self.key_results[metric_name]
                none_indices = [i for i, value in enumerate(metric_data) if value is None]
                if none_indices:
                    warnings.append(f"Metric '{metric_name}' has missing data (None) at indices: {none_indices}")
        
        # Return errors and warnings combined
        return errors + [f"WARNING: {warning}" for warning in warnings]
    
    def get_justification_text(self, justification_item: Union[str, Dict[str, Union[str, int]]]) -> str:
        """Extract justification text from various formats."""
        if isinstance(justification_item, str):
            return justification_item
        elif isinstance(justification_item, dict):
            return justification_item.get("justification", "")
        return ""
    
    def get_justification_agent_reference(self, justification_item: Union[str, Dict[str, Union[str, int]]]) -> Optional[str]:
        """Get agent reference from justification, returning name if available."""
        if isinstance(justification_item, dict):
            # Direct agent name
            if "agent_name" in justification_item:
                return justification_item["agent_name"]
            # Agent index reference
            elif "agent_index" in justification_item:
                return self.get_agent_name(justification_item["agent_index"])
        return None


class SimulationExperimentEmpiricalValidationResult(BaseModel):
    """
    Contains the results of a simulation experiment validation against empirical data.
    
    This represents the outcome of validating simulation experiment data
    against empirical benchmarks, using statistical and semantic methods.
    
    Attributes:
        validation_type: Type of validation performed
        control_name: Name of the control/empirical dataset
        treatment_name: Name of the treatment/simulation experiment dataset
        statistical_results: Results from statistical tests (if performed)
        semantic_results: Results from semantic proximity analysis (if performed)
        overall_score: Overall validation score (0.0 to 1.0)
        summary: Summary of validation findings
        timestamp: When the validation was performed
    """
    validation_type: str
    control_name: str
    treatment_name: str
    statistical_results: Optional[Dict[str, Any]] = None
    semantic_results: Optional[Dict[str, Any]] = None
    overall_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Overall validation score between 0.0 and 1.0")
    summary: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        """Pydantic configuration."""
        extra = "forbid"
        validate_assignment = True


class SimulationExperimentEmpiricalValidator:
    """
    A validator for comparing simulation experiment data against empirical control data.
    
    This validator performs data-driven validation using statistical hypothesis testing
    and semantic proximity analysis of agent justifications. It is designed to validate
    simulation experiment results against known empirical benchmarks, distinct from LLM-based evaluations.
    """

    def __init__(self):
        """Initialize the simulation experiment empirical validator."""
        pass

    def validate(self, 
                 control: SimulationExperimentDataset, 
                 treatment: SimulationExperimentDataset,
                 validation_types: List[str] = ["statistical", "semantic"],
                 significance_level: float = 0.05,
                 output_format: str = "values") -> Union[SimulationExperimentEmpiricalValidationResult, str]:
        """
        Validate a simulation experiment dataset against an empirical control dataset.
        
        Args:
            control: The control/empirical reference dataset
            treatment: The treatment/simulation experiment dataset to validate
            validation_types: List of validation types to perform ("statistical", "semantic")
            significance_level: Significance level for statistical tests
            output_format: "values" for SimulationExperimentEmpiricalValidationResult object, "report" for markdown report
            
        Returns:
            SimulationExperimentEmpiricalValidationResult object or markdown report string
        """
        result = SimulationExperimentEmpiricalValidationResult(
            validation_type=", ".join(validation_types),
            control_name=control.name or "Control",
            treatment_name=treatment.name or "Treatment"
        )

        # Perform statistical validation
        if "statistical" in validation_types:
            result.statistical_results = self._perform_statistical_validation(
                control, treatment, significance_level
            )

        # Perform semantic validation
        if "semantic" in validation_types:
            result.semantic_results = self._perform_semantic_validation(
                control, treatment
            )

        # Calculate overall score and summary
        result.overall_score = self._calculate_overall_score(result)
        result.summary = self._generate_summary(result)

        if output_format == "report":
            return self._generate_markdown_report(result)
        else:
            return result

    def _perform_statistical_validation(self, 
                                      control: SimulationExperimentDataset, 
                                      treatment: SimulationExperimentDataset,
                                      significance_level: float) -> Dict[str, Any]:
        """Perform statistical hypothesis testing on simulation experiment key results."""
        if not control.key_results or not treatment.key_results:
            return {"error": "No key results available for statistical testing"}

        try:
            # Prepare data for StatisticalTester
            control_data = {"control": {}}
            treatment_data = {"treatment": {}}

            # Convert single values to lists if needed and find common metrics
            common_metrics = set(control.key_results.keys()) & set(treatment.key_results.keys())
            
            for metric in common_metrics:
                control_value = control.key_results[metric]
                treatment_value = treatment.key_results[metric]
                
                # Convert single values to lists and filter out None values
                if not isinstance(control_value, list):
                    control_value = [control_value] if control_value is not None else []
                else:
                    control_value = [v for v in control_value if v is not None]
                    
                if not isinstance(treatment_value, list):
                    treatment_value = [treatment_value] if treatment_value is not None else []
                else:
                    treatment_value = [v for v in treatment_value if v is not None]
                
                # Only include metrics that have valid data points
                if len(control_value) > 0 and len(treatment_value) > 0:
                    control_data["control"][metric] = control_value
                    treatment_data["treatment"][metric] = treatment_value

            if not common_metrics:
                return {"error": "No common metrics found between control and treatment"}

            # Run statistical tests
            tester = StatisticalTester(control_data, treatment_data)
            test_results = tester.run_test(
                test_type="welch_t_test",
                alpha=significance_level
            )

            return {
                "common_metrics": list(common_metrics),
                "test_results": test_results,
                "significance_level": significance_level
            }

        except Exception as e:
            return {"error": f"Statistical testing failed: {str(e)}"}

    def _perform_semantic_validation(self, 
                                   control: SimulationExperimentDataset, 
                                   treatment: SimulationExperimentDataset) -> Dict[str, Any]:
        """Perform semantic proximity analysis on simulation experiment agent justifications."""
        results = {
            "individual_comparisons": [],
            "summary_comparison": None,
            "average_proximity": None
        }

        # Compare individual justifications if available
        if control.agent_justifications and treatment.agent_justifications:
            proximities = []
            
            for i, control_just in enumerate(control.agent_justifications):
                for j, treatment_just in enumerate(treatment.agent_justifications):
                    control_text = control.get_justification_text(control_just)
                    treatment_text = treatment.get_justification_text(treatment_just)
                    
                    if control_text and treatment_text:
                        proximity_result = compute_semantic_proximity(
                            control_text, 
                            treatment_text,
                            context="Comparing agent justifications from simulation experiments"
                        )
                        
                        # Get agent references (names or indices)
                        control_agent_ref = control.get_justification_agent_reference(control_just) or f"Agent_{i}"
                        treatment_agent_ref = treatment.get_justification_agent_reference(treatment_just) or f"Agent_{j}"
                        
                        comparison = {
                            "control_agent": control_agent_ref,
                            "treatment_agent": treatment_agent_ref,
                            "proximity_score": proximity_result["proximity_score"],
                            "justification": proximity_result["justification"]
                        }
                        
                        results["individual_comparisons"].append(comparison)
                        proximities.append(proximity_result["proximity_score"])
            
            if proximities:
                results["average_proximity"] = sum(proximities) / len(proximities)

        # Compare summary justifications if available
        if control.justification_summary and treatment.justification_summary:
            summary_proximity = compute_semantic_proximity(
                control.justification_summary,
                treatment.justification_summary,
                context="Comparing summary justifications from simulation experiments"
            )
            results["summary_comparison"] = summary_proximity

        return results

    def _calculate_overall_score(self, result: SimulationExperimentEmpiricalValidationResult) -> float:
        """Calculate an overall simulation experiment empirical validation score based on statistical and semantic results."""
        scores = []
        
        # Statistical component based on effect sizes
        if result.statistical_results and "test_results" in result.statistical_results:
            test_results = result.statistical_results["test_results"]
            effect_sizes = []
            
            for treatment_name, treatment_results in test_results.items():
                for metric, metric_result in treatment_results.items():
                    # Extract effect size based on test type
                    effect_size = self._extract_effect_size(metric_result)
                    if effect_size is not None:
                        effect_sizes.append(effect_size)
            
            if effect_sizes:
                # Convert effect sizes to similarity scores (closer to 0 = more similar)
                # Use inverse transformation: similarity = 1 / (1 + |effect_size|)
                similarity_scores = [1.0 / (1.0 + abs(es)) for es in effect_sizes]
                statistical_score = sum(similarity_scores) / len(similarity_scores)
                scores.append(statistical_score)

        # Semantic component
        if result.semantic_results:
            semantic_scores = []
            
            # Average proximity from individual comparisons
            if result.semantic_results.get("average_proximity") is not None:
                semantic_scores.append(result.semantic_results["average_proximity"])
            
            # Summary proximity
            if result.semantic_results.get("summary_comparison"):
                semantic_scores.append(result.semantic_results["summary_comparison"]["proximity_score"])
            
            if semantic_scores:
                scores.append(sum(semantic_scores) / len(semantic_scores))

        return sum(scores) / len(scores) if scores else 0.0

    def _generate_summary(self, result: SimulationExperimentEmpiricalValidationResult) -> str:
        """Generate a text summary of the simulation experiment empirical validation results."""
        summary_parts = []
        
        if result.statistical_results:
            if "error" in result.statistical_results:
                summary_parts.append(f"Statistical validation: {result.statistical_results['error']}")
            else:
                test_results = result.statistical_results.get("test_results", {})
                effect_sizes = []
                significant_tests = 0
                total_tests = 0
                
                for treatment_results in test_results.values():
                    for metric_result in treatment_results.values():
                        total_tests += 1
                        if metric_result.get("significant", False):
                            significant_tests += 1
                        
                        # Collect effect sizes
                        effect_size = self._extract_effect_size(metric_result)
                        if effect_size is not None:
                            effect_sizes.append(abs(effect_size))
                
                if effect_sizes:
                    avg_effect_size = sum(effect_sizes) / len(effect_sizes)
                    summary_parts.append(
                        f"Statistical validation: {significant_tests}/{total_tests} tests significant, "
                        f"average effect size: {avg_effect_size:.3f}"
                    )
                else:
                    summary_parts.append(
                        f"Statistical validation: {significant_tests}/{total_tests} tests showed significant differences"
                    )

        if result.semantic_results:
            avg_proximity = result.semantic_results.get("average_proximity")
            if avg_proximity is not None:
                summary_parts.append(
                    f"Semantic validation: Average proximity score of {avg_proximity:.3f}"
                )
            
            summary_comparison = result.semantic_results.get("summary_comparison")
            if summary_comparison:
                summary_parts.append(
                    f"Summary proximity: {summary_comparison['proximity_score']:.3f}"
                )

        if result.overall_score is not None:
            summary_parts.append(f"Overall validation score: {result.overall_score:.3f}")

        return "; ".join(summary_parts) if summary_parts else "No validation results available"

    def _generate_markdown_report(self, result: SimulationExperimentEmpiricalValidationResult) -> str:
        """Generate a comprehensive markdown report for simulation experiment empirical validation."""
        overall_score_str = f"{result.overall_score:.3f}" if result.overall_score is not None else "N/A"
        
        report = f"""# Simulation Experiment Empirical Validation Report

**Validation Type:** {result.validation_type}  
**Control/Empirical:** {result.control_name}  
**Treatment/Simulation:** {result.treatment_name}  
**Timestamp:** {result.timestamp}  
**Overall Score:** {overall_score_str}

## Summary

{result.summary}

"""

        # Statistical Results Section
        if result.statistical_results:
            report += "## Statistical Validation\n\n"
            
            if "error" in result.statistical_results:
                report += f"**Error:** {result.statistical_results['error']}\n\n"
            else:
                stats = result.statistical_results
                report += f"**Common Metrics:** {', '.join(stats.get('common_metrics', []))}\n\n"
                report += f"**Significance Level:** {stats.get('significance_level', 'N/A')}\n\n"
                
                test_results = stats.get("test_results", {})
                if test_results:
                    report += "### Test Results\n\n"
                    
                    for treatment_name, treatment_results in test_results.items():
                        report += f"#### {treatment_name}\n\n"
                        
                        for metric, metric_result in treatment_results.items():
                            report += f"**{metric}:**\n\n"
                            
                            significant = metric_result.get("significant", False)
                            p_value = metric_result.get("p_value", "N/A")
                            test_type = metric_result.get("test_type", "N/A")
                            effect_size = self._extract_effect_size(metric_result)
                            
                            # Get the appropriate statistic based on test type
                            statistic = "N/A"
                            if "t_statistic" in metric_result:
                                statistic = metric_result["t_statistic"]
                            elif "u_statistic" in metric_result:
                                statistic = metric_result["u_statistic"]
                            elif "f_statistic" in metric_result:
                                statistic = metric_result["f_statistic"]
                            elif "chi2_statistic" in metric_result:
                                statistic = metric_result["chi2_statistic"]
                            
                            status = "✅ Significant" if significant else "❌ Not Significant"
                            
                            report += f"- **{test_type}:** {status}\n"
                            report += f"  - p-value: {p_value}\n"
                            report += f"  - statistic: {statistic}\n"
                            if effect_size is not None:
                                effect_interpretation = self._interpret_effect_size(abs(effect_size))
                                report += f"  - effect size: {effect_size:.3f} ({effect_interpretation})\n"
                            
                            report += "\n"

        # Semantic Results Section
        if result.semantic_results:
            report += "## Semantic Validation\n\n"
            
            semantic = result.semantic_results
            
            # Individual comparisons
            individual_comps = semantic.get("individual_comparisons", [])
            if individual_comps:
                report += "### Individual Agent Comparisons\n\n"
                
                for comp in individual_comps:
                    score = comp["proximity_score"]
                    control_agent = comp["control_agent"]
                    treatment_agent = comp["treatment_agent"]
                    justification = comp["justification"]
                    
                    report += f"**{control_agent} vs {treatment_agent}:** {score:.3f}\n\n"
                    report += f"{justification}\n\n"
                
                avg_proximity = semantic.get("average_proximity")
                if avg_proximity:
                    report += f"**Average Proximity Score:** {avg_proximity:.3f}\n\n"
            
            # Summary comparison
            summary_comp = semantic.get("summary_comparison")
            if summary_comp:
                report += "### Summary Comparison\n\n"
                report += f"**Proximity Score:** {summary_comp['proximity_score']:.3f}\n\n"
                report += f"**Justification:** {summary_comp['justification']}\n\n"

        return report

    def _extract_effect_size(self, metric_result: Dict[str, Any]) -> Optional[float]:
        """Extract effect size from statistical test result, regardless of test type."""
        # Cohen's d for t-tests (most common)
        if "effect_size" in metric_result:
            return metric_result["effect_size"]
        
        # For tests that don't provide Cohen's d, calculate standardized effect size
        test_type = metric_result.get("test_type", "").lower()
        
        if "t-test" in test_type:
            # For t-tests, effect_size should be Cohen's d
            return metric_result.get("effect_size", 0.0)
        
        elif "mann-whitney" in test_type:
            # For Mann-Whitney, use Common Language Effect Size (CLES)
            # Convert CLES to Cohen's d equivalent: d ≈ 2 * Φ^(-1)(CLES)
            cles = metric_result.get("effect_size", 0.5)
            # Simple approximation: convert CLES to d-like measure
            # CLES of 0.5 = no effect, CLES of 0.71 ≈ small effect (d=0.2)
            return 2 * (cles - 0.5)
        
        elif "anova" in test_type:
            # For ANOVA, use eta-squared and convert to Cohen's d equivalent
            eta_squared = metric_result.get("effect_size", 0.0)
            # Convert eta-squared to Cohen's d: d = 2 * sqrt(eta^2 / (1 - eta^2))
            if eta_squared > 0 and eta_squared < 1:
                return 2 * (eta_squared / (1 - eta_squared)) ** 0.5
            return 0.0
        
        elif "chi-square" in test_type:
            # For Chi-square, use Cramer's V and convert to Cohen's d equivalent
            cramers_v = metric_result.get("effect_size", 0.0)
            # Rough conversion: d ≈ 2 * Cramer's V
            return 2 * cramers_v
        
        # Fallback: try to calculate from means and standard deviations
        if all(k in metric_result for k in ["control_mean", "treatment_mean", "control_std", "treatment_std"]):
            control_mean = metric_result["control_mean"]
            treatment_mean = metric_result["treatment_mean"]
            control_std = metric_result["control_std"]
            treatment_std = metric_result["treatment_std"]
            
            # Calculate pooled standard deviation
            pooled_std = ((control_std ** 2 + treatment_std ** 2) / 2) ** 0.5
            if pooled_std > 0:
                return abs(treatment_mean - control_mean) / pooled_std
        
        # If all else fails, return 0 (no effect)
        return 0.0

    def _interpret_effect_size(self, effect_size: float) -> str:
        """Provide interpretation of effect size magnitude (Cohen's conventions)."""
        if effect_size < 0.2:
            return "negligible"
        elif effect_size < 0.5:
            return "small"
        elif effect_size < 0.8:
            return "medium"
        else:
            return "large"


def validate_simulation_experiment_empirically(control_data: Dict[str, Any],
                                              treatment_data: Dict[str, Any],
                                              validation_types: List[str] = ["statistical", "semantic"],
                                              significance_level: float = 0.05,
                                              output_format: str = "values") -> Union[SimulationExperimentEmpiricalValidationResult, str]:
    """
    Convenience function to validate simulation experiment data against empirical control data.
    
    This performs data-driven validation using statistical and semantic methods,
    distinct from LLM-based evaluations.
    
    Args:
        control_data: Dictionary containing control/empirical data
        treatment_data: Dictionary containing treatment/simulation experiment data
        validation_types: List of validation types to perform
        significance_level: Significance level for statistical tests
        output_format: "values" for SimulationExperimentEmpiricalValidationResult object, "report" for markdown report
        
    Returns:
        SimulationExperimentEmpiricalValidationResult object or markdown report string
    """
    # Use Pydantic's built-in parsing instead of from_dict
    control_dataset = SimulationExperimentDataset.parse_obj(control_data)
    treatment_dataset = SimulationExperimentDataset.parse_obj(treatment_data)
    
    validator = SimulationExperimentEmpiricalValidator()
    return validator.validate(
        control_dataset,
        treatment_dataset,
        validation_types=validation_types,
        significance_level=significance_level,
        output_format=output_format
    )
