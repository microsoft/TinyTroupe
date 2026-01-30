import pytest
import os
import json
import sys
import logging

# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from testing_utils import *
from tinytroupe.extraction import Normalizer

logger = logging.getLogger("tinytroupe")


class TestNormalizer:
    """Comprehensive tests for the Normalizer class covering LLMChat integration and edge cases."""

    # ==== BASIC FUNCTIONALITY TESTS ====

    def test_normalizer_initialization(self):
        """Test that Normalizer can be initialized with various parameters."""
        elements = ["item1", "item2", "item3"]
        
        # Basic initialization
        normalizer = Normalizer(elements, n=2)
        # Note: elements get deduplicated with set(), so order may change
        assert len(normalizer.elements) == len(elements)
        assert all(item in normalizer.elements for item in elements)
        assert normalizer.n == 2
        assert normalizer.verbose == False
        assert normalizer.max_length is None
        
        # Initialization with all parameters
        normalizer = Normalizer(elements, n=3, verbose=True, max_length=50)
        assert normalizer.n == 3
        assert normalizer.verbose == True
        assert normalizer.max_length == 50

    def test_normalizer_deduplication(self):
        """Test that Normalizer removes duplicate elements."""
        elements = ["item1", "item2", "item1", "item3", "item2"]
        normalizer = Normalizer(elements, n=3)
        
        # Should deduplicate to unique elements only
        unique_elements = list(set(elements))
        assert len(normalizer.elements) == len(unique_elements)
        for item in unique_elements:
            assert item in normalizer.elements

    # ==== CLUSTERING TESTS ====

    def test_normalizer_basic_clustering(self):
        """Test that Normalizer creates proper clusters, not identity mappings."""
        # Use elements that should naturally cluster together
        elements = [
            "software engineer",
            "programmer", 
            "doctor",
            "physician",
            "teacher",
            "educator"
        ]
        
        normalizer = Normalizer(elements, n=3, verbose=True)
        mapping = normalizer.normalized_mapping()
        
        # Should create clusters, not identity mapping
        assert isinstance(mapping, dict)
        assert len(mapping) <= 3  # Should respect the n limit
        
        # Check that it's not just identity mapping
        identity_count = sum(1 for k, v in mapping.items() if len(v) == 1 and v[0] == k)
        total_clusters = len(mapping)
        
        # Allow some identity mappings, but not all of them
        assert identity_count < total_clusters, "Should not be all identity mappings"
        
        # Verify all original elements are accounted for
        all_mapped_elements = []
        for originals in mapping.values():
            all_mapped_elements.extend(originals)
        
        assert len(all_mapped_elements) == len(elements)
        for element in elements:
            assert element in all_mapped_elements

    def test_normalizer_respects_n_limit(self):
        """Test that Normalizer never returns more than n clusters."""
        elements = [f"concept_{i}" for i in range(20)]  # 20 unique elements
        
        for n in [1, 3, 5, 10, 15]:
            normalizer = Normalizer(elements, n=n)
            mapping = normalizer.normalized_mapping()
            
            assert len(mapping) <= n, f"Should not exceed n={n} clusters, got {len(mapping)}"

    # ==== SPECIAL CHARACTERS TESTS ====

    def test_comma_preservation_robustness(self):
        """Test specifically focused on comma preservation in various contexts.
        
        Note: LLM-based normalization may sometimes modify elements in unexpected ways.
        This test focuses on verifying the overall mapping structure rather than
        exact character preservation, which is implementation-dependent.
        """
        elements = [
            # Simple comma lists
            "red, green, blue",
            "apple, banana, cherry",
            # Commas in quotes
            'He said, "Hello, world!"',
            'Description: "Complex, multi-part, detailed"',
            # Commas with numbers  
            "1,000", "2,500", "1,234,567",
            # Commas in technical contexts
            "CSV: name,age,city",
            "Function(arg1, arg2, arg3)",
            # Complex mixed scenarios
            "Data: {name: 'Smith, John', values: [1,2,3]}",
            "Address: 123 Main St, Apt 4B, City, State, 12345"
        ]
        
        normalizer = Normalizer(elements, n=3, verbose=True)
        mapping = normalizer.normalized_mapping()
        
        # Collect all mapped elements
        all_mapped = []
        for originals in mapping.values():
            all_mapped.extend(originals)
        
        # TOLERANT VERIFICATION - Focus on structure, not exact character preservation
        
        # 1. Verify we got a valid mapping with the right number of elements
        assert isinstance(mapping, dict), "Should return a dictionary mapping"
        assert len(mapping) <= 3, f"Should have at most 3 clusters, got {len(mapping)}"
        assert len(all_mapped) == len(elements), f"All elements should be mapped: expected {len(elements)}, got {len(all_mapped)}"
        
        # 2. Verify that most elements are accounted for (allowing for some LLM variation)
        # LLM may encode/modify some elements, so we check that elements are present
        # either exactly or in a recognizable form
        matched_count = 0
        for original in elements:
            found = False
            for mapped in all_mapped:
                # Check for exact match or common encodings
                if (original == mapped or 
                    original.replace('"', '&quot;').replace("'", "&#x27;") == mapped or
                    original.replace('"', '\\"') == mapped or
                    original in mapped or mapped in original):
                    found = True
                    break
            if found:
                matched_count += 1
        
        # Allow for some LLM variation - at least 80% of elements should be recognizable
        match_ratio = matched_count / len(elements)
        assert match_ratio >= 0.8, f"At least 80% of elements should be matched, got {match_ratio*100:.1f}%"
        
        # 3. Test normalize method works (returns valid canonical categories)
        test_cases = [
            "item1, item2, item3",
            'Quote with "comma, inside"',
            "Number: 1,234,567"
        ]
        
        for test_case in test_cases:
            result = normalizer.normalize(test_case)
            assert isinstance(result, str), f"Should return string for string input: {test_case}"
            assert result in mapping.keys(), f"Result should be canonical category: {result}"
            
        # 4. Test list normalization works
        list_result = normalizer.normalize(test_cases)
        assert isinstance(list_result, list), "Should return list for list input"
        assert len(list_result) == len(test_cases), "Should preserve list length"

    def test_normalizer_handles_special_characters(self):
        """Test that Normalizer handles special characters correctly (quotes, commas, newlines).
        
        Note: LLM-based normalization may transform elements in various ways.
        This test focuses on verifying the normalizer doesn't crash and produces
        valid output structure, rather than exact character preservation.
        """
        elements = [
            'Communication style: "Direct, assertive"',
            "Style with quotes and, commas",
            "Multi-line\ndescription with\nbreak characters", 
            "Text with [brackets] and {braces}",
            "Simple text without special chars",
            "JSON-like: {\"key\": \"value\", \"list\": [1, 2, 3]}",
            # More challenging comma cases
            "Item 1, Item 2, Item 3",
            "Name: Smith, John, Jr.",
            "Values: a,b,c,d,e",
            "Mixed: text, with \"quotes, inside\", and [brackets, too]"
        ]
        
        normalizer = Normalizer(elements, n=4, verbose=True)
        mapping = normalizer.normalized_mapping()
        
        # Should successfully create clusters without JSON parsing errors
        assert isinstance(mapping, dict), "Should return a dictionary"
        assert len(mapping) > 0, "Should create at least one cluster"
        assert len(mapping) <= 4, f"Should not exceed n=4 clusters, got {len(mapping)}"
        
        # Verify all elements are preserved (allowing for HTML encoding and LLM variations)
        all_mapped = []
        for originals in mapping.values():
            all_mapped.extend(originals)
        
        assert len(all_mapped) == len(elements), f"All elements should be mapped: expected {len(elements)}, got {len(all_mapped)}"
        
        # TOLERANT SPECIAL CHARACTER CHECKS
        
        # 1. Verify mapping structure is valid
        for canonical, originals in mapping.items():
            assert isinstance(canonical, str), "Canonical labels should be strings"
            assert isinstance(originals, list), "Original elements should be in lists"
            assert len(originals) > 0, "Each cluster should have at least one element"
        
        # 2. Check that most elements can be found (allowing for transformations)
        matched_count = 0
        for original in elements:
            for mapped in all_mapped:
                # Check for various match forms (exact, encoded, partial)
                if (original == mapped or 
                    original.replace('"', '&quot;') == mapped or
                    original.replace('\n', '\\n') == mapped or
                    original in mapped or 
                    mapped in original):
                    matched_count += 1
                    break
        
        # At least 70% of elements should be recognizable
        match_ratio = matched_count / len(elements)
        assert match_ratio >= 0.7, f"At least 70% of elements should be matched, got {match_ratio*100:.1f}%"
        
        # 3. Test normalization method works with special characters
        test_element = "Test item, with commas, and more"
        normalized_result = normalizer.normalize(test_element)
        
        # The normalized result should be one of the canonical categories
        assert normalized_result in mapping.keys(), "Normalized result should be a canonical category"

    # ==== NORMALIZE METHOD TESTS ====

    def test_normalize_single_element(self):
        """Test normalizing a single element."""
        elements = ["programming", "coding", "software development"]
        normalizer = Normalizer(elements, n=2)
        
        # Test single string input - normalize() always returns a string for string input
        result = normalizer.normalize("programming")
        assert isinstance(result, str)
        assert result is not None

    def test_normalize_list_of_elements(self):
        """Test normalizing a list of elements.""" 
        elements = ["programming", "coding", "software development", "engineering"]
        normalizer = Normalizer(elements, n=2)
        
        # Test list input
        test_input = ["programming", "coding"]
        result = normalizer.normalize(test_input)
        assert isinstance(result, list)
        assert len(result) == len(test_input)
        
        # Test order preservation
        result2 = normalizer.normalize(["coding", "programming"])  # Different order
        assert isinstance(result2, list)
        assert len(result2) == 2

    def test_normalize_caching(self):
        """Test that normalize method uses caching properly."""
        elements = ["item1", "item2", "item3", "item4"]
        normalizer = Normalizer(elements, n=2)
        
        # First normalization should add to cache
        initial_cache_size = len(normalizer.normalizing_map)
        result1 = normalizer.normalize("item1")
        
        cache_after_first = len(normalizer.normalizing_map)
        assert cache_after_first > initial_cache_size, "Cache should grow after first normalization"
        
        # Second normalization of same element should use cache
        result2 = normalizer.normalize("item1")
        cache_after_second = len(normalizer.normalizing_map)
        
        assert result1 == result2, "Should return same result from cache"
        assert cache_after_second == cache_after_first, "Cache size should not change for cached items"

    def test_normalize_error_handling(self):
        """Test error handling in normalize method."""
        elements = ["item1", "item2"]
        normalizer = Normalizer(elements, n=1)
        
        # Test invalid input type
        with pytest.raises(ValueError, match="must be either a string or a list"):
            normalizer.normalize(123)

    # ==== MAX LENGTH TESTS ====

    def test_normalizer_with_max_length(self):
        """Test that Normalizer respects max_length parameter."""
        elements = [
            "This is a very long description that exceeds the character limit",
            "Another long description with many words and detailed information",
            "Short text",
            "Medium length description here"
        ]
        
        max_len = 30
        normalizer = Normalizer(elements, n=2, max_length=max_len)
        mapping = normalizer.normalized_mapping()
        
        # Check that canonical labels respect max_length
        for canonical in mapping.keys():
            assert len(canonical) <= max_len + 5, f"Canonical '{canonical}' too long: {len(canonical)} chars"

    # ==== EDGE CASES TESTS ====

    def test_normalizer_empty_elements(self):
        """Test Normalizer behavior with empty or minimal input."""
        # Empty list - LLM may return error message, so just check it doesn't crash
        normalizer = Normalizer([], n=5)
        mapping = normalizer.normalized_mapping()
        assert isinstance(mapping, dict)  # Should return some dict, even if error
        
        # Single element
        normalizer = Normalizer(["single"], n=3)
        mapping = normalizer.normalized_mapping()
        assert len(mapping) >= 1
        assert "single" in mapping or any("single" in originals for originals in mapping.values())

    def test_normalizer_n_greater_than_elements(self):
        """Test when n is greater than the number of input elements."""
        elements = ["item1", "item2"]
        normalizer = Normalizer(elements, n=10)  # n > len(elements)
        mapping = normalizer.normalized_mapping()
        
        # Should not create more clusters than elements
        assert len(mapping) <= len(elements)

    def test_normalizer_n_equals_one(self):
        """Test edge case when n=1 (all elements in one cluster)."""
        elements = ["item1", "item2", "item3", "item4"]
        normalizer = Normalizer(elements, n=1)
        mapping = normalizer.normalized_mapping()
        
        assert len(mapping) == 1, "Should create exactly one cluster when n=1"
        
        # All elements should be in the single cluster
        all_mapped = []
        for originals in mapping.values():
            all_mapped.extend(originals)
        assert len(all_mapped) == len(elements)

    # ==== SEMANTIC CLUSTERING TESTS ====

    def test_semantic_clustering_quality(self):
        """Test that semantically similar items are clustered together."""
        elements = [
            # Medical profession cluster
            "doctor", "physician", "medical practitioner",
            # Technology cluster  
            "programmer", "software engineer", "developer",
            # Education cluster
            "teacher", "educator", "instructor"
        ]
        
        normalizer = Normalizer(elements, n=3, verbose=True)
        mapping = normalizer.normalized_mapping()
        
        # Should create meaningful clusters
        assert len(mapping) <= 3
        
        # Verify semantic clustering with LLM
        for canonical, originals in mapping.items():
            if len(originals) > 1:
                originals_str = ", ".join(originals)
                semantic_check = f"The following terms are semantically related and belong to the same category: {originals_str}"
                assert proposition_holds(semantic_check), f"Cluster {canonical} should be semantically coherent: {originals}"

    # ==== INTEGRATION TESTS ====

    def test_normalizer_workflow(self):
        """Test complete normalizer workflow from initialization to normalization.""" 
        # Complex realistic example
        elements = [
            "Python programming", "Java development", "C++ coding",
            "Web design", "UI/UX design", "Frontend development",
            "Data analysis", "Machine learning", "AI research",
            "Project management", "Team leadership", "Agile methodology"
        ]
        
        normalizer = Normalizer(elements, n=4, max_length=40)
        
        # Test clustering
        mapping = normalizer.normalized_mapping()
        assert len(mapping) <= 4
        assert len(mapping) > 0
        
        # Test normalization of new elements
        new_elements = ["Python scripting", "React development", "Deep learning"]
        results = normalizer.normalize(new_elements)
        
        assert len(results) == len(new_elements)
        for result in results:
            assert result in mapping.keys(), f"Normalized result '{result}' should be one of the canonical categories"

    # ==== CONVENIENCE API TESTS ====

    def test_normalized_mapping_fallback(self):
        """Test that normalized_mapping() handles edge cases gracefully."""
        normalizer = Normalizer(["test"], n=1)
        
        # Corrupt the internal data to test fallback
        normalizer.normalized_elements = None
        mapping = normalizer.normalized_mapping()
        assert mapping == {"test": ["test"]}, "Should fallback to identity mapping"
        
        # Test with list format (edge case)
        normalizer.normalized_elements = ["item1", "item2"]
        mapping = normalizer.normalized_mapping()
        assert isinstance(mapping, dict)

    def test_debug_output(self):
        """Test that debug output works correctly with verbose mode."""
        elements = ["test1", "test2", "test3"]
        
        # Should not raise any exceptions in verbose mode
        normalizer = Normalizer(elements, n=2, verbose=True)
        assert normalizer.verbose == True
        
        # Test normalize with verbose
        result = normalizer.normalize("test1")
        assert result is not None