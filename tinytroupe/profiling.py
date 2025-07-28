"""
Provides mechanisms for creating understanding the characteristics of agent populations, such as
their age distribution, typical interests, and so on.

Guideline for plotting the methods: all plot methods should also return a Pandas dataframe with the data used for 
plotting.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from typing import List, Dict, Any, Optional, Union, Callable
from collections import Counter, defaultdict
import warnings

# Handle TinyPerson import gracefully
try:
    from tinytroupe.agent import TinyPerson
except ImportError:
    # Fallback if import fails
    TinyPerson = None


class Profiler:
    """
    Advanced profiler for analyzing agent population characteristics with support for 
    complex attributes, statistical analysis, and comprehensive visualizations.
    """

    def __init__(self, attributes: List[str] = ["age", "occupation.title", "nationality"]) -> None: 
        self.attributes = attributes
        self.attributes_distributions = {}  # attribute -> DataFrame
        self.agents_data = None  # Store processed agent data
        self.analysis_results = {}  # Store various analysis results
        
        # Set up better plotting style
        plt.style.use('default')
        sns.set_palette("husl")

    def profile(self, agents: Union[List[dict], List[TinyPerson]], plot: bool = True, 
                advanced_analysis: bool = True) -> Dict[str, Any]:   
        """
        Profiles the given agents with comprehensive analysis.

        Args:
            agents: The agents to be profiled (either dicts or TinyPerson objects)
            plot: Whether to generate visualizations
            advanced_analysis: Whether to perform advanced statistical analysis
        
        Returns:
            Dictionary containing all analysis results
        """
        # Convert agents to consistent format
        self.agents_data = self._prepare_agent_data(agents)
        
        # Basic attribute distributions
        self.attributes_distributions = self._compute_attributes_distributions(self.agents_data)
        
        if advanced_analysis:
            self._perform_advanced_analysis()
        
        if plot:
            self.render(advanced=advanced_analysis)
            
        return {
            'distributions': self.attributes_distributions,
            'analysis': self.analysis_results,
            'summary_stats': self._generate_summary_statistics()
        }

    def _prepare_agent_data(self, agents: Union[List[dict], List[TinyPerson]]) -> List[Dict[str, Any]]:
        """Convert agents to a consistent dictionary format for analysis."""
        processed_agents = []
        
        for agent in agents:
            if isinstance(agent, TinyPerson):
                # Extract data from TinyPerson object
                agent_data = self._extract_tinyperson_data(agent)
            else:
                agent_data = agent.copy()
            
            processed_agents.append(agent_data)
        
        return processed_agents

    def _extract_tinyperson_data(self, agent: TinyPerson) -> Dict[str, Any]:
        """Extract comprehensive data from a TinyPerson object."""
        data = {}
        
        # Basic persona attributes
        if hasattr(agent, '_persona') and agent._persona:
            data.update(agent._persona)
        
        # Mental state information
        if hasattr(agent, '_mental_state') and agent._mental_state:
            mental_state = agent._mental_state
            data['current_emotions'] = mental_state.get('emotions')
            data['current_goals'] = mental_state.get('goals', [])
            data['current_context'] = mental_state.get('context', [])
            data['accessible_agents_count'] = len(mental_state.get('accessible_agents', []))
        
        # Behavioral metrics
        if hasattr(agent, 'actions_count'):
            data['actions_count'] = agent.actions_count
        if hasattr(agent, 'stimuli_count'):
            data['stimuli_count'] = agent.stimuli_count
            
        # Memory statistics
        if hasattr(agent, 'episodic_memory') and agent.episodic_memory:
            try:
                # Get total memory size including both committed memory and current episode buffer
                memory_size = len(agent.episodic_memory.memory) + len(agent.episodic_memory.episodic_buffer)
                data['episodic_memory_size'] = memory_size
            except AttributeError:
                # Fallback if memory structure is different
                data['episodic_memory_size'] = 0
        
        # Social connections
        if hasattr(agent, '_accessible_agents'):
            data['social_connections'] = len(agent._accessible_agents)
        
        return data

    def _perform_advanced_analysis(self):
        """Perform advanced statistical and behavioral analysis."""
        self.analysis_results = {}
        
        # Demographic analysis
        self.analysis_results['demographics'] = self._analyze_demographics()
        
        # Behavioral patterns
        self.analysis_results['behavioral_patterns'] = self._analyze_behavioral_patterns()
        
        # Social network analysis
        self.analysis_results['social_analysis'] = self._analyze_social_patterns()
        
        # Personality clustering
        self.analysis_results['personality_clusters'] = self._analyze_personality_clusters()
        
        # Correlations
        self.analysis_results['correlations'] = self._analyze_correlations()

    def _analyze_demographics(self) -> Dict[str, Any]:
        """Analyze demographic patterns in the population."""
        demographics = {}
        
        # Age analysis
        ages = [agent.get('age') for agent in self.agents_data if agent.get('age') is not None]
        if ages:
            demographics['age_stats'] = {
                'mean': np.mean(ages),
                'median': np.median(ages),
                'std': np.std(ages),
                'range': (min(ages), max(ages)),
                'distribution': 'normal' if self._test_normality(ages) else 'non-normal'
            }
        
        # Occupation diversity
        occupations = [agent.get('occupation', {}).get('title') if isinstance(agent.get('occupation'), dict) 
                      else agent.get('occupation') for agent in self.agents_data]
        occupations = [occ for occ in occupations if occ is not None]
        
        if occupations:
            occ_counts = Counter(occupations)
            demographics['occupation_diversity'] = {
                'unique_count': len(occ_counts),
                'diversity_index': self._calculate_diversity_index(occ_counts),
                'most_common': occ_counts.most_common(5)
            }
        
        # Geographic distribution
        nationalities = [agent.get('nationality') for agent in self.agents_data if agent.get('nationality')]
        if nationalities:
            nat_counts = Counter(nationalities)
            demographics['geographic_diversity'] = {
                'unique_countries': len(nat_counts),
                'diversity_index': self._calculate_diversity_index(nat_counts),
                'distribution': dict(nat_counts)
            }
        
        return demographics

    def _analyze_behavioral_patterns(self) -> Dict[str, Any]:
        """Analyze behavioral patterns across the population."""
        behavioral = {}
        
        # Activity levels
        actions_data = [agent.get('actions_count', 0) for agent in self.agents_data]
        stimuli_data = [agent.get('stimuli_count', 0) for agent in self.agents_data]
        
        if any(actions_data):
            behavioral['activity_levels'] = {
                'actions_mean': np.mean(actions_data),
                'actions_std': np.std(actions_data),
                'stimuli_mean': np.mean(stimuli_data),
                'stimuli_std': np.std(stimuli_data),
                'activity_ratio': np.mean(actions_data) / max(np.mean(stimuli_data), 1)
            }
        
        # Goal patterns
        all_goals = []
        for agent in self.agents_data:
            goals = agent.get('current_goals', [])
            if isinstance(goals, list):
                all_goals.extend(goals)
        
        if all_goals:
            goal_counts = Counter(all_goals)
            behavioral['goal_patterns'] = {
                'common_goals': goal_counts.most_common(10),
                'goal_diversity': self._calculate_diversity_index(goal_counts)
            }
        
        return behavioral

    def _analyze_social_patterns(self) -> Dict[str, Any]:
        """Analyze social connection patterns."""
        social = {}
        
        # Social connectivity
        connections = [agent.get('social_connections', 0) for agent in self.agents_data]
        accessible_counts = [agent.get('accessible_agents_count', 0) for agent in self.agents_data]
        
        if any(connections + accessible_counts):
            social['connectivity'] = {
                'avg_connections': np.mean(connections),
                'avg_accessible': np.mean(accessible_counts),
                'connectivity_distribution': self._categorize_connectivity(connections),
                'social_isolation_rate': sum(1 for c in connections if c == 0) / len(connections)
            }
        
        return social

    def _analyze_personality_clusters(self) -> Dict[str, Any]:
        """Identify personality-based clusters if Big Five data is available."""
        personality = {}
        
        # Extract Big Five traits if available
        big_five_data = []
        for agent in self.agents_data:
            if 'big_five' in agent and isinstance(agent['big_five'], dict):
                traits = agent['big_five']
                # Convert text descriptions to numerical values (simplified approach)
                numerical_traits = {}
                for trait, value in traits.items():
                    if isinstance(value, str):
                        if 'high' in value.lower():
                            numerical_traits[trait] = 0.8
                        elif 'medium' in value.lower():
                            numerical_traits[trait] = 0.5
                        elif 'low' in value.lower():
                            numerical_traits[trait] = 0.2
                        else:
                            numerical_traits[trait] = 0.5  # Default
                    else:
                        numerical_traits[trait] = value
                
                if len(numerical_traits) == 5:  # Full Big Five
                    big_five_data.append(numerical_traits)
        
        if len(big_five_data) >= 2:  # Need minimum agents for analysis (reduced from >3 to >=2)
            df_traits = pd.DataFrame(big_five_data)
            
            # Simple clustering based on dominant traits
            personality['trait_analysis'] = {
                'average_traits': df_traits.mean().to_dict(),
                'trait_correlations': df_traits.corr().to_dict() if len(big_five_data) > 1 else {},
                'dominant_traits': self._identify_dominant_traits(df_traits)
            }
        
        return personality

    def _analyze_correlations(self) -> Dict[str, Any]:
        """Analyze correlations between different attributes."""
        correlations = {}
        
        # Create a numerical dataset for correlation analysis
        numerical_data = {}
        
        for agent in self.agents_data:
            for attr in ['age', 'actions_count', 'stimuli_count', 'social_connections']:
                if attr not in numerical_data:
                    numerical_data[attr] = []
                numerical_data[attr].append(agent.get(attr, 0))
        
        if len(numerical_data) > 1:
            df_corr = pd.DataFrame(numerical_data)
            correlation_matrix = df_corr.corr()
            
            # Find strong correlations (> 0.5)
            strong_correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.5:
                        strong_correlations.append({
                            'variables': (correlation_matrix.columns[i], correlation_matrix.columns[j]),
                            'correlation': corr_value
                        })
            
            correlations['numerical_correlations'] = strong_correlations
            correlations['correlation_matrix'] = correlation_matrix.to_dict()
        
        return correlations

    def render(self, advanced: bool = True) -> None:
        """
        Renders comprehensive visualizations of the agent population analysis.
        """
        # Basic attribute distributions
        self._plot_basic_distributions()
        
        if advanced and self.analysis_results:
            self._plot_advanced_analysis()

    def _plot_basic_distributions(self) -> None:
        """Plot basic attribute distributions with improved styling."""
        n_attrs = len(self.attributes)
        if n_attrs == 0:
            return
        
        # Calculate subplot layout
        n_cols = min(3, n_attrs)
        n_rows = (n_attrs + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 4 * n_rows))
        if n_attrs == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = [axes] if n_attrs == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, attribute in enumerate(self.attributes):
            ax = axes[i] if n_attrs > 1 else axes[0]
            
            if attribute in self.attributes_distributions:
                df = self.attributes_distributions[attribute]
                
                # Create better visualizations based on data type
                if len(df) <= 15:  # Categorical data
                    df.plot(kind='bar', ax=ax, color=sns.color_palette("husl", len(df)))
                    ax.set_title(f"{attribute.replace('_', ' ').title()} Distribution", fontsize=12, fontweight='bold')
                    ax.tick_params(axis='x', rotation=45)
                else:  # Many categories - use horizontal bar for readability
                    df.head(15).plot(kind='barh', ax=ax, color=sns.color_palette("husl", 15))
                    ax.set_title(f"Top 15 {attribute.replace('_', ' ').title()}", fontsize=12, fontweight='bold')
                
                ax.grid(axis='y', alpha=0.3)
                ax.set_xlabel('Count')
        
        # Hide empty subplots
        for i in range(n_attrs, len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        plt.show()

    def _plot_advanced_analysis(self) -> None:
        """Create advanced visualizations for the analysis results."""
        
        # 1. Demographics overview
        if 'demographics' in self.analysis_results:
            self._plot_demographics()
        
        # 2. Behavioral patterns
        if 'behavioral_patterns' in self.analysis_results:
            self._plot_behavioral_patterns()
        
        # 3. Correlation heatmap
        if 'correlations' in self.analysis_results and 'correlation_matrix' in self.analysis_results['correlations']:
            self._plot_correlation_heatmap()

    def _plot_demographics(self) -> None:
        """Plot demographic analysis results."""
        demo = self.analysis_results['demographics']
        
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('Population Demographics Analysis', fontsize=16, fontweight='bold')
        
        # Age distribution
        if 'age_stats' in demo:
            ages = [agent.get('age') for agent in self.agents_data if agent.get('age') is not None]
            axes[0, 0].hist(ages, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
            axes[0, 0].axvline(demo['age_stats']['mean'], color='red', linestyle='--', 
                              label=f"Mean: {demo['age_stats']['mean']:.1f}")
            axes[0, 0].set_title('Age Distribution')
            axes[0, 0].set_xlabel('Age')
            axes[0, 0].set_ylabel('Count')
            axes[0, 0].legend()
        
        # Occupation diversity
        if 'occupation_diversity' in demo:
            occ_data = demo['occupation_diversity']['most_common']
            if occ_data:
                occs, counts = zip(*occ_data)
                axes[0, 1].pie(counts, labels=occs, autopct='%1.1f%%')
                axes[0, 1].set_title('Top Occupations')
        
        # Geographic distribution
        if 'geographic_diversity' in demo:
            geo_data = demo['geographic_diversity']['distribution']
            if geo_data:
                countries = list(geo_data.keys())[:10]  # Top 10
                counts = [geo_data[c] for c in countries]
                axes[1, 0].barh(countries, counts, color='lightcoral')
                axes[1, 0].set_title('Geographic Distribution')
                axes[1, 0].set_xlabel('Count')
        
        # Diversity metrics
        diversity_metrics = []
        diversity_values = []
        
        if 'occupation_diversity' in demo:
            diversity_metrics.append('Occupation\nDiversity')
            diversity_values.append(demo['occupation_diversity']['diversity_index'])
        
        if 'geographic_diversity' in demo:
            diversity_metrics.append('Geographic\nDiversity')
            diversity_values.append(demo['geographic_diversity']['diversity_index'])
        
        if diversity_metrics:
            axes[1, 1].bar(diversity_metrics, diversity_values, color='lightgreen')
            axes[1, 1].set_title('Diversity Indices')
            axes[1, 1].set_ylabel('Diversity Score')
            axes[1, 1].set_ylim(0, 1)
        
        plt.tight_layout()
        plt.show()

    def _plot_behavioral_patterns(self) -> None:
        """Plot behavioral analysis results."""
        behavioral = self.analysis_results['behavioral_patterns']
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle('Behavioral Patterns Analysis', fontsize=16, fontweight='bold')
        
        # Activity levels scatter plot
        if 'activity_levels' in behavioral:
            actions_data = [agent.get('actions_count', 0) for agent in self.agents_data]
            stimuli_data = [agent.get('stimuli_count', 0) for agent in self.agents_data]
            
            axes[0].scatter(stimuli_data, actions_data, alpha=0.6, color='purple')
            axes[0].set_xlabel('Stimuli Count')
            axes[0].set_ylabel('Actions Count')
            axes[0].set_title('Activity Patterns')
            
            # Add trend line
            if len(stimuli_data) > 1 and len(actions_data) > 1:
                z = np.polyfit(stimuli_data, actions_data, 1)
                p = np.poly1d(z)
                axes[0].plot(stimuli_data, p(stimuli_data), "r--", alpha=0.8)
        
        # Goal patterns
        if 'goal_patterns' in behavioral and behavioral['goal_patterns']['common_goals']:
            goals, counts = zip(*behavioral['goal_patterns']['common_goals'][:8])
            axes[1].barh(range(len(goals)), counts, color='orange')
            axes[1].set_yticks(range(len(goals)))
            axes[1].set_yticklabels([g[:30] + '...' if len(str(g)) > 30 else str(g) for g in goals])
            axes[1].set_xlabel('Frequency')
            axes[1].set_title('Common Goals')
        
        plt.tight_layout()
        plt.show()

    def _plot_correlation_heatmap(self) -> None:
        """Plot correlation heatmap for numerical attributes."""
        corr_data = self.analysis_results['correlations']['correlation_matrix']
        corr_df = pd.DataFrame(corr_data)
        
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr_df, annot=True, cmap='coolwarm', center=0, 
                   square=True, cbar_kws={'label': 'Correlation Coefficient'})
        plt.title('Attribute Correlations Heatmap', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.show()

    def _compute_attributes_distributions(self, agents: list) -> dict:
        """
        Computes the distributions of the attributes for the agents.
        """
        distributions = {}
        for attribute in self.attributes:
            distributions[attribute] = self._compute_attribute_distribution(agents, attribute)
        
        return distributions
    
    def _compute_attribute_distribution(self, agents: list, attribute: str) -> pd.DataFrame:
        """
        Computes the distribution of a given attribute with support for nested attributes.
        """
        values = []
        
        for agent in agents:
            value = self._get_nested_attribute(agent, attribute)
            values.append(value)
        
        # Handle None values
        values = [v for v in values if v is not None]
        
        if not values:
            return pd.DataFrame()
        
        # Convert mixed types to string for consistent sorting
        try:
            value_counts = pd.Series(values).value_counts().sort_index()
        except TypeError:
            # Handle mixed data types by converting to strings
            string_values = [str(v) for v in values]
            value_counts = pd.Series(string_values).value_counts().sort_index()
        
        return value_counts

    def _get_nested_attribute(self, agent: dict, attribute: str) -> Any:
        """Get nested attribute using dot notation (e.g., 'occupation.title')."""
        keys = attribute.split('.')
        value = agent
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value

    # Utility methods for advanced analysis
    def _test_normality(self, data: List[float]) -> bool:
        """Simple normality test using skewness."""
        if len(data) < 3:
            return False
        
        skewness = pd.Series(data).skew()
        return abs(skewness) < 0.3  # Stringent normality test - threshold to catch bimodal distributions

    def _calculate_diversity_index(self, counts: Counter) -> float:
        """Calculate Shannon diversity index."""
        total = sum(counts.values())
        if total <= 1:
            return 0.0
        
        diversity = 0
        for count in counts.values():
            if count > 0:
                p = count / total
                diversity -= p * np.log(p)
        
        return diversity / np.log(len(counts)) if len(counts) > 1 else 0

    def _categorize_connectivity(self, connections: List[int]) -> Dict[str, int]:
        """Categorize agents by their connectivity level."""
        categories = {'isolated': 0, 'low': 0, 'medium': 0, 'high': 0}
        
        for conn in connections:
            if conn == 0:
                categories['isolated'] += 1
            elif conn <= 2:
                categories['low'] += 1
            elif conn <= 5:
                categories['medium'] += 1
            else:
                categories['high'] += 1
        
        return categories

    def _identify_dominant_traits(self, traits_df: pd.DataFrame) -> Dict[str, str]:
        """Identify the dominant personality traits in the population."""
        trait_means = traits_df.mean()
        dominant = {}
        
        for trait, mean_value in trait_means.items():
            if mean_value > 0.6:
                dominant[trait] = 'high'
            elif mean_value < 0.4:
                dominant[trait] = 'low'
            else:
                dominant[trait] = 'moderate'
        
        return dominant

    def _generate_summary_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive summary statistics."""
        summary = {
            'total_agents': len(self.agents_data),
            'attributes_analyzed': len(self.attributes),
            'data_completeness': {}
        }
        
        # Calculate data completeness for each attribute - handle empty data
        if len(self.agents_data) > 0:
            for attr in self.attributes:
                non_null_count = sum(1 for agent in self.agents_data 
                                   if self._get_nested_attribute(agent, attr) is not None)
                summary['data_completeness'][attr] = non_null_count / len(self.agents_data)
        else:
            # No agents - set all completeness to 0
            for attr in self.attributes:
                summary['data_completeness'][attr] = 0.0
        
        return summary

    def export_analysis_report(self, filename: str = "agent_population_analysis.txt") -> None:
        """Export a comprehensive text report of the analysis."""
        with open(filename, 'w', encoding="utf-8", errors="replace") as f:
            f.write("AGENT POPULATION ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
    def export_analysis_report(self, filename: str = "agent_population_analysis.txt") -> None:
        """Export a comprehensive text report of the analysis."""
        with open(filename, 'w', encoding="utf-8", errors="replace") as f:
            f.write("AGENT POPULATION ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Summary statistics - always generate from current data
            summary = self._generate_summary_statistics()
            f.write(f"Total Agents Analyzed: {summary['total_agents']}\n")
            f.write(f"Attributes Analyzed: {summary['attributes_analyzed']}\n\n")
            
            f.write("Data Completeness:\n")
            for attr, completeness in summary['data_completeness'].items():
                f.write(f"  {attr}: {completeness:.2%}\n")
            f.write("\n")
            
            # Demographics
            if 'demographics' in self.analysis_results:
                demo = self.analysis_results['demographics']
                f.write("DEMOGRAPHICS\n")
                f.write("-" * 20 + "\n")
                
                if 'age_stats' in demo:
                    age_stats = demo['age_stats']
                    f.write(f"Age Statistics:\n")
                    f.write(f"  Mean: {age_stats['mean']:.1f} years\n")
                    f.write(f"  Median: {age_stats['median']:.1f} years\n")
                    f.write(f"  Range: {age_stats['range'][0]}-{age_stats['range'][1]} years\n\n")
                
                if 'occupation_diversity' in demo:
                    occ_div = demo['occupation_diversity']
                    f.write(f"Occupation Diversity:\n")
                    f.write(f"  Unique Occupations: {occ_div['unique_count']}\n")
                    f.write(f"  Diversity Index: {occ_div['diversity_index']:.3f}\n\n")
            
            # Behavioral patterns
            if 'behavioral_patterns' in self.analysis_results:
                behavioral = self.analysis_results['behavioral_patterns']
                f.write("BEHAVIORAL PATTERNS\n")
                f.write("-" * 20 + "\n")
                
                if 'activity_levels' in behavioral:
                    activity = behavioral['activity_levels']
                    f.write(f"Activity Levels:\n")
                    f.write(f"  Average Actions: {activity['actions_mean']:.1f}\n")
                    f.write(f"  Average Stimuli: {activity['stimuli_mean']:.1f}\n")
                    f.write(f"  Activity Ratio: {activity['activity_ratio']:.2f}\n\n")
        
        print(f"Analysis report exported to {filename}")

    def add_custom_analysis(self, name: str, analysis_func: Callable[[List[Dict]], Any]) -> None:
        """
        Add a custom analysis function that will be executed during profiling.
        
        Args:
            name: Name for the custom analysis
            analysis_func: Function that takes agent data and returns analysis results
        """
        if not hasattr(self, '_custom_analyses'):
            self._custom_analyses = {}
        
        self._custom_analyses[name] = analysis_func

    def compare_populations(self, other_agents: Union[List[dict], List[TinyPerson]], 
                          attributes: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Compare this population with another population.
        
        Args:
            other_agents: Another set of agents to compare with
            attributes: Specific attributes to compare (uses self.attributes if None)
            
        Returns:
            Comparison results
        """
        if attributes is None:
            attributes = self.attributes
        
        # Create temporary profiler for the other population
        other_profiler = Profiler(attributes)
        other_results = other_profiler.profile(other_agents, plot=False, advanced_analysis=True)
        
        comparison = {
            'population_sizes': {
                'current': len(self.agents_data),
                'comparison': len(other_profiler.agents_data)
            },
            'attribute_comparisons': {}
        }
        
        # Compare distributions for each attribute
        for attr in attributes:
            if (attr in self.attributes_distributions and 
                attr in other_profiler.attributes_distributions):
                
                current_dist = self.attributes_distributions[attr]
                other_dist = other_profiler.attributes_distributions[attr]
                
                # Statistical comparison (simplified)
                comparison['attribute_comparisons'][attr] = {
                    'current_unique_values': len(current_dist),
                    'comparison_unique_values': len(other_dist),
                    'current_top_3': current_dist.head(3).to_dict(),
                    'comparison_top_3': other_dist.head(3).to_dict()
                }
        
        return comparison