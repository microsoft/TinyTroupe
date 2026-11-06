"""Compare a fresh CSV export with the exact DataFrame captured by a notebook."""

import argparse
import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def main():
    """Check every exported cell, preserving empty values and original row order."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--tables", type=Path, required=True)
    parser.add_argument("--table", required=True)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args()
    receipt = json.loads(args.run.read_text(encoding="utf-8"))
    if receipt.get("status") != "completed":
        raise RuntimeError("CSV review requires a completed notebook execution.")
    started = datetime.fromisoformat(receipt["started_at"]).timestamp()
    if any(path.stat().st_mtime < started for path in (args.csv, args.tables)):
        raise RuntimeError("CSV or captured table predates this execution.")
    captured = json.loads(args.tables.read_text(encoding="utf-8"))[args.table]
    expected = pd.DataFrame(**captured).reset_index(drop=True).fillna("").astype(str)
    actual = pd.read_csv(args.csv, dtype=str, keep_default_na=False)
    pd.testing.assert_frame_equal(actual, expected)
    print(f"CSV exactly matches {len(expected)} rows and {len(expected.columns)} columns.")


if __name__ == "__main__":
    main()
