# Experiment bundles and guardrails

Two additional improvements from the multidomain plan are now available:

- **Reproducible experiment bundles** capture configs, metadata, and results in a zipped artifact.
- **Moderation preflight** blocks or warns on unsafe prompts before calling the model.
- **Persona/world preflight checks** highlight missing specs before a run starts.

## Running experiments with bundles

Use `run_with_bundle` to execute any callable that returns JSON-serializable results while saving the surrounding context:

```python
from tinytroupe.experimentation.experiment_bundle import run_with_bundle


def run_my_sim():
    # ... run simulation ...
    return {"status": "ok", "summary": "hello"}

bundle_info = run_with_bundle(run_my_sim, metadata={"scenario": "demo"})
print(bundle_info["archive_path"])  # path to the zipped artifact
```

Each bundle includes:

- A copy of `config.ini` to capture knobs used during the run.
- Metadata (timestamp, seed, git commit when available, custom metadata) in `metadata.json`.
- Serialized results in `results.json`.
- Telemetry logs if `LLM_TELEMETRY_ENABLED` was true and the log file existed.

## Enabling moderation

Add or toggle the moderation entries in `tinytroupe/config.ini`:

```ini
[Moderation]
ENABLE_MODERATION=True
MODERATION_ACTION=block  # or warn
MODERATION_MODEL=omni-moderation-latest
MODERATION_BLOCK_MESSAGE=[BLOCKED BY MODERATION]
```

When enabled, prompts are sent through OpenAI's moderation endpoint before the model call. Flagged content will either log a warning (`warn`) or immediately return `MODERATION_BLOCK_MESSAGE` (`block`). Moderation only runs when `API_TYPE=openai`.

## Persona and world preflight

```python
from tinytroupe.validation import assert_simulation_ready

assert_simulation_ready(personas=[alice, bob], world=my_world)
```

This call raises a `ValueError` describing missing persona fields (name, backstory, beliefs, goals, personality, knowledge) or an empty world, helping catch setup gaps early.
