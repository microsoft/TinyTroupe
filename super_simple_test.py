#!/usr/bin/env python3
"""
Super simple test script to verify Gemini model handling in TinyTroupeLiteLLM.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test")

# Add the tinytroupe directory to the path
sys.path.insert(0, '')

def main():
    try:
        import tinytroupe.litellm_utils as litellm_utils
        
        # Create a simple client
        client = litellm_utils.client()
        
        # Test with different model formats
        test_models = [
            "gemini/gemini-2.0-flash",
            "vertex_ai/gemini-2.0-flash"
        ]
        
        # Override completion function
        original_completion = litellm_utils.litellm.completion
        
        def mock_completion(**kwargs):
            print(f"Parameters sent to LiteLLM:")
            for k, v in kwargs.items():
                if k != "messages":
                    print(f"  {k}: {v}")
            
            # Return a mock response
            class MockResponse:
                def __init__(self):
                    self.choices = [type('obj', (object,), {
                        'message': type('obj', (object,), {
                            'role': 'assistant',
                            'content': 'This is a mock response'
                        })
                    })]
                    self.usage = type('obj', (object,), {
                        'prompt_tokens': 10,
                        'completion_tokens': 20,
                        'total_tokens': 30
                    })
            
            return MockResponse()
        
        # Replace completion function
        litellm_utils.litellm.completion = mock_completion
        
        for model in test_models:
            print(f"\nTesting model: {model}")
            
            # Create test messages
            messages = [{"role": "user", "content": "Test message"}]
            
            # Test with presence_penalty (should be removed for Gemini)
            response = client.send_message(
                messages,
                model=model,
                temperature=0.7,
                presence_penalty=0.5
            )
            
            print(f"Response: {response}")
        
        # Restore original function
        litellm_utils.litellm.completion = original_completion
        
        print("\nTest completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
