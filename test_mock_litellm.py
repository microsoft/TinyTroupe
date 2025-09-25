"""
Test LiteLLM with Vertex AI integration
"""

import os
import sys
from pathlib import Path

# Add the TinyTroupeLiteLLM directory to sys.path
sys.path.append("/workspaces/TinyTroupeLiteLLM")

# Print which Python we're using
print(f"Using Python from: {sys.executable}")

# Set the API key to a mock value for testing
os.environ["GOOGLE_API_KEY"] = "mock_key_for_testing"

try:
    import google.auth

    print("✅ Successfully imported google.auth")

    from google.cloud import aiplatform

    print("✅ Successfully imported google.cloud.aiplatform")
except ImportError as e:
    print(f"❌ Failed to import Google Cloud libraries: {str(e)}")
    sys.exit(1)

try:
    import litellm

    print("✅ Successfully imported litellm")
except ImportError as e:
    print(f"❌ Failed to import litellm: {str(e)}")
    sys.exit(1)

try:
    from tinytroupe import litellm_utils

    print("✅ Successfully imported tinytroupe.litellm_utils")
except ImportError as e:
    print(f"❌ Failed to import tinytroupe.litellm_utils: {str(e)}")
    sys.exit(1)

# Enable debug logging for LiteLLM
litellm._turn_on_debug()

# Try to authenticate with Google Cloud
try:
    credentials, project = google.auth.default()
    print(f"✅ Successfully authenticated with Google Cloud. Project ID: {project}")
except Exception as e:
    print(f"❌ Failed to authenticate with Google Cloud: {str(e)}")
    print("Setting project ID to 'default-project' for testing purposes")
    project = "default-project"

# Set project ID for Vertex AI
os.environ["GOOGLE_CLOUD_PROJECT_ID"] = project

# Set up a mock handler to prevent actual API calls
from types import SimpleNamespace


# Define a fake completion response that matches the litellm response structure
def fake_completion(*args, **kwargs):
    print(
        f"Mock called with: model={kwargs.get('model')}, provider={kwargs.get('provider')}"
    )
    # Create a proper LiteLLM response object
    response = SimpleNamespace()
    response.choices = [SimpleNamespace()]
    response.choices[0].message = SimpleNamespace()
    response.choices[0].message.content = (
        "This is a simulated response for demo purposes."
    )
    response.choices[0].message.role = "assistant"
    return response


# Apply the mock to avoid actual API calls
litellm.completion = fake_completion

# Try to get a response from Vertex AI using litellm_utils
try:
    print("\nTrying to get a response from Vertex AI using litellm_utils...")

    response = litellm_utils.get_completion(
        provider="vertex_ai",
        model="gemini-1.5-flash",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        max_tokens=50,
    )

    print("✅ Successfully got a response from the mock:")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"❌ Failed to get a response: {str(e)}")

    # Print more detailed error information
    import traceback

    print("\nDetailed error information:")
    traceback.print_exc()
