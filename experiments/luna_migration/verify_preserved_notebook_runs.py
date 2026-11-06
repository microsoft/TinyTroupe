"""Verify saved notebook outputs and paused-run caches without making API calls."""

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import nbformat

from run_notebook_comparison import library_fingerprint


def main():
    """Compare promoted outputs with their reviewed executions and validate paused files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_root
    audit = json.loads((root / "luna-sweep-execution-audit.json").read_text(encoding="utf-8"))
    reviews = json.loads((root / "luna-sweep-quality-reviews.json").read_text(encoding="utf-8"))
    promotions = json.loads((root / "luna-sweep-promotion-receipts.json").read_text(encoding="utf-8"))
    resume = json.loads((root / "luna-sweep-resume-state.json").read_text(encoding="utf-8"))
    rows = {row["name"]: row for row in audit["runs"]}
    fingerprint = library_fingerprint(args.source_dir.parent / "tinytroupe")
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "api_calls": 0,
        "library_sha256": fingerprint,
        "promotions": [],
        "rejected_executions": [],
        "paused_runs": [],
    }
    for name, receipt in promotions.items():
        row = rows[name]
        review = reviews[name]
        assert row["execution_audit_passed"], name
        assert review["decision"] in {"accept", "accept_with_caveats"}, name
        assert fingerprint == receipt["library_sha256"] == row["library_sha256"], name
        assert receipt["started_at"] == row["started_at"] == review["reviewed_started_at"], name
        saved = nbformat.read(args.source_dir / (name + ".ipynb"), as_version=4)
        executed = nbformat.read(root / row["folder"] / (name + ".ipynb"), as_version=4)
        target_cells = [cell for cell in saved.cells if cell.cell_type == "code"]
        executed_cells = [cell for cell in executed.cells if cell.cell_type == "code"][1:-1]
        assert [cell.source for cell in target_cells] == [cell.source for cell in executed_cells], name
        for target, source in zip(target_cells, executed_cells):
            expected_outputs = copy.deepcopy(source.outputs)
            for output in expected_outputs:
                if output.output_type == "execute_result":
                    output.execution_count -= 1
            assert target.outputs == expected_outputs, (name, "saved outputs differ")
            expected_count = source.execution_count - 1 if source.execution_count is not None else None
            assert target.execution_count == expected_count, (name, "execution count differs")
            assert not any(output.output_type == "error" for output in target.outputs), name
        nbformat.validate(saved)
        result["promotions"].append({"name": name, "source_and_outputs_match": True})
    for name, review in reviews.items():
        if review["decision"] != "reject":
            continue
        row = rows[name]
        assert row["execution_audit_passed"], name
        assert fingerprint == row["library_sha256"], name
        assert review["reviewed_started_at"] == row["started_at"], name
        notebook_path = root / row["folder"] / (name + ".ipynb")
        executed = nbformat.read(notebook_path, as_version=4)
        assert notebook_path.with_suffix(".txt").is_file(), name
        nbformat.validate(executed)
        result["rejected_executions"].append({"name": name, "preserved": True})
    for run in resume["stopped_runs"]:
        directory = root / run["case"]
        notebook_path = directory / run["notebook"]
        notebook = nbformat.read(notebook_path, as_version=4)
        receipt = json.loads(notebook_path.with_suffix(".run.json").read_text(encoding="utf-8"))
        assert receipt["started_at"] == run["started_at"], run["case"]
        assert receipt["status"] == "error" and receipt["library_unchanged_during_run"], run["case"]
        assert receipt["library_sha256"] == fingerprint, run["case"]
        assert notebook_path.with_suffix(".txt").is_file(), run["case"]
        cache_path = directory / "api.cache.json"
        assert cache_path.stat().st_size == run["cache_bytes"], run["case"]
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        assert isinstance(cache, dict) and cache, run["case"]
        result["paused_runs"].append({
            "case": run["case"],
            "notebook": run["notebook"],
            "notebook_cells": len(notebook.cells),
            "cache_entries": len(cache),
            "cache_bytes": cache_path.stat().st_size,
            "preserved": True,
        })
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"Verified {len(result['promotions'])} saved executions, "
        f"{len(result['rejected_executions'])} preserved negative executions and "
        f"{len(result['paused_runs'])} paused runs; no API calls."
    )


if __name__ == "__main__":
    main()
