import pytest
import logging
import pandas as pd
import numpy as np
from collections import Counter
from unittest.mock import Mock, patch

logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')  # ensures that the package is imported from the parent directory
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.profiling import Profiler
from tinytroupe.agent import TinyPerson
from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist

from testing_utils import *


class TestProfiler:
    """Test suite for the enhanced Profiler class."""

    @pytest.fixture
    def sample_agent_dicts(self):
        """Create sample agent data as dictionaries for testing."""
        return [
            {
                "name": "Alice",
                "age": 28,
                "nationality": "American",
                "occupation": {"title": "Software Engineer"},
                "actions_count": 15,
                "stimuli_count": 20,
                "social_connections": 5,
                "current_emotions": "Happy and motivated",
                "current_goals": ["Complete project", "Learn new skills"],
                "big_five": {
                    "openness": "High. Very creative and curious.",
                    "conscientiousness": "High. Well organized.",
                    "extraversion": "Medium. Socially comfortable.",
                    "agreeableness": "High. Very cooperative.",
                    "neuroticism": "Low. Emotionally stable."
                }
            },
            {
                "name": "Bob",
                "age": 35,
                "nationality": "Canadian",
                "occupation": {"title": "Data Scientist"},
                "actions_count": 22,
                "stimuli_count": 18,
                "social_connections": 3,
                "current_emotions": "Focused and analytical",
                "current_goals": ["Analyze data", "Present findings"],
                "big_five": {
                    "openness": "High. Loves learning.",
                    "conscientiousness": "High. Very methodical.",
                    "extraversion": "Low. Prefers working alone.",
                    "agreeableness": "Medium. Collaborative when needed.",
                    "neuroticism": "Low. Calm under pressure."
                }
            },
            {
                "name": "Carol",
                "age": 42,
                "nationality": "British",
                "occupation": {"title": "Marketing Manager"},
                "actions_count": 30,
                "stimuli_count": 25,
                "social_connections": 8,
                "current_emotions": "Enthusiastic and creative",
                "current_goals": ["Launch campaign", "Increase brand awareness"],
                "big_five": {
                    "openness": "High. Very imaginative.",
                    "conscientiousness": "Medium. Generally organized.",
                    "extraversion": "High. Very outgoing.",
                    "agreeableness": "High. Team player.",
                    "neuroticism": "Medium. Sometimes stressed."
                }
            }
        ]

    @pytest.fixture
    def profiler(self):
        """Create a basic profiler instance for testing."""
        return Profiler(attributes=["age", "nationality", "occupation.title"])

    @pytest.fixture
    def advanced_profiler(self):
        """Create a profiler with more attributes for advanced testing."""
        return Profiler(attributes=["age", "nationality", "occupation.title", "actions_count", "social_connections"])

    def test_profiler_initialization(self):
        """Test that the profiler initializes correctly."""
        profiler = Profiler()
        
        assert profiler.attributes == ["age", "occupation.title", "nationality"]
        assert profiler.attributes_distributions == {}
        assert profiler.agents_data is None
        assert profiler.analysis_results == {}

    def test_profiler_custom_attributes(self):
        """Test profiler initialization with custom attributes."""
        custom_attrs = ["name", "age", "occupation.title"]
        profiler = Profiler(attributes=custom_attrs)
        
        assert profiler.attributes == custom_attrs

    def test_prepare_agent_data_with_dicts(self, profiler, sample_agent_dicts):
        """Test data preparation with dictionary agents."""
        processed_data = profiler._prepare_agent_data(sample_agent_dicts)
        
        assert len(processed_data) == 3
        assert all(isinstance(agent, dict) for agent in processed_data)
        assert processed_data[0]["name"] == "Alice"
        assert processed_data[1]["age"] == 35
        assert processed_data[2]["nationality"] == "British"

    def test_get_nested_attribute(self, profiler):
        """Test nested attribute extraction."""
        agent = {
            "name": "Test",
            "occupation": {"title": "Engineer", "company": "TechCorp"},
            "skills": ["Python", "ML"]
        }
        
        # Test simple attribute
        assert profiler._get_nested_attribute(agent, "name") == "Test"
        
        # Test nested attribute
        assert profiler._get_nested_attribute(agent, "occupation.title") == "Engineer"
        assert profiler._get_nested_attribute(agent, "occupation.company") == "TechCorp"
        
        # Test non-existent attribute
        assert profiler._get_nested_attribute(agent, "nonexistent") is None
        assert profiler._get_nested_attribute(agent, "occupation.nonexistent") is None

    def test_compute_attribute_distribution(self, profiler, sample_agent_dicts):
        """Test attribute distribution computation."""
        # Test age distribution
        age_dist = profiler._compute_attribute_distribution(sample_agent_dicts, "age")
        
        assert isinstance(age_dist, pd.Series)
        assert len(age_dist) == 3  # 3 unique ages
        assert age_dist[28] == 1
        assert age_dist[35] == 1
        assert age_dist[42] == 1

    def test_compute_attribute_distribution_nested(self, profiler, sample_agent_dicts):
        """Test nested attribute distribution computation."""
        # Test occupation.title distribution
        occ_dist = profiler._compute_attribute_distribution(sample_agent_dicts, "occupation.title")
        
        assert isinstance(occ_dist, pd.Series)
        assert len(occ_dist) == 3  # 3 different occupations
        assert "Software Engineer" in occ_dist.index
        assert "Data Scientist" in occ_dist.index
        assert "Marketing Manager" in occ_dist.index

    def test_basic_profiling(self, profiler, sample_agent_dicts):
        """Test basic profiling functionality."""
        # Mock matplotlib to avoid display issues in tests
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile(sample_agent_dicts, plot=False, advanced_analysis=False)
        
        assert "distributions" in results
        assert "summary_stats" in results
        
        # Check that distributions were computed
        assert "age" in results["distributions"]
        assert "nationality" in results["distributions"]
        assert "occupation.title" in results["distributions"]
        
        # Check summary stats
        assert results["summary_stats"]["total_agents"] == 3
        assert results["summary_stats"]["attributes_analyzed"] == 3

    def test_advanced_profiling(self, advanced_profiler, sample_agent_dicts):
        """Test advanced profiling with statistical analysis."""
        with patch('matplotlib.pyplot.show'):
            results = advanced_profiler.profile(sample_agent_dicts, plot=False, advanced_analysis=True)
        
        assert "analysis" in results
        assert "demographics" in results["analysis"]
        assert "behavioral_patterns" in results["analysis"]
        assert "social_analysis" in results["analysis"]
        assert "personality_clusters" in results["analysis"]
        assert "correlations" in results["analysis"]

    def test_demographics_analysis(self, profiler, sample_agent_dicts):
        """Test demographic analysis functionality."""
        profiler.agents_data = sample_agent_dicts
        demographics = profiler._analyze_demographics()
        
        # Test age statistics
        assert "age_stats" in demographics
        age_stats = demographics["age_stats"]
        assert age_stats["mean"] == pytest.approx((28 + 35 + 42) / 3, rel=1e-2)
        assert age_stats["median"] == 35
        assert age_stats["range"] == (28, 42)
        
        # Test occupation diversity
        assert "occupation_diversity" in demographics
        occ_div = demographics["occupation_diversity"]
        assert occ_div["unique_count"] == 3
        assert len(occ_div["most_common"]) <= 5

    def test_behavioral_analysis(self, profiler, sample_agent_dicts):
        """Test behavioral pattern analysis."""
        profiler.agents_data = sample_agent_dicts
        behavioral = profiler._analyze_behavioral_patterns()
        
        # Test activity levels
        assert "activity_levels" in behavioral
        activity = behavioral["activity_levels"]
        
        expected_actions_mean = (15 + 22 + 30) / 3
        expected_stimuli_mean = (20 + 18 + 25) / 3
        
        assert activity["actions_mean"] == pytest.approx(expected_actions_mean, rel=1e-2)
        assert activity["stimuli_mean"] == pytest.approx(expected_stimuli_mean, rel=1e-2)
        assert activity["activity_ratio"] > 0

    def test_social_analysis(self, profiler, sample_agent_dicts):
        """Test social pattern analysis."""
        profiler.agents_data = sample_agent_dicts
        social = profiler._analyze_social_patterns()
        
        # Test connectivity analysis
        assert "connectivity" in social
        connectivity = social["connectivity"]
        
        expected_avg_connections = (5 + 3 + 8) / 3
        assert connectivity["avg_connections"] == pytest.approx(expected_avg_connections, rel=1e-2)
        assert connectivity["social_isolation_rate"] == 0  # No isolated agents in sample

    def test_personality_analysis(self, profiler, sample_agent_dicts):
        """Test personality clustering analysis."""
        profiler.agents_data = sample_agent_dicts
        personality = profiler._analyze_personality_clusters()
        
        # Should have trait analysis since we have Big Five data
        assert "trait_analysis" in personality
        trait_analysis = personality["trait_analysis"]
        
        assert "average_traits" in trait_analysis
        assert "trait_correlations" in trait_analysis
        assert "dominant_traits" in trait_analysis
        
        # Check that we have all Big Five traits
        avg_traits = trait_analysis["average_traits"]
        expected_traits = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        for trait in expected_traits:
            assert trait in avg_traits

    def test_correlation_analysis(self, profiler, sample_agent_dicts):
        """Test correlation analysis."""
        profiler.agents_data = sample_agent_dicts
        correlations = profiler._analyze_correlations()
        
        assert "correlation_matrix" in correlations
        assert "numerical_correlations" in correlations
        
        # Check that correlation matrix is properly formatted
        corr_matrix = correlations["correlation_matrix"]
        assert isinstance(corr_matrix, dict)

    def test_diversity_index_calculation(self, profiler):
        """Test Shannon diversity index calculation."""
        # Test with uniform distribution
        uniform_counts = Counter(["A", "B", "C", "D"])
        diversity = profiler._calculate_diversity_index(uniform_counts)
        assert diversity == pytest.approx(1.0, rel=1e-2)  # Maximum diversity
        
        # Test with single item
        single_counts = Counter(["A", "A", "A", "A"])
        diversity = profiler._calculate_diversity_index(single_counts)
        assert diversity == 0.0  # No diversity
        
        # Test with empty counter
        empty_counts = Counter()
        diversity = profiler._calculate_diversity_index(empty_counts)
        assert diversity == 0.0

    def test_connectivity_categorization(self, profiler):
        """Test social connectivity categorization."""
        connections = [0, 1, 2, 3, 5, 6, 8, 10]
        categories = profiler._categorize_connectivity(connections)
        
        assert categories["isolated"] == 1  # 0 connections
        assert categories["low"] == 2       # 1, 2 connections
        assert categories["medium"] == 2    # 3, 5 connections
        assert categories["high"] == 3      # 6, 8, 10 connections

    def test_normality_test(self, profiler):
        """Test normality testing function."""
        # Test with normal-ish data
        normal_data = [1, 2, 3, 4, 5, 4, 3, 2, 1]
        result = profiler._test_normality(normal_data)
        assert result == True
        
        # Test with skewed data
        skewed_data = [1, 1, 1, 1, 10, 10, 10]
        result = profiler._test_normality(skewed_data)
        assert result == False
        
        # Test with insufficient data
        small_data = [1, 2]
        result = profiler._test_normality(small_data)
        assert result == False

    def test_dominant_traits_identification(self, profiler):
        """Test identification of dominant personality traits."""
        # Create test data with clear dominant traits
        traits_data = pd.DataFrame([
            {"openness": 0.8, "conscientiousness": 0.3, "extraversion": 0.5},
            {"openness": 0.9, "conscientiousness": 0.2, "extraversion": 0.6},
            {"openness": 0.7, "conscientiousness": 0.4, "extraversion": 0.4}
        ])
        
        dominant = profiler._identify_dominant_traits(traits_data)
        
        assert dominant["openness"] == "high"      # Mean ~0.8
        assert dominant["conscientiousness"] == "low"  # Mean ~0.3
        assert dominant["extraversion"] == "moderate"  # Mean ~0.5

    def test_summary_statistics_generation(self, profiler, sample_agent_dicts):
        """Test summary statistics generation."""
        profiler.agents_data = sample_agent_dicts
        summary = profiler._generate_summary_statistics()
        
        assert summary["total_agents"] == 3
        assert summary["attributes_analyzed"] == 3
        assert "data_completeness" in summary
        
        # Check data completeness calculation
        completeness = summary["data_completeness"]
        assert completeness["age"] == 1.0  # All agents have age
        assert completeness["nationality"] == 1.0  # All agents have nationality
        assert completeness["occupation.title"] == 1.0  # All agents have occupation.title

    def test_export_analysis_report(self, profiler, sample_agent_dicts, tmp_path):
        """Test analysis report export functionality."""
        # Run analysis first
        with patch('matplotlib.pyplot.show'):
            profiler.profile(sample_agent_dicts, plot=False, advanced_analysis=True)
        
        # Export report to temporary file
        report_file = tmp_path / "test_report.txt"
        profiler.export_analysis_report(str(report_file))
        
        # Check that file was created and contains expected content
        assert report_file.exists()
        content = report_file.read_text()
        
        assert "AGENT POPULATION ANALYSIS REPORT" in content
        assert "Total Agents Analyzed: 3" in content
        assert "DEMOGRAPHICS" in content
        assert "BEHAVIORAL PATTERNS" in content

    def test_add_custom_analysis(self, profiler, sample_agent_dicts):
        """Test adding custom analysis functions."""
        def custom_analysis(agents_data):
            return {"custom_metric": len(agents_data) * 2}
        
        profiler.add_custom_analysis("test_analysis", custom_analysis)
        
        assert hasattr(profiler, '_custom_analyses')
        assert "test_analysis" in profiler._custom_analyses
        assert profiler._custom_analyses["test_analysis"] == custom_analysis

    def test_compare_populations(self, profiler, sample_agent_dicts):
        """Test population comparison functionality."""
        # Create a second population
        other_agents = [
            {"name": "Dave", "age": 30, "nationality": "German", "occupation": {"title": "Designer"}},
            {"name": "Eve", "age": 25, "nationality": "French", "occupation": {"title": "Writer"}}
        ]
        
        # Run initial profiling
        with patch('matplotlib.pyplot.show'):
            profiler.profile(sample_agent_dicts, plot=False, advanced_analysis=False)
        
        # Compare populations
        with patch('matplotlib.pyplot.show'):
            comparison = profiler.compare_populations(other_agents)
        
        assert "population_sizes" in comparison
        assert comparison["population_sizes"]["current"] == 3
        assert comparison["population_sizes"]["comparison"] == 2
        
        assert "attribute_comparisons" in comparison
        # Should have comparisons for overlapping attributes
        for attr in ["age", "nationality", "occupation.title"]:
            if attr in comparison["attribute_comparisons"]:
                attr_comp = comparison["attribute_comparisons"][attr]
                assert "current_unique_values" in attr_comp
                assert "comparison_unique_values" in attr_comp

    @patch('matplotlib.pyplot.show')
    def test_plotting_functions(self, mock_show, profiler, sample_agent_dicts):
        """Test that plotting functions run without errors."""
        # Run profiling with plots enabled
        results = profiler.profile(sample_agent_dicts, plot=True, advanced_analysis=True)
        
        # Verify that matplotlib show was called (plots were generated)
        assert mock_show.called
        
        # Test individual plotting methods
        profiler._plot_basic_distributions()
        profiler._plot_advanced_analysis()
        
        if 'demographics' in profiler.analysis_results:
            profiler._plot_demographics()
        
        if 'behavioral_patterns' in profiler.analysis_results:
            profiler._plot_behavioral_patterns()
        
        if ('correlations' in profiler.analysis_results and 
            'correlation_matrix' in profiler.analysis_results['correlations']):
            profiler._plot_correlation_heatmap()

    def test_error_handling_empty_data(self, profiler):
        """Test error handling with empty or invalid data."""
        # Test with empty list
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile([], plot=False, advanced_analysis=False)
        
        assert results["summary_stats"]["total_agents"] == 0
        
        # Test with agents missing attributes
        incomplete_agents = [{"name": "Incomplete"}]  # Missing most attributes
        
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile(incomplete_agents, plot=False, advanced_analysis=False)
        
        # Should handle gracefully
        assert results["summary_stats"]["total_agents"] == 1

    def test_mixed_data_types(self, profiler):
        """Test handling of mixed data types in attributes."""
        mixed_agents = [
            {"age": 25, "occupation": "Engineer"},  # occupation as string
            {"age": 30, "occupation": {"title": "Scientist"}},  # occupation as dict
            {"age": "35", "occupation": {"title": "Manager"}}  # age as string
        ]
        
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile(mixed_agents, plot=False, advanced_analysis=False)
        
        # Should handle mixed types gracefully
        assert results["summary_stats"]["total_agents"] == 3

    @pytest.mark.skipif(TinyPerson is None, reason="TinyPerson not available")
    def test_tinyperson_integration(self, profiler):
        """Test integration with actual TinyPerson objects."""
        # Clear any existing agents to avoid name conflicts
        TinyPerson.clear_agents()
        
        # Create TinyPerson objects
        oscar = create_oscar_the_architect()
        lisa = create_lisa_the_data_scientist()
        
        agents = [oscar, lisa]
        
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile(agents, plot=False, advanced_analysis=True)
        
        assert results["summary_stats"]["total_agents"] == 2
        
        # Check that TinyPerson-specific data was extracted
        agent_data = profiler.agents_data[0]
        assert "name" in agent_data  # Should have extracted name from persona
        
        # Should have attempted to extract behavioral and social data
        # (exact values depend on the specific TinyPerson state)

    def test_large_population_performance(self, profiler):
        """Test profiler performance with larger populations."""
        # Create a larger dataset
        large_population = []
        for i in range(100):
            agent = {
                "name": f"Agent_{i}",
                "age": 20 + (i % 50),
                "nationality": ["American", "Canadian", "British", "German", "French"][i % 5],
                "occupation": {"title": ["Engineer", "Scientist", "Manager", "Designer", "Writer"][i % 5]},
                "actions_count": i % 20,
                "stimuli_count": (i + 5) % 25,
                "social_connections": i % 10
            }
            large_population.append(agent)
        
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile(large_population, plot=False, advanced_analysis=True)
        
        assert results["summary_stats"]["total_agents"] == 100
        
        # Check that analysis completed successfully
        assert "demographics" in results["analysis"]
        assert "behavioral_patterns" in results["analysis"]


if __name__ == "__main__":
    pytest.main([__file__])
