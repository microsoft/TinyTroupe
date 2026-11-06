"""Compare saved model outputs and calculate list-price costs from actual API usage."""

import argparse
import csv
import html
import json
from decimal import Decimal
from pathlib import Path


def response_cost(response, prices):
    """Partition actual input usage; never double-count cached/write or reasoning tokens."""
    model = response["model"]
    rate = prices["models"][model]
    tier = response.get("service_tier")
    if tier not in (None, "default", "standard"):
        raise ValueError(f"Unpriced service tier: {tier}")
    usage = response["usage"]
    details = usage["prompt_tokens_details"]
    counts = {
        "input_tokens": usage["prompt_tokens"],
        "cached_input_tokens": details["cached_tokens"],
        "cache_write_tokens": details["cache_write_tokens"],
        "output_tokens": usage["completion_tokens"],
        "reasoning_tokens": usage["completion_tokens_details"]["reasoning_tokens"],
    }
    counts["uncached_input_tokens"] = (
        counts["input_tokens"] - counts["cached_input_tokens"] - counts["cache_write_tokens"]
    )
    if any(not isinstance(n, int) or n < 0 for n in counts.values()):
        raise ValueError("Invalid token usage partition.")
    if counts["reasoning_tokens"] > counts["output_tokens"]:
        raise ValueError("Reasoning tokens must be included in completion tokens.")
    long = counts["input_tokens"] > rate["long_context_threshold"]
    input_multiplier = Decimal(rate["long_input_multiplier"] if long else "1")
    output_multiplier = Decimal(rate["long_output_multiplier"] if long else "1")
    parts = {}
    for label, count, multiplier in [
        ("input", counts["uncached_input_tokens"], input_multiplier),
        ("cached_input", counts["cached_input_tokens"], input_multiplier),
        ("cache_write", counts["cache_write_tokens"], input_multiplier),
        ("output", counts["output_tokens"], output_multiplier),
    ]:
        parts[label + "_usd"] = str(Decimal(count) * Decimal(rate[label]) * multiplier / 1000000)
    parts["total_usd"] = str(sum(Decimal(value) for value in parts.values()))
    return {**counts, **parts, "long_context": long}


def build_report(corpus, results, prices_path, output, reviews_path=None):
    """Save paired full outputs, per-call costs and machine-readable usage totals."""
    cases = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines() if line.strip()]
    runs = [json.loads(line) for line in results.read_text(encoding="utf-8").splitlines() if line.strip()]
    prices = json.loads(prices_path.read_text(encoding="utf-8"))
    indexed = {case["case_id"]: case for case in cases}
    pairs = []
    for run in runs:
        case = indexed[run["case_id"]]
        if run["request"]["messages"] != case["request"]["messages"]:
            raise ValueError(f"Changed input messages: {run['case_id']}")
        pair = {
            "case_id": run["case_id"], "phase": case["phase"], "group": case["group"],
            "assessment": case["assessment"], "status": run["status"],
            "elapsed_seconds": run["elapsed_seconds"],
            "baseline_output": case["original_response"]["choices"][0]["message"]["content"],
            "baseline_cost": response_cost(case["original_response"], prices),
        }
        if "response" in run:
            pair["candidate_output"] = run["response"]["choices"][0]["message"]["content"]
            pair["candidate_cost"] = response_cost(run["response"], prices)
            pair["candidate_model"] = run["response"]["model"]
        else:
            pair["error"] = run["error"]
        pairs.append(pair)
    totals = {}
    for side in ("baseline", "candidate"):
        costs = [pair[side + "_cost"] for pair in pairs if side + "_cost" in pair]
        totals[side] = {
            "calls_with_usage": len(costs),
            **{name: sum(cost[name] for cost in costs) for name in [
                "input_tokens", "uncached_input_tokens", "cached_input_tokens",
                "cache_write_tokens", "output_tokens", "reasoning_tokens",
            ]},
            **{name: str(sum(Decimal(cost[name]) for cost in costs)) for name in [
                "input_usd", "cached_input_usd", "cache_write_usd", "output_usd", "total_usd",
            ]},
        }
    summary = {
        "result_count": len(runs), "corpus_count": len(cases),
        "distinct_case_count": len({run["case_id"] for run in runs}),
        "api_completed": sum(run["status"] == "completed" for run in runs),
        "elapsed_call_seconds": sum(run["elapsed_seconds"] for run in runs),
        "totals": totals, "pricing": prices, "pairs": pairs,
        "limitations": [
            "One candidate response per case, conditioned on fixed Luna-generated histories.",
            "Original/repaired extraction prompts are separate interventions.",
            "List-price calculation from actual usage; not account invoice reconciliation.",
            "Reasoning tokens are already part of output tokens and are not added again.",
            "Population-level findings require full cohorts; selected individual preferences are not gold answers.",
        ],
    }
    if reviews_path:
        reviews = json.loads(reviews_path.read_text(encoding="utf-8"))
        review_ids = [review["case_id"] for review in reviews["cases"]]
        if len(set(review_ids)) != len(review_ids) or set(review_ids) != {p["case_id"] for p in pairs}:
            raise ValueError("Provide exactly one human review for every compared case.")
        summary["quality_review"] = reviews
    output.mkdir(parents=True, exist_ok=True)
    (output / "comparison.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (output / "costs.csv").open("w", encoding="utf-8", newline="") as stream:
        fields = ["case_id", "side", "elapsed_seconds", *totals["candidate"].keys()]
        fields.remove("calls_with_usage")
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for pair in pairs:
            for side in ("baseline", "candidate"):
                if side + "_cost" in pair:
                    writer.writerow({
                        "case_id": pair["case_id"], "side": side,
                        "elapsed_seconds": pair["elapsed_seconds"] if side == "candidate" else "",
                        **pair[side + "_cost"],
                    })
    page = (
        "<!doctype html><meta charset='utf-8'><title>Model comparison and usage cost</title>"
        "<style>body{font:16px/1.5 system-ui;max-width:1200px;margin:32px auto}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:16px}"
        "summary{font-weight:bold;cursor:pointer}details{margin:20px 0}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:9px;"
        "text-align:left;vertical-align:top}</style>"
        "<h1>Model comparison and usage cost</h1><p>Unblinded diagnostic review inputs, "
        "not an aggregate model ranking. All outputs below are complete, not paraphrased.</p>"
    )
    if reviews_path:
        page += "<h2>Quality findings</h2><p>" + html.escape(reviews["synthesis"]) + "</p>"
        page += "<p>" + html.escape(reviews["method"]) + "</p>"
        page += "<table><tr><th>Case</th><th>Relative result</th><th>Evidence and caveats</th></tr>"
        for review in reviews["cases"]:
            page += "<tr>" + "".join("<td>" + html.escape(review[key]) + "</td>" for key in [
                "case_id", "verdict", "finding",
            ]) + "</tr>"
        page += "</table>"
    page += (
        "<h2>Usage and costs</h2><p>Prices applied to actual returned usage, including "
        "cache writes. Reasoning is included in output billing, not added a second time. "
        "This is a list-price calculation, not an invoice.</p><pre>"
        + html.escape(json.dumps({key: value for key, value in summary.items()
                                 if key not in ("pairs", "quality_review")}, indent=2))
        + "</pre><h2>Complete paired outputs</h2>"
    )
    for pair in pairs:
        page += (
            "<details><summary>" + html.escape(pair["case_id"]) + "</summary><p>"
            + html.escape(pair["assessment"]["criterion"])
            + "</p><h3>Original Luna</h3><pre>" + html.escape(pair["baseline_output"] or "")
            + "</pre><h3>Candidate</h3><pre>"
            + html.escape(pair.get("candidate_output") or json.dumps(pair.get("error")))
            + "</pre></details>"
        )
    (output / "comparison.html").write_text(page, encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key in [
        "result_count", "corpus_count", "api_completed", "elapsed_call_seconds", "totals",
    ]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    args = parser.parse_args()
    build_report(args.corpus, args.results, args.prices, args.output, args.reviews)
