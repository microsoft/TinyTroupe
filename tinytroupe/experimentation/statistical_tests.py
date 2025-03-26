import numpy as np
import scipy.stats as stats
from typing import Dict, List, Union, Callable, Any, Optional

from tinytroupe.experimentation import logger


class StatisticalTester:
    """
    A class to perform statistical tests on experiment results. To do so, a control is defined, and then one or 
    more treatments are compared to the control. The class supports various statistical tests, including t-tests,
    Mann-Whitney U tests, and ANOVA. The user can specify the type of test to run, the significance level, and
    the specific metrics to analyze. The results of the tests are returned in a structured format.
    """

    def __init__(self, control_experiment_data: Dict[str, list], 
                 treatments_experiment_data: Dict[str, Dict[str, list]],
                 results_key:str = None):
        """
        Initialize with experiment results.
        
        Args:
            control_experiment_data (dict): Dictionary containing control experiment results with keys 
                as metric names and values as lists of values.
                e.g.,{"control_exp": {"metric1": [0.1, 0.2], "metric2": [0.3, 0.4], ...}}
           treatments_experiment_data (dict): Dictionary containing experiment results with keys 
                as experiment IDs and values as dicts of metric names to lists of values.
                e.g., {"exp1": {"metric1": [0.1, 0.2], "metric2": [0.3, 0.4]}, 
                       "exp2": {"metric1": [0.5, 0.6], "metric2": [0.7, 0.8]}, ...}
        """
        
        # if results_key is provided, use it to extract the relevant data from the control and treatment data
        # e.g., {"exp1": {"results": {"metric1": [0.1, 0.2], "metric2": [0.3, 0.4]}}
        if results_key:
            control_experiment_data = {k: v[results_key] for k, v in control_experiment_data.items()}
            treatments_experiment_data = {k: v[results_key] for k, v in treatments_experiment_data.items()}
            
        self.control_experiment_data = control_experiment_data
        self.treatments_experiment_data = treatments_experiment_data
        
        # Validate input data
        self._validate_input_data()
    
    def _validate_input_data(self):
        """Validate the input data formats and structure."""
        # Check that control and treatments are dictionaries
        if not isinstance(self.control_experiment_data, dict):
            raise TypeError("Control experiment data must be a dictionary")
        if not isinstance(self.treatments_experiment_data, dict):
            raise TypeError("Treatments experiment data must be a dictionary")
        
        # Check that control has at least one experiment
        if not self.control_experiment_data:
            raise ValueError("Control experiment data cannot be empty")

        # Check only one control
        if len(self.control_experiment_data) > 1:
            raise ValueError("Only one control experiment is allowed")
            
        # Validate control experiment structure
        for control_id, control_metrics in self.control_experiment_data.items():
            if not isinstance(control_metrics, dict):
                raise TypeError(f"Metrics for control experiment '{control_id}' must be a dictionary")
            
            # Check that the metrics dictionary is not empty
            if not control_metrics:
                raise ValueError(f"Control experiment '{control_id}' has no metrics")
                
            # Validate that metric values are lists
            for metric, values in control_metrics.items():
                if not isinstance(values, list):
                    raise TypeError(f"Values for metric '{metric}' in control experiment '{control_id}' must be a list")
        
        # Check treatments have at least one experiment
        if not self.treatments_experiment_data:
            raise ValueError("Treatments experiment data cannot be empty")
        
        # Validate treatment experiment structure
        for treatment_id, treatment_data in self.treatments_experiment_data.items():
            if not isinstance(treatment_data, dict):
                raise TypeError(f"Data for treatment '{treatment_id}' must be a dictionary")
                
            # Check that the metrics dictionary is not empty
            if not treatment_data:
                raise ValueError(f"Treatment '{treatment_id}' has no metrics")
            
            # Get all control metrics for overlap checking
            all_control_metrics = set()
            for control_metrics in self.control_experiment_data.values():
                all_control_metrics.update(control_metrics.keys())
                
            # Check if there's any overlap between control and treatment metrics
            common_metrics = all_control_metrics.intersection(set(treatment_data.keys()))
            if not common_metrics:
                logger.warning(f"Treatment '{treatment_id}' has no metrics in common with any control experiment")
            
            # Check that treatment metrics are lists
            for metric, values in treatment_data.items():
                if not isinstance(values, list):
                    raise TypeError(f"Values for metric '{metric}' in treatment '{treatment_id}' must be a list")
    
    def run_test(self, 
                test_type: str="welch_t_test", 
                alpha: float = 0.05, 
                **kwargs) -> Dict[str, Dict[str, Any]]:
        """
        Run the specified statistical test on the control and treatments data.

        Args:
            test_type (str): Type of statistical test to run. 
                Options: 't_test', 'welch_t_test', 'mann_whitney', 'anova', 'chi_square'
            alpha (float): Significance level, defaults to 0.05
            **kwargs: Additional arguments for specific test types.

        Returns:
            dict: Dictionary containing the results of the statistical tests for each treatment (vs the one control).
                Each key is the treatment ID and each value is a dictionary with test results.
        """
        supported_tests = {
            't_test': self._run_t_test,
            'welch_t_test': self._run_welch_t_test,
            'mann_whitney': self._run_mann_whitney,
            'anova': self._run_anova,
            'chi_square': self._run_chi_square
        }
        
        if test_type not in supported_tests:
            raise ValueError(f"Unsupported test type: {test_type}. Supported types: {list(supported_tests.keys())}")
            
        results = {}
        for control_id, control_data in self.control_experiment_data.items():
            # get all metrics from control data
            metrics = set()
            metrics.update(control_data.keys())
            for treatment_id, treatment_data in self.treatments_experiment_data.items():
                results[treatment_id] = {}
                
                for metric in metrics:
                    # Skip metrics not in treatment data
                    if metric not in treatment_data:
                        logger.warning(f"Metric '{metric}' not found in treatment '{treatment_id}'")
                        continue
                    
                    control_values = control_data[metric]
                    treatment_values = treatment_data[metric]
                    
                    # Skip if either control or treatment has no values
                    if len(control_values) == 0 or len(treatment_values) == 0:
                        logger.warning(f"Skipping metric '{metric}' for treatment '{treatment_id}' due to empty values")
                        continue
                    
                    # Run the selected test and convert to JSON serializable types
                    test_result = supported_tests[test_type](control_values, treatment_values, alpha, **kwargs)
                    results[treatment_id][metric] = convert_to_serializable(test_result)
        
        return results
    
    def _run_t_test(self, control_values: list, treatment_values: list, alpha: float, **kwargs) -> Dict[str, Any]:
        """Run Student's t-test (equal variance assumed)."""
        # Convert to numpy arrays for calculations
        control = np.array(control_values, dtype=float)
        treatment = np.array(treatment_values, dtype=float)
        
        # Calculate basic statistics
        control_mean = np.mean(control)
        treatment_mean = np.mean(treatment)
        mean_diff = treatment_mean - control_mean
        
        # Run the t-test
        t_stat, p_value = stats.ttest_ind(control, treatment, equal_var=True)
        
        # Calculate confidence interval
        control_std = np.std(control, ddof=1)
        treatment_std = np.std(treatment, ddof=1)
        pooled_std = np.sqrt(((len(control) - 1) * control_std**2 + 
                              (len(treatment) - 1) * treatment_std**2) / 
                            (len(control) + len(treatment) - 2))
        
        se = pooled_std * np.sqrt(1/len(control) + 1/len(treatment))
        critical_value = stats.t.ppf(1 - alpha/2, len(control) + len(treatment) - 2)
        margin_error = critical_value * se
        ci_lower = mean_diff - margin_error
        ci_upper = mean_diff + margin_error
        
        # Determine if the result is significant
        significant = p_value < alpha
        
        return {
            'test_type': 'Student t-test (equal variance)',
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'mean_difference': mean_diff,
            'percent_change': (mean_diff / control_mean * 100) if control_mean != 0 else float('inf'),
            't_statistic': t_stat,
            'p_value': p_value,
            'confidence_interval': (ci_lower, ci_upper),
            'confidence_level': 1 - alpha,
            'significant': significant,
            'control_sample_size': len(control),
            'treatment_sample_size': len(treatment),
            'effect_size': cohen_d(control, treatment)
        }
    
    def _run_welch_t_test(self, control_values: list, treatment_values: list, alpha: float, **kwargs) -> Dict[str, Any]:
        """Run Welch's t-test (unequal variance)."""
        # Convert to numpy arrays for calculations
        control = np.array(control_values, dtype=float)
        treatment = np.array(treatment_values, dtype=float)
        
        # Calculate basic statistics
        control_mean = np.mean(control)
        treatment_mean = np.mean(treatment)
        mean_diff = treatment_mean - control_mean
        
        # Run Welch's t-test
        t_stat, p_value = stats.ttest_ind(control, treatment, equal_var=False)
        
        # Calculate confidence interval (for Welch's t-test)
        control_var = np.var(control, ddof=1)
        treatment_var = np.var(treatment, ddof=1)
        
        # Calculate effective degrees of freedom (Welch-Satterthwaite equation)
        v_num = (control_var/len(control) + treatment_var/len(treatment))**2
        v_denom = (control_var/len(control))**2/(len(control)-1) + (treatment_var/len(treatment))**2/(len(treatment)-1)
        df = v_num / v_denom if v_denom > 0 else float('inf')
        
        se = np.sqrt(control_var/len(control) + treatment_var/len(treatment))
        critical_value = stats.t.ppf(1 - alpha/2, df)
        margin_error = critical_value * se
        ci_lower = mean_diff - margin_error
        ci_upper = mean_diff + margin_error
        
        # Determine if the result is significant
        significant = p_value < alpha
        
        return {
            'test_type': 'Welch t-test (unequal variance)',
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'mean_difference': mean_diff,
            'percent_change': (mean_diff / control_mean * 100) if control_mean != 0 else float('inf'),
            't_statistic': t_stat,
            'p_value': p_value,
            'confidence_interval': (ci_lower, ci_upper),
            'confidence_level': 1 - alpha,
            'significant': significant,
            'degrees_of_freedom': df,
            'control_sample_size': len(control),
            'treatment_sample_size': len(treatment),
            'effect_size': cohen_d(control, treatment)
        }
    
    def _run_mann_whitney(self, control_values: list, treatment_values: list, alpha: float, **kwargs) -> Dict[str, Any]:
        """Run Mann-Whitney U test (non-parametric test)."""
        # Convert to numpy arrays
        control = np.array(control_values, dtype=float)
        treatment = np.array(treatment_values, dtype=float)
        
        # Calculate basic statistics
        control_median = np.median(control)
        treatment_median = np.median(treatment)
        median_diff = treatment_median - control_median
        
        # Run the Mann-Whitney U test
        u_stat, p_value = stats.mannwhitneyu(control, treatment, alternative='two-sided')
        
        # Calculate common language effect size
        # (probability that a randomly selected value from treatment is greater than control)
        count = 0
        for tc in treatment:
            for cc in control:
                if tc > cc:
                    count += 1
        cles = count / (len(treatment) * len(control))
        
        # Calculate approximate confidence interval using bootstrap
        try:
            from scipy.stats import bootstrap
            
            def median_diff_func(x, y):
                return np.median(x) - np.median(y)
            
            res = bootstrap((control, treatment), median_diff_func, 
                            confidence_level=1-alpha, 
                            n_resamples=1000,
                            random_state=42)
            ci_lower, ci_upper = res.confidence_interval
        except ImportError:
            # If bootstrap is not available, return None for confidence interval
            ci_lower, ci_upper = None, None
            logger.warning("SciPy bootstrap not available, skipping confidence interval calculation")
        
        # Determine if the result is significant
        significant = p_value < alpha
        
        return {
            'test_type': 'Mann-Whitney U test',
            'control_median': control_median,
            'treatment_median': treatment_median,
            'median_difference': median_diff,
            'percent_change': (median_diff / control_median * 100) if control_median != 0 else float('inf'),
            'u_statistic': u_stat,
            'p_value': p_value,
            'confidence_interval': (ci_lower, ci_upper) if ci_lower is not None else None,
            'confidence_level': 1 - alpha,
            'significant': significant,
            'control_sample_size': len(control),
            'treatment_sample_size': len(treatment),
            'effect_size': cles
        }
    
    def _run_anova(self, control_values: list, treatment_values: list, alpha: float, **kwargs) -> Dict[str, Any]:
        """Run one-way ANOVA test."""
        # For ANOVA, we typically need multiple groups, but we can still run it with just two
        # Convert to numpy arrays
        control = np.array(control_values, dtype=float)
        treatment = np.array(treatment_values, dtype=float)
        
        # Run one-way ANOVA
        f_stat, p_value = stats.f_oneway(control, treatment)
        
        # Calculate effect size (eta-squared)
        total_values = np.concatenate([control, treatment])
        grand_mean = np.mean(total_values)
        
        ss_total = np.sum((total_values - grand_mean) ** 2)
        ss_between = (len(control) * (np.mean(control) - grand_mean) ** 2 + 
                     len(treatment) * (np.mean(treatment) - grand_mean) ** 2)
        
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        # Determine if the result is significant
        significant = p_value < alpha
        
        return {
            'test_type': 'One-way ANOVA',
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': significant,
            'control_sample_size': len(control),
            'treatment_sample_size': len(treatment),
            'effect_size': eta_squared,
            'effect_size_type': 'eta_squared'
        }
    
    def _run_chi_square(self, control_values: list, treatment_values: list, alpha: float, **kwargs) -> Dict[str, Any]:
        """Run Chi-square test for categorical data."""
        # For chi-square, we assume the values represent counts in different categories
        # Convert to numpy arrays
        control = np.array(control_values, dtype=float)
        treatment = np.array(treatment_values, dtype=float)
        
        # Check if the arrays are the same length (same number of categories)
        if len(control) != len(treatment):
            raise ValueError("Control and treatment must have the same number of categories for chi-square test")
        
        # Run chi-square test
        contingency_table = np.vstack([control, treatment])
        chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)
        
        # Calculate Cramer's V as effect size
        n = np.sum(contingency_table)
        min_dim = min(contingency_table.shape) - 1
        cramers_v = np.sqrt(chi2_stat / (n * min_dim)) if n * min_dim > 0 else 0
        
        # Determine if the result is significant
        significant = p_value < alpha
        
        return {
            'test_type': 'Chi-square test',
            'chi2_statistic': chi2_stat,
            'p_value': p_value,
            'degrees_of_freedom': dof,
            'significant': significant,
            'effect_size': cramers_v,
            'effect_size_type': 'cramers_v'
        }
    
    def check_assumptions(self, metric: str) -> Dict[str, Dict[str, Any]]:
        """
        Check statistical assumptions for the given metric across all treatments.
        
        Args:
            metric (str): The metric to check assumptions for.
            
        Returns:
            dict: Dictionary with results of assumption checks for each treatment.
        """
        if metric not in self.control_experiment_data:
            raise ValueError(f"Metric '{metric}' not found in control data")
            
        results = {}
        control_values = np.array(self.control_experiment_data[metric], dtype=float)
        
        # Check normality of control
        control_shapiro = stats.shapiro(control_values)
        control_normality = {
            'test': 'Shapiro-Wilk',
            'statistic': control_shapiro[0],
            'p_value': control_shapiro[1],
            'normal': control_shapiro[1] >= 0.05
        }
        
        for treatment_id, treatment_data in self.treatments_experiment_data.items():
            if metric not in treatment_data:
                logger.warning(f"Metric '{metric}' not found in treatment '{treatment_id}'")
                continue
                
            treatment_values = np.array(treatment_data[metric], dtype=float)
            
            # Check normality of treatment
            treatment_shapiro = stats.shapiro(treatment_values)
            treatment_normality = {
                'test': 'Shapiro-Wilk',
                'statistic': treatment_shapiro[0],
                'p_value': treatment_shapiro[1],
                'normal': treatment_shapiro[1] >= 0.05
            }
            
            # Check homogeneity of variance
            levene_test = stats.levene(control_values, treatment_values)
            variance_homogeneity = {
                'test': 'Levene',
                'statistic': levene_test[0],
                'p_value': levene_test[1],
                'equal_variance': levene_test[1] >= 0.05
            }
            
            # Store results and convert to JSON serializable types
            results[treatment_id] = convert_to_serializable({
                'control_normality': control_normality,
                'treatment_normality': treatment_normality,
                'variance_homogeneity': variance_homogeneity,
                'recommended_test': self._recommend_test(control_normality['normal'], 
                                                       treatment_normality['normal'],
                                                       variance_homogeneity['equal_variance'])
            })
            
        return results
    
    def _recommend_test(self, control_normal: bool, treatment_normal: bool, equal_variance: bool) -> str:
        """Recommend a statistical test based on assumption checks."""
        if control_normal and treatment_normal:
            if equal_variance:
                return 't_test'
            else:
                return 'welch_t_test'
        else:
            return 'mann_whitney'


def cohen_d(x: Union[list, np.ndarray], y: Union[list, np.ndarray]) -> float:
    """
    Calculate Cohen's d effect size for two samples.
    
    Args:
        x: First sample
        y: Second sample
        
    Returns:
        float: Cohen's d effect size
    """
    nx = len(x)
    ny = len(y)
    
    # Convert to numpy arrays
    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)
    
    # Calculate means
    mx = np.mean(x)
    my = np.mean(y)
    
    # Calculate standard deviations
    sx = np.std(x, ddof=1)
    sy = np.std(y, ddof=1)
    
    # Pooled standard deviation
    pooled_sd = np.sqrt(((nx - 1) * sx**2 + (ny - 1) * sy**2) / (nx + ny - 2))
    
    # Cohen's d
    return (my - mx) / pooled_sd if pooled_sd > 0 else 0


def convert_to_serializable(obj):
    """
    Convert NumPy types to native Python types recursively to ensure JSON serialization works.
    
    Args:
        obj: Any object that might contain NumPy types
        
    Returns:
        Object with NumPy types converted to Python native types
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.number, np.bool_)):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_serializable(i) for i in obj)
    else:
        return obj