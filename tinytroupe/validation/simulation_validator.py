"""
Simulation experiment empirical validation mechanisms for TinyTroupe.

This module provides tools to validate simulation experiment results against empirical control data,
supporting both statistical hypothesis testing and semantic validation approaches.
This is distinct from LLM-based evaluations, focusing on data-driven validation
against known empirical benchmarks.
"""

from typing import Dict, List, Optional, Union, Any
import json
import csv
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

import pandas as pd

from tinytroupe.experimentation.statistical_tests import StatisticalTester
from tinytroupe.utils.semantics import compute_semantic_proximity

# TODO Work-in-Progress below

class SimulationExperimentDataset(BaseModel):
    """
    Represents a dataset from a simulation experiment or empirical study.
    
    This contains data that can be used for validation, including quantitative metrics 
    and qualitative agent justifications from simulation experiments or empirical studies.
    
    Supports both numeric and categorical data. Categorical data (strings) is automatically
    converted to ordinal values for statistical analysis while preserving the original
    categories for interpretation.
    
    Attributes:
        name: Optional name for the dataset
        description: Optional description of the dataset
        key_results: Map from result names to their values (numbers, proportions, booleans, strings, etc.)
        result_types: Map indicating whether each result is "aggregate" or "per_agent"
        data_types: Map indicating the data type for each result ("numeric", "categorical", "ordinal", "ranking", "count", "proportion", "binary")
        categorical_mappings: Internal mappings from categorical strings to ordinal values
        ordinal_mappings: Internal mappings for ordinal data with explicit ordering
        ranking_info: Information about ranking data (items being ranked, ranking direction)
        agent_names: Optional list of agent names (can be referenced by index in results)
        agent_justifications: List of justifications (with optional agent references)
        justification_summary: Optional summary of all agent justifications
        agent_attributes: Agent attributes for manual inspection only (not used in statistical comparisons)
    """
    name: Optional[str] = None
    description: Optional[str] = None
    key_results: Dict[str, Union[float, int, bool, str, List[Union[float, int, bool, str, None]], None]] = Field(default_factory=dict)
    result_types: Dict[str, str] = Field(default_factory=dict, description="Map from result name to 'aggregate' or 'per_agent'")
    data_types: Dict[str, str] = Field(default_factory=dict, description="Map indicating data type: 'numeric', 'categorical', 'ordinal', 'ranking', 'count', 'proportion', 'binary'")
    categorical_mappings: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Internal mappings from categorical strings to ordinal values")
    ordinal_mappings: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="Internal mappings for ordinal data with explicit ordering")
    ranking_info: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Information about ranking data (items, direction, etc.)")
    agent_names: Optional[List[Optional[str]]] = Field(None, description="Optional list of agent names for reference (can contain None for unnamed agents)")
    agent_justifications: List[Union[str, Dict[str, Union[str, int]]]] = Field(
        default_factory=list, 
        description="List of justifications as strings or dicts with optional 'agent_name'/'agent_index' and 'justification'"
    )
    justification_summary: Optional[str] = None
    agent_attributes: Dict[str, List[Union[str, None]]] = Field(
        default_factory=dict,
        description="Agent attributes loaded from CSV but not used in statistical comparisons (e.g., age, gender, etc.)"
    )

    class Config:
        """Pydantic configuration."""
        extra = "forbid"  # Prevent accidental extra fields
        validate_assignment = True  # Validate on assignment after creation
    
    def __init__(self, **data):
        """Initialize with automatic data processing."""
        super().__init__(**data)
        self._process_data_types()
    
    def _process_data_types(self):
        """
        Process different data types and convert them appropriately.
        
        Automatically detects and processes:
        - Categorical data (strings) -> ordinal mapping
        - Ordinal data (explicit ordering) -> validation of ordering
        - Ranking data (ranks/positions) -> validation and normalization
        - Count data (non-negative integers) -> validation
        - Proportion data (0-1 or 0-100) -> normalization to 0-1
        - Binary data (boolean/yes-no) -> conversion to 0/1
        """
        for metric_name, metric_data in self.key_results.items():
            data_type = self.data_types.get(metric_name, "auto")
            
            if data_type == "auto":
                # Auto-detect data type
                data_type = self._detect_data_type(metric_data)
                self.data_types[metric_name] = data_type
            
            # Process based on data type
            if data_type == "categorical":
                self._process_categorical_data_for_metric(metric_name, metric_data)
            elif data_type == "ordinal":
                self._process_ordinal_data_for_metric(metric_name, metric_data)
            elif data_type == "ranking":
                self._process_ranking_data_for_metric(metric_name, metric_data)
            elif data_type == "count":
                self._validate_count_data_for_metric(metric_name, metric_data)
            elif data_type == "proportion":
                self._process_proportion_data_for_metric(metric_name, metric_data)
            elif data_type == "binary":
                self._process_binary_data_for_metric(metric_name, metric_data)
            # "numeric" requires no special processing
    
    def _detect_data_type(self, data: Union[float, int, bool, str, List, None]) -> str:
        """Auto-detect the data type based on the data content."""
        if data is None:
            return "numeric"  # Default fallback
        
        # Handle single values
        if not isinstance(data, list):
            data = [data]
        
        # Filter out None values for analysis
        valid_data = [item for item in data if item is not None]
        if not valid_data:
            return "numeric"  # Default fallback
        
        # Check for string data (categorical) - but only if ALL non-None values are strings
        string_count = sum(1 for item in valid_data if isinstance(item, str))
        if string_count > 0:
            # If we have mixed types (strings + numbers), default to categorical for simplicity
            # since the string conversion will handle the mixed case
            return "categorical"
        
        # Check for boolean data
        if all(isinstance(item, bool) for item in valid_data):
            return "binary"
        
        # Check for numeric data
        numeric_data = [item for item in valid_data if isinstance(item, (int, float))]
        if len(numeric_data) != len(valid_data):
            return "numeric"  # Mixed types, default to numeric
        
        # Check for count data (non-negative integers, including whole number floats)
        def is_whole_number(x):
            """Check if a number is a whole number (either int or float with no decimal part)."""
            return isinstance(x, int) or (isinstance(x, float) and x.is_integer())
        
        if all(is_whole_number(item) and item >= 0 for item in numeric_data):
            # Convert floats to ints for ranking detection
            int_data = [int(item) for item in numeric_data]
            
            # For ranking detection, be more strict:
            # 1. Must have at least 3 data points
            # 2. Must have consecutive integers starting from 1
            # 3. Must have some repetition (indicating actual rankings rather than just sequence)
            sorted_data = sorted(set(int_data))
            min_val = min(sorted_data)
            max_val = max(sorted_data)
            
            # Only consider as ranking if:
            # - Starts from 1
            # - Has at least 2 different rank values
            # - Is consecutive (no gaps)
            # - Has repetition (more data points than unique values) - this is key for rankings
            if (len(int_data) >= 3 and  # At least 3 data points
                min_val == 1 and  # Starts from 1
                len(sorted_data) >= 2 and  # At least 2 different ranks
                max_val <= 10 and  # Reasonable upper limit for rankings
                sorted_data == list(range(1, max_val + 1)) and  # Consecutive
                len(int_data) > len(sorted_data)):  # Has repetition (essential for rankings)
                return "ranking"
            
            # Otherwise, it's count data
            return "count"
        
        # Check for proportion data (0-1 range) - only for floats
        if all(isinstance(item, (int, float)) and 0 <= item <= 1 for item in numeric_data):
            # If all values are 0 or 1 integers, it's likely binary
            if all(isinstance(item, int) and item in [0, 1] for item in numeric_data):
                return "binary"
            return "proportion"
        
        # Default to numeric
        return "numeric"
    
    def _process_categorical_data_for_metric(self, metric_name: str, metric_data):
        """Process categorical data for a specific metric."""
        if self._is_categorical_data(metric_data):
            # Extract all unique categories
            categories = self._extract_categories(metric_data)
            
            if categories:
                # Create sorted categorical mapping for consistency
                sorted_categories = sorted(categories)
                categorical_mapping = {category: idx for idx, category in enumerate(sorted_categories)}
                self.categorical_mappings[metric_name] = categorical_mapping
                
                # Convert string data to ordinal values
                self.key_results[metric_name] = self._convert_to_ordinal(metric_data, categorical_mapping)
    
    def _process_ordinal_data_for_metric(self, metric_name: str, metric_data):
        """Process ordinal data for a specific metric."""
        # For ordinal data, we expect either:
        # 1. Numeric values that represent ordinal levels (e.g., 1, 2, 3, 4, 5 for Likert)
        # 2. String values that need explicit ordering (e.g., "Poor", "Fair", "Good", "Excellent")
        
        if self._is_categorical_data(metric_data):
            # String ordinal data - need explicit ordering
            categories = self._extract_categories(metric_data)
            if categories:
                # For string ordinal data, we need to define a meaningful order
                # This could be enhanced to accept explicit ordering from user
                sorted_categories = self._order_ordinal_categories(list(categories))
                ordinal_mapping = {category: idx for idx, category in enumerate(sorted_categories)}
                self.ordinal_mappings[metric_name] = ordinal_mapping
                
                # Convert to ordinal values
                self.key_results[metric_name] = self._convert_to_ordinal(metric_data, ordinal_mapping)
        else:
            # Numeric ordinal data - validate that values are reasonable
            self._validate_ordinal_numeric_data(metric_name, metric_data)
    
    def _process_ranking_data_for_metric(self, metric_name: str, metric_data):
        """Process ranking data for a specific metric."""
        # Ranking data should be integers representing positions (1, 2, 3, etc.)
        valid_data = self._get_valid_numeric_data(metric_data)
        
        if valid_data:
            unique_ranks = sorted(set(valid_data))
            min_rank = min(unique_ranks)
            max_rank = max(unique_ranks)
            
            # Check if ranking_info already exists (e.g., from ordinal processing)
            existing_info = self.ranking_info.get(metric_name, {})
            
            # Store ranking information, preserving existing keys
            ranking_info = {
                "min_rank": min_rank,
                "max_rank": max_rank,
                "num_ranks": len(unique_ranks),
                "rank_values": unique_ranks,
                "direction": existing_info.get("direction", "ascending")  # Preserve existing direction or default
            }
            
            # Preserve any additional keys from existing ranking info (e.g., ordinal-specific data)
            ranking_info.update({k: v for k, v in existing_info.items() 
                               if k not in ranking_info})
            
            self.ranking_info[metric_name] = ranking_info
            
            # Validate ranking data
            self._validate_ranking_data(metric_name, metric_data)
    
    def _process_proportion_data_for_metric(self, metric_name: str, metric_data):
        """Process proportion data for a specific metric."""
        # Normalize proportion data to 0-1 range if needed
        if isinstance(metric_data, list):
            normalized_data = []
            for item in metric_data:
                if item is None:
                    normalized_data.append(None)
                elif isinstance(item, (int, float)):
                    # If value > 1, assume it's percentage (0-100), convert to proportion
                    normalized_data.append(item / 100.0 if item > 1 else item)
                else:
                    normalized_data.append(item)  # Keep as-is
            self.key_results[metric_name] = normalized_data
        elif isinstance(metric_data, (int, float)) and metric_data > 1:
            # Single percentage value
            self.key_results[metric_name] = metric_data / 100.0
    
    def _process_binary_data_for_metric(self, metric_name: str, metric_data):
        """Process binary data for a specific metric."""
        # Convert boolean/string binary data to 0/1
        if isinstance(metric_data, list):
            binary_data = []
            for item in metric_data:
                if item is None:
                    binary_data.append(None)
                else:
                    binary_data.append(self._convert_to_binary(item))
            self.key_results[metric_name] = binary_data
        elif metric_data is not None:
            self.key_results[metric_name] = self._convert_to_binary(metric_data)
    
    def _validate_count_data_for_metric(self, metric_name: str, metric_data):
        """Validate count data for a specific metric."""
        valid_data = self._get_valid_numeric_data(metric_data)
        
        # Check that all values are non-negative integers (including whole number floats)
        for value in valid_data:
            # Accept both integers and whole number floats
            is_whole_number = isinstance(value, int) or (isinstance(value, float) and value.is_integer())
            if not is_whole_number or value < 0:
                raise ValueError(f"Count data for metric '{metric_name}' must be non-negative integers, found: {value}")
    
    def _order_ordinal_categories(self, categories: List[str]) -> List[str]:
        """Order ordinal categories in a meaningful way."""
        # Common ordinal patterns for automatic ordering
        likert_patterns = {
            "strongly disagree": 1, "disagree": 2, "neutral": 3, "agree": 4, "strongly agree": 5,
            "very poor": 1, "poor": 2, "fair": 3, "good": 4, "very good": 5, "excellent": 6,
            "never": 1, "rarely": 2, "sometimes": 3, "often": 4, "always": 5,
            "very low": 1, "low": 2, "medium": 3, "high": 4, "very high": 5,
            "terrible": 1, "bad": 2, "okay": 3, "good": 4, "great": 5, "amazing": 6
        }
        
        # Try to match patterns
        category_scores = {}
        for category in categories:
            normalized_cat = self._normalize_category(category)
            if normalized_cat in likert_patterns:
                category_scores[category] = likert_patterns[normalized_cat]
        
        # If we found matches for all categories, use that ordering
        if len(category_scores) == len(categories):
            return sorted(categories, key=lambda x: category_scores[x])
        
        # Otherwise, fall back to alphabetical ordering with a warning
        return sorted(categories)
    
    def _validate_ordinal_numeric_data(self, metric_name: str, metric_data):
        """Validate numeric ordinal data."""
        valid_data = self._get_valid_numeric_data(metric_data)
        
        if valid_data:
            unique_values = sorted(set(valid_data))
            # Check if values are reasonable for ordinal data (consecutive or at least ordered)
            if len(unique_values) < 2:
                return  # Single value is fine
            
            # Store ordinal information
            self.ordinal_mappings[metric_name] = {
                "min_value": min(unique_values),
                "max_value": max(unique_values),
                "unique_values": unique_values,
                "num_levels": len(unique_values)
            }
    
    def _validate_ranking_data(self, metric_name: str, metric_data):
        """Validate ranking data structure."""
        valid_data = self._get_valid_numeric_data(metric_data)
        
        if not valid_data:
            return
        
        unique_ranks = set(valid_data)
        min_rank = min(unique_ranks)
        max_rank = max(unique_ranks)
        
        # Check for reasonable ranking structure
        if min_rank < 1:
            raise ValueError(f"Ranking data for metric '{metric_name}' should start from 1, found minimum: {min_rank}")
        
        # Check for gaps in ranking (warning, not error)
        expected_ranks = set(range(min_rank, max_rank + 1))
        missing_ranks = expected_ranks - unique_ranks
        if missing_ranks:
            # This is often okay in ranking data (tied ranks, incomplete rankings)
            pass
    
    def _get_valid_numeric_data(self, data) -> List[Union[int, float]]:
        """Get valid numeric data from a metric, handling both single values and lists."""
        if data is None:
            return []
        
        if not isinstance(data, list):
            data = [data]
        
        return [item for item in data if item is not None and isinstance(item, (int, float))]
    
    def _convert_to_binary(self, value) -> int:
        """Convert various binary representations to 0 or 1."""
        if isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, str):
            normalized = value.lower().strip()
            true_values = {"true", "yes", "y", "1", "on", "success", "positive"}
            false_values = {"false", "no", "n", "0", "off", "failure", "negative"}
            
            if normalized in true_values:
                return 1
            elif normalized in false_values:
                return 0
            else:
                raise ValueError(f"Cannot convert string '{value}' to binary")
        elif isinstance(value, (int, float)):
            return 1 if value != 0 else 0
        else:
            raise ValueError(f"Cannot convert {type(value)} to binary")
    
    def _process_categorical_data(self):
        """
        Legacy method for backward compatibility.
        Process categorical string data by converting to ordinal values.
        """
        for metric_name, metric_data in self.key_results.items():
            if metric_name not in self.data_types:  # Only process if data type not explicitly set
                if self._is_categorical_data(metric_data):
                    self.data_types[metric_name] = "categorical"
                    self._process_categorical_data_for_metric(metric_name, metric_data)
    
    def _is_categorical_data(self, data: Union[float, int, bool, str, List, None]) -> bool:
        """Check if data contains categorical (string) values."""
        if isinstance(data, str):
            return True
        elif isinstance(data, list):
            return any(isinstance(item, str) for item in data if item is not None)
        return False
    
    def _extract_categories(self, data: Union[float, int, bool, str, List, None]) -> set:
        """Extract unique string categories from data."""
        categories = set()
        
        if isinstance(data, str):
            categories.add(self._normalize_category(data))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    categories.add(self._normalize_category(item))
        
        return categories
    
    def _normalize_category(self, category: str) -> str:
        """Normalize categorical string (lowercase, strip whitespace)."""
        return category.lower().strip()
    
    def _convert_to_ordinal(self, data: Union[str, List], mapping: Dict[str, int]) -> Union[int, List[Union[int, None]]]:
        """Convert categorical data to ordinal values using the mapping."""
        if isinstance(data, str):
            normalized = self._normalize_category(data)
            return mapping.get(normalized, 0)  # Default to 0 if not found
        elif isinstance(data, list):
            converted = []
            for item in data:
                if isinstance(item, str):
                    normalized = self._normalize_category(item)
                    converted.append(mapping.get(normalized, 0))
                elif item is None:
                    converted.append(None)  # Preserve None values
                else:
                    converted.append(item)  # Keep numeric values as-is
            return converted
        else:
            return data
    
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
    
    def get_categorical_values(self, metric_name: str) -> Optional[List[str]]:
        """Get the original categorical values for a metric, if it was categorical."""
        if metric_name in self.categorical_mappings:
            # Return categories sorted by their ordinal values
            mapping = self.categorical_mappings[metric_name]
            return [category for category, _ in sorted(mapping.items(), key=lambda x: x[1])]
        elif metric_name in self.ordinal_mappings and isinstance(self.ordinal_mappings[metric_name], dict):
            # Handle string-based ordinal data
            mapping = self.ordinal_mappings[metric_name]
            if all(isinstance(k, str) for k in mapping.keys()):
                return [category for category, _ in sorted(mapping.items(), key=lambda x: x[1])]
        return None
    
    def convert_ordinal_to_categorical(self, metric_name: str, ordinal_value: Union[int, float]) -> Optional[str]:
        """Convert an ordinal value back to its original categorical string."""
        # Check categorical mappings first
        if metric_name in self.categorical_mappings:
            mapping = self.categorical_mappings[metric_name]
            # Reverse lookup: find category with this ordinal value
            for category, value in mapping.items():
                if value == int(ordinal_value):
                    return category
        
        # Check ordinal mappings for string-based ordinal data
        elif metric_name in self.ordinal_mappings:
            mapping = self.ordinal_mappings[metric_name]
            if isinstance(mapping, dict) and all(isinstance(k, str) for k in mapping.keys()):
                for category, value in mapping.items():
                    if value == int(ordinal_value):
                        return category
        
        return None
    
    def get_data_type_info(self, metric_name: str) -> Dict[str, Any]:
        """Get comprehensive information about a metric's data type."""
        data_type = self.data_types.get(metric_name, "numeric")
        info = {
            "data_type": data_type,
            "result_type": self.result_types.get(metric_name, "unknown")
        }
        
        if data_type == "categorical" and metric_name in self.categorical_mappings:
            info["categories"] = self.get_categorical_values(metric_name)
            info["category_mapping"] = self.categorical_mappings[metric_name].copy()
        
        elif data_type == "ordinal":
            if metric_name in self.ordinal_mappings:
                mapping = self.ordinal_mappings[metric_name]
                if isinstance(mapping, dict):
                    # Check if this is a string-to-number mapping (categorical ordinal)
                    # vs info dict (numeric ordinal)
                    if "min_value" in mapping or "max_value" in mapping:
                        # Numeric ordinal info
                        info["ordinal_info"] = mapping.copy()
                    elif all(isinstance(k, str) for k in mapping.keys()) and all(isinstance(v, int) for v in mapping.values()):
                        # String-based ordinal - safely sort by values
                        try:
                            info["ordinal_categories"] = [cat for cat, _ in sorted(mapping.items(), key=lambda x: x[1])]
                            info["ordinal_mapping"] = mapping.copy()
                        except TypeError:
                            # Fallback if sorting fails
                            info["ordinal_categories"] = list(mapping.keys())
                            info["ordinal_mapping"] = mapping.copy()
                    else:
                        # Unknown ordinal format, treat as info
                        info["ordinal_info"] = mapping.copy()
        
        elif data_type == "ranking" and metric_name in self.ranking_info:
            info["ranking_info"] = self.ranking_info[metric_name].copy()
        
        return info
    
    def get_metric_summary(self, metric_name: str) -> Dict[str, Any]:
        """Get a comprehensive summary of a metric including data type information."""
        summary = {
            "metric_name": metric_name,
            "result_type": self.result_types.get(metric_name, "unknown"),
            "data_type": self.data_types.get(metric_name, "numeric"),
        }
        
        # Add legacy categorical flag for backward compatibility
        summary["is_categorical"] = (metric_name in self.categorical_mappings or 
                                   (metric_name in self.ordinal_mappings and 
                                    isinstance(self.ordinal_mappings[metric_name], dict) and
                                    all(isinstance(k, str) for k in self.ordinal_mappings[metric_name].keys())))
        
        if metric_name in self.key_results:
            data = self.key_results[metric_name]
            summary["data_type_name"] = type(data).__name__
            
            if isinstance(data, list):
                valid_data = [x for x in data if x is not None]
                summary["total_values"] = len(data)
                summary["valid_values"] = len(valid_data)
                summary["missing_values"] = len(data) - len(valid_data)
                
                if valid_data:
                    summary["min_value"] = min(valid_data)
                    summary["max_value"] = max(valid_data)
            
            # Add data type specific information
            data_type_info = self.get_data_type_info(metric_name)
            summary.update(data_type_info)
            
            # Add distribution information for per-agent data
            if isinstance(data, list) and self.result_types.get(metric_name) == "per_agent":
                data_type = summary["data_type"]
                
                if data_type in ["categorical", "ordinal"] and summary.get("is_categorical"):
                    # Category distribution
                    category_counts = {}
                    for value in data:
                        if value is not None:
                            category = self.convert_ordinal_to_categorical(metric_name, value)
                            if category:
                                category_counts[category] = category_counts.get(category, 0) + 1
                    summary["category_distribution"] = category_counts
                
                elif data_type == "ranking":
                    # Ranking distribution
                    rank_counts = {}
                    for value in data:
                        if value is not None:
                            rank_counts[value] = rank_counts.get(value, 0) + 1
                    summary["rank_distribution"] = rank_counts
                
                elif data_type == "binary":
                    # Binary distribution
                    true_count = sum(1 for x in data if x == 1)
                    false_count = sum(1 for x in data if x == 0)
                    summary["binary_distribution"] = {"true": true_count, "false": false_count}
        
        return summary
    
    def is_categorical_metric(self, metric_name: str) -> bool:
        """Check if a metric contains categorical data (including string-based ordinal)."""
        return (metric_name in self.categorical_mappings or 
                (metric_name in self.ordinal_mappings and 
                 isinstance(self.ordinal_mappings[metric_name], dict) and
                 all(isinstance(k, str) for k in self.ordinal_mappings[metric_name].keys())))


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
                 statistical_test_type: str = "welch_t_test",
                 significance_level: float = 0.05,
                 output_format: str = "values") -> Union[SimulationExperimentEmpiricalValidationResult, str]:
        """
        Validate a simulation experiment dataset against an empirical control dataset.
        
        Args:
            control: The control/empirical reference dataset
            treatment: The treatment/simulation experiment dataset to validate
            validation_types: List of validation types to perform ("statistical", "semantic")
            statistical_test_type: Type of statistical test ("welch_t_test", "ks_test", "mann_whitney", etc.)
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
                control, treatment, significance_level, statistical_test_type
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
            return self._generate_markdown_report(result, control, treatment)
        else:
            return result

    def _perform_statistical_validation(self, 
                                      control: SimulationExperimentDataset, 
                                      treatment: SimulationExperimentDataset,
                                      significance_level: float,
                                      test_type: str = "welch_t_test") -> Dict[str, Any]:
        """
        Perform statistical hypothesis testing on simulation experiment key results.
        
        Args:
            control: Control dataset
            treatment: Treatment dataset  
            significance_level: Alpha level for statistical tests
            test_type: Type of statistical test to perform
        """
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
                test_type=test_type,
                alpha=significance_level
            )

            return {
                "common_metrics": list(common_metrics),
                "test_results": test_results,
                "test_type": test_type,
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
                        proximity_score = compute_semantic_proximity(
                            control_text, 
                            treatment_text,
                            context="Comparing agent justifications from simulation experiments"
                        )
                        
                        # Handle case where LLM call fails or returns invalid data
                        if proximity_score is None or not isinstance(proximity_score, (int, float)):
                            raise ValueError("Invalid semantic proximity score")

                        # Get agent references (names or indices)
                        control_agent_ref = control.get_justification_agent_reference(control_just) or f"Agent_{i}"
                        treatment_agent_ref = treatment.get_justification_agent_reference(treatment_just) or f"Agent_{j}"
                        
                        comparison = {
                            "control_agent": control_agent_ref,
                            "treatment_agent": treatment_agent_ref,
                            "proximity_score": proximity_score,
                            "justification": f"Semantic proximity score: {proximity_score:.3f}"
                        }
                        
                        results["individual_comparisons"].append(comparison)
                        proximities.append(proximity_score)
            
            if proximities:
                results["average_proximity"] = sum(proximities) / len(proximities)

        # Compare summary justifications if available
        if control.justification_summary and treatment.justification_summary:
            summary_proximity_score = compute_semantic_proximity(
                control.justification_summary,
                treatment.justification_summary,
                context="Comparing summary justifications from simulation experiments"
            )
            
            # Handle case where LLM call fails or returns invalid data
            if summary_proximity_score is None or not isinstance(summary_proximity_score, (int, float)):
                summary_proximity_score = 0.5  # Default neutral score
            
            results["summary_comparison"] = {
                "proximity_score": summary_proximity_score,
                "justification": f"Summary semantic proximity score: {summary_proximity_score:.3f}"
            }

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
                # For very small effect sizes (< 0.1), give even higher scores
                similarity_scores = []
                for es in effect_sizes:
                    abs_es = abs(es)
                    if abs_es < 0.1:  # Very small effect size
                        similarity_scores.append(0.95 + 0.05 * (1.0 / (1.0 + abs_es)))
                    else:
                        similarity_scores.append(1.0 / (1.0 + abs_es))
                
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
                semantic_score = sum(semantic_scores) / len(semantic_scores)
                scores.append(semantic_score)

        # If we have both statistical and semantic scores, and the statistical score is very high (>0.9)
        # indicating statistically equivalent data, weight the statistical component more heavily
        if len(scores) == 2 and scores[0] > 0.9:  # First score is statistical
            # Weight statistical component at 70%, semantic at 30% for equivalent data
            return 0.7 * scores[0] + 0.3 * scores[1]
        
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

    def _generate_markdown_report(self, result: SimulationExperimentEmpiricalValidationResult, 
                                 control: SimulationExperimentDataset = None, 
                                 treatment: SimulationExperimentDataset = None) -> str:
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

        # Add data type information if available
        if control or treatment:
            data_type_info = self._generate_data_type_info_section(control, treatment)
            if data_type_info:
                report += data_type_info

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
                            elif "ks_statistic" in metric_result:
                                statistic = metric_result["ks_statistic"]
                            
                            status = "✅ Significant" if significant else "❌ Not Significant"
                            
                            report += f"- **{test_type}:** {status}\n"
                            report += f"  - p-value: {p_value}\n"
                            report += f"  - statistic: {statistic}\n"
                            if effect_size is not None:
                                effect_interpretation = self._interpret_effect_size(abs(effect_size), test_type)
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

    def _generate_data_type_info_section(self, control: SimulationExperimentDataset, 
                                       treatment: SimulationExperimentDataset) -> str:
        """Generate comprehensive data type information section for the report."""
        all_metrics = set()
        
        # Collect all metrics from both datasets
        if control:
            all_metrics.update(control.key_results.keys())
        if treatment:
            all_metrics.update(treatment.key_results.keys())
        
        if not all_metrics:
            return ""
        
        # Group metrics by data type
        data_type_groups = {}
        for metric in all_metrics:
            for dataset_name, dataset in [("control", control), ("treatment", treatment)]:
                if dataset and metric in dataset.data_types:
                    data_type = dataset.data_types[metric]
                    if data_type not in data_type_groups:
                        data_type_groups[data_type] = set()
                    data_type_groups[data_type].add(metric)
                    break  # Use first available data type
        
        if not data_type_groups:
            return ""
        
        report = "## Data Type Information\n\n"
        
        for data_type, metrics in sorted(data_type_groups.items()):
            if not metrics:
                continue
                
            report += f"### {data_type.title()} Data\n\n"
            
            if data_type == "categorical":
                report += "String categories converted to ordinal values for statistical analysis.\n\n"
            elif data_type == "ordinal":
                report += "Ordered categories or levels with meaningful ranking.\n\n"
            elif data_type == "ranking":
                report += "Rank positions (1st, 2nd, 3rd, etc.) indicating preference or order.\n\n"
            elif data_type == "count":
                report += "Non-negative integer counts (frequencies, occurrences, etc.).\n\n"
            elif data_type == "proportion":
                report += "Values between 0-1 representing proportions or percentages.\n\n"
            elif data_type == "binary":
                report += "Binary outcomes converted to 0/1 for analysis.\n\n"
            elif data_type == "numeric":
                report += "Continuous numeric values.\n\n"
            
            for metric in sorted(metrics):
                report += f"#### {metric}\n\n"
                
                # Show information from both datasets
                for dataset_name, dataset in [("Control", control), ("Treatment", treatment)]:
                    if not dataset or metric not in dataset.key_results:
                        continue
                    
                    data_type_info = dataset.get_data_type_info(metric)
                    summary = dataset.get_metric_summary(metric)
                    
                    report += f"**{dataset_name}:**\n"
                    
                    if data_type == "categorical":
                        if "categories" in data_type_info:
                            categories = data_type_info["categories"]
                            mapping = data_type_info.get("category_mapping", {})
                            
                            report += f"- Categories: {', '.join(f'`{cat}`' for cat in categories)}\n"
                            report += f"- Ordinal mapping: {mapping}\n"
                            
                            if "category_distribution" in summary:
                                distribution = summary["category_distribution"]
                                total = sum(distribution.values())
                                report += "- Distribution: "
                                dist_items = []
                                for cat in categories:
                                    count = distribution.get(cat, 0)
                                    pct = (count / total * 100) if total > 0 else 0
                                    dist_items.append(f"`{cat}`: {count} ({pct:.1f}%)")
                                report += ", ".join(dist_items) + "\n"
                    
                    elif data_type == "ordinal":
                        if "ordinal_categories" in data_type_info:
                            # String-based ordinal
                            categories = data_type_info["ordinal_categories"]
                            mapping = data_type_info.get("ordinal_mapping", {})
                            report += f"- Ordered categories: {' < '.join(f'`{cat}`' for cat in categories)}\n"
                            report += f"- Ordinal mapping: {mapping}\n"
                        elif "ordinal_info" in data_type_info:
                            # Numeric ordinal
                            info = data_type_info["ordinal_info"]
                            report += f"- Value range: {info.get('min_value')} to {info.get('max_value')}\n"
                            report += f"- Unique levels: {info.get('num_levels')} ({info.get('unique_values')})\n"
                    
                    elif data_type == "ranking":
                        if "ranking_info" in data_type_info:
                            info = data_type_info["ranking_info"]
                            report += f"- Rank range: {info.get('min_rank')} to {info.get('max_rank')}\n"
                            report += f"- Number of ranks: {info.get('num_ranks')}\n"
                            report += f"- Direction: {info.get('direction', 'ascending')} (1 = best)\n"
                            
                            if "rank_distribution" in summary:
                                distribution = summary["rank_distribution"]
                                report += "- Distribution: "
                                rank_items = []
                                for rank in sorted(distribution.keys()):
                                    count = distribution[rank]
                                    rank_items.append(f"Rank {rank}: {count}")
                                report += ", ".join(rank_items) + "\n"
                    
                    elif data_type == "binary":
                        if "binary_distribution" in summary:
                            distribution = summary["binary_distribution"]
                            true_count = distribution.get("true", 0)
                            false_count = distribution.get("false", 0)
                            total = true_count + false_count
                            if total > 0:
                                true_pct = (true_count / total * 100)
                                false_pct = (false_count / total * 100)
                                report += f"- Distribution: True: {true_count} ({true_pct:.1f}%), False: {false_count} ({false_pct:.1f}%)\n"
                    
                    elif data_type in ["count", "proportion", "numeric"]:
                        if "min_value" in summary and "max_value" in summary:
                            report += f"- Range: {summary['min_value']} to {summary['max_value']}\n"
                        if "valid_values" in summary:
                            report += f"- Valid values: {summary['valid_values']}/{summary.get('total_values', 'N/A')}\n"
                    
                    report += "\n"
        
        return report
    
    def _generate_categorical_info_section(self, control: SimulationExperimentDataset, 
                                         treatment: SimulationExperimentDataset) -> str:
        """
        Generate categorical data information section for the report.
        This is kept for backward compatibility and now calls the more comprehensive data type method.
        """
        return self._generate_data_type_info_section(control, treatment)

    @classmethod
    def read_empirical_data_from_csv(cls,
                                   file_path: Union[str, Path],
                                   experimental_data_type: str = "single_value_per_agent",
                                   agent_id_column: Optional[str] = None,
                                   agent_comments_column: Optional[str] = None,
                                   agent_attributes_columns: Optional[List[str]] = None,
                                   value_column: Optional[str] = None,
                                   ranking_columns: Optional[List[str]] = None,
                                   ordinal_ranking_column: Optional[str] = None,
                                   ordinal_ranking_separator: str = "-",
                                   ordinal_ranking_options: Optional[List[str]] = None,
                                   dataset_name: Optional[str] = None,
                                   dataset_description: Optional[str] = None,
                                   encoding: str = "utf-8") -> 'SimulationExperimentDataset':
        """
        Read empirical data from a CSV file and convert it to a SimulationExperimentDataset.
        
        Args:
            file_path: Path to the CSV file
            experimental_data_type: Type of experimental data:
                - "single_value_per_agent": Each agent has a single value (e.g., score, rating)
                - "ranking_per_agent": Each agent provides rankings for multiple items (separate columns)
                - "ordinal_ranking_per_agent": Each agent provides ordinal ranking in single column with separator
            agent_id_column: Column name containing agent identifiers (optional)
            agent_comments_column: Column name containing agent comments/explanations (optional)
            agent_attributes_columns: List of column names containing agent attributes (age, gender, etc.)
            value_column: Column name containing the main value for single_value_per_agent mode
            ranking_columns: List of column names containing rankings for ranking_per_agent mode
            ordinal_ranking_column: Column name containing ordinal rankings for ordinal_ranking_per_agent mode
            ordinal_ranking_separator: Separator used in ordinal ranking strings (default: "-")
            ordinal_ranking_options: List of options being ranked (if None, auto-detected from data)
            dataset_name: Optional name for the dataset
            dataset_description: Optional description of the dataset
            encoding: File encoding (default: utf-8)
            
        Returns:
            SimulationExperimentDataset object populated with the CSV data
            
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            ValueError: If required columns are missing or data format is invalid
            pandas.errors.EmptyDataError: If the CSV file is empty
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        try:
            # Read CSV with UTF-8 encoding and error handling
            df = pd.read_csv(file_path, encoding=encoding, encoding_errors='replace')
        except pd.errors.EmptyDataError:
            raise pd.errors.EmptyDataError(f"CSV file is empty: {file_path}")
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to read CSV file with encoding {encoding}: {e}")
        
        if df.empty:
            raise ValueError(f"CSV file contains no data: {file_path}")
        
        # Use common processing method
        return cls._process_empirical_data_from_dataframe(
            df=df,
            experimental_data_type=experimental_data_type,
            agent_id_column=agent_id_column,
            agent_comments_column=agent_comments_column,
            agent_attributes_columns=agent_attributes_columns,
            value_column=value_column,
            ranking_columns=ranking_columns,
            ordinal_ranking_column=ordinal_ranking_column,
            ordinal_ranking_separator=ordinal_ranking_separator,
            ordinal_ranking_options=ordinal_ranking_options,
            dataset_name=dataset_name or f"Empirical_Data_{file_path.stem}",
            dataset_description=dataset_description or f"Empirical data loaded from {file_path.name}"
        )
    
    @classmethod
    def read_empirical_data_from_dataframe(cls,
                                         df: pd.DataFrame,
                                         experimental_data_type: str = "single_value_per_agent",
                                         agent_id_column: Optional[str] = None,
                                         agent_comments_column: Optional[str] = None,
                                         agent_attributes_columns: Optional[List[str]] = None,
                                         value_column: Optional[str] = None,
                                         ranking_columns: Optional[List[str]] = None,
                                         ordinal_ranking_column: Optional[str] = None,
                                         ordinal_ranking_separator: str = "-",
                                         ordinal_ranking_options: Optional[List[str]] = None,
                                         dataset_name: Optional[str] = None,
                                         dataset_description: Optional[str] = None) -> 'SimulationExperimentDataset':
        """
        Read empirical data from a pandas DataFrame and convert it to a SimulationExperimentDataset.
        
        This method provides the same functionality as read_empirical_data_from_csv but accepts
        a pandas DataFrame directly, eliminating the need to save DataFrames to CSV files first.
        
        Args:
            df: The pandas DataFrame containing the empirical data
            experimental_data_type: Type of experimental data:
                - "single_value_per_agent": Each agent has a single value (e.g., score, rating)
                - "ranking_per_agent": Each agent provides rankings for multiple items (separate columns)
                - "ordinal_ranking_per_agent": Each agent provides ordinal ranking in single column with separator
            agent_id_column: Column name containing agent identifiers (optional)
            agent_comments_column: Column name containing agent comments/explanations (optional)
            agent_attributes_columns: List of column names containing agent attributes (age, gender, etc.)
            value_column: Column name containing the main value for single_value_per_agent mode
            ranking_columns: List of column names containing rankings for ranking_per_agent mode
            ordinal_ranking_column: Column name containing ordinal rankings for ordinal_ranking_per_agent mode
            ordinal_ranking_separator: Separator used in ordinal ranking strings (default: "-")
            ordinal_ranking_options: List of options being ranked (if None, auto-detected from data)
            dataset_name: Optional name for the dataset
            dataset_description: Optional description of the dataset
            
        Returns:
            SimulationExperimentDataset object populated with the DataFrame data
            
        Raises:
            ValueError: If required columns are missing or data format is invalid
            TypeError: If df is not a pandas DataFrame
        """
        # Validate input
        if not isinstance(df, pd.DataFrame):
            raise TypeError(f"Expected pandas DataFrame, got {type(df)}")
        
        if df.empty:
            raise ValueError("DataFrame contains no data")
        
        # Use common processing method
        return cls._process_empirical_data_from_dataframe(
            df=df,
            experimental_data_type=experimental_data_type,
            agent_id_column=agent_id_column,
            agent_comments_column=agent_comments_column,
            agent_attributes_columns=agent_attributes_columns,
            value_column=value_column,
            ranking_columns=ranking_columns,
            ordinal_ranking_column=ordinal_ranking_column,
            ordinal_ranking_separator=ordinal_ranking_separator,
            ordinal_ranking_options=ordinal_ranking_options,
            dataset_name=dataset_name or "Empirical_Data_from_DataFrame",
            dataset_description=dataset_description or "Empirical data loaded from pandas DataFrame"
        )
    
    @classmethod
    def _process_empirical_data_from_dataframe(cls,
                                             df: pd.DataFrame,
                                             experimental_data_type: str,
                                             agent_id_column: Optional[str],
                                             agent_comments_column: Optional[str],
                                             agent_attributes_columns: Optional[List[str]],
                                             value_column: Optional[str],
                                             ranking_columns: Optional[List[str]],
                                             ordinal_ranking_column: Optional[str],
                                             ordinal_ranking_separator: str,
                                             ordinal_ranking_options: Optional[List[str]],
                                             dataset_name: str,
                                             dataset_description: str) -> 'SimulationExperimentDataset':
        """
        Common processing method for both CSV and DataFrame inputs.
        
        This method contains the shared logic for processing empirical data regardless of input source.
        """
        # Initialize dataset
        dataset = SimulationExperimentDataset(
            name=dataset_name,
            description=dataset_description
        )
        
        # Process based on experimental data type
        if experimental_data_type == "single_value_per_agent":
            cls._process_single_value_per_agent_csv(df, dataset, value_column, 
                                                  agent_id_column, agent_comments_column,
                                                  agent_attributes_columns)
        elif experimental_data_type == "ranking_per_agent":
            cls._process_ranking_per_agent_csv(df, dataset, ranking_columns,
                                             agent_id_column, agent_comments_column,
                                             agent_attributes_columns)
        elif experimental_data_type == "ordinal_ranking_per_agent":
            cls._process_ordinal_ranking_per_agent_csv(df, dataset, ordinal_ranking_column,
                                                     ordinal_ranking_separator, ordinal_ranking_options,
                                                     agent_id_column, agent_comments_column,
                                                     agent_attributes_columns)
        else:
            raise ValueError(f"Unsupported experimental_data_type: {experimental_data_type}. "
                           f"Supported types: 'single_value_per_agent', 'ranking_per_agent', 'ordinal_ranking_per_agent'")
        
        # Process data types after all data is loaded
        dataset._process_data_types()
        
        return dataset
    
    @classmethod
    def _process_single_value_per_agent_csv(cls,
                                          df: pd.DataFrame,
                                          dataset: 'SimulationExperimentDataset',
                                          value_column: Optional[str],
                                          agent_id_column: Optional[str],
                                          agent_comments_column: Optional[str],
                                          agent_attributes_columns: Optional[List[str]]):
        """Process CSV data for single value per agent experiments."""
        
        # Auto-detect value column if not specified
        if value_column is None:
            # Look for common column names that might contain the main value
            value_candidates = [col for col in df.columns if any(keyword in col.lower() 
                               for keyword in ['vote', 'score', 'rating', 'value', 'response', 'answer'])]
            
            if len(value_candidates) == 1:
                value_column = value_candidates[0]
            elif len(value_candidates) > 1:
                # Prefer shorter, more specific names
                value_column = min(value_candidates, key=len)
            else:
                # Fall back to first numeric column
                numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                if numeric_cols:
                    value_column = numeric_cols[0]
                else:
                    raise ValueError("No suitable value column found. Please specify value_column parameter.")
        
        if value_column not in df.columns:
            raise ValueError(f"Value column '{value_column}' not found in CSV. Available columns: {list(df.columns)}")
        
        # Extract main values (handling mixed types)
        values = []
        for val in df[value_column]:
            if pd.isna(val):
                values.append(None)
            else:
                # Try to convert to numeric if possible, otherwise keep as string
                try:
                    if isinstance(val, str) and val.strip().isdigit():
                        values.append(int(val.strip()))
                    elif isinstance(val, str):
                        try:
                            float_val = float(val.strip())
                            # If it's a whole number, convert to int
                            values.append(int(float_val) if float_val.is_integer() else float_val)
                        except ValueError:
                            values.append(val.strip())
                    else:
                        values.append(val)
                except (AttributeError, ValueError):
                    values.append(val)
        
        # Store the main experimental result
        dataset.key_results[value_column] = values
        dataset.result_types[value_column] = "per_agent"
        
        # Process agent IDs/names
        agent_names = []
        if agent_id_column and agent_id_column in df.columns:
            for agent_id in df[agent_id_column]:
                if pd.isna(agent_id):
                    agent_names.append(None)
                else:
                    agent_names.append(str(agent_id))
        else:
            # Generate default agent names
            for i in range(len(df)):
                agent_names.append(f"Agent_{i+1}")
        
        dataset.agent_names = agent_names
        
        # Process agent comments/justifications
        if agent_comments_column and agent_comments_column in df.columns:
            justifications = []
            for i, comment in enumerate(df[agent_comments_column]):
                # Include all comments, even empty ones, to maintain agent alignment
                agent_name = agent_names[i] if i < len(agent_names) else f"Agent_{i+1}"
                comment_text = str(comment).strip() if pd.notna(comment) else ""
                justifications.append({
                    "agent_name": agent_name,
                    "agent_index": i,
                    "justification": comment_text
                })
            dataset.agent_justifications = justifications
        
        # Process agent attributes
        if agent_attributes_columns:
            for attr_col in agent_attributes_columns:
                if attr_col in df.columns:
                    attr_values = []
                    for val in df[attr_col]:
                        if pd.isna(val):
                            attr_values.append(None)
                        else:
                            attr_values.append(str(val).strip())
                    
                    # Store in agent_attributes instead of key_results
                    dataset.agent_attributes[attr_col] = attr_values
    
    @classmethod
    def _process_ranking_per_agent_csv(cls,
                                     df: pd.DataFrame,
                                     dataset: 'SimulationExperimentDataset',
                                     ranking_columns: Optional[List[str]],
                                     agent_id_column: Optional[str],
                                     agent_comments_column: Optional[str],
                                     agent_attributes_columns: Optional[List[str]]):
        """Process CSV data for ranking per agent experiments."""
        
        # Auto-detect ranking columns if not specified
        if ranking_columns is None:
            # Look for columns that might contain rankings
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            # Exclude agent ID column if specified
            if agent_id_column and agent_id_column in numeric_cols:
                numeric_cols.remove(agent_id_column)
            
            if len(numeric_cols) < 2:
                raise ValueError("No suitable ranking columns found. Please specify ranking_columns parameter.")
            
            ranking_columns = numeric_cols
        
        # Validate ranking columns exist
        missing_cols = [col for col in ranking_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Ranking columns not found in CSV: {missing_cols}. Available columns: {list(df.columns)}")
        
        # Process each ranking column
        for rank_col in ranking_columns:
            rankings = []
            for val in df[rank_col]:
                if pd.isna(val):
                    rankings.append(None)
                else:
                    try:
                        # Convert to integer rank
                        rankings.append(int(float(val)))
                    except (ValueError, TypeError):
                        rankings.append(None)
            
            dataset.key_results[rank_col] = rankings
            dataset.result_types[rank_col] = "per_agent"
            dataset.data_types[rank_col] = "ranking"
        
        # Process agent IDs/names (same as single value method)
        agent_names = []
        if agent_id_column and agent_id_column in df.columns:
            for agent_id in df[agent_id_column]:
                if pd.isna(agent_id):
                    agent_names.append(None)
                else:
                    agent_names.append(str(agent_id))
        else:
            # Generate default agent names
            for i in range(len(df)):
                agent_names.append(f"Agent_{i+1}")
        
        dataset.agent_names = agent_names
        
        # Process agent comments (same as single value method)
        if agent_comments_column and agent_comments_column in df.columns:
            justifications = []
            for i, comment in enumerate(df[agent_comments_column]):
                # Include all comments, even empty ones, to maintain agent alignment
                agent_name = agent_names[i] if i < len(agent_names) else f"Agent_{i+1}"
                comment_text = str(comment).strip() if pd.notna(comment) else ""
                justifications.append({
                    "agent_name": agent_name,
                    "agent_index": i,
                    "justification": comment_text
                })
            dataset.agent_justifications = justifications
        
        # Process agent attributes (same as single value method)
        if agent_attributes_columns:
            for attr_col in agent_attributes_columns:
                if attr_col in df.columns:
                    attr_values = []
                    for val in df[attr_col]:
                        if pd.isna(val):
                            attr_values.append(None)
                        else:
                            attr_values.append(str(val).strip())
                    
                    # Store in agent_attributes instead of key_results
                    dataset.agent_attributes[attr_col] = attr_values

    @classmethod
    def _process_ordinal_ranking_per_agent_csv(cls,
                                             df: pd.DataFrame,
                                             dataset: 'SimulationExperimentDataset',
                                             ordinal_ranking_column: Optional[str],
                                             ordinal_ranking_separator: str,
                                             ordinal_ranking_options: Optional[List[str]],
                                             agent_id_column: Optional[str],
                                             agent_comments_column: Optional[str],
                                             agent_attributes_columns: Optional[List[str]]):
        """Process CSV data for ordinal ranking per agent experiments (single column with separator)."""
        
        # Auto-detect ranking column if not specified
        if ordinal_ranking_column is None:
            # Look for columns that might contain ordinal rankings
            ranking_candidates = [col for col in df.columns if any(keyword in col.lower() 
                                for keyword in ['ranking', 'rank', 'order', 'preference', 'choice'])]
            
            if len(ranking_candidates) == 1:
                ordinal_ranking_column = ranking_candidates[0]
            elif len(ranking_candidates) > 1:
                # Prefer shorter, more specific names
                ordinal_ranking_column = min(ranking_candidates, key=len)
            else:
                # Fall back to first string column that contains separator
                string_cols = df.select_dtypes(include=['object']).columns.tolist()
                if agent_id_column and agent_id_column in string_cols:
                    string_cols.remove(agent_id_column)
                if agent_comments_column and agent_comments_column in string_cols:
                    string_cols.remove(agent_comments_column)
                
                # Check which string columns contain the separator
                for col in string_cols:
                    if df[col].astype(str).str.contains(ordinal_ranking_separator, na=False).any():
                        ordinal_ranking_column = col
                        break
                
                if ordinal_ranking_column is None:
                    raise ValueError("No suitable ordinal ranking column found. Please specify ordinal_ranking_column parameter.")
        
        if ordinal_ranking_column not in df.columns:
            raise ValueError(f"Ordinal ranking column '{ordinal_ranking_column}' not found in CSV. Available columns: {list(df.columns)}")
        
        # Auto-detect ranking options if not specified
        if ordinal_ranking_options is None:
            ordinal_ranking_options = cls._auto_detect_ranking_options(df[ordinal_ranking_column], ordinal_ranking_separator)
        
        # Parse ordinal rankings and convert to individual ranking columns
        ranking_data = cls._parse_ordinal_rankings(df[ordinal_ranking_column], ordinal_ranking_separator, ordinal_ranking_options)
        
        # Store parsed rankings as separate metrics
        for option in ordinal_ranking_options:
            option_ranking_key = f"{option}_rank"
            dataset.key_results[option_ranking_key] = ranking_data[option]
            dataset.result_types[option_ranking_key] = "per_agent"
            dataset.data_types[option_ranking_key] = "ranking"
            
            # Store ranking info (always for ordinal ranking data)
            valid_ranks = [r for r in ranking_data[option] if r is not None]
            
            # Always store ranking info for ordinal ranking data, regardless of valid ranks
            ranking_info = {
                "direction": "ascending",  # 1 = best, higher = worse
                "original_options": ordinal_ranking_options,
                "separator": ordinal_ranking_separator,
                "source_column": ordinal_ranking_column
            }
            
            # Add rank statistics if valid ranks exist
            if valid_ranks:
                ranking_info.update({
                    "min_rank": min(valid_ranks),
                    "max_rank": max(valid_ranks),
                    "num_ranks": len(set(valid_ranks)),
                    "rank_values": sorted(set(valid_ranks))
                })
            else:
                # Set reasonable defaults based on options
                ranking_info.update({
                    "min_rank": 1,
                    "max_rank": len(ordinal_ranking_options),
                    "num_ranks": 0,
                    "rank_values": []
                })
            
            dataset.ranking_info[option_ranking_key] = ranking_info
        
        # Process agent IDs/names (same as other methods)
        agent_names = []
        if agent_id_column and agent_id_column in df.columns:
            for agent_id in df[agent_id_column]:
                if pd.isna(agent_id):
                    agent_names.append(None)
                else:
                    agent_names.append(str(agent_id))
        else:
            # Generate default agent names
            for i in range(len(df)):
                agent_names.append(f"Agent_{i+1}")
        
        dataset.agent_names = agent_names
        
        # Process agent comments (same as other methods)
        if agent_comments_column and agent_comments_column in df.columns:
            justifications = []
            for i, comment in enumerate(df[agent_comments_column]):
                # Include all comments, even empty ones, to maintain agent alignment
                agent_name = agent_names[i] if i < len(agent_names) else f"Agent_{i+1}"
                comment_text = str(comment).strip() if pd.notna(comment) else ""
                justifications.append({
                    "agent_name": agent_name,
                    "agent_index": i,
                    "justification": comment_text
                })
            dataset.agent_justifications = justifications
        
        # Process agent attributes (same as other methods)
        if agent_attributes_columns:
            for attr_col in agent_attributes_columns:
                if attr_col in df.columns:
                    attr_values = []
                    for val in df[attr_col]:
                        if pd.isna(val):
                            attr_values.append(None)
                        else:
                            attr_values.append(str(val).strip())
                    
                    # Store in agent_attributes instead of key_results
                    dataset.agent_attributes[attr_col] = attr_values

    @classmethod
    def _auto_detect_ranking_options(cls, ranking_series: pd.Series, separator: str) -> List[str]:
        """Auto-detect the ranking options from ordinal ranking data."""
        all_options = set()
        
        for ranking_str in ranking_series.dropna():
            if pd.isna(ranking_str):
                continue
            
            ranking_str = str(ranking_str).strip()
            if separator in ranking_str:
                options = [opt.strip() for opt in ranking_str.split(separator)]
                all_options.update(options)
        
        if not all_options:
            raise ValueError(f"No ranking options found in data using separator '{separator}'")
        
        # Sort options for consistency (could be enhanced to preserve meaningful order)
        return sorted(list(all_options))

    @classmethod
    def _parse_ordinal_rankings(cls, ranking_series: pd.Series, separator: str, options: List[str]) -> Dict[str, List[Optional[int]]]:
        """Parse ordinal ranking strings into individual option rankings."""
        result = {option: [] for option in options}
        
        for ranking_str in ranking_series:
            if pd.isna(ranking_str) or str(ranking_str).strip() == "":
                # Handle missing data
                for option in options:
                    result[option].append(None)
                continue
            
            ranking_str = str(ranking_str).strip()
            
            if separator not in ranking_str:
                # Handle malformed data
                for option in options:
                    result[option].append(None)
                continue
            
            # Parse the ranking
            ranked_options = [opt.strip() for opt in ranking_str.split(separator)]
            
            # Create rank mapping (position in list = rank, starting from 1)
            option_to_rank = {}
            for rank, option in enumerate(ranked_options, 1):
                if option in options:
                    option_to_rank[option] = rank
            
            # Fill in ranks for each option
            for option in options:
                rank = option_to_rank.get(option, None)
                result[option].append(rank)
        
        return result

    @classmethod
    def create_from_csv(cls,
                       file_path: Union[str, Path],
                       experimental_data_type: str = "single_value_per_agent",
                       agent_id_column: Optional[str] = None,
                       agent_comments_column: Optional[str] = None,
                       agent_attributes_columns: Optional[List[str]] = None,
                       value_column: Optional[str] = None,
                       ranking_columns: Optional[List[str]] = None,
                       ordinal_ranking_column: Optional[str] = None,
                       ordinal_ranking_separator: str = "-",
                       ordinal_ranking_options: Optional[List[str]] = None,
                       dataset_name: Optional[str] = None,
                       dataset_description: Optional[str] = None,
                       encoding: str = "utf-8") -> tuple['SimulationExperimentEmpiricalValidator', 'SimulationExperimentDataset']:
        """
        Create a validator and load empirical data from CSV in one step.
        
        This is a convenience method that combines validator creation with CSV loading.
        
        Args:
            Same as read_empirical_data_from_csv()
            
        Returns:
            Tuple of (validator_instance, loaded_dataset)
        """
        validator = cls()
        dataset = cls.read_empirical_data_from_csv(
            file_path=file_path,
            experimental_data_type=experimental_data_type,
            agent_id_column=agent_id_column,
            agent_comments_column=agent_comments_column,
            agent_attributes_columns=agent_attributes_columns,
            value_column=value_column,
            ranking_columns=ranking_columns,
            ordinal_ranking_column=ordinal_ranking_column,
            ordinal_ranking_separator=ordinal_ranking_separator,
            ordinal_ranking_options=ordinal_ranking_options,
            dataset_name=dataset_name,
            dataset_description=dataset_description,
            encoding=encoding
        )
        return validator, dataset

    @classmethod
    def create_from_dataframe(cls,
                            df: pd.DataFrame,
                            experimental_data_type: str = "single_value_per_agent",
                            agent_id_column: Optional[str] = None,
                            agent_comments_column: Optional[str] = None,
                            agent_attributes_columns: Optional[List[str]] = None,
                            value_column: Optional[str] = None,
                            ranking_columns: Optional[List[str]] = None,
                            ordinal_ranking_column: Optional[str] = None,
                            ordinal_ranking_separator: str = "-",
                            ordinal_ranking_options: Optional[List[str]] = None,
                            dataset_name: Optional[str] = None,
                            dataset_description: Optional[str] = None) -> tuple['SimulationExperimentEmpiricalValidator', 'SimulationExperimentDataset']:
        """
        Create a validator and load empirical data from a pandas DataFrame in one step.
        
        This is a convenience method that combines validator creation with DataFrame loading.
        
        Args:
            Same as read_empirical_data_from_dataframe()
            
        Returns:
            Tuple of (validator_instance, loaded_dataset)
        """
        validator = cls()
        dataset = cls.read_empirical_data_from_dataframe(
            df=df,
            experimental_data_type=experimental_data_type,
            agent_id_column=agent_id_column,
            agent_comments_column=agent_comments_column,
            agent_attributes_columns=agent_attributes_columns,
            value_column=value_column,
            ranking_columns=ranking_columns,
            ordinal_ranking_column=ordinal_ranking_column,
            ordinal_ranking_separator=ordinal_ranking_separator,
            ordinal_ranking_options=ordinal_ranking_options,
            dataset_name=dataset_name,
            dataset_description=dataset_description
        )
        return validator, dataset

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
        
        elif "kolmogorov-smirnov" in test_type or "ks" in test_type:
            # For KS test, the effect size is the KS statistic itself
            # It represents the maximum difference between CDFs (0 to 1)
            return metric_result.get("effect_size", metric_result.get("ks_statistic", 0.0))
        
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

    def _interpret_effect_size(self, effect_size: float, test_type: str = "") -> str:
        """Provide interpretation of effect size magnitude based on test type."""
        test_type_lower = test_type.lower()
        
        # For KS test, use different thresholds since KS statistic ranges 0-1
        if "kolmogorov-smirnov" in test_type_lower or "ks" in test_type_lower:
            if effect_size < 0.1:
                return "negligible difference"
            elif effect_size < 0.25:
                return "small difference"
            elif effect_size < 0.5:
                return "medium difference"
            else:
                return "large difference"
        
        # For other tests, use Cohen's conventions
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
                                              statistical_test_type: str = "welch_t_test",
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
        statistical_test_type: Type of statistical test ("welch_t_test", "ks_test", "mann_whitney", etc.)
        significance_level: Significance level for statistical tests
        output_format: "values" for SimulationExperimentEmpiricalValidationResult object, "report" for markdown report
        
    Returns:
        SimulationExperimentEmpiricalValidationResult object or markdown report string
    """
    # Use Pydantic's built-in parsing instead of from_dict
    control_dataset = SimulationExperimentDataset.model_validate(control_data)
    treatment_dataset = SimulationExperimentDataset.model_validate(treatment_data)
    
    validator = SimulationExperimentEmpiricalValidator()
    return validator.validate(
        control_dataset,
        treatment_dataset,
        validation_types=validation_types,
        statistical_test_type=statistical_test_type,
        significance_level=significance_level,
        output_format=output_format
    )
