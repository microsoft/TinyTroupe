"""
Test LiteLLM with Vertex AI integration
"""

import os
import sys
from pathlib import Path

# Add the TinyTroupeLiteLLM directory to sys.path
sys.path.append("/workspaces/TinyTroupeLiteLLM")

try:
    from tinytroupe import litellm_utils

    print("✅ Successfully imported litellm_utils")
except ImportError as e:
    print(f"❌ Failed to import litellm_utils: {str(e)}")
    sys.exit(1)

# Try to authenticate with Google Cloud
try:
    import google.auth

    try:
        credentials, project = google.auth.default()
        print(f"✅ Successfully authenticated with Google Cloud. Project ID: {project}")
        os.environ["GOOGLE_CLOUD_PROJECT_ID"] = project
    except Exception as e:
        print(f"⚠️ Failed to authenticate with Google Cloud: {str(e)}")
        print("You need to set up authentication. Options:")
        print("1. Run: gcloud auth application-default login")
        print("2. Set GOOGLE_APPLICATION_CREDENTIALS environment variable")
        print("3. Use a service account key file")
        project = "your-project-id"  # Replace with your actual project ID
        os.environ["GOOGLE_CLOUD_PROJECT_ID"] = project
except ImportError as e:
    print(f"❌ Failed to import google.auth: {str(e)}")
    sys.exit(1)

# Try to use litellm_utils to get a response from Vertex AI
try:
    print("\nTrying to get a response from Vertex AI using litellm_utils...")

    # Use the default litellm API type (which is the universal interface)
    # The provider (vertex_ai) is handled through the model configuration
    litellm_utils.force_api_type("litellm")

    # Get the client instance from litellm_utils
    client = litellm_utils.client()

    # Try to get a response from Vertex AI using send_message
    # The model is configured in config.ini as vertex_ai/gemini-2.0-flash
    messages = [
        {"role": "user", "content": "Hello, how are you? Please respond briefly."}
    ]
    response = client.send_message(current_messages=messages, max_tokens=50)

    print("✅ Successfully got a response from Vertex AI:")
    print(response)
except Exception as e:
    print(f"❌ Failed to get a response from Vertex AI: {str(e)}")

    # Print more detailed error information
    import traceback

    print("\nDetailed error information:")
    traceback.print_exc()
