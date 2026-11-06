"""Combine indexed prompt experiments, preserving every attempt and rejecting ID collisions."""

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from analyze_ablations import analyze, result_labels
from audit_prompt_revision import load_lines
from model_case_study import validate_case


def assemble(index_path, prices, reviews, output):
    """Build a reproducible aggregate from an explicit experiment index, without API calls."""
    if output.exists():
        raise FileExistsError(f"Use a new report directory: {output}")
    index = json.loads(index_path.read_text(encoding="utf-8"))
    cases, paths, roles = {}, [], {}
    for experiment in index["experiments"]:
        corpus = index_path.parent / experiment["corpus"]
        path = index_path.parent / experiment["results"]
        if path.resolve() in roles:
            raise ValueError(f"Repeated result file: {path}")
        source = {case["case_id"]: case for case in load_lines(corpus)}
        runs = load_lines(path)
        if not runs:
            raise ValueError(f"Empty result file: {path}")
        if "expected_calls" in experiment and len(runs) != experiment["expected_calls"]:
            raise ValueError(f"Unexpected attempt count in {path}: {len(runs)}")
        for run in runs:
            case = source[run["case_id"]]
            validate_case(case)
            if case["case_id"] in cases:
                previous = cases[case["case_id"]]
                for key in ["request", "original_response", "phase", "experiment"]:
                    if previous[key] != case[key]:
                        raise ValueError(f"Conflicting case ID {case['case_id']}: {key}")
            cases[case["case_id"]] = case
        paths.append(path)
        roles[path.resolve()] = experiment["role"]
    output.mkdir(parents=True)
    combined = output / "combined-cases.jsonl"
    combined.write_text("".join(json.dumps(case, ensure_ascii=False) + "\n"
                               for case in cases.values()), encoding="utf-8")
    analyze(combined, paths, prices, output, reviews)
    report = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
    labels = result_labels(paths)
    role_by_label = {labels[path]: roles[path.resolve()] for path in paths}
    totals = defaultdict(lambda: {
        "calls": 0, "completed": 0, "cost_usd": Decimal(0), "calls_without_usage": 0,
    })
    for row in report["observations"]:
        total = totals[role_by_label[row["result_file"]]]
        total["calls"] += 1
        total["completed"] += row["status"] == "completed"
        if "cost" in row:
            total["cost_usd"] += Decimal(row["cost"]["total_usd"])
        else:
            total["calls_without_usage"] += 1
    with (output / "stage-costs.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["role", "calls", "completed", "cost_usd", "calls_without_usage"]
        )
        writer.writeheader()
        for role, total in totals.items():
            writer.writerow({"role": role, **total})
    (output / "experiment-index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assemble(args.index, args.prices, args.reviews, args.output)
