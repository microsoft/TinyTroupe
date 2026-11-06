"""Verify preserved inputs and observable gates for standalone prompt revisions."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path
import jsonschema

from analyze_ablations import output_checks, result_labels
from model_case_study import digest, validate_case


def load_lines(path):
    """Read a saved JSONL corpus or result file."""
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def message_text(content):
    """Decode string envelopes while rejecting unexpected protected-input structures."""
    try:
        decoded = json.loads(content)
    except ValueError:
        return content
    if not isinstance(decoded, str):
        raise ValueError("Protected section requires a plain text or JSON-string message.")
    return decoded


def audit(original_path, corpus_path, results, output, expected_repeats=None, allow_plan_schema=False):
    """Check invariants and collect diagnostics without substituting for semantic review."""
    originals = {case["case_id"]: case for case in load_lines(original_path)}
    cases = {case["case_id"]: case for case in load_lines(corpus_path)}
    plan_schema_changes = []
    for case in cases.values():
        validate_case(case)
        old = originals[case["experiment"]["source_case_id"]]
        request = case["request"]
        settings = {k: v for k, v in request.items() if k != "messages"}
        old_settings = {k: v for k, v in old["request"].items() if k != "messages"}
        if (allow_plan_schema and case["phase"] == "persona_generation_plan"
                and settings.get("response_format") != old_settings.get("response_format")):
            fmt = settings.get("response_format", {})
            if fmt.get("type") != "json_schema" or fmt.get("json_schema", {}).get("strict") is not True:
                raise ValueError(f"Only explicit strict planning schemas are allowed: {case['case_id']}")
            jsonschema.Draft202012Validator.check_schema(fmt["json_schema"]["schema"])
            settings.pop("response_format")
            old_settings.pop("response_format", None)
            plan_schema_changes.append(case["case_id"])
        if settings != old_settings:
            raise ValueError(f"Non-message setting changed: {case['case_id']}")
        if case["phase"] == "agent_action":
            before = message_text(old["request"]["messages"][0]["content"])
            after = message_text(request["messages"][0]["content"])
            for pattern in [
                r"(?s)## Persona\s*(.*?)### Rules for interpreting your persona",
                r"(?s)## Additional Constraints \(if any\)\s*(.*?)## Persona",
            ]:
                left, right = re.search(pattern, before), re.search(pattern, after)
                if not left or not right or left[1].strip() != right[1].strip():
                    raise ValueError(f"Protected persona or safety text changed: {case['case_id']}")
        elif case["phase"] in ("persona_generation", "persona_generation_plan"):
            before = old["request"]["messages"][1]["content"].split("## Generation Rules")[0]
            after = request["messages"][1]["content"].split("## Generation Rules")[0]
            if before != after:
                raise ValueError(f"Generation constraints changed: {case['case_id']}")
    observations = []
    seen = set()
    labels = result_labels(results) if results else {}
    for path in results:
        for run in load_lines(path):
            key = (labels[path], run["case_id"], run.get("condition_id"), run["replicate"])
            if key in seen:
                raise ValueError(f"Duplicate observation: {key}")
            seen.add(key)
            case = cases[run["case_id"]]
            if run["request"] != case["request"] or run["request_sha256"] != digest(run["request"]):
                raise ValueError(f"Executed request mismatch: {key}")
            row = {
                "file": labels[path], "case_id": run["case_id"], "replicate": run["replicate"],
                "status": run["status"], "phase": case["phase"],
            }
            if "response" in run:
                row["checks"] = output_checks(case, run["response"])
                public = row["checks"].get("public_text", "")
                row["review_flags"] = []
                source = case["experiment"]["source_case_id"]
                if source.startswith(("travel-", "gazpacho-")) and re.search(
                    r"top[- ](?:10|ten)|my interests are|my ideal vacation", public, re.I
                ):
                    row["review_flags"].append("Possible superseded introduction")
                if source.startswith("gazpacho-"):
                    row["checks"]["leading_score"] = bool(re.match(
                        r"\s*(?:\*\*)?(?:[1-5]\b|my propensity(?: to buy)? is [1-5]\b)", public, re.I
                    ))
                if source.startswith("extraction-"):
                    row["checks"]["expected_original_extraction"] = row["checks"].get("extracted") == {
                        "response": "No", "justification": "No public justification provided."
                    }
            observations.append(row)
    counts = Counter(row["case_id"] for row in observations if row["status"] == "completed")
    if expected_repeats is not None and counts != Counter({key: expected_repeats for key in cases}):
        raise ValueError(f"Coverage differs from {expected_repeats} completed observations per cell: {counts}")
    report = {
        "protected_inputs_preserved": True,
        "explicit_plan_schema_changes": plan_schema_changes,
        "case_count": len(cases), "attempts": len(observations),
        "completed": sum(counts.values()), "completed_by_case": dict(counts),
        "observations": observations,
        "warning": "Flags and structural checks do not prove semantic quality. Review complete public outputs and profiles.",
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "observations"}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--results", type=Path, nargs="*", default=[])
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-repeats", type=int)
    parser.add_argument("--allow-plan-schema", action="store_true")
    args = parser.parse_args()
    audit(args.original, args.corpus, args.results, args.output, args.expected_repeats, args.allow_plan_schema)
