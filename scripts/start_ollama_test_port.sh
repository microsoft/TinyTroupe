#!/bin/bash
# Start Ollama on non-standard port 11444 for testing (avoids clash with default 11434)
# Usage: ./scripts/start_ollama_test_port.sh
# Then: ollama pull gemma3:1b
#       uv run python examples/test_recent_improvements_ollama.py

export OLLAMA_HOST=127.0.0.1:11444
ollama serve
