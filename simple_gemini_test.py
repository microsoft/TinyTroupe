#!/usr/bin/env python3
"""
Simple test script to verify Gemini model handling in TinyTroupeLiteLLM.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("simple_gemini_test")

# Add the tinytroupe directory to the path
sys.path.insert(0, '')

def main():
    """Test Gemini model handling."""
    try:
        print("Testing Gemini model handling...")
        
        # Import TinyTroupe modules
        import tinytroupe.litellm_utils as litellm_utils
        from tinytroupe import utils
        
        # Read configuration
        config = utils.read_config_file()
        print(f"Current config: provider={config['LLM']['PROVIDER']}, model={config['LLM']['MODEL']}")
        
        # Ensure we're using the correct provider for Gemini
        provider = "vertex_ai"
        model = "vertex_ai/gemini-2.0-flash"
        
        # Modify the mock function to capture parameters
        original_completion = litellm_utils.litellm.completion
        
        # Variables to capture parameters
        processed_params = {}
        
        def mock_completion(**kwargs):
            """Mock function to capture parameters."""
            nonlocal processed_params
            processed_params = kwargs.copy()
            
            # Create a mock response
            class MockResponse:
                def __init__(self):
                    self.choices = [type('obj', (object,), {
                        'message': type('obj', (object,), {
                            'role': 'assistant',
                            'content': 'Mock response'
                        })
                    })]
                    self.usage = type('obj', (object,), {
                        'prompt_tokens': 10,
                        'completion_tokens': 20,
                        'total_tokens': 30
                    })
            
            return MockResponse()
        
        # Replace the litellm.completion function
        litellm_utils.litellm.completion = mock_completion
        
        # Test cases for different model formats
        test_cases = [
            {"model": "gemini/gemini-2.0-flash", "presence_penalty": 0.5},
            {"model": "gemini-2.0-flash", "presence_penalty": 0.5},
            {"model": "vertex_ai/gemini-2.0-flash", "presence_penalty": 0.5}
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\nTest {i+1}: model={test_case['model']}")
            
            # Create a client
            client = litellm_utils.client()
            
            # Reset processed params
            processed_params = {}
            
            # Call send_message
            messages = [{"role": "user", "content": "Test message"}]
            client.send_message(messages, **test_case)
            
            # Print processed parameters
            print("Processed parameters:")
            for k, v in processed_params.items():
                if k != "messages":  # Skip messages to keep output clean
                    print(f"  {k}: {v}")
            
            # Check for correct model format and parameter removal
            if "presence_penalty" not in processed_params:
                print("✓ presence_penalty was correctly removed")
            else:
                print("✗ presence_penalty was not removed")
            
            if processed_params.get("model", "").startswith("vertex_ai/"):
                print("✓ Model was correctly formatted with vertex_ai/ prefix")
            else:
                print(f"✗ Model was not correctly formatted: {processed_params.get('model')}")
        
        # Restore the original function
        litellm_utils.litellm.completion = original_completion
        
        print("\nAll tests completed.")
        return 0
        
    except Exception as e:
        print(f"Error running test: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
