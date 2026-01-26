# TinyTroupe Test Strategy

## Test Categories

| Directory | Purpose |
|-----------|---------|
| `unit/` | Unit tests for individual components (agents, memory, config, extraction, etc.) |
| `scenarios/` | End-to-end scenario tests (brainstorming, advertisements, market research) |
| `non_functional/` | Non-functional tests (security) |

## LLM Testing Philosophy

Tests that exercise LLM functionality use **real LLM API calls** rather than mocks. This means these tests serve as **integration tests** as well, verifying actual model behavior. We deliberately avoid mocking LLM calls because:

1. **Centrality** - LLM calls are so central to TinyTroupe that mocking them would undermine test validity
2. **Behavioral verification** - Real calls ensure agent behaviors remain coherent across model updates
3. **Caching support** - The `--use_cache` option provides determinism and speed without sacrificing realism

Use `--use_cache` for fast, reproducible runs; use `--refresh_cache` when validating against fresh model responses.

## Pytest Markers

| Marker | Purpose | Command Example |
|--------|---------|-----------------|
| `core` | Quick validation tests (~1 hour with cache). Run after important modifications. | `pytest -m "core"` |
| `slow` | Long-running tests (large-scale generation, extensive scenarios). Excluded from core. | `pytest -m "not slow"` |
| `examples` | Jupyter notebook execution tests | `pytest -m "examples"` |
| `notebooks` | Specific notebook execution examples | `pytest -m "notebooks"` |
| `gpt41mini` | Tests using gpt-4.1-mini model for alternative model compatibility | `pytest -m "gpt41mini"` |

## Running Tests

### Quick Validation (Core Tests)
```bash
# Run core tests with caching (~1 hour)
pytest -s --use_cache -m "core and not slow and not examples"

# Or use the batch file
test_core_with_cache.bat
```

### Full Test Suite
```bash
# All tests except examples/slow (faster)
pytest -s --use_cache -m "not examples and not slow"

# Or use the batch file
test_with_cache_without_slow.bat
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--use_cache` | Use cached LLM API responses (faster, deterministic) |
| `--refresh_cache` | Delete cache and make fresh API calls |

## Test Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `setup` | function | Auto-runs before each test. Resets simulation state, clears agents/worlds/factories. |
| `focus_group_world` | function | Pre-built `TinyWorld` with Lisa (data scientist), Oscar (architect), and Marcos (physician). |

## Key Testing Utilities

**`testing_utils.py`** provides:
- `proposition_holds(text)` - Uses LLM to verify semantic properties of text
- `contains_action_type(actions, type)` - Checks action lists for specific types
- `contains_action_content(actions, content)` - Checks action content
- `remove_file_if_exists(path)` - Safe file deletion
- `agents_personas_are_equal(a1, a2)` - Compare agent configurations

## Core Test Coverage

The `@pytest.mark.core` marker identifies tests that:
1. **Run quickly** - Prioritize fast unit tests and small-scale LLM tests
2. **Cover critical paths** - Agent lifecycle, memory, config, caching, extraction
3. **Catch regressions** - End-to-end scenarios with multi-agent collaboration

### Core Tests by Component

| Component | Tests | Coverage |
|-----------|-------|----------|
| Config | 4 | Reading, caching, global state, thread safety |
| API Cache | 5 | Save/load, roundtrip, retrieval, error handling |
| Memory | 7 | Episodic & semantic storage/retrieval |
| LLM Chat | 7 | Initialization, calls, type coercion, errors |
| Utils | 3 | JSON parsing, error decorators |
| Extraction | 4 | JSON/text/docx export, normalization |
| ResultsExtractor | 5 | Agent/world extraction, field hints, caching |
| Enrichment | 1 | Content enrichment |
| TinyPerson | 11 | act, listen, define, socialize, see, think, goal, move, save |
| TinyWorld | 4 | run, broadcast, state encode/decode |
| Control | 3 | Agent/world/factory checkpointing |
| Factory | 5 | Person generation, post-processing, demography |
| ActionGenerator | 4 | Initialization, quality checks, serialization |
| Scenarios | 8 | Tool usage, conversations, brainstorming, ads, stories, research |

**Total: ~71 core tests** targeting ~60 min runtime with `--use_cache`

## Writing New Tests

1. **Add `@pytest.mark.core`** to tests that validate critical functionality
2. **Add `@pytest.mark.slow`** to tests with large-scale generation or extended runtimes
3. **Use `proposition_holds()`** for semantic verification of LLM outputs
4. **Use fixtures** - Leverage `setup` (auto) and `focus_group_world` for consistency
5. **Use cache** - Design tests to work with `--use_cache` for faster CI runs
