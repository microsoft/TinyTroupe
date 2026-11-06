"""Build auditable prompt variants from a data manifest, without making API calls."""

import argparse
import copy
import difflib
import html
import json
import random
import re
from pathlib import Path

from model_case_study import digest, validate_case


def transform_content(content, operation):
    """Edit text inside JSON-encoded message envelopes without corrupting their encoding."""
    try:
        decoded = json.loads(content)
    except (ValueError, TypeError):
        decoded = None
    edits = 0

    def transform(value):
        nonlocal edits
        if isinstance(value, str):
            if operation["kind"] == "append":
                edits += 1
                return value + operation["text"]
            if operation["kind"] == "replace":
                edits += value.count(operation["old"])
                return value.replace(operation["old"], operation["new"])
            if operation["kind"] == "regex":
                value, count = re.subn(operation["pattern"], operation["new"], value)
                edits += count
                return value
            raise ValueError(f"Unknown operation: {operation['kind']}")
        if isinstance(value, list):
            return [transform(item) for item in value]
        if isinstance(value, dict):
            return {key: transform(item) for key, item in value.items()}
        return value

    result = transform(content if decoded is None else decoded)
    if not edits:
        return content, 0
    return (result if decoded is None else json.dumps(result, ensure_ascii=False)), edits


def build_variants(corpus_path, manifest_path, output):
    """Keep immutable baselines and add variants with explicit immediate-parent provenance."""
    originals = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines()
                 if line.strip()]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    cases = []
    index = {}
    audit = []
    for original in originals:
        validate_case(original)
        case = copy.deepcopy(original)
        case["case_id"] = original["case_id"] + "::baseline"
        case["experiment"] = {
            "source_case_id": original["case_id"], "variant": "baseline",
            "parent_case_id": None, "original_request_sha256": digest(original["request"]),
            "reference_response_is_from_original_prompt": True,
        }
        cases.append(case)
        index[case["case_id"]] = case
    for recipe in manifest["variants"]:
        for source_id in recipe["cases"]:
            parent_id = source_id + "::" + recipe.get("parent", "baseline")
            parent = index[parent_id]
            case = copy.deepcopy(parent)
            case["case_id"] = source_id + "::" + recipe["id"]
            if "phase" in recipe:
                case["phase"] = recipe["phase"]
            if "response_format" in recipe:
                case["request"]["response_format"] = copy.deepcopy(recipe["response_format"])
            if case["case_id"] in index:
                raise ValueError(f"Duplicate variant: {case['case_id']}")
            edit_counts = []
            for operation in recipe["operations"]:
                count = 0
                for position, message in enumerate(case["request"]["messages"]):
                    if operation["message"] != "all" and position != operation["message"]:
                        continue
                    message["content"], found = transform_content(message["content"], operation)
                    count += found
                if not operation.get("min_matches", 1) <= count <= operation.get("max_matches", 100):
                    raise ValueError(f"{case['case_id']}: unexpected edit count {count}: {operation}")
                edit_counts.append(count)
            if case["request"] == parent["request"]:
                raise ValueError(f"No change in {case['case_id']}")
            case["experiment"] = {
                **parent["experiment"], "variant": recipe["id"],
                "parent_case_id": parent_id, "hypothesis": recipe["hypothesis"],
                "edit_counts": edit_counts,
            }
            case["provenance"]["request_sha256"] = digest(case["request"])
            case["provenance"]["normalization"] = [
                *parent["provenance"].get("normalization", []),
                "Experimental prompt edit; original_response and source_cache_key refer to "
                "the unchanged source case, NOT an observed response to this variant.",
            ]
            validate_case(case)
            cases.append(case)
            index[case["case_id"]] = case
            before = json.dumps(parent["request"]["messages"], ensure_ascii=False, indent=2)
            after = json.dumps(case["request"]["messages"], ensure_ascii=False, indent=2)
            audit.append({
                "case_id": case["case_id"], "parent_case_id": parent_id,
                "hypothesis": recipe["hypothesis"], "edit_counts": edit_counts,
                "diff": "".join(difflib.unified_diff(
                    before.splitlines(True), after.splitlines(True), parent_id, case["case_id"]
                )),
            })
    random.Random(manifest["order_seed"]).shuffle(cases)
    output.mkdir(parents=True, exist_ok=True)
    for name, ordered in [("cases.jsonl", cases), ("cases-reversed.jsonl", list(reversed(cases)))]:
        (output / name).write_text(
            "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in ordered), encoding="utf-8"
        )
    (output / "variant-audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    page = (
        "<!doctype html><meta charset='utf-8'><title>Prompt experiment protocol</title>"
        "<style>body{font:16px/1.5 system-ui;max-width:1100px;margin:32px auto}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:16px}</style>"
        "<h1>Prompt experiment protocol</h1><p>" + html.escape(manifest["protocol"])
        + "</p><h2>Exact human-readable treatment definitions</h2><pre>"
        + html.escape(json.dumps(manifest, ensure_ascii=False, indent=2)) + "</pre>"
        "<p>Per-case machine-readable edits and complete resulting requests are bundled. "
        "Original responses remain historical references, not treatment observations.</p>"
    )
    (output / "protocol.html").write_text(page, encoding="utf-8")
    print(f"Built {len(cases)} requests: {len(originals)} baselines, {len(audit)} variants.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_variants(args.corpus, args.manifest, args.output)
