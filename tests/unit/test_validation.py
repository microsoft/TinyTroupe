"""
Unit tests for security and validation utilities.
"""

import pytest
from tinytroupe.exceptions import SecurityException, ValidationException
from tinytroupe.security_utils import (
    validate_prompt_length,
    sanitize_input,
    validate_json_structure,
    validate_llm_response,
)


class TestValidation:
    """Test suite for validation utilities."""

    def test_validate_prompt_length_valid(self):
        """Test prompt length validation with valid input."""
        validate_prompt_length("Hello, world!", max_length=1000)

    def test_validate_prompt_length_invalid(self):
        """Test prompt length validation with invalid input."""
        long_prompt = "a" * 100001
        with pytest.raises(ValidationException):
            validate_prompt_length(long_prompt, max_length=100000)

    def test_sanitize_input_valid(self):
        """Test input sanitization with valid input."""
        result = sanitize_input("Hello, world!")
        assert result == "Hello, world!"

    def test_sanitize_input_truncates(self):
        """Test that long input is truncated."""
        long_input = "a" * 15000
        result = sanitize_input(long_input, max_length=10000)
        assert len(result) == 10000

    def test_sanitize_input_blocks_script(self):
        """Test that script tags are blocked."""
        malicious = "<script>alert('xss')</script>"
        with pytest.raises(SecurityException):
            sanitize_input(malicious)

    def test_sanitize_input_blocks_javascript(self):
        """Test that javascript protocol is blocked."""
        malicious = "javascript:alert('xss')"
        with pytest.raises(SecurityException):
            sanitize_input(malicious)

    def test_sanitize_input_requires_string(self):
        """Test that non-string input raises exception."""
        with pytest.raises(SecurityException):
            sanitize_input(123)

    def test_validate_json_structure_valid(self):
        """Test JSON structure validation with valid data."""
        data = {"name": "test", "value": 123}
        validate_json_structure(data, required_fields=["name", "value"])

    def test_validate_json_structure_missing_field(self):
        """Test JSON structure validation with missing field."""
        data = {"name": "test"}
        with pytest.raises(ValidationException):
            validate_json_structure(data, required_fields=["name", "value"])

    def test_validate_json_structure_not_dict(self):
        """Test JSON structure validation with non-dict."""
        with pytest.raises(ValidationException):
            validate_json_structure("not a dict", required_fields=["field"])

    def test_validate_llm_response_valid(self):
        """Test LLM response validation with valid input."""
        validate_llm_response("This is a reasonable response.")

    def test_validate_llm_response_too_long(self):
        """Test LLM response validation with too long input."""
        long_response = "a" * 20000  # ~5000 tokens
        with pytest.raises(ValidationException):
            validate_llm_response(long_response, max_tokens=4096)

    def test_validate_llm_response_not_string(self):
        """Test LLM response validation with non-string."""
        with pytest.raises(ValidationException):
            validate_llm_response(123)
