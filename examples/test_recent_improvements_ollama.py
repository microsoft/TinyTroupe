#!/usr/bin/env python3
"""
Small scene to test recent enhancements with Ollama.

Exercises:
- TinyCalendar: add_event, find_events (improved implementation)
- Caching: create_compact_text_representation with template_ref
- listen_and_act (sync behavior) + TinyToolUse with TinyCalendar
- Memory consolidation / episodic buffer (via multi-step run)
- Parallel agent actions (parallelize=True) for concurrent Ollama calls

Requires: ollama serve on a free port. Use non-standard ports to avoid clashes:
  OLLAMA_HOST=127.0.0.1:11444 ollama serve
  ollama pull gemma3:1b  # small model for testing
"""

import sys
import time
import os

# Force Ollama before any tinytroupe imports that touch the API
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tinytroupe import clients as openai_utils
from tinytroupe import config_manager
from tinytroupe.clients.ollama_client import OllamaClient

openai_utils.force_api_type("ollama")

# Use non-standard port (11444) or default 11434 if OLLAMA_TEST_PORT unset
_test_port = os.environ.get("OLLAMA_TEST_PORT", "11444")
_config = config_manager
_config.update("ollama_base_urls", [f"http://localhost:{_test_port}/v1"])
_config.update("model", os.environ.get("OLLAMA_TEST_MODEL", "gemma3:1b"))
_config.update("reasoning_model", os.environ.get("OLLAMA_TEST_MODEL", "gemma3:1b"))
openai_utils.register_client("ollama", OllamaClient())

# Tests that avoid agent package (no circular import)
from tinytroupe.tools import TinyCalendar
from tinytroupe.caching import create_compact_text_representation


def test_tiny_calendar_direct():
    """Direct test of TinyCalendar add_event and find_events (no LLM)."""
    print("\n--- 1. TinyCalendar direct test (add_event, find_events) ---")
    cal = TinyCalendar()
    cal.add_event("2026-02-14", "Team sync", description="Weekly standup")
    cal.add_event("2026-02-14", "Lunch with Oscar")
    ev = cal.find_events(2026, 2, 14)
    assert len(ev) == 2
    assert ev[0]["title"] == "Team sync"
    print(f"   Added 2 events on 2026-02-14, find_events returned {len(ev)} events. OK")


def test_cache_compact_representation():
    """Test create_compact_text_representation with template_ref."""
    print("\n--- 2. Cache compact representation (template_ref) ---")
    key = create_compact_text_representation("my_func", "arg1", "arg2", template_ref="tpl_v1")
    assert "Function:" in key and "TemplateRef:" in key and "tpl_v1" in key
    print(f"   Created cache key (len={len(key)}). OK")


def run_simulation_scene():
    """Run a short simulation with calendar tool and two agents."""
    print("\n--- 3. Simulation scene (Ollama) ---")

    try:
        from tinytroupe.environment import TinyWorld
        from tinytroupe.agent import TinyPerson, TinyToolUse
        from tinytroupe.control import begin, end
        from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect
    except ImportError as e:
        print(f"   Skipping: agent import failed ({e})")
        return

    begin()

    # Shared calendar tool
    calendar = TinyCalendar()
    tooluse = TinyToolUse(tools=[calendar])

    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()
    lisa.add_mental_faculties([tooluse])
    oscar.add_mental_faculties([tooluse])

    world = TinyWorld("Planning Room", [lisa, oscar])
    world.make_everyone_accessible()

    # Prompt that may encourage calendar use
    lisa.listen(
        "Suggest we schedule a short architecture review for next Tuesday. "
        "Then greet Oscar."
    )

    print("   Running 3 simulation steps (Ollama can be slow)...")
    world.run(3, parallelize=False)

    end()
    print("   Simulation complete.")


def run_parallel_speed_test():
    """
    Second test: run a minimal scene with parallelize=True.
    Lisa and Oscar act concurrently (multiple Ollama calls in parallel per step).
    For best speed, use a small model: ollama pull gemma3:1b or llama3.2:1b
    """
    print("\n--- 4. Parallel speed test (parallelize=True) ---")

    try:
        from tinytroupe.environment import TinyWorld
        from tinytroupe.agent import TinyPerson, TinyToolUse
        from tinytroupe.control import begin, end
        from tinytroupe.examples import create_lisa_the_data_scientist, create_oscar_the_architect
    except ImportError as e:
        print(f"   Skipping: {e}")
        return

    begin()
    lisa = create_lisa_the_data_scientist()
    oscar = create_oscar_the_architect()
    world = TinyWorld("Parallel Room", [lisa, oscar])
    world.make_everyone_accessible()
    lisa.listen("Say hi to Oscar briefly.")

    print("   Running 2 steps with parallelize=True (agents act concurrently)...")
    t0 = time.perf_counter()
    world.run(2, parallelize=True)
    elapsed = time.perf_counter() - t0

    end()
    print(f"   Completed in {elapsed:.1f}s.")


if __name__ == "__main__":
    print("TinyTroupe recent improvements test (Ollama)")
    test_tiny_calendar_direct()
    test_cache_compact_representation()
    run_simulation_scene()
    run_parallel_speed_test()
    print("\nDone.")
