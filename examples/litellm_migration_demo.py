#!/usr/bin/env python3
"""
Demonstration script showing the LiteLLM migration in action.
This script shows how to use the new LiteLLM utilities with different providers.
"""

import os
import sys

# Add the tinytroupe directory to the path
sys.path.insert(0, '../tinytroupe')

def demo_basic_litellm_usage():
    """Demonstrate basic LiteLLM usage."""
    print("=== Basic LiteLLM Usage ===")
    
    # Set up environment variables for the demo
    os.environ["LITELLM_URL"] = "https://utils-litellm-app.nvdvcu.easypanel.host/"
    os.environ["LITELLM_KEY"] = "sk-mfOXFYylzZg_hi-24TvBAg"
    
    try:
        import tinytroupe.litellm_utils as litellm_utils
        
        # Create client
        client = litellm_utils.client()
        
        # Test message
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What are the benefits of using LiteLLM?"}
        ]
        
        response = client.send_message(messages, model="groq/llama3-8b-8192")
        
        print(f"Response: {response['content']}")
        print("✓ Basic LiteLLM usage successful!")
        
    except Exception as e:
        print(f"✗ Error: {e}")

def demo_agent_with_litellm():
    """Demonstrate agent creation with LiteLLM."""
    print("\n=== Agent with LiteLLM ===")
    
    # Set up environment variables for the demo
    os.environ["LITELLM_URL"] = "https://utils-litellm-app.nvdvcu.easypanel.host/"
    os.environ["LITELLM_KEY"] = "sk-mfOXFYylzZg_hi-24TvBAg"
    
    try:
        from tinytroupe.agent import TinyPerson
        
        # Create an agent
        agent = TinyPerson("Alice")
        agent.define("occupation", "Data Scientist")
        agent.define("personality_traits", ["analytical", "curious", "helpful"])
        
        print(f"Created agent: {agent.name}")
        print(f"Occupation: {agent.get('occupation')}")
        print(f"Personality: {agent.get('personality_traits')}")
        
        # Test agent interaction
        agent.listen("Hello! Can you tell me about your work?")
        actions = agent.pop_latest_actions()
        
        if actions:
            print(f"Agent response: {actions[0]['action']['content']}")
        else:
            print("No actions generated")
            
        print("✓ Agent with LiteLLM successful!")
        
    except Exception as e:
        print(f"✗ Error: {e}")

def demo_multi_provider_support():
    """Demonstrate multi-provider support."""
    print("\n=== Multi-Provider Support ===")
    
    try:
        import tinytroupe.litellm_utils as litellm_utils
        
        # Set up environment variables for the demo
        os.environ["LITELLM_URL"] = "https://utils-litellm-app.nvdvcu.easypanel.host/"
        os.environ["LITELLM_KEY"] = "sk-mfOXFYylzZg_hi-24TvBAg"
        
        client = litellm_utils.client()
        
        # Test with different models (LiteLLM will route to appropriate providers)
        models_to_test = [
            "groq/llama3-8b-8192",    # OpenAI
            # "claude-3-haiku-20240307",  # Anthropic (if API key available)
            # "command-nightly",          # Cohere (if API key available)
        ]
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello from [MODEL_NAME]'"}
        ]
        
        for model in models_to_test:
            try:
                print(f"Testing model: {model}")
                response = client.send_message(messages, model=model)
                print(f"  Response: {response['content'][:50]}...")
            except Exception as e:
                print(f"  Error with {model}: {e}")
        
        print("✓ Multi-provider support demonstrated!")
        
    except Exception as e:
        print(f"✗ Error: {e}")

def demo_usage_tracking():
    """Demonstrate usage tracking."""
    print("\n=== Usage Tracking ===")
    
    try:
        import tinytroupe.litellm_utils as litellm_utils
        
        # Set up environment variables for the demo
        os.environ["LITELLM_URL"] = "https://utils-litellm-app.nvdvcu.easypanel.host/"
        os.environ["LITELLM_KEY"] = "sk-mfOXFYylzZg_hi-24TvBAg"
        
        client = litellm_utils.client()
        
        # Send a few messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Count to 3."}
        ]
        
        for i in range(3):
            response = client.send_message(messages, model="groq/llama3-8b-8192")
            print(f"Message {i+1}: {response['content'][:30]}...")
        
        # Get usage report
        usage = client.get_usage_report()
        print(f"Usage report: {usage}")
        
        print("✓ Usage tracking demonstrated!")
        
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    """Run all demonstrations."""
    print("LiteLLM Migration Demonstration")
    print("=" * 50)
    
    demos = [
        demo_basic_litellm_usage,
        demo_agent_with_litellm,
        demo_multi_provider_support,
        demo_usage_tracking,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"Demo failed: {e}")
        
        print()  # Add spacing between demos
    
    print("=" * 50)
    print("LiteLLM Migration Demo Complete!")
    print("\nKey Benefits of the Migration:")
    print("1. Universal API: Support for 100+ LLM providers")
    print("2. Standardized Interface: Consistent API across providers")
    print("3. Built-in Fallbacks: Automatic fallback between models")
    print("4. Cost Tracking: Built-in usage and cost monitoring")
    print("5. Rate Limiting: Automatic rate limit handling")

if __name__ == "__main__":
    main() 