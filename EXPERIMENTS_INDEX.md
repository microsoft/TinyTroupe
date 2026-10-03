# TinyTroupe Experiments Index

This document tracks experiments and unique content consolidated from multiple clones (local, iCloud tinyexperiment, iCloud prison) into this canonical repo.

## Consolidation summary (2026-02-15)

| Source | Location | Status |
|--------|----------|--------|
| **Local main** | `/Users/pup/TinyTroupe` | Primary; most advanced |
| **iCloud github_other** | `pup8725/github_other/TinyTroupe` | On `sync-upstream-nov-2025`; behind main |
| **iCloud tinyexperiment** | `pup8725/tinyexperiment/tinytroupe` | Content archived → `experiment_archives/tinyexperiment/` |
| **iCloud prison** | `pup8725/prison/TinyTroupe` | Upstream baseline; merged via sync-upstream |

## Contents from tinyexperiment

Archived under `experiment_archives/tinyexperiment/`:

### Docs
- `ASYNC_FIX_SURGICAL_PLAN.md` — Async/coroutine fix for epic simulations
- `ROVODEV_TEAM_PRESERVATION.md` — Multi-agent team personas and sprint notes
- `optimization_analysis.md` — Cache and prompt optimization analysis

### Simulation scripts
- `demo_enterprise_simulation.py`
- `epic_20_agent_crisis_simulation.py`
- `epic_simulation_demo.py`
- `optimized_simulation_framework.py`
- `real_simulation_demo.py`
- `theatre_simulation.py`

### Design / planning
- `business/` — Market analysis, business strategy
- `infrastructure/` — Docker, Kubernetes, scaling
- `quality/` — Test strategy

### Examples (also copied to `examples/`)
- `TheatreCompany.ipynb`, `TheatreCompany_output.ipynb`
- `aethelburg_scenario/` — Scenario experiment
- `theatre_tools.py` — Helper for theatre demos

### Result JSONs (archival)
- `epic_simulation_results.json`, `optimized_simulation_results.json`, `simulation_results.json`, `extracted_real_ai_results.json`

## Code changes already in main

- **config_manager.get** — tinyexperiment had fixes for `config_manager.get` in `tiny_person.py`; main already uses `config_manager` throughout.

## Branch recap (canonical)

- **main** — Canonical branch; includes Phase 1 work, memory limits, semantic caching, expansion docs, and consolidated experiments.
- Remote branches: `sync-upstream-nov-2025`, `fix-loglevel-initialization`, `claude/*` feature branches.
