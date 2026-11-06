"""Mine cached execution pairs without API calls; preserve provenance and group validation splits."""

import argparse
import csv
import hashlib
import html
import json
import math
import re
import sqlite3
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import jsonschema

from model_case_study import digest, normalize_cache_request, validate_case


def load_lines(path):
    """Stream JSONL records without loading the complete corpus."""
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                yield json.loads(line)


def file_hash(path):
    """Hash large execution files with bounded memory."""
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def message_text(content):
    """Read text for classification only; never modify the saved request."""
    if isinstance(content, str):
        try:
            decoded = json.loads(content)
        except ValueError:
            return content
        return decoded if isinstance(decoded, str) else content
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


def classify(request, schema_class, rules):
    """Apply ordered manifest rules and make unmatched prompt families explicit."""
    text = message_text(request["messages"][0].get("content"))
    for rule in rules:
        if ("schema_class" in rule and rule["schema_class"] == schema_class
                or "system_contains" in rule and rule["system_contains"] in text):
            return rule["phase"]
    return "unclassified"


def output_diagnostics(request, response):
    """Record observable format properties, never infer realism or desirable preferences."""
    choice = response.get("choices", [{}])[0]
    message = choice.get("message", {})
    checks = {
        "finish_reason": choice.get("finish_reason"),
        "refused": bool(message.get("refusal")),
        "content_present": bool(message.get("content")),
    }
    try:
        value = json.loads(message.get("content"))
    except (TypeError, ValueError):
        checks["json_valid"] = False
        return checks
    checks["json_valid"] = True
    fmt = request.get("response_format") or {}
    if fmt.get("type") == "json_schema":
        validator = jsonschema.Draft202012Validator(fmt["json_schema"]["schema"])
        checks["schema_errors"] = [error.message for error in validator.iter_errors(value)]
        checks["schema_valid"] = not checks["schema_errors"]
    return checks


class Groups:
    """Join scenario families connected by duplicate observations or identical replay inputs."""

    def __init__(self):
        self.parents = {}

    def root(self, value):
        self.parents.setdefault(value, value)
        if self.parents[value] != value:
            self.parents[value] = self.root(self.parents[value])
        return self.parents[value]

    def join(self, first, second):
        left, right = sorted((self.root(first), self.root(second)))
        self.parents[right] = left


def balanced_ids(rows, maximum, seed):
    """Round-robin seeded phase/scenario cells; prioritize rare cells over abundant utility calls."""
    cells = defaultdict(list)
    for row in rows:
        cells[(row["phase"], row["split_group"])].append(row["case_id"])
    ordered = []
    for cell in sorted(cells):
        ordered.append(sorted(cells[cell], key=lambda value: digest([seed, value])))
    selected = []
    depth = 0
    while len(selected) < maximum:
        added = False
        for cell in ordered:
            if depth < len(cell) and len(selected) < maximum:
                selected.append(cell[depth])
                added = True
        if not added:
            break
        depth += 1
    return selected


def mine(manifest_path, output):
    """Export all distinct completed observations, exclusions and reproducible stratified subsets."""
    if output.exists():
        raise FileExistsError(f"Use a new output directory: {output}")
    spec = json.loads(manifest_path.read_text(encoding="utf-8"))
    seed = spec["seed"]
    fraction = spec["validation_fraction"]
    if not 0 < fraction < 1:
        raise ValueError("validation_fraction must be between zero and one.")
    if any(type(n) is not int or n <= 0 for n in spec["subset_limits"].values()):
        raise ValueError("Subset limits must be positive integers.")
    base = manifest_path.parent
    schemas = json.loads((base / spec["schemas"]).read_text(encoding="utf-8"))
    for fmt in schemas.values():
        jsonschema.Draft202012Validator.check_schema(fmt["json_schema"]["schema"])
    prior = list(load_lines(base / spec["prior_corpus"]))
    prior_by_response = {case["original_response"]["id"]: case for case in prior}
    for case in prior:
        validate_case(case)
    audit_path = base / spec["source_audit"]
    sources = json.loads(audit_path.read_text(encoding="utf-8"))["runs"]
    root = (base / spec["source_root"]).resolve()
    output.mkdir(parents=True)
    groups = Groups()
    observed, excluded, copied = 0, 0, 0
    inventory, metadata = [], {}
    request_groups, response_groups, pinned = {}, {}, set()
    with tempfile.TemporaryDirectory(prefix="mining-", dir=output) as temp:
        connection = sqlite3.connect(str(Path(temp) / "staging.sqlite"))
        connection.execute("CREATE TABLE cases (response_id TEXT PRIMARY KEY, body TEXT, request_hash TEXT, response_hash TEXT)")
        try:
            with (output / "occurrences.jsonl").open("x", encoding="utf-8") as occurrences, (
                output / "excluded.jsonl"
            ).open("x", encoding="utf-8") as exclusions:
                for source in sources:
                    name = source["name"]
                    family = name
                    for rule in spec["group_rules"]:
                        if re.search(rule["pattern"], name):
                            family = rule["group"]
                            break
                    groups.root(family)
                    path = root / source["folder"] / spec["cache_filename"]
                    source_digest = file_hash(path)
                    cache = json.loads(path.read_text(encoding="utf-8"))
                    local = Counter()
                    for key, response in cache.items():
                        observed += 1
                        request, schema_class, normalization = normalize_cache_request(key, schemas)
                        request_hash, response_hash = digest(request), digest(response)
                        response_id = response.get("id")
                        if not isinstance(response_id, str) or not response_id:
                            raise ValueError(f"Response ID missing in {path}")
                        phase = classify(request, schema_class, spec["phase_rules"])
                        diagnostics = output_diagnostics(request, response)
                        local[phase] += 1
                        occurrence = {
                            "source": source["folder"], "notebook": name, "family": family,
                            "response_id": response_id, "phase": phase,
                            "cache_key_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
                            "request_sha256": request_hash,
                            "source_sha256": source_digest,
                        }
                        occurrences.write(json.dumps(occurrence, ensure_ascii=False) + "\n")
                        if diagnostics["finish_reason"] != "stop" or diagnostics["refused"]:
                            excluded += 1
                            exclusions.write(json.dumps({
                                **occurrence, "request": request, "response": response,
                                "source_cache_key": key, "diagnostics": diagnostics,
                            }, ensure_ascii=False) + "\n")
                            continue
                        if request_hash in request_groups:
                            groups.join(family, request_groups[request_hash])
                        request_groups[request_hash] = family
                        if response_id in response_groups:
                            groups.join(family, response_groups[response_id])
                        response_groups[response_id] = family
                        if response_id in prior_by_response:
                            pinned.add(family)
                            old = prior_by_response[response_id]
                            if old["request"] != request or old["original_response"] != response:
                                raise ValueError(f"Prior diagnostic provenance differs: {old['case_id']}")
                        existing = connection.execute(
                            "SELECT request_hash,response_hash FROM cases WHERE response_id=?",
                            (response_id,),
                        ).fetchone()
                        if existing:
                            if existing != (request_hash, response_hash):
                                raise ValueError(f"Conflicting duplicate response ID: {response_id}")
                            copied += 1
                            continue
                        case_id = "exec-" + response_id
                        assessment = {
                            "label": "unreviewed",
                            "finding": "Mined execution output; notebook-level verdict is not a case-level judgment.",
                            "criterion": spec["criteria"].get(phase, spec["default_criterion"]),
                        }
                        case = {
                            "case_id": case_id, "phase": phase, "group": family,
                            "assessment": assessment, "request": request, "original_response": response,
                            "provenance": {
                                "cache": str(Path(source["folder"]) / spec["cache_filename"]),
                                "response_id": response_id, "response_model": response.get("model"),
                                "cache_key_sha256": occurrence["cache_key_sha256"],
                                "source_cache_key": key, "source_file_sha256": source_digest,
                                "request_sha256": request_hash, "response_sha256": response_hash,
                                "sdk_schema_class": schema_class, "normalization": normalization,
                                "execution_scope": "Retained cache includes earlier attempts; membership in final run not established.",
                            },
                            "diagnostics": diagnostics,
                        }
                        if response_id in prior_by_response:
                            case["prior_diagnostic"] = {
                                "case_id": prior_by_response[response_id]["case_id"],
                                "assessment": prior_by_response[response_id]["assessment"],
                            }
                        validate_case(case)
                        connection.execute("INSERT INTO cases VALUES (?,?,?,?)", (
                            response_id, json.dumps(case, ensure_ascii=False), request_hash, response_hash,
                        ))
                        metadata[response_id] = {
                            "case_id": case_id, "phase": phase, "family": family,
                            "first_notebook": name, "request_sha256": request_hash,
                            "has_images": any(isinstance(m.get("content"), list) and any(
                                isinstance(part, dict) and part.get("type") == "image_url"
                                for part in m["content"]
                            ) for m in request["messages"]),
                            "input_tokens": (response.get("usage") or {}).get("prompt_tokens"),
                            "requires_json": (request.get("response_format") or {}).get("type")
                            in ("json_object", "json_schema"),
                            "diagnostics": diagnostics,
                        }
                    connection.commit()
                    if file_hash(path) != source_digest:
                        raise ValueError(f"Source changed while reading: {path}")
                    inventory.append({
                        "notebook": name, "cache": str(path.relative_to(root)),
                        "sha256": source_digest, "bytes": path.stat().st_size,
                        "cached_entries": len(cache), "phases": dict(local),
                        "final_execution_audited": source.get("execution_audit_passed", False),
                    })
                    del cache
                    print(f"MINED {name}: {sum(local.values())} entries", flush=True)
            missing = set(prior_by_response) - set(metadata)
            if missing:
                raise ValueError(f"Prior diagnostic responses not found: {sorted(missing)}")
            pinned_roots = {groups.root(family) for family in pinned}
            split_groups = defaultdict(list)
            for family in groups.parents:
                split_groups[groups.root(family)].append(family)
            eligible = sorted(
                set(split_groups) - pinned_roots, key=lambda group: digest([seed, "split", group])
            )
            validation_count = math.ceil(len(split_groups) * fraction)
            if len(eligible) < validation_count:
                raise ValueError(
                    f"Need {validation_count} unexposed connected groups for validation; "
                    f"only {len(eligible)} remain. Change the declared fraction or collect fresh scenarios."
                )
            validation_groups = set(eligible[:validation_count])
            assignments = {
                group: "validation" if group in validation_groups else "optimization"
                for group in split_groups
            }
            for item in metadata.values():
                group = groups.root(item["family"])
                item.update(split_group=group, split=assignments[group])
            if set(assignments.values()) != {"optimization", "validation"}:
                raise ValueError("Grouped assignment produced an empty split; change the declared split seed.")
            selected = {
                split: balanced_ids(
                    [item for item in metadata.values() if item["split"] == split],
                    spec["subset_limits"][split], seed,
                )
                for split in ("optimization", "validation")
            }
            selected_sets = {key: set(value) for key, value in selected.items()}
            coverage = Counter()
            with (output / "cases.jsonl").open("x", encoding="utf-8") as all_cases, (
                output / "optimization.jsonl"
            ).open("x", encoding="utf-8") as development, (
                output / "validation.jsonl"
            ).open("x", encoding="utf-8") as validation, (
                output / "case-index.csv"
            ).open("x", encoding="utf-8", newline="") as index_stream:
                subsets = {"optimization": development, "validation": validation}
                fields = ["case_id", "phase", "family", "first_notebook", "request_sha256",
                          "split_group", "split", "has_images", "input_tokens"]
                writer = csv.DictWriter(index_stream, fieldnames=fields, extrasaction="ignore")
                writer.writeheader()
                for response_id, body in connection.execute("SELECT response_id,body FROM cases ORDER BY response_id"):
                    item = metadata[response_id]
                    case = json.loads(body)
                    case["selection"] = {
                        "split": item["split"], "split_group": item["split_group"],
                        "seed": seed, "semantic_review": "not performed",
                    }
                    line = json.dumps(case, ensure_ascii=False) + "\n"
                    all_cases.write(line)
                    if item["case_id"] in selected_sets[item["split"]]:
                        subsets[item["split"]].write(line)
                    writer.writerow(item)
                    coverage[(item["split"], item["phase"])] += 1
            report = {
                "source_count": len(inventory), "cached_entries": observed,
                "distinct_completed_responses": len(metadata), "copied_entries_removed": copied,
                "excluded_entries": excluded, "distinct_requests": len(request_groups),
                "prior_diagnostic_cases_found": len(prior),
                "new_responses_beyond_prior": len(metadata) - len(prior_by_response),
                "phase_counts": dict(Counter(item["phase"] for item in metadata.values())),
                "split_counts": dict(Counter(item["split"] for item in metadata.values())),
                "subset_counts": {key: len(value) for key, value in selected.items()},
                "split_groups": [{
                    "group": group, "families": sorted(families), "split": assignments[group],
                    "prior_diagnostic_pinned": group in pinned_roots,
                } for group, families in sorted(split_groups.items())],
                "split_phase_counts": [{"split": s, "phase": p, "count": n}
                                       for (s, p), n in sorted(coverage.items())],
                "multimodal_cases": sum(item["has_images"] for item in metadata.values()),
                "format_diagnostics": {
                    "non_json_outputs": sum(not item["diagnostics"].get("json_valid", False) for item in metadata.values()),
                    "json_contract_violations": sum(
                        item["requires_json"] and not item["diagnostics"].get("json_valid", False)
                        for item in metadata.values()
                    ),
                    "invalid_schema": sum(item["diagnostics"].get("schema_valid") is False for item in metadata.values()),
                },
                "sources": inventory, "limitations": spec["limitations"],
            }
            write_json(output / "summary.json", report)
            write_json(output / "subset-selection.json", {
                "seed": seed, "method": "Round-robin phase/scenario cells with seeded order; no quality selection.",
                "selected_ids": selected,
            })
            write_json(output / "source-manifest.json", spec)
            write_json(output / "schemas.json", schemas)
            page = (
                "<!doctype html><meta charset='utf-8'><title>Expanded execution corpus</title>"
                "<style>body{font:16px/1.5 system-ui;max-width:1100px;margin:32px auto}"
                "pre{white-space:pre-wrap;overflow-wrap:anywhere}table{border-collapse:collapse}"
                "td,th{border:1px solid #ccc;padding:8px;text-align:left}</style>"
                "<h1>Expanded execution corpus</h1><p>Exact cached messages and observed responses; "
                "no new model calls. Newly mined outputs are unreviewed, not gold answers. "
                "The full corpus is in cases.jsonl; case-index.csv is a compact browseable index.</p>"
                "<h2>Prompt families</h2><table><tr><th>Family</th><th>Cases</th></tr>"
                + "".join(f"<tr><td>{html.escape(phase)}</td><td>{count}</td></tr>"
                          for phase, count in sorted(report["phase_counts"].items()))
                + "</table><h2>Counts, sources, splits and limitations</h2><pre>"
                + html.escape(json.dumps(report, ensure_ascii=False, indent=2)) + "</pre>"
            )
            (output / "report.html").write_text(page, encoding="utf-8")
        finally:
            connection.close()
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ("sources", "split_groups", "split_phase_counts", "limitations")}, indent=2))
    return report


def write_json(path, value):
    """Save generated artifacts as UTF-8 JSON."""
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    mine(args.manifest, args.output)
