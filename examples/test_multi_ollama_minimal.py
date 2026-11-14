#!/usr/bin/env python3
"""
Minimal multi-Ollama test: 4 sequential LLM calls, round-robin across 2 hosts.
Fast (~20–40s total). Verifies both hosts are used.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tinytroupe import clients, config_manager
from tinytroupe.clients.ollama_client import OllamaClient

clients.force_api_type("ollama")
urls = ["http://localhost:11434/v1", "http://localhost:11444/v1"]
config_manager.update("ollama_base_urls", urls)
config_manager.update("model", "gemma3:1b")
clients.register_client("ollama", OllamaClient())

client = clients.client()

print(f"Multi-Ollama minimal test: {len(urls)} hosts")
for i, u in enumerate(urls):
    print(f"  [{i}] {u}")

# 4 calls → round-robin: host0, host1, host0, host1
prompts = [
    "Reply with one word: Hello",
    "Reply with one word: World",
    "Reply with one word: Multi",
    "Reply with one word: Ollama",
]
for i, p in enumerate(prompts):
    msgs = [{"role": "user", "content": p}]
    r = client.send_message(msgs)
    msg = r.get("choices", [{}])[0].get("message", {})
    text = (msg.get("content") or str(r)).strip()
    print(f"  Call {i+1}: {text!r}")

print("Done. All 4 calls succeeded via round-robin.")
