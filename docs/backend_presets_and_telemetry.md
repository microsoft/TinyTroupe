# Backend presets and LLM telemetry

TinyTroupe now ships two small utilities inspired by the multidomain brainstorm:

- **Backend presets with env warnings**: quickly switch between OpenAI, Azure, and Ollama modes and surface missing environment variables early.
- **LLM telemetry toggles**: emit structured JSONL traces for every model call with latency and token usage details.

## Switching backends safely

Use `apply_backend_preset` to stamp a backend choice into `config.ini` and receive immediate warnings for missing secrets:

```python
from tinytroupe.utils.backend_presets import apply_backend_preset

# Options: "openai", "azure", "ollama"
apply_backend_preset("openai")
```

The helper preserves other config fields and only updates the `API_TYPE` entry. It also checks for the environment variables expected by each backend:

| Backend | Required env vars | Optional env vars |
| --- | --- | --- |
| `openai` | `OPENAI_API_KEY` | – |
| `azure` | `AZURE_OPENAI_ENDPOINT` | `AZURE_OPENAI_KEY` (or Entra ID auth) |
| `ollama` | – | `OLLAMA_BASE_URL`, `OLLAMA_API_KEY` |

Whenever TinyTroupe selects a backend, it now logs a warning if required variables are missing.

## Enabling LLM telemetry

Enable per-call telemetry by flipping the logging flags in `tinytroupe/config.ini`:

```ini
[Logging]
LLM_TELEMETRY_ENABLED=True
LLM_TELEMETRY_PATH=logs/llm_telemetry.jsonl
```

Each LLM invocation appends a JSON line including timestamp, backend, model name, latency, whether the response was served from cache, a prompt token estimate, and any usage metrics returned by the provider. The log file is created automatically if it doesn’t exist.
