"""Prepare seeded, phase-balanced paired prompt comparisons without API calls."""

import argparse
import copy
import difflib
import json
import random
from collections import defaultdict
from pathlib import Path

from mine_execution_cases import load_lines
from model_case_study import digest, validate_case


def prepare(corpus, protocol_path, output, stage):
    """Freeze exact source pairs and documented general revisions, preserving all evidence messages."""
    if output.exists():
        raise FileExistsError(f"Use a new experiment directory: {output}")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    plan = protocol["stages"][stage]
    cells = defaultdict(list)
    for case in load_lines(corpus):
        if case["selection"]["split"] != plan["split"]:
            raise ValueError(f"Unexpected split in {case['case_id']}")
        if case["phase"] in plan["counts"]:
            validate_case(case)
            cells[case["phase"]].append(case)
    originals = []
    for phase, count in sorted(plan["counts"].items()):
        candidates = sorted(cells[phase], key=lambda case: digest(
            [protocol["selection_seed"], stage, case["case_id"]]
        ))
        selected, groups = [], set()
        for case in candidates:
            group = case["provenance"]["cache"]
            if group not in groups and len(selected) < count:
                selected.append(case)
                groups.add(group)
        for case in candidates:
            if len(selected) < count and case not in selected:
                selected.append(case)
        if len(selected) != count:
            raise ValueError(f"Need {count} {phase} inputs, found {len(selected)}")
        originals.extend(selected)
    cases, edits = [], []
    for source in originals:
        for variant in ["baseline", protocol["variant"]]:
            case = copy.deepcopy(source)
            case["case_id"] = source["case_id"] + "::" + variant
            case["experiment"] = {
                "source_case_id": source["case_id"], "variant": variant,
                "stage": stage, "hypothesis": protocol["hypotheses"][source["phase"]],
                "reference_response_is_from_original_prompt": True,
            }
            if variant != "baseline":
                instruction = protocol["instructions"][source["phase"]]
                case["request"]["messages"].append({"role": "system", "content": instruction})
                case["experiment"]["reference_response_is_from_original_prompt"] = True
                case["provenance"]["request_sha256"] = digest(case["request"])
                case["provenance"]["normalization"].append(
                    "Experimental task-specific final system instruction appended. Original response "
                    "belongs to the unmodified source request, not the revised prompt."
                )
                before = json.dumps(source["request"], ensure_ascii=False, indent=2)
                after = json.dumps(case["request"], ensure_ascii=False, indent=2)
                edits.append({
                    "case_id": case["case_id"], "phase": case["phase"],
                    "original_request_sha256": digest(source["request"]),
                    "revised_request_sha256": digest(case["request"]),
                    "diff": "".join(difflib.unified_diff(
                        before.splitlines(True), after.splitlines(True), "baseline", variant
                    )),
                })
                assert case["request"]["messages"][:-1] == source["request"]["messages"]
                assert {k: v for k, v in case["request"].items() if k != "messages"} == {
                    k: v for k, v in source["request"].items() if k != "messages"
                }
            validate_case(case)
            cases.append(case)
    random.Random(protocol["execution_order_seed"] + plan["order_offset"]).shuffle(cases)
    output.mkdir(parents=True)
    for name, records in [("sources.jsonl", originals), ("cases.jsonl", cases)]:
        (output / name).write_text(
            "".join(json.dumps(case, ensure_ascii=False) + "\n" for case in records), encoding="utf-8"
        )
    (output / "prompt-audit.json").write_text(json.dumps(edits, indent=2), encoding="utf-8")
    (output / "frozen-protocol.json").write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Prepared {len(originals)} sources and {len(cases)} paired requests for {stage}. No API calls.")
    return cases


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", required=True)
    args = parser.parse_args()
    prepare(args.corpus, args.protocol, args.output, args.stage)
