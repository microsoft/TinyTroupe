"""Audit isolated notebook runs without treating execution success as quality approval."""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from run_notebook_comparison import library_fingerprint


def read_json(path):
    """Return a JSON document, or a visible status for absent/in-progress artifacts."""
    if not path.exists():
        return None, "not_started"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except json.JSONDecodeError:
        return None, "artifact_write_in_progress"


def audit(source_dir, artifact_root, assignments, expected_model, expected_effort):
    """Check real outputs, model settings, source correspondence, and captured tables."""
    rows = []
    expected_library = library_fingerprint(source_dir.parent / "tinytroupe")
    for name, folder in assignments.items():
        stem = artifact_root / folder / name
        record, status = read_json(stem.with_suffix(".run.json"))
        row = {"name": name, "folder": folder, "status": status or record.get("status", "running")}
        rows.append(row)
        if record is None:
            continue
        row.update({key: record.get(key) for key in ("elapsed_seconds", "current_cell", "started_at", "library_sha256")})
        row["expected_model"] = (
            record.get("model") == expected_model and record.get("effort") == expected_effort
        )
        row["library_matches"] = (
            record.get("library_sha256") == expected_library
            and record.get("library_unchanged_during_run") is True
        )
        if record.get("status") == "error":
            row["error_tail"] = record["error"][-1200:]
        if record.get("status") != "completed":
            continue
        notebook, status = read_json(stem.with_suffix(".ipynb"))
        if notebook is None:
            row["status"] = status
            continue
        source = json.loads((source_dir / (name + ".ipynb")).read_text(encoding="utf-8"))
        original_code = [cell for cell in source["cells"] if cell["cell_type"] == "code"]
        executed_code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
        source_text = lambda cell: "".join(cell["source"])
        row["instrumentation_identified"] = (
            "COMPARISON_MODEL" in source_text(executed_code[0])
            and "COMPARISON_USAGE" in source_text(executed_code[-1])
        )
        executed_code = executed_code[1:-1]
        row["source_matches"] = (
            [source_text(cell) for cell in original_code]
            == [source_text(cell) for cell in executed_code]
        )
        row["all_code_executed"] = all(
            cell.get("execution_count") is not None
            for cell in executed_code if source_text(cell).strip()
        )
        row["errors"] = [
            {"ename": output["ename"], "evalue": output["evalue"]}
            for cell in executed_code for output in cell.get("outputs", [])
            if output["output_type"] == "error"
        ]
        row["simulation_errors"] = [
            message
            for cell in executed_code for output in cell.get("outputs", [])
            if output["output_type"] == "stream"
            for message in re.findall(
                r"Agent [^\n]+ generated an exception:[^\n]*",
                "".join(output.get("text", [])),
            )
        ]
        tables, _ = read_json(stem.with_suffix(".tables.json"))
        row["tables"] = {
            key: {"rows": len(value["data"]), "columns": value["columns"]}
            for key, value in (tables or {}).items()
        }
        row["execution_audit_passed"] = all(
            row[key] for key in (
                "expected_model", "library_matches", "instrumentation_identified", "source_matches", "all_code_executed"
            )
        ) and not row["errors"] and not row["simulation_errors"]
    return {"updated_at": datetime.now(timezone.utc).isoformat(), "runs": rows}


def main():
    """Write a compact, reproducible execution audit for the notebook sweep."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--expected-model", required=True)
    parser.add_argument("--expected-effort", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    queue = json.loads(args.manifest.read_text(encoding="utf-8"))
    assignments = {
        job["name"].removesuffix(".ipynb"): job["id"]
        for lane in queue.values() for job in lane
    }
    report = audit(args.source_dir, args.artifact_root, assignments,
                   args.expected_model, args.expected_effort)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for row in report["runs"]:
        print(row["folder"], row["status"], "audit", row.get("execution_audit_passed"),
              "seconds", row.get("elapsed_seconds"), "source_matches", row.get("source_matches"))


if __name__ == "__main__":
    main()
