# Development Log (between commits)

## 2026-02-17 – Ollama embeddings, extract_json, retry, plain-text fallback

### Changes
1. **Ollama embeddings (e2e)**: Added `tinytroupe/embeddings/ollama_embedding.py` – `OllamaEmbedding` extends LlamaIndex `BaseEmbedding`, calls `/api/embed`. `__init__.py` wires it when `api_type == "ollama"`. No OpenAI key needed for EpisodicMemory/Grounding.
2. **config_ollama.ini**: `EMBEDDING_MODEL=nomic-embed-text`, `MODEL=qwen-128k:latest` (long context), `REASONING_MODEL=qwen-128k:latest`. Pull `nomic-embed-text` and `qwen-128k` before tests.
3. **extract_json improvements** (`utils/llm.py`): Strip markdown code blocks; use `_extract_first_json_object()` when multiple JSON objects; handle plain strings from models.
4. **Action generator retry**: Retry up to 2 times on empty/unparseable LLM responses. Fallback: when model returns plain text (not JSON), wrap as TALK action.

### Test status
- **test_advanced_memory**: All 9 passed (EpisodicMemory, reflection, semantic indexing with Ollama embeddings).
- **Scenario tests (test_basic_scenarios, test_tool_usage_1)**: Flaky with qwen-128k – model sometimes returns empty, XML-like tags, or plain text. Retries and plain-text fallback help but not always.
- **test_action_generator_with_agent**: Same flakiness – requires real LLM; can fail when model returns non-JSON.

### Run commands
- `ollama pull nomic-embed-text qwen-128k`
- `TINYTROUPE_CONFIG=tests/config_ollama.ini uv run pytest tests/agent/test_advanced_memory.py -v`
- For deterministic scenario tests, use OpenAI/Azure config; Ollama scenario tests are best-effort.

## 2026-02-17 – Scenario fixes, model config, reflection feature

### Changes
1. **Cache serialization fix**: `ensure_serializable` now converts `deque`→list and skips `Lock`; `_save_cache_file` uses it before `json.dump`. Fixes test_basic_scenario_1.
2. **Blank LLM response protection**: Action generator raises clear `ValueError` when content is None/unparseable instead of `TypeError: argument of type 'NoneType' is not iterable`. Retries still apply.
3. **Ollama config**: Switched to `gemma3:4b`, `MAX_COMPLETION_TOKENS=8192`, `NUM_CTX=8192`. gemma3:1b too small for complex scenarios; run `ollama pull gemma3:4b` before tests.
4. **reflect_and_synthesize_knowledge**: Implemented on TinyPerson; reflection tests no longer skipped.

## 2026-02-16 – Testing status

### Change
- `test_llm_decorator`: Skip when `OPENAI_API_KEY` not set and using OpenAI. Test passes with Ollama config (`TINYTROUPE_CONFIG=tests/config_ollama.ini`) or when key is set.

### Fast unit tests (utils, config, cache)
- **32 passed, 1 skipped** (test_llm_decorator skips without API key)
- Run: `uv run pytest tests/unit/test_utils.py tests/unit/test_config.py tests/unit/test_cache_management.py -v`

### Full suite (2026-02-16 run)
- **632 tests** collected; full run in progress (Ollama on 11444/11445)
- First ~20 tests: 3 PASSED, 15 FAILED (agent/scenario tests; LLM-dependent)
- Known failing: `test_advanced_memory` (7), `test_advertisement_scenarios` (2), `test_basic_scenarios` (2), `test_brainstorming_scenarios` (1), `test_extended_scenarios` (3+)
- Unit + non_functional: 583 tests; run ongoing (some action_generator failures seen)
