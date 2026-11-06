"""Audit prompt-ablation results and render complete outputs with actual usage costs."""

import argparse
import csv
import html
import json
import os
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

import jsonschema

from model_case_study import digest, validate_case
from study_report import response_cost


def result_labels(paths):
    """Disambiguate same-named result files across experiment rounds using relative paths."""
    if not paths:
        raise ValueError("At least one results file is required.")
    root = Path(os.path.commonpath([str(path.resolve().parent) for path in paths]))
    return {path: path.resolve().relative_to(root).as_posix() for path in paths}


def output_checks(case, response):
    """Measure observable output properties, not subjective realism or preferred sentiment."""
    content = response["choices"][0]["message"].get("content")
    checks = {"json_valid": False, "schema_valid": None}
    try:
        value = json.loads(content)
    except (TypeError, json.JSONDecodeError) as error:
        checks["parse_error"] = str(error)
        return checks
    checks["json_valid"] = True
    fmt = case["request"].get("response_format", {})
    if fmt.get("type") == "json_schema":
        errors = list(jsonschema.Draft202012Validator(fmt["json_schema"]["schema"]).iter_errors(value))
        checks["schema_valid"] = not errors
        if errors:
            checks["schema_errors"] = [error.message for error in errors]
    if not isinstance(value, dict):
        checks["object_valid"] = False
        return checks
    if case["phase"] == "agent_action":
        actions = value.get("actions", [])
        talks = [action.get("content", "") for action in actions if action.get("type") == "TALK"]
        public = "\n".join(talks)
        checks.update(
            public_answer_present=bool(public.strip()), talk_count=len(talks),
            ends_with_done=bool(actions and actions[-1].get("type") == "DONE"),
            public_words=len(public.split()), public_text=public,
        )
        ranking = re.search(r"Ranking:\s*([A-E](?:\s*,\s*[A-E]){4})", public, re.I)
        if ranking:
            order = re.findall(r"[A-E]", ranking[1].upper())
            checks["ranking"] = order
            checks["ranking_is_permutation"] = sorted(order) == list("ABCDE")
        decision = re.match(r"\s*(Yes|No)\b[.!,:;\s]*(.*)", public, re.I | re.S)
        if decision:
            checks["decision"] = decision[1].lower()
            checks["public_reason_present"] = bool(decision[2].strip())
        score = re.search(r"(?<!\d)([1-5])(?!\d)", public)
        if score:
            checks["first_public_number_1_to_5"] = int(score[1])
    elif case["phase"] == "extraction":
        checks["extracted"] = value
    elif case["phase"] == "persona_generation":
        mandatory = [
            "name", "age", "gender", "nationality", "residence", "education",
            "long_term_goals", "occupation", "style", "personality", "preferences",
            "beliefs", "skills", "behaviors", "health", "relationships", "other_facts",
        ]
        checks["missing_persona_fields"] = [key for key in mandatory if key not in value]
        checks["persona"] = {key: value.get(key) for key in [
            "name", "age", "gender", "nationality", "residence", "occupation",
            "personality", "preferences", "style",
        ]}
    checks["content_words"] = len(content.split())
    return checks


def analyze(corpus, results, prices_path, output, reviews_path=None):
    """Verify requests and save transparent metrics, avoiding automatic semantic pass labels."""
    cases = {case["case_id"]: case for case in map(
        json.loads, corpus.read_text(encoding="utf-8").splitlines()
    )}
    for case in cases.values():
        validate_case(case)
    prices = json.loads(prices_path.read_text(encoding="utf-8"))
    rows = []
    seen = set()
    labels = result_labels(results)
    for path in results:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            run = json.loads(line)
            identity = (labels[path], run["case_id"], run["condition_id"], run["replicate"])
            if identity in seen:
                raise ValueError(f"Duplicate observation: {identity}")
            seen.add(identity)
            case = cases[run["case_id"]]
            body = {key: value for key, value in run["request"].items() if key != "model"}
            expected = {key: value for key, value in case["request"].items() if key != "model"}
            if body != expected or digest(run["request"]) != run["request_sha256"]:
                raise ValueError(f"Request changed unexpectedly: {identity}")
            row = {
                "result_file": labels[path], "case_id": run["case_id"],
                "source_case_id": case["experiment"]["source_case_id"],
                "variant": case["experiment"]["variant"], "phase": case["phase"],
                "model": run["request"]["model"], "replicate": run["replicate"],
                "status": run["status"], "elapsed_seconds": run["elapsed_seconds"],
                "started_at": run["started_at"],
            }
            if "response" in run:
                if run["response"]["model"] != row["model"]:
                    raise ValueError(f"Unexpected returned model: {identity}")
                row["response_id"] = run["response"]["id"]
                row["cost"] = response_cost(run["response"], prices)
                row["checks"] = output_checks(case, run["response"])
                row["content"] = run["response"]["choices"][0]["message"].get("content")
            else:
                row["error"] = run["error"]
            rows.append(row)
    totals = defaultdict(lambda: {
        "calls": 0, "api_completed": 0, "calls_with_usage": 0, "elapsed_call_seconds": 0,
        "input_tokens": 0, "cached_input_tokens": 0, "cache_write_tokens": 0,
        "output_tokens": 0, "reasoning_tokens": 0, "cost_usd": Decimal(0),
    })
    for row in rows:
        total = totals[row["model"]]
        total["calls"] += 1
        total["api_completed"] += row["status"] == "completed"
        total["elapsed_call_seconds"] += row["elapsed_seconds"]
        if "cost" in row:
            total["calls_with_usage"] += 1
            total["cost_usd"] += Decimal(row["cost"]["total_usd"])
            for key in ("input_tokens", "cached_input_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens"):
                total[key] += row["cost"][key]
    for total in totals.values():
        total["cost_usd"] = str(total["cost_usd"])
    report = {
        "totals": dict(totals), "pricing": prices, "observations": rows,
        "interpretation": "API stop, JSON validity and schema validity are not semantic success. "
        "Public-answer checks do not infer answers from private THINK. Ranking/purchase changes "
        "are not automatically improvements. A numeric score candidate requires manual context review.",
    }
    if reviews_path:
        report["quality_review"] = json.loads(reviews_path.read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    (output / "analysis.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    fields = [
        "result_file", "case_id", "model", "replicate", "status", "elapsed_seconds",
        "input_tokens", "uncached_input_tokens", "cached_input_tokens", "cache_write_tokens",
        "output_tokens", "reasoning_tokens", "input_usd", "cached_input_usd",
        "cache_write_usd", "output_usd", "total_usd",
    ]
    with (output / "costs.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, **row.get("cost", {})})
    page = (
        "<!doctype html><meta charset='utf-8'><title>Prompt ablation results</title>"
        "<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:16px}"
        "details{margin:18px 0}summary{cursor:pointer;font-weight:bold}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:9px;"
        "vertical-align:top;text-align:left}</style><h1>Prompt ablation results</h1>"
        "<p>" + html.escape(report["interpretation"]) + "</p>"
    )
    if reviews_path:
        review = report["quality_review"]
        page += "<h2>Findings</h2><p>" + html.escape(review["summary"]) + "</p>"
        for section, columns in [
            ("hypotheses", ["hypothesis", "luna", "terra", "conclusion"]),
            ("case_reviews", ["case", "status", "evidence"]),
        ]:
            if section not in review:
                continue
            page += "<table><tr>" + "".join("<th>" + key.title() + "</th>" for key in columns) + "</tr>"
            for finding in review[section]:
                page += "<tr>" + "".join("<td>" + html.escape(finding[key]) + "</td>"
                                        for key in columns) + "</tr>"
            page += "</table>"
        page += "<h2>Limitations</h2><pre>" + html.escape(
            json.dumps(review["limitations"], ensure_ascii=False, indent=2)
        ) + "</pre>"
    page += "<h2>Actual usage-based costs</h2><pre>" + html.escape(
        json.dumps(dict(totals), indent=2)
    ) + "</pre><h2>Complete outputs and observable checks</h2>"
    for row in sorted(rows, key=lambda x: (x["source_case_id"], x["model"], x["variant"], x["result_file"], x["replicate"])):
        title = f"{row['case_id']} | {row['model']} | {row['result_file']} #{row['replicate']}"
        page += "<details><summary>" + html.escape(title) + "</summary><pre>" + html.escape(
            json.dumps(row, ensure_ascii=False, indent=2)
        ) + "</pre></details>"
    (output / "report.html").write_text(page, encoding="utf-8")
    print(json.dumps(dict(totals), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--results", type=Path, nargs="+", required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()
    analyze(args.corpus, args.results, args.prices, args.output, args.reviews)
