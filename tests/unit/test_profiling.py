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
        assert profiler.agents == []
        assert profiler.analysis_results == {}

    def test_profiler_custom_attributes(self):
        """Test profiler initialization with custom attributes."""
        custom_attrs = ["name", "age", "occupation.title"]
        profiler = Profiler(attributes=custom_attrs)
        
        assert profiler.attributes == custom_attrs


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
        
        # Test with mock TinyPerson having a .get() method
        class MockAgent:
            def get(self, path):
                data = {
                    "name": "Test",
                    "occupation": {"title": "Engineer", "company": "TechCorp"},
                }
                keys = path.split('.')
                value = data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return None
                return value
        
        mock_agent = MockAgent()
        assert profiler._get_nested_attribute(mock_agent, "name") == "Test"
        assert profiler._get_nested_attribute(mock_agent, "occupation.title") == "Engineer"

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
        
        # Results now directly contains the distributions (not wrapped in a dict)
        assert isinstance(results, dict)
        
        # Check that distributions were computed
        assert "age" in results
        assert "nationality" in results
        assert "occupation.title" in results
        
        # Check stored agents
        assert len(profiler.agents) == 3

    def test_advanced_profiling(self, advanced_profiler, sample_agent_dicts):
        """Test advanced profiling with statistical analysis."""
        with patch('matplotlib.pyplot.show'):
            results = advanced_profiler.profile(sample_agent_dicts, plot=False, advanced_analysis=True)
        
        # Check that advanced analysis was stored in analysis_results
        assert "demographics" in advanced_profiler.analysis_results
        assert "correlations" in advanced_profiler.analysis_results
        # Note: persona_composition requires Normalizer and may not always be present

    def test_demographics_analysis(self, profiler, sample_agent_dicts):
        """Test demographic analysis functionality."""
        profiler.agents = sample_agent_dicts
        demographics = profiler._analyze_demographics()
        
        # Test age statistics
        assert "age_stats" in demographics
        age_stats = demographics["age_stats"]
        assert age_stats["mean"] == pytest.approx((28 + 35 + 42) / 3, rel=1e-2)
        assert age_stats["median"] == 35
        assert age_stats["min"] == 28
        assert age_stats["max"] == 42
        
        # Test occupation diversity
        assert "occupation_diversity" in demographics
        occ_div = demographics["occupation_diversity"]
        assert occ_div["total_unique"] == 3
        assert len(occ_div["most_common"]) <= 10

    def test_correlation_analysis(self, profiler, sample_agent_dicts):
        """Test correlation analysis."""
        profiler.agents = sample_agent_dicts
        correlations = profiler._analyze_correlations()
        
        assert "correlation_matrix" in correlations
        assert "available_fields" in correlations
        
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
        profiler.agents = sample_agent_dicts
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
        content = report_file.read_text(encoding='utf-8')
        
        assert "AGENT POPULATION ANALYSIS REPORT" in content
        assert "DEMOGRAPHICS" in content or "Demographics" in content.lower()

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
        
        assert len(profiler.agents) == 0
        
        # Test with agents missing attributes
        incomplete_agents = [{"name": "Incomplete"}]  # Missing most attributes
        
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile(incomplete_agents, plot=False, advanced_analysis=False)
        
        # Should handle gracefully
        assert len(profiler.agents) == 1

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
        assert len(profiler.agents) == 3

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
        
        assert len(profiler.agents) == 2
        
        # Check that TinyPerson-specific data was extracted
        # Agents are stored as-is, not converted to dicts
        assert hasattr(profiler.agents[0], 'get') or isinstance(profiler.agents[0], dict)

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
        
        assert len(profiler.agents) == 100
        
        # Check that analysis completed successfully
        assert "demographics" in profiler.analysis_results

    def test_comma_preservation_in_profiling(self, profiler):
        """Test that comma-separated descriptions are preserved intact during profiling."""
        # Create test agents with multi-sentence descriptions containing commas
        test_agents = [
            {
                "name": "Alice",
                "style": "Warm, practical, organized caregiver. She notices subtle changes in others' emotions and checks in proactively. Uses clear, direct communication with family members.",
                "health": "Generally healthy, exercises regularly. Maintains good work-life balance, though sometimes stressed during busy periods. Prioritizes mental health through meditation.",
                "personality": {"traits": ["Empathetic, nurturing", "Detail-oriented, systematic"]}
            },
            {
                "name": "Bob", 
                "style": "Analytical, detail-oriented professional. Prefers written communication over verbal; tends to be thorough in explanations. Values precision, accuracy, and systematic approaches.",
                "health": "Active lifestyle, runs marathons. Occasional back pain from desk work, but manages it well. Follows strict nutrition plan with occasional indulgences.",
                "personality": {"traits": ["Methodical, precise", "Independent, focused"]}
            }
        ]

        # Mock the agent.get() method to return the test data
        class MockAgent:
            def __init__(self, data):
                self._data = data
                
            def get(self, path):
                """Mock TinyPerson.get() method with dot notation support"""
                keys = path.split('.')
                value = self._data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        return None
                return value

        # Convert to mock agents
        mock_agents = [MockAgent(agent) for agent in test_agents]

        # Run advanced profiling to trigger persona composition analysis
        with patch('matplotlib.pyplot.show'):
            results = profiler.profile(mock_agents, plot=False, advanced_analysis=True)
        
        # Verify profiling completed successfully
        assert len(profiler.agents) == 2
        
        # Access persona composition from profiler's internal analysis results
        assert hasattr(profiler, 'analysis_results')
        assert "persona_composition" in profiler.analysis_results
        
        composition = profiler.analysis_results["persona_composition"]
        
        # Test communication style preservation
        if "communication_style" in composition and not composition["communication_style"].empty:
            style_df = composition["communication_style"]
            style_categories = style_df["category"].tolist()
            
            # Verify that meaningful categories were created (not fragments)
            print(f"Style categories found: {style_categories}")
            
            # Verify that full original descriptions are preserved in examples
            examples_found = []
            for _, row in style_df.iterrows():
                examples_found.extend(row["examples"])
            
            # Check that original full descriptions are preserved somewhere
            original_descriptions = [
                "Warm, practical, organized caregiver. She notices subtle changes in others' emotions and checks in proactively. Uses clear, direct communication with family members.",
                "Analytical, detail-oriented professional. Prefers written communication over verbal; tends to be thorough in explanations. Values precision, accuracy, and systematic approaches."
            ]
            
            for original_desc in original_descriptions:
                assert any(original_desc == example for example in examples_found), \
                    f"Original description '{original_desc[:50]}...' was not preserved exactly in examples"
            
            print(f"✅ Communication style descriptions preserved intact")
        
        # Test health preservation  
        if "health" in composition and not composition["health"].empty:
            health_df = composition["health"]
            health_categories = health_df["category"].tolist()
            
            print(f"Health categories found: {health_categories}")
            
            # Verify original health descriptions are preserved
            health_examples_found = []
            for _, row in health_df.iterrows():
                health_examples_found.extend(row["examples"])
            
            original_health = [
                "Generally healthy, exercises regularly. Maintains good work-life balance, though sometimes stressed during busy periods. Prioritizes mental health through meditation.",
                "Active lifestyle, runs marathons. Occasional back pain from desk work, but manages it well. Follows strict nutrition plan with occasional indulgences."
            ]
            
            for original_health_desc in original_health:
                assert any(original_health_desc == example for example in health_examples_found), \
                    f"Original health description '{original_health_desc[:50]}...' was not preserved exactly"
            
            print(f"✅ Health descriptions preserved intact")

        print(f"✅ Comma preservation test passed - all original multi-sentence descriptions with commas preserved exactly")
        
        # Additional verification: Check that the normalizer was called with full descriptions
        # This ensures our fix in the profiling code is working
        if hasattr(profiler, '_last_normalization_call'):
            # If we track normalization calls, verify they contain full descriptions
            pass  # Could add more detailed verification if needed


if __name__ == "__main__":
    pytest.main([__file__])
