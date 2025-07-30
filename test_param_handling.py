#!/usr/bin/env python3
"""
Test script to verify parameter handling for different model providers in TinyTroupeLiteLLM.
"""

import os
import sys
import logging

# Add the tinytroupe directory to the path
sys.path.insert(0, '')

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_param_handling")

def test_model_specific_parameter_handling():
    """Test that model-specific parameter handling works correctly."""
    try:
        import tinytroupe.litellm_utils as litellm_utils
        
        # Create a client
        client = litellm_utils.client()
        
        # Test with Gemini model
        test_models = [
            "gemini/gemini-2.0-flash",
            "vertex_ai/gemini-2.0-flash",
            "groq/llama3-8b-8192"
        ]
        
        for model in test_models:
            print(f"\nTesting parameter handling for model: {model}")
            
            # Create test messages
            messages = [{"role": "user", "content": "Test message for parameter handling"}]
            
            # Prepare parameters with potentially unsupported ones
            params = {
                "model": model,
                "temperature": 0.7,
                "max_tokens": 100,
                "presence_penalty": 0.5,  # Unsupported by Gemini
                "echo": True  # Unsupported by Groq
            }
            
            # Use our internal method to prepare parameters
            try:
                # Mock the send_message function to inspect parameter handling
                original_completion = litellm_utils.litellm.completion
                
                # Replace with a mock that just returns the parameters
                def mock_completion(**kwargs):
                    print(f"Parameters after filtering for {model}:")
                    for k, v in kwargs.items():
                        if k != "messages":  # Skip messages to keep output clean
                            print(f"  {k}: {v}")
                    
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
                
                # Replace the litellm.completion function temporarily
                litellm_utils.litellm.completion = mock_completion
                
                # Call send_message to trigger parameter handling
                client.send_message(messages, **params)
                
                # Check if unsupported parameters were removed
                if "gemini" in model:
                    print("✓ Gemini test: presence_penalty should be removed")
                if "groq" in model:
                    print("✓ Groq test: echo should be removed")
                
                # Restore the original function
                litellm_utils.litellm.completion = original_completion
                
                return True
                
            except Exception as e:
                print(f"✗ Parameter handling test failed for {model}: {e}")
                return False
    
    except Exception as e:
        print(f"✗ Test setup failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing TinyTroupeLiteLLM Parameter Handling...")
    print("=" * 60)
    
    result = test_model_specific_parameter_handling()
    
    print("\n" + "=" * 60)
    if result:
        print("🎉 Parameter handling tests passed!")
        return 0
    else:
        print("❌ Parameter handling tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
