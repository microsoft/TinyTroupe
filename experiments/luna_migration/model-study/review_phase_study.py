"""Verify paired study integrity and expose complete outputs for semantic review."""

import argparse
import copy
import csv
import html
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import jsonschema

from mine_execution_cases import load_lines
from model_case_study import digest, validate_case
from study_report import response_cost


def named_parameters(case):
    """Recover the library's literal named-parameter payload, when present."""
    for message in case["request"]["messages"]:
        text = message.get("content")
        if isinstance(text, str) and "## Named parameters\n" in text:
            return json.JSONDecoder().raw_decode(text.split("## Named parameters\n", 1)[1].lstrip())[0]
    return None


def checks(case, content):
    """Check observable contracts only; never infer semantic quality from validity."""
    fmt = case["request"].get("response_format") or {}
    result = {"output_characters": len(content or ""), "output_words": len((content or "").split())}
    if case["phase"] == "content_enrichment":
        for message in case["request"]["messages"]:
            text = message.get("content")
            if not isinstance(text, str) or "## CONTENT TO ENRICH" not in text:
                continue
            match = re.search(r"## CONTENT TO ENRICH.*?```\r?\n(.*)\r?\n```", text, re.S)
            factor = re.search(r"at least (\d+(?:\.\d+)?) times", text)
            if match and factor:
                size = len(match[1])
                minimum = Decimal(factor[1]) * size
                result.update(source_characters=size, minimum_characters=str(minimum),
                              expansion_ratio=result["output_characters"] / size,
                              minimum_expansion_met=result["output_characters"] >= minimum)
    try:
        value = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        result["json_valid"] = False
        result["json_required"] = fmt.get("type") in ("json_object", "json_schema")
        if case["phase"] == "story_continuation":
            result["within_100_words"] = result["output_words"] <= 100
        return result
    result["json_valid"] = True
    if fmt.get("type") == "json_schema":
        errors = list(jsonschema.Draft202012Validator(fmt["json_schema"]["schema"]).iter_errors(value))
        result["schema_valid"] = not errors
        result["schema_errors"] = [e.message for e in errors]
    params = named_parameters(case)
    phase = case["phase"]
    if phase == "agent_action":
        actions = value.get("actions", [])
        result["action_types"] = [a.get("type") for a in actions]
        result["public_text"] = "\n".join(a.get("content", "") for a in actions if a.get("type") == "TALK")
        result["ends_with_done"] = bool(actions and actions[-1].get("type") == "DONE")
    elif phase == "persona_generation":
        required = "name age gender nationality residence education long_term_goals occupation style personality preferences beliefs skills behaviors health relationships other_facts".split()
        result["missing_persona_fields"] = sorted(set(required) - set(value))
    elif phase == "sampling_plan" and params:
        plan = value.get("sample_plan", [])
        quantities = [p.get("quantity") for p in plan]
        numeric = all(type(q) is int and q >= 1 for q in quantities)
        total = params.get("N", params.get("n"))
        result.update(directive_count=len(plan), quantities=quantities,
                      positive_integer_quantities=numeric,
                      expected_total=total, actual_total=sum(quantities) if numeric else None,
                      exact_total=numeric and sum(quantities) == total)
        result["sequential_directive_ids"] = (
            all(type(p.get("id")) is int for p in plan)
            and [p["id"] for p in plan] == list(range(1, len(plan) + 1))
        )
        for key in ["min_sampling_directives", "max_sampling_directives", "max_quantity_per_sample_directive"]:
            limit = params.get(key)
            if limit is not None:
                result[key] = limit
                result[key + "_satisfied"] = (
                    len(plan) >= limit if key.startswith("min_") else
                    len(plan) <= limit if key == "max_sampling_directives" else
                    numeric and all(q <= limit for q in quantities)
                )
        dimensions = {d["name"] for d in params["sampling_dimensions"]["dimensions"]}
        specifications = {d["name"]: d for d in params["sampling_dimensions"]["dimensions"]}
        result["unknown_dimensions"] = sorted({
            k for p in plan for k in p.get("sampled_values", {}) if k not in dimensions
        })
        if params.get("enforce_usage_of_all_dimensions"):
            result["missing_dimensions_by_directive"] = [
                sorted(dimensions - set(p.get("sampled_values", {}))) for p in plan
            ]
        value_errors = []
        for directive in plan:
            for name, chosen in directive.get("sampled_values", {}).items():
                if name not in specifications:
                    continue
                specification = specifications[name]
                values = chosen if isinstance(chosen, list) else [chosen]
                if "range" in specification:
                    low, high = specification["range"]
                    valid = (bool(values) and all(type(v) in (int, float) and low <= v <= high for v in values)
                             and (not isinstance(chosen, list) or len(values) == 2 and values[0] <= values[1]))
                else:
                    allowed = specification["values"]
                    valid = bool(values) and all(isinstance(v, str) and v in allowed for v in values)
                if not valid:
                    value_errors.append({"directive": directive.get("id"), "dimension": name,
                                         "selected": chosen})
        result["invalid_or_rewritten_sampled_values"] = value_errors
    elif phase == "normalization" and isinstance(value, dict):
        result["category_count"] = len(value)
        result["label_lengths"] = {key: len(key) for key in value}
        result["labels_within_40_characters"] = all(len(k) <= 40 for k in value)
        original, limit = None, None
        if params:
            result["input_parameter_keys"] = sorted(params)
            original = params.get("elements", params.get("strings", params.get("items")))
            limit = params.get("n", params.get("N"))
        else:
            for message in case["request"]["messages"]:
                text = message.get("content")
                if message["role"] != "user" or not isinstance(text, str) or "INPUT ELEMENTS:\n" not in text:
                    continue
                original = text.split("INPUT ELEMENTS:\n", 1)[1].removeprefix("  - ").removesuffix("\n").split("\n  - ")
                bound = re.search(r"Produce UP TO (\d+)", text)
                limit = int(bound[1]) if bound else None
        if limit is not None:
            result["within_category_limit"] = len(value) <= limit
        if isinstance(original, list) and all(isinstance(s, str) for s in original):
            output = [s for members in value.values() for s in members]
            result["membership_multiset_preserved"] = Counter(original) == Counter(output)
            result["input_occurrences"] = len(original)
            result["output_occurrences"] = len(output)
            result["missing_members"] = list((Counter(original) - Counter(output)).elements())
            result["unexpected_members"] = list((Counter(output) - Counter(original)).elements())
    elif phase == "sampling_dimensions":
        result["dimensions"] = [d["name"] for d in value.get("dimensions", [])]
        result["weighted_dimension_totals"] = {
            d["name"]: sum(Decimal(str(weight)) for weight in d["values"].values())
            for d in value.get("dimensions", [])
            if isinstance(d.get("values"), dict) and all(
                isinstance(w, (int, float)) for w in d["values"].values()
            )
        }
        result["weighted_dimension_totals"] = {
            k: str(v) for k, v in result["weighted_dimension_totals"].items()
        }
    return result


def review(corpora, results, prices_path, output):
    """Reject missing, duplicate or altered observations; preserve explicit failed attempts."""
    cases = {}
    for path in corpora:
        for case in load_lines(path):
            validate_case(case)
            if case["case_id"] in cases:
                raise ValueError(f"Duplicate corpus case: {case['case_id']}")
            cases[case["case_id"]] = case
    prices = json.loads(prices_path.read_text(encoding="utf-8"))
    pairs, seen, response_ids, records = defaultdict(dict), set(), set(), []
    for path in results:
        for run in load_lines(path):
            case_id = run["case_id"]
            if case_id in seen:
                raise ValueError(f"Duplicate result: {case_id}")
            seen.add(case_id)
            case = cases[case_id]
            if digest(run["request"]) != run["request_sha256"]:
                raise ValueError(f"Result hash mismatch: {case_id}")
            if run["request"] != case["request"]:
                raise ValueError(f"Unexpected parameter changes: {case_id}")
            record = {
                "case_id": case_id, "phase": case["phase"], **case["experiment"],
                "status": run["status"], "elapsed_seconds": run["elapsed_seconds"],
            }
            if "response" in run:
                response = run["response"]
                if response["id"] in response_ids:
                    raise ValueError(f"Reused response: {response['id']}")
                response_ids.add(response["id"])
                record["response_id"] = response["id"]
                record["content"] = response["choices"][0]["message"].get("content")
                record["checks"] = checks(case, record["content"])
                record["cost"] = cost_with_bounds(response, prices)
            else:
                record["error"] = run["error"]
            pair_key = (case["experiment"]["stage"], case["experiment"]["source_case_id"])
            variant = case["experiment"]["variant"]
            if variant in pairs[pair_key]:
                raise ValueError("Duplicate paired variant")
            pairs[pair_key][variant] = record
            records.append(record)
    if seen != set(cases):
        raise ValueError(f"Missing/extra observations: {set(cases) ^ seen}")
    output.mkdir(parents=True, exist_ok=True)
    costs = [r["cost"] for r in records if "cost" in r]
    total = sum((Decimal(c["total_usd"]) for c in costs if c["total_usd"] is not None), Decimal(0))
    lower = sum((Decimal(c["total_usd"] if c["total_usd"] is not None else c["minimum_usd"])
                 for c in costs), Decimal(0))
    upper = sum((Decimal(c["total_usd"] if c["total_usd"] is not None else c["maximum_usd"])
                 for c in costs), Decimal(0))
    summary = {
        "calls": len(records), "calls_without_usage": sum("cost" not in r for r in records),
        "statuses": dict(Counter(r["status"] for r in records)),
        "known_list_price_usd": str(total),
        "distinct_sources": len({c["experiment"]["source_case_id"] for c in cases.values()}),
        "paired_stage_cells": len(pairs),
        "calls_with_unknown_cache_writes": sum(c["total_usd"] is None for c in costs),
        "total_list_price_bounds_usd": [str(lower), str(upper)],
        "limitations": "Automatic checks are observable contracts, not quality verdicts. "
                       "Single paired responses; fixed histories; assistant semantic review, not blinded human review.",
        "records": records,
    }
    (output / "observations.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    page = ["<!doctype html><meta charset='utf-8'><title>Paired Luna prompt study</title>",
            "<style>body{font:16px/1.5 system-ui;margin:30px auto;max-width:1400px}"
            "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:15px}"
            "details{margin:20px 0}.pair{display:grid;grid-template-columns:1fr 1fr;gap:15px}</style>",
            "<h1>Paired Luna prompt study</h1><p>" + html.escape(summary["limitations"]) + "</p>",
            "<pre>" + html.escape(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2)) + "</pre>"]
    text = []
    for index, ((stage, source_id), variants) in enumerate(sorted(pairs.items()), 1):
        record = next(iter(variants.values()))
        label = f"{index:02d}-{record['phase']}-{source_id}"
        page.append("<details><summary>" + html.escape(f"{stage} / {label}") + "</summary><div class='pair'>")
        section = [f"### {stage} / {label}"]
        for variant, entry in sorted(variants.items()):
            content = entry.get("content") or json.dumps(entry.get("error"))
            page.append("<section><h2>" + html.escape(variant) + "</h2><pre>"
                        + html.escape(content) + "</pre><pre>"
                        + html.escape(json.dumps(entry.get("checks"), ensure_ascii=False, indent=2))
                        + "</pre></section>")
            section += [f"## {variant}", content, "CHECKS", json.dumps(entry.get("checks"), indent=2, ensure_ascii=False)]
        page.append("</div><details><summary>Complete original request and source provenance</summary><pre>"
                    + html.escape(json.dumps(cases[next(iter(variants.values()))["case_id"]],
                                             ensure_ascii=False, indent=2)) + "</pre></details></details>")
        text += section
        (output / (label + ".txt")).write_text("\n".join(section), encoding="utf-8")
    page.append("<h2>Interpretation</h2><p>No sentiment, ranking, purchase or score distribution is a gold answer. "
                "No runtime templates were deployed by this study.</p>")
    (output / "report.html").write_text("\n".join(page), encoding="utf-8")
    (output / "complete-outputs.txt").write_text("\n\n".join(text), encoding="utf-8")
    with (output / "costs.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["case_id", "stage", "phase", "variant", "status", "total_usd",
                                                    "input_tokens", "cached_input_tokens", "cache_write_tokens",
                                                    "output_tokens", "reasoning_tokens"])
        writer.writeheader()
        for record in records:
            writer.writerow({key: record.get(key, record.get("cost", {}).get(key)) for key in writer.fieldnames})
    print(json.dumps({k: v for k, v in summary.items() if k != "records"}, indent=2))
    return summary


def cost_with_bounds(response, prices):
    """Keep unknown cache-write counts explicit instead of assuming missing means zero."""
    details = response["usage"]["prompt_tokens_details"]
    if "cache_write_tokens" in details:
        return response_cost(response, prices)
    low, high = copy.deepcopy(response), copy.deepcopy(response)
    uncertain = response["usage"]["prompt_tokens"] - details["cached_tokens"]
    low["usage"]["prompt_tokens_details"]["cache_write_tokens"] = 0
    high["usage"]["prompt_tokens_details"]["cache_write_tokens"] = uncertain
    lower, upper = response_cost(low, prices), response_cost(high, prices)
    bounds = sorted([Decimal(lower["total_usd"]), Decimal(upper["total_usd"])])
    return {
        "input_tokens": response["usage"]["prompt_tokens"],
        "cached_input_tokens": details["cached_tokens"],
        "cache_write_tokens": None,
        "output_tokens": response["usage"]["completion_tokens"],
        "reasoning_tokens": response["usage"]["completion_tokens_details"]["reasoning_tokens"],
        "total_usd": None, "minimum_usd": str(bounds[0]), "maximum_usd": str(bounds[1]),
        "uncertainty": "Response omits cache_write_tokens. Bounds price all non-read input "
                       "as either ordinary input or cache writes; no zero-write assumption.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", action="append", type=Path, required=True)
    parser.add_argument("--results", action="append", type=Path, required=True)
    parser.add_argument("--prices", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review(args.corpus, args.results, args.prices, args.output)
