"""Prepare global-theme planning and bounded assignment calls for large semantic partitions."""

import argparse
import copy
import json
from pathlib import Path

import jsonschema

from mine_execution_cases import load_lines
from model_case_study import digest, validate_case
from normalization_assignments import reconstruct, source_items


def derived(source, request, stage, variant, metadata=None):
    """Keep immutable source provenance while recording an explicit intermediate contract."""
    case = copy.deepcopy(source)
    case["case_id"] = source["case_id"] + "::" + variant
    case["request"] = request
    case["experiment"] = {
        "stage": stage, "source_case_id": source["case_id"], "variant": variant,
        "adapter": "normalization_pipeline", **(metadata or {}),
    }
    case["provenance"]["request_sha256"] = digest(request)
    case["provenance"]["normalization"].append(
        "Explicit global-theme/bounded-assignment pipeline; original_response remains historical.")
    validate_case(case)
    return case


def write(output, cases, sources):
    """Persist prepared pipeline calls without making API calls or overwriting prior attempts."""
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    for name, rows in [("cases.jsonl", cases), ("sources.jsonl", sources)]:
        (output / name).write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in rows),
                                   encoding="utf-8")
    print(f"Prepared {len(cases)} pipeline requests; no API calls.")


def plans(corpus, instruction_path, output, stage):
    """Ask for global theme boundaries over every original item, without assigning/copying them."""
    cases, sources = [], list(load_lines(corpus))
    for source in sources:
        items, limit = source_items(source)
        keys = [str(i) for i in range(1, min(len(items), limit) + 1)]
        group = {"type": "object", "additionalProperties": False,
                 "properties": {"label": {"type": "string", "minLength": 1, "maxLength": 40},
                                "scope": {"type": "string", "minLength": 1}},
                 "required": ["label", "scope"]}
        schema = {"type": "object", "additionalProperties": False,
                  "properties": {"groups": {"type": "object", "additionalProperties": False,
                                              "properties": {k: group for k in keys}, "required": keys}},
                  "required": ["groups"]}
        request = copy.deepcopy(source["request"])
        request["messages"] = [
            {"role": "system", "content": instruction_path.read_text(encoding="utf-8")},
            {"role": "user", "content": json.dumps({"groups_to_use": len(keys),
                                                  "items": {str(i): s for i, s in enumerate(items, 1)}},
                                                 ensure_ascii=False)},
        ]
        request["response_format"] = {"type": "json_schema", "json_schema": {
            "name": "global_semantic_themes", "strict": True, "schema": schema}}
        cases.append(derived(source, request, stage, stage + "-themes",
                             {"pipeline_step": "themes"}))
    write(output, cases, sources)


def assignments(prepared, results, instruction_path, output, stage, chunk_size):
    """Freeze successful global themes and assign every item in bounded, complete keyed chunks."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive.")
    sources = {c["case_id"]: c for c in load_lines(prepared / "sources.jsonl")}
    plans_by_id = {c["case_id"]: c for c in load_lines(prepared / "cases.jsonl")}
    cases, seen = [], set()
    for run in load_lines(results):
        if run["case_id"] in seen or run["status"] != "completed":
            raise ValueError("Require one successful, unrepeated global plan per source.")
        seen.add(run["case_id"])
        parent = plans_by_id[run["case_id"]]
        if run["request"] != parent["request"]:
            raise ValueError("Global planning request changed.")
        value = json.loads(run["response"]["choices"][0]["message"]["content"])
        jsonschema.validate(value, parent["request"]["response_format"]["json_schema"]["schema"])
        groups = value["groups"]
        if len({g["label"] for g in groups.values()}) != len(groups):
            raise ValueError("Global theme labels must be distinct.")
        source = sources[parent["experiment"]["source_case_id"]]
        items, _ = source_items(source)
        for start in range(0, len(items), chunk_size):
            chunk = {str(i + 1): items[i] for i in range(start, min(start + chunk_size, len(items)))}
            schema = {"type": "object", "additionalProperties": False,
                      "properties": {"assignments": {"type": "object", "additionalProperties": False,
                          "properties": {k: {"type": "integer", "minimum": 1, "maximum": len(groups)}
                                         for k in chunk}, "required": list(chunk)}},
                      "required": ["assignments"]}
            request = copy.deepcopy(source["request"])
            request["messages"] = [
                {"role": "system", "content": instruction_path.read_text(encoding="utf-8")},
                {"role": "user", "content": json.dumps({"fixed_global_groups": groups, "items": chunk},
                                                     ensure_ascii=False)},
            ]
            request["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "bounded_theme_assignments", "strict": True, "schema": schema}}
            variant = stage + f"-chunk-{start + 1}-{start + len(chunk)}"
            cases.append(derived(source, request, stage, variant, {
                "pipeline_step": "assignments", "chunk_ids": list(chunk), "global_groups": groups,
                "parent_plan_response_id": run["response"]["id"],
                "parent_plan_case_id": parent["case_id"],
            }))
    if seen != set(plans_by_id):
        raise ValueError("Missing or extra global plans.")
    write(output, cases, list(sources.values()))


def assemble(prepared, results, output):
    """Reject missing/duplicate chunks and recover a complete exact-string partition per source."""
    if output.exists():
        raise FileExistsError(output)
    cases = {c["case_id"]: c for c in load_lines(prepared / "cases.jsonl")}
    sources = {c["case_id"]: c for c in load_lines(prepared / "sources.jsonl")}
    seen, partitions, parents = set(), {}, {}
    for run in load_lines(results):
        if run["case_id"] in seen or run["status"] != "completed":
            raise ValueError("Require one completed result for every chunk.")
        seen.add(run["case_id"])
        case = cases[run["case_id"]]
        if run["request"] != case["request"]:
            raise ValueError("Chunk request changed.")
        value = json.loads(run["response"]["choices"][0]["message"]["content"])
        jsonschema.validate(value, case["request"]["response_format"]["json_schema"]["schema"])
        metadata = case["experiment"]
        sid = metadata["source_case_id"]
        groups = metadata["global_groups"]
        if sid in parents and parents[sid] != metadata["parent_plan_response_id"]:
            raise ValueError("Chunks cannot mix different global theme plans.")
        parents[sid] = metadata["parent_plan_response_id"]
        partition = partitions.setdefault(sid, {
            "labels": {k: g["label"] for k, g in groups.items()}, "assignments": {},
            "group_definitions": groups, "chunk_response_ids": [],
        })
        if partition["group_definitions"] != groups:
            raise ValueError("Global group definitions changed between chunks.")
        if set(partition["assignments"]) & set(value["assignments"]):
            raise ValueError("Overlapping chunk assignments.")
        partition["assignments"].update(value["assignments"])
        partition["chunk_response_ids"].append(run["response"]["id"])
    if seen != set(cases):
        raise ValueError("Missing or extra chunk result.")
    records = []
    for sid, partition in partitions.items():
        restored = reconstruct(sources[sid], partition)
        records.append({"source_case_id": sid, "parent_plan_response_id": parents[sid],
                        **partition, "reconstructed": restored})
    output.mkdir(parents=True)
    (output / "partitions.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Assembled {len(records)} exact partitions from {len(seen)} complete chunks.")
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan")
    plan.add_argument("--corpus", type=Path, required=True)
    assign = commands.add_parser("assign")
    assign.add_argument("--prepared", type=Path, required=True)
    assign.add_argument("--results", type=Path, required=True)
    assign.add_argument("--chunk-size", type=int, default=240)
    finish = commands.add_parser("assemble")
    finish.add_argument("--prepared", type=Path, required=True)
    finish.add_argument("--results", type=Path, required=True)
    finish.add_argument("--output", type=Path, required=True)
    for command in [plan, assign]:
        command.add_argument("--instruction", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        command.add_argument("--stage", required=True)
    args = parser.parse_args()
    if args.command == "plan":
        plans(args.corpus, args.instruction, args.output, args.stage)
    elif args.command == "assign":
        assignments(args.prepared, args.results, args.instruction, args.output, args.stage, args.chunk_size)
    else:
        assemble(args.prepared, args.results, args.output)
