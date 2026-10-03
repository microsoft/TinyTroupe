"""Simple script to evaluate multiple Ollama models with TinyTroupe."""

import os
from tinytroupe import config_manager
from tinytroupe import clients as openai_utils


# Ensure we're using the local Ollama server
openai_utils.force_api_type("ollama")

# Optionally override the model list via environment variable
models = os.getenv("OLLAMA_MODELS", "llama2\nphi3\nllava-llama3").split('\n')

prompt = "Give me a short fun fact about artificial intelligence."

for model in models:
    print(f"\n### Testing model: {model}")
    # temporarily override model
    config_manager.update("model", model)
    response = openai_utils.client().send_message([
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ])
    print(response["content"])

# Reset configuration and API type
openai_utils.force_api_type("openai")
config_manager.reset()
