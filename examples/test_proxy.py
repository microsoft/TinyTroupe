#!/usr/bin/env python3
"""
Simple test to verify LiteLLM proxy connection.
"""

import os
import sys

# Set environment variables BEFORE any imports
os.environ["LITELLM_URL"] = "https://utils-litellm-app.nvdvcu.easypanel.host/"
os.environ["LITELLM_KEY"] = "sk-mfOXFYylzZg_hi-24TvBAg"

# Add the tinytroupe directory to the path
sys.path.insert(0, '../tinytroupe')

# Now import
import tinytroupe.litellm_utils as litellm_utils

def test_proxy_connection():
    """Test connection to LiteLLM proxy."""
    print("Testing LiteLLM proxy connection...")
    
    client = litellm_utils.client()
    
    messages = [
        {"role": "user", "content": "Say 'Hello from proxy!'"}
    ]
    
    # Try different model names that might work with the proxy
    model_names_to_try = [
        "groq/llama3-8b-8192",    # Original format        
    ]
    
    for model_name in model_names_to_try:
        try:
            print(f"\nTesting model: {model_name}")
            response = client.send_message(messages, model=model_name)
            print(f"✓ Success with {model_name}")
            print(f"Response: {response['content'][:100]}...")
            break  # If one works, we're good
        except Exception as e:
            print(f"✗ Failed with {model_name}: {str(e)[:100]}...")
    
if __name__ == "__main__":
    test_proxy_connection()
