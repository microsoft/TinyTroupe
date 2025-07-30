#!/usr/bin/env python3
"""
Test script to verify the LiteLLM migration works correctly.
This script tests the basic functionality of the migrated code.
"""

import os
import sys

# Add the tinytroupe directory to the path
sys.path.insert(0, 'tinytroupe')

def test_litellm_import():
    """Test that LiteLLM utilities can be imported."""
    try:
        import tinytroupe.litellm_utils as litellm_utils
        print("✓ Successfully imported litellm_utils")
        return True
    except Exception as e:
        print(f"✗ Failed to import litellm_utils: {e}")
        return False

def test_litellm_client_creation():
    """Test that LiteLLM client can be created."""
    try:
        import tinytroupe.litellm_utils as litellm_utils
        client = litellm_utils.client()
        print("✓ Successfully created LiteLLM client")
        return True
    except Exception as e:
        print(f"✗ Failed to create LiteLLM client: {e}")
        return False

def test_litellm_message_sending():
    """Test that LiteLLM can send messages."""
    try:
        import tinytroupe.litellm_utils as litellm_utils
        
        # Set up environment variables for the test
        os.environ["LITELLM_URL"] = "https://utils-litellm-app.nvdvcu.easypanel.host/"
        os.environ["LITELLM_KEY"] = "sk-mfOXFYylzZg_hi-24TvBAg"
        
        client = litellm_utils.client()
        
        # Test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, LiteLLM migration successful!'"}
        ]
        
        response = client.send_message(messages, model="groq/llama3-8b-8192")
        
        if response and "content" in response:
            print(f"✓ Successfully sent message via LiteLLM: {response['content'][:100]}...")
            return True
        else:
            print(f"✗ Unexpected response format: {response}")
            return False
            
    except Exception as e:
        print(f"✗ Failed to send message via LiteLLM: {e}")
        return False

def test_agent_creation():
    """Test that agents can be created with the new LiteLLM utilities."""
    try:
        import tinytroupe.agent.tiny_person as tiny_person
        from tinytroupe.agent import TinyPerson
        
        # Set up environment variables for the test
        os.environ["LITELLM_URL"] = "https://utils-litellm-app.nvdvcu.easypanel.host/"
        os.environ["LITELLM_KEY"] = "sk-mfOXFYylzZg_hi-24TvBAg"
        
        # Create a simple agent
        agent = TinyPerson("Test Agent")
        print("✓ Successfully created TinyPerson agent")
        return True
        
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
        return False

def test_configuration():
    """Test that the new configuration structure works."""
    try:
        import tinytroupe.utils as utils
        config = utils.read_config_file()
        
        # Check that LLM section exists
        if "LLM" in config:
            print("✓ Found LLM configuration section")
            print(f"  - Provider: {config['LLM'].get('PROVIDER', 'Not set')}")
            print(f"  - Model: {config['LLM'].get('MODEL', 'Not set')}")
            return True
        else:
            print("✗ LLM configuration section not found")
            return False
            
    except Exception as e:
        print(f"✗ Failed to read configuration: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing LiteLLM Migration...")
    print("=" * 50)
    
    tests = [
        ("LiteLLM Import", test_litellm_import),
        ("LiteLLM Client Creation", test_litellm_client_creation),
        ("Configuration", test_configuration),
        ("LiteLLM Message Sending", test_litellm_message_sending),
        ("Agent Creation", test_agent_creation),
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
    print(f"Migration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LiteLLM migration successful!")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 