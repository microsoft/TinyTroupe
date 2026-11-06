"""Verify repaired requests, expose exact outputs and validate indexed reconstructions."""

import argparse
import html
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import jsonschema

from mine_execution_cases import load_lines
from model_case_study import digest, validate_case
from normalization_assignments import reconstruct
from sampling_selections import reconstruct as reconstruct_sampling
from review_phase_study import checks, cost_with_bounds


def review(case_paths, result_paths, source_paths, prices_path, output):
    """Keep failures explicit and semantic judgments separate from mechanical gates."""
    cases, sources = {}, {}
    for path in source_paths:
        for source in load_lines(path):
            validate_case(source)
            if source["case_id"] in sources and source != sources[source["case_id"]]:
                raise ValueError("Conflicting original sources.")
            sources[source["case_id"]] = source
    for path in case_paths:
        for case in load_lines(path):
            validate_case(case)
            if case["case_id"] in cases:
                raise ValueError("Duplicate case ID.")
            cases[case["case_id"]] = case
    prices = json.loads(prices_path.read_text(encoding="utf-8"))
    records, ids, response_ids = [], set(), set()
    output.mkdir(parents=True, exist_ok=True)
    for path in result_paths:
        for run in load_lines(path):
            if run["case_id"] in ids:
                raise ValueError("Duplicate replay observation.")
            ids.add(run["case_id"])
            case = cases[run["case_id"]]
            source = sources[case["experiment"]["source_case_id"]]
            if run["request"] != case["request"] or digest(run["request"]) != run["request_sha256"]:
                raise ValueError("Replay request changed.")
            record = {"case_id": run["case_id"], "phase": case["phase"],
                      **case["experiment"], "status": run["status"],
                      "elapsed_seconds": run["elapsed_seconds"]}
            if "response" not in run:
                record["error"] = run["error"]
                records.append(record)
                continue
            response = run["response"]
            if response["id"] in response_ids:
                raise ValueError("Duplicate API response ID.")
            response_ids.add(response["id"])
            content = response["choices"][0]["message"].get("content")
            record.update(content=content, response_id=response["id"],
                          cost=cost_with_bounds(response, prices))
            indexed = case["experiment"]["adapter"] in ("indexed_normalization", "indexed_sampling")
            pipeline = case["experiment"]["adapter"] == "normalization_pipeline"
            measured = {"raw_output_characters": len(content or "")} if indexed or pipeline else checks(case, content)
            if pipeline:
                try:
                    value = json.loads(content)
                    jsonschema.validate(value, case["request"]["response_format"]["json_schema"]["schema"])
                except (ValueError, jsonschema.ValidationError) as exc:
                    measured.update(schema_valid=False, schema_error=str(exc))
                else:
                    measured["schema_valid"] = True
            if indexed:
                try:
                    value = json.loads(content)
                    jsonschema.validate(value, case["request"]["response_format"]["json_schema"]["schema"])
                    restored = (reconstruct(source, value)
                                if case["experiment"]["adapter"] == "indexed_normalization"
                                else reconstruct_sampling(source, value))
                except (ValueError, jsonschema.ValidationError) as exc:
                    measured["reconstruction_valid"] = False
                    measured["reconstruction_error"] = str(exc)
                else:
                    measured = checks(source, json.dumps(restored, ensure_ascii=False))
                    measured["reconstruction_valid"] = True
                    measured["assignment_schema_valid"] = True
                    record["reconstructed"] = restored
                    if case["experiment"]["adapter"] == "indexed_normalization":
                        record["group_sizes"] = {k: len(v) for k, v in restored.items()}
                        record["semantic_samples"] = {}
                        for label, members in restored.items():
                            positions = sorted({round(i * (len(members) - 1) / 9) for i in range(10)})
                            record["semantic_samples"][label] = [members[i] for i in positions]
            record["checks"] = measured
            records.append(record)
    if ids != set(cases):
        raise ValueError(f"Missing/extra observations: {ids ^ set(cases)}")
    costs = [r["cost"] for r in records if "cost" in r]
    lower = sum((Decimal(c["total_usd"] if c["total_usd"] is not None else c["minimum_usd"])
                 for c in costs), Decimal(0))
    upper = sum((Decimal(c["total_usd"] if c["total_usd"] is not None else c["maximum_usd"])
                 for c in costs), Decimal(0))
    summary = {
        "calls": len(records), "unique_sources": len({r["source_case_id"] for r in records}),
        "statuses": dict(Counter(r["status"] for r in records)),
        "list_price_bounds_usd": [str(lower), str(upper)],
        "calls_without_usage": len(records) - len(costs),
        "missing_write_usage": sum(c["total_usd"] is None for c in costs),
        "semantic_success_not_automatically_inferred": True, "records": records,
    }
    (output / "observations.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    page = ["<!doctype html><meta charset='utf-8'><title>Failing prompt iteration</title>",
            "<style>body{font:16px/1.5 system-ui;max-width:1300px;margin:32px auto}"
            "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f4f6;padding:14px}</style>",
            "<h1>Failing prompt iteration</h1><p>Automatic gates are not semantic quality verdicts. "
            "Indexed normalization explicitly changes the intermediate schema; original strings are restored deterministically.</p>",
            "<pre>" + html.escape(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2)) + "</pre>"]
    for i, record in enumerate(records, 1):
        path = output / f"{i:03d}-{record['phase']}.txt"
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        page += ["<details><summary>" + html.escape(record["case_id"]) + "</summary><pre>",
                 html.escape(json.dumps(record, ensure_ascii=False, indent=2)), "</pre>",
                 "<details><summary>Exact paid request</summary><pre>",
                 html.escape(json.dumps(cases[record["case_id"]]["request"], ensure_ascii=False, indent=2)),
                 "</pre></details></details>"]
    (output / "report.html").write_text("\n".join(page), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, action="append", required=True)
    parser.add_argument("--results", type=Path, action="append", required=True)
    parser.add_argument("--sources", type=Path, action="append", required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review(args.corpus, args.results, args.sources, args.prices, args.output)
