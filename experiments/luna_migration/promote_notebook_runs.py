"""Merge explicitly approved execution outputs into source-matching notebooks."""

import argparse
import copy
import json
from pathlib import Path

import nbformat
from run_notebook_comparison import library_fingerprint


def promote(row, source_dir, artifact_root):
    """Preserve current sources and metadata while replacing only execution artifacts."""
    if not row.get("execution_audit_passed"):
        raise ValueError(f"Execution audit has not passed: {row['name']}")
    record_path = artifact_root / row["folder"] / (row["name"] + ".run.json")
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if (
        record.get("library_sha256") != library_fingerprint(source_dir.parent / "tinytroupe")
        or record.get("library_unchanged_during_run") is not True
    ):
        raise ValueError(f"Library changed since execution: {row['name']}")
    source_path = source_dir / (row["name"] + ".ipynb")
    original_text = source_path.read_text(encoding="utf-8")
    source = nbformat.reads(original_text, as_version=4)
    executed = nbformat.read(
        artifact_root / row["folder"] / source_path.name, as_version=4
    )
    source_cells = [cell for cell in source.cells if cell.cell_type == "code"]
    executed_cells = [cell for cell in executed.cells if cell.cell_type == "code"][1:-1]
    if [cell.source for cell in source_cells] != [cell.source for cell in executed_cells]:
        raise ValueError(f"Sources changed since execution: {row['name']}")
    for target, result in zip(source_cells, executed_cells):
        if result.source.strip() and result.execution_count is None:
            raise ValueError(f"Unexecuted source cell: {row['name']}")
        if any(output.output_type == "error" for output in result.outputs):
            raise ValueError(f"Notebook has error output: {row['name']}")
        target.outputs = copy.deepcopy(result.outputs)
        target.execution_count = (
            result.execution_count - 1 if result.execution_count is not None else None
        )
        for output in target.outputs:
            if output.output_type == "execute_result":
                output.execution_count -= 1
        if "execution" in result.metadata:
            target.metadata["execution"] = copy.deepcopy(result.metadata["execution"])
    for key in ("language_info", "widgets"):
        if key in executed.metadata:
            source.metadata[key] = copy.deepcopy(executed.metadata[key])
        elif key == "widgets":
            source.metadata.pop(key, None)
    nbformat.validate(source)
    if source_path.read_text(encoding="utf-8") != original_text:
        raise ValueError(f"Concurrent notebook edit detected: {row['name']}")
    nbformat.write(source, source_path)
    saved = nbformat.read(source_path, as_version=4)
    if [(c.cell_type, c.source) for c in saved.cells] != [
        (c.cell_type, c.source) for c in source.cells
    ]:
        raise ValueError(f"Saved notebook source verification failed: {row['name']}")
    return {
        "name": row["name"], "folder": row["folder"], "saved": str(source_path),
        "started_at": record["started_at"], "library_sha256": record["library_sha256"],
    }


def main():
    """Promote only notebooks named by the caller after their quality review."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("names", nargs="+")
    args = parser.parse_args()
    rows = {
        row["name"]: row for row in json.loads(args.audit.read_text(encoding="utf-8"))["runs"]
    }
    receipts = (
        json.loads(args.receipts.read_text(encoding="utf-8")) if args.receipts.exists() else {}
    )
    for name in args.names:
        receipts[name] = promote(rows[name], args.source_dir, args.artifact_root)
        args.receipts.write_text(json.dumps(receipts, indent=2), encoding="utf-8")
        print("PROMOTED", name)


if __name__ == "__main__":
    main()
