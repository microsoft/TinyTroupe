"""
Integration tests for the LLM API caching mechanism.

These tests make real API calls to verify the cache is actually working end-to-end.
"""
import json
import os
import pytest
from pydantic import BaseModel

from tinytroupe.clients import client, force_api_cache
from tinytroupe import config_manager


def _missing_live_llm_backend():
    api_type = (config_manager.get("api_type") or "").lower()
    if api_type == "openai":
        return not os.environ.get("OPENAI_API_KEY")
    if api_type == "azure":
        return not os.environ.get("AZURE_OPENAI_API_KEY")
    return False


requires_live_llm = pytest.mark.skipif(
    _missing_live_llm_backend(),
    reason="Live API cache integration test requires credentials, or use TINYTROUPE_CONFIG=tests/config_ollama.ini",
)


@requires_live_llm
class TestAPICacheIntegration:
    """Integration tests for API caching with real API calls."""

    def test_cache_with_default_config(self):
        """Test caching behavior using default config settings."""
        api_client = client()
        cache_file_name = config_manager.get("cache_file_name")
        cache_path = os.path.abspath(cache_file_name)
        
        print(f"\n=== Cache file: {cache_file_name}")
        print(f"=== Full path: {cache_path}")
        print(f"=== Current working directory: {os.getcwd()}")
        print(f"=== Client cache_api_calls: {api_client.cache_api_calls}")
        print(f"=== Client cache_file_name: {api_client.cache_file_name}")
        
        # Make a simple API call
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'integration cache test' and nothing else."}
        ]
        
        file_existed_before = os.path.exists(cache_path)
        cache_size_before = os.path.getsize(cache_path) if file_existed_before else 0
        print(f"=== Cache file exists BEFORE call: {file_existed_before}")
        print(f"=== Cache file size BEFORE call: {cache_size_before} bytes")
        
        response = api_client.send_message(messages)
        
        file_exists_after = os.path.exists(cache_path)
        cache_size_after = os.path.getsize(cache_path) if file_exists_after else 0
        print(f"=== Response received: {response is not None}")
        print(f"=== Cache file exists AFTER call: {file_exists_after}")
        print(f"=== Cache file size AFTER call: {cache_size_after} bytes")
        
        # If caching is enabled, verify cache file exists and has content
        if api_client.cache_api_calls:
            assert file_exists_after, f"Cache file should exist at {cache_path}"
            assert cache_size_after > 0, "Cache file should not be empty"
            
            # Verify cache file is valid JSON
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            
            print(f"=== Cache entries: {len(cache_data)}")
            assert len(cache_data) >= 1, "Cache should have at least one entry"
        else:
            print("=== Caching is disabled - use --use_cache flag to enable")

    def test_cache_with_response_format_pydantic(self):
        """
        Test caching with response_format (Pydantic structured output).
        
        This specifically tests the case where ParsedChatCompletion[T] is returned,
        which requires special handling for JSON serialization due to generic type parameters.
        """
        api_client = client()
        
        if not api_client.cache_api_calls:
            pytest.skip("Caching is disabled - use --use_cache flag to enable")
        
        cache_file_name = config_manager.get("cache_file_name")
        cache_path = os.path.abspath(cache_file_name)
        
        # Define a Pydantic model for structured output
        class SimpleResponse(BaseModel):
            message: str
            number: int
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant that responds in JSON."},
            {"role": "user", "content": "Say hello and pick a number between 1 and 10."}
        ]
        
        print(f"\n=== Testing cache with response_format (Pydantic)")
        cache_size_before = os.path.getsize(cache_path) if os.path.exists(cache_path) else 0
        
        # First call - should hit the API and cache the result
        response1 = api_client.send_message(messages, response_format=SimpleResponse)
        
        assert response1 is not None, "First call should return a response"
        print(f"=== First response: {response1}")
        
        cache_size_after_first = os.path.getsize(cache_path) if os.path.exists(cache_path) else 0
        print(f"=== Cache size before: {cache_size_before}, after first call: {cache_size_after_first}")
        
        # Verify cache file can be loaded (this would fail with non-serializable objects)
        with open(cache_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        print(f"=== Cache successfully loaded with {len(cache_data)} entries")
        
        # Second call with same params - should hit the cache
        response2 = api_client.send_message(messages, response_format=SimpleResponse)
        
        assert response2 is not None, "Second call should return a response from cache"
        print(f"=== Second response (from cache): {response2}")
        
        # Responses should be equivalent - the parsed content is nested under 'parsed' key
        # Response format: {'content': '...', 'parsed': {'message': '...', 'number': ...}, ...}
        assert "parsed" in response1, "Response should have 'parsed' key with structured output"
        assert "parsed" in response2, "Cached response should have 'parsed' key"
        assert response1["parsed"]["message"] == response2["parsed"]["message"], "Messages should match"
        assert response1["parsed"]["number"] == response2["parsed"]["number"], "Numbers should match"
