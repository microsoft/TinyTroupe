"""
Test cases for the improved extract_json function security enhancements.
"""
import pytest
import json
from tinytroupe.utils.llm import extract_json


class TestExtractJsonSecurity:
    """Test security improvements in extract_json function."""
    
    def test_basic_json_extraction(self):
        """Test basic valid JSON extraction."""
        test_cases = [
            ('{"key": "value"}', {"key": "value"}),
            ('[1, 2, 3]', [1, 2, 3]),
            ('{"nested": {"key": "value"}}', {"nested": {"key": "value"}}),
        ]
        
        for input_text, expected in test_cases:
            result = extract_json(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_markdown_code_block_extraction(self):
        """Test extraction from markdown code blocks."""
        test_cases = [
            ('```json\n{"key": "value"}\n```', {"key": "value"}),
            ('```\n[1, 2, 3]\n```', [1, 2, 3]),
            ('Some text\n```json\n{"data": "test"}\n```\nMore text', {"data": "test"}),
        ]
        
        for input_text, expected in test_cases:
            result = extract_json(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_cleaned_json_extraction(self):
        """Test extraction with common LLM output issues."""
        test_cases = [
            # Trailing comma in object
            ('{"key": "value",}', {"key": "value"}),
            # Trailing comma in array  
            ('[1, 2, 3,]', [1, 2, 3]),
            # Extra text around JSON
            ('Here is the JSON: {"key": "value"} and some more text', {"key": "value"}),
            # Escaped single quotes
            ('{"key": "value\'s"}', {"key": "value's"}),
        ]
        
        for input_text, expected in test_cases:
            result = extract_json(input_text)
            assert result == expected, f"Failed for input: {input_text}"
    
    def test_security_limits(self):
        """Test security limits and protections."""
        # Test input size limit
        large_input = '{"key": "' + 'x' * 2_000_000 + '"}'
        result = extract_json(large_input)
        # Should either return None or handle gracefully without crashing
        assert result is None or isinstance(result, (dict, list))
        
        # Test deeply nested structure limit
        deeply_nested = '{"a":' * 100 + '"value"' + '}' * 100
        result = extract_json(deeply_nested)
        # Should return None due to depth limit
        assert result is None
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON."""
        test_cases = [
            '',  # Empty string
            'not json at all',  # No JSON structure
            '{"unclosed": "object"',  # Unclosed object
            '{"invalid": json}',  # Invalid JSON syntax
            None,  # None input
            123,  # Non-string input
        ]
        
        for input_text in test_cases:
            result = extract_json(input_text)
            assert result is None, f"Should return None for invalid input: {input_text}"
    
    def test_edge_cases(self):
        """Test edge cases and corner scenarios."""
        test_cases = [
            # Empty object and array
            ('{}', {}),
            ('[]', []),
            # JSON with special characters
            ('{"unicode": "\\u0041"}', {"unicode": "A"}),
            # Nested structures
            ('{"arr": [{"nested": true}]}', {"arr": [{"nested": True}]}),
        ]
        
        for input_text, expected in test_cases:
            result = extract_json(input_text)
            assert result == expected, f"Failed for input: {input_text}"


def test_extract_json_backward_compatibility():
    """Ensure the improved function maintains backward compatibility."""
    # Test with typical LLM outputs that should still work
    llm_outputs = [
        '```json\n{"action": "TALK", "content": "Hello"}\n```',
        'The response is: {"status": "success", "data": [1, 2, 3]}',
        '{"reasoning": "step by step", "conclusion": "yes"}',
    ]
    
    for output in llm_outputs:
        result = extract_json(output)
        assert result is not None, f"Backward compatibility failed for: {output}"
        assert isinstance(result, (dict, list)), f"Invalid result type for: {output}"


if __name__ == "__main__":
    # Run basic tests
    test_instance = TestExtractJsonSecurity()
    
    test_methods = [
        test_instance.test_basic_json_extraction,
        test_instance.test_markdown_code_block_extraction, 
        test_instance.test_cleaned_json_extraction,
        test_instance.test_security_limits,
        test_instance.test_malformed_json_handling,
        test_instance.test_edge_cases,
    ]
    
    print("Running extract_json security tests...")
    
    for test_method in test_methods:
        try:
            test_method()
            print(f"✅ {test_method.__name__} passed")
        except Exception as e:
            print(f"❌ {test_method.__name__} failed: {e}")
    
    try:
        test_extract_json_backward_compatibility()
        print("✅ test_extract_json_backward_compatibility passed")
    except Exception as e:
        print(f"❌ test_extract_json_backward_compatibility failed: {e}")
    
    print("Tests completed.")