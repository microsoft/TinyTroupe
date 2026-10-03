#!/bin/bash
# Start TinyTroupe's dual Ollama instances (11444, 11445) for parallel agents.
# Usage: ./scripts/start_tinytroupe_ollama.sh
# Then: TINYTROUPE_CONFIG=tests/config_ollama.ini pytest tests/unit/ -v

set -e

export OLLAMA_HOST=127.0.0.1:11444
ollama serve &
PID1=$!

export OLLAMA_HOST=127.0.0.1:11445
ollama serve &
PID2=$!

echo "Ollama started on 11444 (pid=$PID1) and 11445 (pid=$PID2)"
echo "Pull model: OLLAMA_HOST=127.0.0.1:11444 ollama pull gemma3:1b"
echo "Stop: kill $PID1 $PID2"
wait
