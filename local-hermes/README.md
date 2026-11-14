# Local Hermes stack for Mac Studio M2 64GB

Recommendation after checking current model catalogs:

Primary local stack
- Planner / main conversation: Qwen3-14B
- Fast discussion / lightweight follow-up: Qwen3-8B
- Tool caller / executor: Phi-4-mini
- American 14B fallback planner: Phi-4-reasoning

Why Qwen3-14B stays primary
- It has the strongest long-context story in the 14B class.
- Qwen3 docs and model cards explicitly call out agent/tool capabilities.
- Qwen3 supports switching between thinking and non-thinking modes.
- Phi-4 is good, but the official Phi-4 card is 16K context and Phi-4-reasoning is 32K; that is weaker than Qwen3-14B's long-context path.

Why Phi-4 is still useful
- Phi-4-reasoning is the closest American 14B model worth considering.
- Phi-4-mini supports function calling and is well suited to tool-heavy execution.

Suggested role split
- qwen3:14b -> default planner / general conversation
- qwen3:8b -> fast chat / router / lightweight assistant
- phi4-mini -> tool calling / executor
- phi4-reasoning -> American fallback planner

Notes
- Ollama version on this machine: 0.21.1
- Existing local model cache already includes qwen3.5, llama3.2, deepseek-r1:14b, gemma, mistral, and others.
- All model sizes are feasible on 64GB unified memory if you keep only 1-2 hot at once.

Local router
- `/Users/pup/TinyTroupe/hermes` is the top-level entrypoint.
- `/Users/pup/TinyTroupe/local-hermes/hermes` is the underlying router.
- Use `tool:` prefix to force the tool model.
- Use `plan:` prefix to force the planner.
- Use `reason:` prefix to force the American reasoning fallback.
- Otherwise the router picks based on simple heuristics.

Visual layer
- `/Users/pup/TinyTroupe/hermes-gui` launches the browser-based second communication layer.
- `/Users/pup/TinyTroupe/hermesMac` starts the GUI in the background and opens the browser on this Mac.
- It keeps the chat transcript in the browser and sends it to the local router.

Personality matrix
- `personality-matrix.md` captures the TinyTroupe-inspired local assistant rules: structured persona, episodic/semantic memory, grounding, and validation.

