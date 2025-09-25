"""
Simple script to test Google Cloud authentication for Vertex AI.
"""

import os

# Check for Google Cloud credentials
# credentials_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
credentials_file = "generativeus-0d0773590ed1.json"
print(f"GOOGLE_APPLICATION_CREDENTIALS: {credentials_file}")

if credentials_file:
    if os.path.exists(credentials_file):
        print(f"✅ Credentials file exists at {credentials_file}")
    else:
        print(f"❌ Credentials file does not exist at {credentials_file}")
else:
    print("❌ GOOGLE_APPLICATION_CREDENTIALS environment variable is not set")

# Try to import and use Google Cloud libraries
try:
    import google.auth
    from google.cloud import aiplatform

    print("\nTrying to authenticate with Google Cloud...")
    try:
        # Try to get default credentials
        credentials, project = google.auth.default()
        print(f"✅ Successfully authenticated with Google Cloud. Project ID: {project}")
    except Exception as e:
        print(f"❌ Failed to authenticate with Google Cloud: {str(e)}")

    # Try to initialize Vertex AI
    try:
        print("\nTrying to initialize Vertex AI...")
        aiplatform.init()
        print("✅ Successfully initialized Vertex AI")
    except Exception as e:
        print(f"❌ Failed to initialize Vertex AI: {str(e)}")

except ImportError as e:
    print(f"❌ Failed to import Google Cloud libraries: {str(e)}")
