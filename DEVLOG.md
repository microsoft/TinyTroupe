# TinyTroupe dev log (supplements git commits)

## 2026-02-17 — test_tool_usage_1 repairs (stimuli echo, WRITE_DOCUMENT, multi-action)

- **1. Stimuli echo** (`action_generator.py`): Detect when model returns `{"stimuli": ...}` instead of `{"actions"}`; retry with corrective reminder; salvage flattened `{type, content, cognitive_state}` when top-level structure is wrong.
- **2. WRITE_DOCUMENT parse/export** (`tiny_word_processor.py`):
  - Fallback when `extract_json` fails: repair truncated JSON, regex-extract title/content, unescape.
  - Use `agent.name` when author is missing.
  - Default content placeholder when model returns only title.
- **3. Similarity replacement** (`tiny_person.py`): Exempt `WRITE_DOCUMENT` from replacement (to avoid discarding side effects).
- **4. Multi-action handling** (`tiny_person.py`): When generator returns a list of actions (e.g. `{"actions": [], ...}` with DONE appended), iterate and process each; append one content per action so `contains_action_type` finds WRITE_DOCUMENT.
- **Config**: `tests/config_openai_cheap.ini` uses gpt-4o-mini. Ollama: `tests/config_ollama.ini`.

---

## 2026-02-16 — test_llm_decorator fix

- **Cause**: When `extract_json` returned `None` (malformed/missing JSON), code called `self.response_json.get()` → AttributeError, caught as generic Exception → returned None. Test expected `isinstance(response, str)`.
- **Fix**: Guard with `_json = self.response_json if isinstance(self.response_json, dict) else {}` and use `_json.get()`. For str output when "value" missing, fall back to raw response text.

---

## 2026-02-16 — TinyTroupe spawns its own Ollama (dual agents)

- **ollama_runner**: New module to start/stop Ollama on dedicated ports. `OllamaInstances` context manager; `start_instances(ports=[11444, 11445])`.
- **Dual ports**: config_ollama.ini uses 11444 and 11445 only (no default 11434). Round-robin for parallel agents.
- **Auto-start in tests**: When `TINYTROUPE_CONFIG=tests/config_ollama.ini`, conftest starts Ollama on 11444 and 11445 before tests, stops after. Repo is self-contained.
- **scripts/start_tinytroupe_ollama.sh**: Manual start of both instances.

---

## 2026-02-16 — Ollama auto-find ports (reusable)

- **OLLAMA_BASE_URL env override**: If set, overrides config. Use `OLLAMA_BASE_URL=http://localhost:11434/v1` to point at a specific port.
- **Connection fallback**: OllamaClient._make_request tries each URL in the pool on connection failure. Works whether Ollama is on 11434, 11444, etc.
- **config_ollama.ini**: OLLAMA_BASE_URLS now lists both ports (`11444, 11434`). Tries test port first, falls back to default. Repo “just works” with Ollama on either port.

---

## 2026-02-16 — API tests with Ollama (TINYTROUPE_CONFIG)

- **Root cause**: Tests that call `listen_and_act`, `client().send_message()`, etc. use the default config (api_type=openai). OpenAIClient requires OPENAI_API_KEY; if unset, tests fail. They do NOT require OpenAI specifically—any LLM backend (Ollama, Azure) would work.
- **TINYTROUPE_CONFIG**: `read_config_file()` now checks env `TINYTROUPE_CONFIG`. If set (e.g. `tests/config_ollama.ini`), that file overlays the default config. Enables API tests without an API key when Ollama is running.
- **Usage**: `TINYTROUPE_CONFIG=tests/config_ollama.ini pytest tests/unit/`. Requires Ollama on port 11444 (or edit config) and `ollama pull gemma3:1b`.
- **test_cache_management**: Fixed ERROR—tests requested `setup` fixture but didn't import `testing_utils`; added `from testing_utils import setup`.

---

## 2026-02-16 — extract_json fixes (test_extract_json)

- **Return value**: On parse failure, return `None` instead of `{}` so callers can distinguish "no valid JSON" from "empty object". Tests expect `None` for invalid/empty input.
- **Trailing commas**: Strip trailing commas before `}` and `]` before parsing; common in LLM output, invalid in JSON. Enables `text_complex_fluff` and similar cases.
- **Error logging**: Guard `filtered_text` access in exception handler (NameError if exception before assignment).
- **Callers**: llm.py `_coerce_to_dict_or_list` handles both `None` and `{}`; `isinstance(result, (dict, list))` covers `None`.

---

## 2026-02-15 — Multi-Ollama real-world test

- **examples/test_multi_ollama.py**: Full simulation with 2 Ollama hosts (parallelize=True).
- **examples/test_multi_ollama_minimal.py**: 4 sequential LLM calls, round-robin verified.
- Tested with Ollama on 11434 + 11444; all calls succeeded.

---

## 2026-02-15 — Logging RecursionError fix

- **Root cause**: File logging raised `RecursionError` during agent creation (e.g. lisa then oscar). Direct file handler emit in the main logging path triggered recursion.
- **Fix**: Use `QueueHandler` + `QueueListener` so file I/O runs in a background thread. `_NoFormatQueueHandler` skips `format()` in `prepare()` to avoid recursion in the main thread. `ThreadSafeFileHandler` (delegate) overrides `handleError` to avoid re-enqueue recursion. `logging.raiseExceptions = False` suppresses error spam. Two-agent setup runs successfully; log files are written.

---

## 2026-02-15 — Test & env fixes

- **Logging**: Writable path resolution with fallbacks (cwd → project root → ~/.tinytroupe → temp). `_get_writable_base_dir()` verifies write access; `_create_file_handler()` returns `None` on failure instead of raising.
- **Cache**: Control default cache path uses `get_writable_data_dir()/data/`; `_save_cache_file` ensures parent dir exists.
- **Seaborn**: Added to `pyproject.toml` for `test_profiling`.
- **Ollama test config** (`tests/config_ollama.ini`): Port 11444, model `gemma3:1b` to avoid clashes with default 11434.
- **Ollama helper** (`scripts/start_ollama_test_port.sh`): Start Ollama on 11444.
- **llm.py**: Fixed invalid escape sequence `\{` → `{`.
- Tests: `test_ollama_client`, `test_profiling` passing. Control tests require API key or Ollama; use `TINYTROUPE_CONFIG=tests/config_ollama.ini` for Ollama.

---

## 2026-02-15 — Enhancement plan implementation

Implemented items from `tinytroupe_enhancement_opportunities_*.plan.md`:

- **ReflectionConsolidator** (`agent/memory.py`): Implemented `_reflect()`; uses `@utils.llm` to consolidate episodic → semantic reflections.
- **Proposition** (`experimentation/proposition.py`): Re-enabled LLM-based `recommendations_for_improvement()` with error handling.
- **TinyCalendar** (`tools/tiny_calendar.py`): Fixed `calenar` typo, implemented `find_events`, adjusted `add_event` kwargs.
- **Intervention** (`steering/intervention.py`): Documented serialization limits and rehydration for `targets`, `precondition_func`, `effect_func`.
- **Simulation validator** (`validation/simulation_validator.py`): Removed WIP TODO.
- **tiny_person** (`agent/tiny_person.py`): Implemented `optimize_memory()`; documented sync behavior of `listen_and_act` / `act`.
- **Cache optimization** (`caching/semantic_cache.py`): Added `create_compact_text_representation(..., template_ref=)` for template-based cache keys.
- **Indentation fix** (`agent/memory.py`): Fixed `get_current_episode` docstring/body indentation.

Status docs updated: `ASYNC_FIX_SURGICAL_PLAN.md`, `optimization_analysis.md`.

### Test scene (Ollama)

- Added `examples/test_recent_improvements_ollama.py` to exercise TinyCalendar, cache compact representation, and full simulation with Ollama.
- Fixed circular imports: `default` proxy in tinytroupe, lazy `TinyWorld` in Proposition, lazy `Intervention` in tiny_world, `openai_utils` import in tiny_person.

### Ollama host pool

- `OLLAMA_BASE_URLS`: comma-separated URLs for round-robin across multiple Ollama instances.
- When agents act in parallel, each LLM request selects the next host.
- Config: `tinytroupe/__init__.py`; client: `OllamaClient._get_base_url()`; tests: `test_ollama_host_pool_round_robin`, `test_ollama_single_url_unchanged`.

---

## 2026-02-15 — Repo & branch audit

### Remote branches (origin = https://github.com/CrazyDubya/TinyTroupe.git)

| Branch | Latest commit | Description |
|--------|---------------|-------------|
| `main` | d98598b | feat: memory size limits (Phase 1, Task 1.1) — **current default** |
| `fix-loglevel-initialization` | 301f6e0 | Fix: Apply initial log level from config at startup |
| `sync-upstream-nov-2025` | 9644c76 | Merge upstream microsoft/TinyTroupe main |
| `claude/implement-phase-one-01C4EgchBzF9vnG2z1qNdNcf` | 19d7f6e | feat: semantic similarity caching (Phase 1, Task 3.3) |
| `claude/prep-major-expansion-018HXYCcspXCWe3e3M7Wvg81` | 116ed79 | docs: Fix review feedback on expansion documentation |

### Local clone

- **Path:** `/Users/pup/TinyTroupe`
- **Checked-out:** `main`
- **Status:** Clean, up to date with `origin/main`

### Repo copies / iCloud

- **iCloud:** No TinyTroupe folder in `~/Library/Mobile Documents/com~apple~CloudDocs/`
- **car-hub:** TinyTroupe not present in `/Users/pup/car-hub/`
- **Other clones:** None found (single working copy at `/Users/pup/TinyTroupe`)

### Branch ancestry (for canonical discussion)

- `main` has advanced beyond `sync-upstream-nov-2025`; merge-base: 91a6632
- `sync-upstream-nov-2025` merged upstream `microsoft/TinyTroupe` main
- Other branches are feature/docs branches, not separate forks

---

## 2026-02-15 — Canonical consolidation

- Brought in unique content from iCloud **tinyexperiment** and **prison** clones
- Created `experiment_archives/tinyexperiment/` with docs, simulation scripts, business/infrastructure/quality design, result JSONs
- Added `TheatreCompany.ipynb`, `aethelburg_scenario/`, `theatre_tools.py` to `examples/`
- Documented prison as upstream baseline (no unique files; merged via sync-upstream)
- Created `EXPERIMENTS_INDEX.md` and `experiment_archives/prison/README.md`
- **main** is the canonical branch
- Second commit: added CommunityRallyTool.py, UnemployedYouth.agent.json to examples/aethelburg_scenario

### Next steps completed (2026-02-15)

1. **Pushed main** to origin
2. **Removed redundant iCloud clones:** github_other/TinyTroupe, tinyexperiment/tinytroupe, prison/TinyTroupe
3. **Experiments reference:** README now links to EXPERIMENTS_INDEX.md; use it as the reference for what's where

---

## 2026-02-15 — Merge upstream microsoft/TinyTroupe

- Merged upstream/main (8378a11) into main
- Incoming: GPT-5 support, Ollama improvements, clients refactor (openai_utils → tinytroupe/clients)
- openai_utils kept as backward-compat alias to clients
- Preserved Phase 1 enhancements: memory limits, semantic cache, moderation/telemetry in config
