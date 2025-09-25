#!/usr/bin/env python3
"""
Test script to verify the fixes for JSON serialization issues and model selection in TinyTroupeLiteLLM.
"""

import json
import logging
import os
import sys

# Add the tinytroupe directory to the path
sys.path.insert(0, "")

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_serialization")


def test_json_serialization():
    """Test that JSON serialization works with Pydantic models."""
    try:
        from pydantic import BaseModel

        import tinytroupe.litellm_utils as litellm_utils

        # Create a simple Pydantic model for testing
        class TestModel(BaseModel):
            name: str
            value: int

        # Create a test object that includes the Pydantic model class
        test_obj = {
            "model_class": TestModel,
            "instance": TestModel(name="test", value=123),
            "other_type": int,
            "nested": {"model_again": TestModel},
        }

        # Try to serialize with our custom serializer
        try:
            serialized = json.dumps(
                test_obj, default=litellm_utils._json_default_serializer
            )
            print(f"✓ Successfully serialized complex object: {serialized[:100]}...")
            return True
        except Exception as e:
            print(f"✗ Serialization failed: {e}")
            return False

    except Exception as e:
        print(f"✗ Test setup failed: {e}")
        return False


def test_cache_key_generation():
    """Test that cache key generation works with Pydantic models."""
    try:
        from pydantic import BaseModel

        import tinytroupe.litellm_utils as litellm_utils

        # Create a simple Pydantic model for testing
        class TestResponseFormat(BaseModel):
            type: str

        # Create a client
        client = litellm_utils.client()

        # Test with a response format that's a Pydantic model
        try:
            messages = [{"role": "user", "content": "Test message"}]

            # Generate a cache key with a Pydantic model class as response_format
            cache_key = client._create_cache_key(
                messages=messages,
                model="test-model",
                temperature=0.7,
                max_tokens=100,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0,
                stop=[],
                response_format=TestResponseFormat,
            )

            print(
                f"✓ Successfully generated cache key with Pydantic model class: {cache_key}"
            )
            return True
        except Exception as e:
            print(f"✗ Cache key generation failed: {e}")
            return False

    except Exception as e:
        print(f"✗ Test setup failed: {e}")
        return False


def test_model_selection():
    """Test that the correct model is selected from config."""
    try:
        import tinytroupe.litellm_utils as litellm_utils

        # Get the default model from litellm_utils
        model = litellm_utils.default["model"]
        provider = litellm_utils.default["provider"]

        print(f"Default model: {model}")
        print(f"Default provider: {provider}")

        # Check that they match expected values (now looking for Vertex AI Gemini)
        if model == "vertex_ai/gemini-2.0-flash" and provider == "vertex_ai":
            print("✓ Correct model and provider configured")
            return True
        else:
            print(f"✗ Unexpected model or provider configuration: {provider}/{model}")
            return False

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing TinyTroupeLiteLLM Fixes...")
    print("=" * 50)

    tests = [
        ("JSON Serialization", test_json_serialization),
        ("Cache Key Generation", test_cache_key_generation),
        ("Model Selection", test_model_selection),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"  {test_name} failed!")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Fixes are working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
