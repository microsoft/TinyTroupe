#!/usr/bin/env bash
set -euo pipefail

# Local-only Hermes stack setup for Ollama.
# Requires Ollama daemon running.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ollama pull qwen3:14b
ollama pull qwen3:8b
ollama pull phi4-mini
ollama pull phi4-reasoning

ollama create hermes-qwen3-plan -f "$ROOT_DIR/Modelfile.qwen3-plan"
ollama create hermes-qwen3-chat -f "$ROOT_DIR/Modelfile.qwen3-chat"
ollama create hermes-phi4-tools -f "$ROOT_DIR/Modelfile.phi4-tools"
ollama create hermes-phi4-reasoning-alt -f "$ROOT_DIR/Modelfile.phi4-reasoning-alt"

chmod +x "$ROOT_DIR/hermes"
chmod +x "$ROOT_DIR/../hermes" 2>/dev/null || true
chmod +x "$ROOT_DIR/../hermes-gui" 2>/dev/null || true
chmod +x "$ROOT_DIR/../hermesMac" 2>/dev/null || true

cat <<'EOF'
Installed local Hermes tags:
- hermes-qwen3-plan
- hermes-qwen3-chat
- hermes-phi4-tools
- hermes-phi4-reasoning-alt
EOF
ollama list | grep -E 'hermes-|qwen3:14b|qwen3:8b|phi4-mini|phi4-reasoning' || true
