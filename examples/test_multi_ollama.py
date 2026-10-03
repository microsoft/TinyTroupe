#!/usr/bin/env python3
"""
Real-world test: multiple Ollama hosts with round-robin.

Requires two Ollama instances:
  - Default: 127.0.0.1:11434
  - Second:  OLLAMA_HOST=127.0.0.1:11444 ollama serve

Run: uv run python examples/test_multi_ollama.py
"""

import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tinytroupe import clients as openai_utils
from tinytroupe import config_manager
from tinytroupe.clients.ollama_client import OllamaClient

openai_utils.force_api_type("ollama")

# MULTI-OLLAMA: comma-separated URLs, round-robin
urls = os.environ.get(
    "OLLAMA_BASE_URLS",
    "http://localhost:11434/v1,http://localhost:11444/v1"
).split(",")
urls = [u.strip() for u in urls if u.strip()]
config_manager.update("ollama_base_urls", urls)
config_manager.update("model", os.environ.get("OLLAMA_TEST_MODEL", "gemma3:1b"))
config_manager.update("reasoning_model", os.environ.get("OLLAMA_TEST_MODEL", "gemma3:1b"))
openai_utils.register_client("ollama", OllamaClient())

print(f"Multi-Ollama test: {len(urls)} host(s)")
for i, u in enumerate(urls):
    print(f"  [{i}] {u}")

from tinytroupe.control import begin, end
from tinytroupe.environment import TinyWorld
from tinytroupe.agent import TinyPerson, TinyToolUse
from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect

begin()
lisa = create_lisa_the_data_scientist()
oscar = create_oscar_the_architect()
world = TinyWorld("Multi-Ollama Room", [lisa, oscar])
world.make_everyone_accessible()
lisa.listen("Say hi to Oscar in one short sentence.")

print("Running 2 steps with parallelize=True (concurrent LLM calls → round-robin across hosts)...")
t0 = time.perf_counter()
world.run(2, parallelize=True)
elapsed = time.perf_counter() - t0
end()

print(f"Done in {elapsed:.1f}s. Multi-Ollama round-robin working.")
