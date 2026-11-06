"""Select and browse saved cases by explicit filters, without API calls or quality relabeling."""

import argparse
import csv
import html
import json
from pathlib import Path

from mine_execution_cases import load_lines
from model_case_study import validate_case


def select(corpus, output, phases=(), split=None, case_ids=(), limit=20):
    """Write a bounded replay corpus, complete-output review page and blank semantic review queue."""
    if limit <= 0:
        raise ValueError("limit must be positive.")
    if output.exists():
        raise FileExistsError(f"Use a new selection directory: {output}")
    selected, found = [], set()
    wanted = set(case_ids)
    for case in load_lines(corpus):
        if wanted and case["case_id"] not in wanted:
            continue
        if phases and case["phase"] not in phases:
            continue
        if split and case.get("selection", {}).get("split") != split:
            continue
        if len(selected) < limit:
            validate_case(case)
            selected.append(case)
        found.add(case["case_id"])
    if wanted - found:
        raise ValueError(f"Unknown or filtered-out case IDs: {sorted(wanted - found)}")
    if not selected:
        raise ValueError("No matching cases.")
    if wanted and len(found) > limit:
        raise ValueError("Increase limit to include every explicitly requested case.")
    output.mkdir(parents=True)
    (output / "selected.jsonl").write_text(
        "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in selected), encoding="utf-8"
    )
    with (output / "review-queue.csv").open("x", encoding="utf-8", newline="") as stream:
        fields = ["case_id", "phase", "group", "criterion", "status", "evidence"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for case in selected:
            writer.writerow({
                "case_id": case["case_id"], "phase": case["phase"], "group": case["group"],
                "criterion": case["assessment"]["criterion"], "status": "unreviewed", "evidence": "",
            })
    page = (
        "<!doctype html><meta charset='utf-8'><title>Execution case review</title>"
        "<style>body{font:16px/1.5 system-ui;max-width:1100px;margin:32px auto}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:16px}"
        "details{margin:18px 0}</style><h1>Execution case review</h1>"
        "<p>Observed outputs are not gold answers. No output has been truncated; "
        "the exact replay payload, including any image inputs, is in selected.jsonl. "
        "Review public evidence and private simulated thoughts according to each field's scope.</p>"
    )
    for case in selected:
        page += (
            "<details><summary>" + html.escape(case["case_id"] + " | " + case["phase"])
            + "</summary><p>" + html.escape(case["assessment"]["criterion"]) + "</p>"
            "<h3>Complete observed response</h3><pre>"
            + html.escape(json.dumps(case["original_response"], ensure_ascii=False, indent=2))
            + "</pre><details><summary>Complete replay request</summary><pre>"
            + html.escape(json.dumps(case["request"], ensure_ascii=False, indent=2))
            + "</pre></details></details>"
        )
    (output / "review.html").write_text(page, encoding="utf-8")
    print(f"Selected {len(selected)} cases from {len(found)} matches; no API calls.")
    return selected


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--phase", action="append", default=[])
    parser.add_argument("--split", choices=["optimization", "validation"])
    parser.add_argument("--case", action="append", default=[])
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    select(args.corpus, args.output, args.phase, args.split, args.case, args.limit)
