"""Utilities to run experiments with reproducible bundles."""

from __future__ import annotations

import json
import random
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from tinytroupe import config_manager

DEFAULT_OUTPUT_DIR = Path("artifacts/experiment_runs")


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    try:  # numpy is optional
        import numpy as np  # type: ignore

        np.random.seed(seed)
    except Exception:
        pass



def _copy_if_exists(src: Path, dest: Path) -> None:
    if src.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dest)



def run_with_bundle(
    run_callable: Callable[[], Any],
    *,
    run_id: Optional[str] = None,
    output_dir: Path | str = DEFAULT_OUTPUT_DIR,
    seed: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
    include_telemetry: bool = True,
) -> Dict[str, Any]:
    """
    Execute a simulation function and capture a reproducible bundle.

    The bundle contains:
    - A copy of the current config.ini
    - Metadata (timestamp, seed, git commit, extra user metadata)
    - Experiment results serialized to JSON
    - Optional LLM telemetry logs if enabled and present
    - A zipped archive of the bundle directory
    """

    run_identifier = run_id or datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    bundle_root = Path(output_dir) / run_identifier
    bundle_root.mkdir(parents=True, exist_ok=True)

    resolved_seed = seed if seed is not None else int(datetime.utcnow().timestamp())
    _seed_everything(resolved_seed)

    # Persist metadata early
    metadata_payload: Dict[str, Any] = {
        "run_id": run_identifier,
        "seed": resolved_seed,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "config_loglevel": config_manager.get("loglevel"),
    }

    if metadata:
        metadata_payload.update(metadata)

    try:
        git_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent.parent)
            .decode("utf-8")
            .strip()
        )
        metadata_payload["git_commit"] = git_commit
    except Exception:
        pass

    metadata_path = bundle_root / "metadata.json"
    metadata_path.write_text(json.dumps(metadata_payload, indent=2, default=str), encoding="utf-8")

    # Copy config snapshot
    repo_root = Path(__file__).resolve().parent.parent
    _copy_if_exists(repo_root / "config.ini", bundle_root / "config.ini")

    results = run_callable()
    results_path = bundle_root / "results.json"
    results_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")

    if include_telemetry and config_manager.get("llm_telemetry_enabled"):
        telemetry_path = Path(config_manager.get("llm_telemetry_path", "logs/llm_telemetry.jsonl"))
        if telemetry_path.exists():
            _copy_if_exists(telemetry_path, bundle_root / telemetry_path.name)

    archive_path = shutil.make_archive(str(bundle_root), "zip", root_dir=bundle_root)

    return {
        "bundle_root": str(bundle_root),
        "archive_path": archive_path,
        "metadata_path": str(metadata_path),
        "results_path": str(results_path),
    }
