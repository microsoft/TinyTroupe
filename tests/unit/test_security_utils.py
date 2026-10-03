"""
Unit tests for security and validation utilities.
"""

import pytest

from tinytroupe.exceptions import SecurityError, ValidationError
from tinytroupe.security_utils import (
    sanitize_input,
    validate_json_structure,
    validate_llm_response,
    validate_prompt_length,
)


class TestValidation:
    """Test suite for validation utilities."""

    def test_validate_prompt_length_valid(self):
        validate_prompt_length("Hello, world!", max_length=1000)

    def test_validate_prompt_length_invalid(self):
        long_prompt = "a" * 100001
        with pytest.raises(ValidationError):
            validate_prompt_length(long_prompt, max_length=100000)

    def test_sanitize_input_valid(self):
        result = sanitize_input("Hello, world!")
        assert result == "Hello, world!"

    def test_sanitize_input_truncates(self):
        long_input = "a" * 15000
        result = sanitize_input(long_input, max_length=10000)
        assert len(result) == 10000

    def test_sanitize_input_blocks_script(self):
        malicious = "<script>alert('xss')</script>"
        with pytest.raises(SecurityError):
            sanitize_input(malicious)

    def test_sanitize_input_blocks_javascript(self):
        malicious = "javascript:alert('xss')"
        with pytest.raises(SecurityError):
            sanitize_input(malicious)

    def test_sanitize_input_requires_string(self):
        with pytest.raises(SecurityError):
            sanitize_input(123)

    def test_validate_json_structure_valid(self):
        data = {"name": "test", "value": 123}
        validate_json_structure(data, required_fields=["name", "value"])

    def test_validate_json_structure_missing_field(self):
        data = {"name": "test"}
        with pytest.raises(ValidationError):
            validate_json_structure(data, required_fields=["name", "value"])

    def test_validate_json_structure_not_dict(self):
        with pytest.raises(ValidationError):
            validate_json_structure("not a dict", required_fields=["field"])

    def test_validate_llm_response_valid(self):
        validate_llm_response("This is a reasonable response.")

    def test_validate_llm_response_too_long(self):
        long_response = "a" * 20000
        with pytest.raises(ValidationError):
            validate_llm_response(long_response, max_tokens=4096)

    def test_validate_llm_response_not_string(self):
        with pytest.raises(ValidationError):
            validate_llm_response(123)
