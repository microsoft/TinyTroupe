"""
Simple script to test if we can create a mock Vertex AI client
"""
import os
import sys
from unittest.mock import patch, MagicMock

# Set the fake credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/workspaces/TinyTroupeLiteLLM/fake-gcp-credentials.json"
os.environ["GOOGLE_CLOUD_PROJECT_ID"] = "fake-project-id"

# We'll use mocking to avoid actually calling the Vertex AI API
with patch('google.auth.default', return_value=(MagicMock(), "fake-project-id")):
    with patch('google.cloud.aiplatform.init'):
        try:
            import google.auth
            from google.cloud import aiplatform
            
            print("Successfully imported Google Cloud libraries")
            
            # Try to initialize Vertex AI (this will be mocked)
            try:
                print("Trying to initialize Vertex AI (mocked)...")
                aiplatform.init()
                print("✅ Successfully initialized Vertex AI (mocked)")
            except Exception as e:
                print(f"❌ Failed to initialize Vertex AI: {str(e)}")
                
            # Now try to import and use LiteLLM with Vertex AI
            try:
                import sys
                sys.path.insert(0, '/workspaces/TinyTroupeLiteLLM')
                
                import litellm
                
                # Mock the completion method to avoid actual API calls
                with patch('litellm.completion', return_value={"choices": [{"message": {"content": "This is a mock response"}}]}):
                    print("\nTrying to use LiteLLM with Vertex AI...")
                    response = litellm.completion(
                        model="vertex_ai/gemini-2.0-flash",
                        messages=[{"role": "user", "content": "Hello!"}]
                    )
                    print(f"✅ Mock response: {response}")
            except Exception as e:
                print(f"❌ Failed to use LiteLLM with Vertex AI: {str(e)}")
                import traceback
                traceback.print_exc()
            
        except ImportError as e:
            print(f"❌ Failed to import Google Cloud libraries: {str(e)}")
