# Ollama Host Pool Implementation Plan

## Goal
Single simulation, multiple agents. When agents act in parallel, their LLM calls are spread across multiple Ollama instances (different ports) via round-robin, for speed when the machine runs multiple Ollama instances.

## Design

### Config
- **New key**: `ollama_base_urls` (list of URLs)
- **Config.ini**: `OLLAMA_BASE_URLS` = comma-separated URLs, e.g. `http://localhost:11434/v1,http://localhost:11435/v1`
- **Fallback**: If not set, use `OLLAMA_BASE_URL` or `BASE_URL` as single-item list
- **Backward compatible**: Single URL works as today

### OllamaClient
- **Init**: Read `ollama_base_urls`. If list has 2+ URLs, use pool mode. Else use single `base_url`.
- **Request path**: `_make_request` and `_count_tokens` select URL via round-robin (thread-safe)
- **Round-robin**: Atomic counter or lock; each request gets next URL

### Testing
1. **Unit test**: Mock requests; verify round-robin alternates URLs across calls
2. **Unit test**: Single URL mode unchanged
3. **Integration**: Optional test in test_recent_improvements_ollama.py (skipped if single host)

### Documentation
- Update docs/guides/ollama.md with OLLAMA_BASE_URLS usage
- DEVLOG entry

## Files to Modify
- `tinytroupe/__init__.py` - config parsing for ollama_base_urls
- `tinytroupe/clients/ollama_client.py` - pool + round-robin
- `tinytroupe/config.ini` - add OLLAMA_BASE_URLS example (commented)
- `tests/unit/test_ollama_client.py` - add host pool tests
- `docs/guides/ollama.md` - document
- `DEVLOG.md` - note
