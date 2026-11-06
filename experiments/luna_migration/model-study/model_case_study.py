"""Export cached model calls and replay them without importing TinyTroupe."""

import argparse
import ast
import copy
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path


def digest(value):
    """Hash a JSON value independently of dictionary ordering."""
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def decode_key(key):
    """Safely decode a literal cache key with an optional SDK response-model class."""
    match = re.search(
        r", 'response_format': <class '([\w.]+)'>(?=, '[A-Za-z_]\w*':|}\)$)",
        key,
    )
    schema_class = match[1] if match else None
    if match:
        key = key[:match.start()] + ", 'response_format': None" + key[match.end():]
    model, request = ast.literal_eval(key)
    if not isinstance(model, str) or not isinstance(request, dict):
        raise ValueError("Cache key must contain a model name and request dictionary.")
    if request.get("model") != model or not isinstance(request.get("messages"), list):
        raise ValueError("Inconsistent cached model or missing message list.")
    return request, schema_class


def replay_body(case, condition):
    """Change only explicitly selected experimental parameters."""
    body = copy.deepcopy(case["request"])
    body["model"] = condition["model"]
    effort = condition.get("reasoning_effort", "preserve")
    if effort == "omit":
        body.pop("reasoning_effort", None)
    elif effort != "preserve":
        body["reasoning_effort"] = effort
    if "max_completion_tokens" in condition:
        body["max_completion_tokens"] = condition["max_completion_tokens"]
    if (body.get("response_format") or {}).get("type") == "json_object" and not any(
        "json" in json.dumps(message.get("content"), ensure_ascii=False).lower()
        for message in body["messages"]
    ):
        raise ValueError(f"{case['case_id']}: JSON-object mode requires explicit JSON wording in messages.")
    return body


def validate_case(case):
    """Detect modified request/response artifacts and incomplete provenance."""
    for field in ("case_id", "request", "original_response", "provenance", "assessment"):
        if field not in case:
            raise ValueError(f"Missing case field: {field}")
    provenance = case["provenance"]
    if digest(case["request"]) != provenance["request_sha256"]:
        raise ValueError(f"Request hash mismatch: {case['case_id']}")
    if digest(case["original_response"]) != provenance["response_sha256"]:
        raise ValueError(f"Response hash mismatch: {case['case_id']}")
    choices = case["original_response"].get("choices", [])
    if not choices or choices[0].get("finish_reason") != "stop":
        raise ValueError(f"Original case is not a completed response: {case['case_id']}")


def normalize_cache_request(key, schemas):
    """Recover replay parameters while preserving message content and recording transport changes."""
    request, schema_class = decode_key(key)
    normalization = []
    if schema_class:
        request["response_format"] = copy.deepcopy(schemas[schema_class])
        normalization.append(
            "SDK Pydantic response class replaced by its exported strict JSON schema. "
            "Schema exported from the matching current library; not a captured wire body."
        )
    if request.get("reasoning_effort") is not None:
        for name in ("stream", "temperature", "top_p", "frequency_penalty", "presence_penalty"):
            if name in request:
                del request[name]
                normalization.append(f"Removed {name}, matching source client preprocessing.")
    if "response_format" in request:
        request.pop("stream", None)
    request.pop("timeout", None)
    return request, schema_class, normalization


def export_cases(manifest_path, output):
    """Export exact messages, full completions, explicit labels and portable schemas."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    root = manifest_path.parent
    schemas = json.loads((root / manifest["schema_file"]).read_text(encoding="utf-8"))
    output.mkdir(parents=True, exist_ok=True)
    cached_path = None
    cache = None
    cases = []
    for selection in manifest["cases"]:
        path = (root / selection["cache"]).resolve()
        if cached_path != path:
            cache = json.loads(path.read_text(encoding="utf-8"))
            cached_path = path
        matches = [(key, value) for key, value in cache.items()
                   if value.get("id") == selection["response_id"]]
        if len(matches) != 1:
            raise ValueError(f"Expected one response: {selection['case_id']}, got {len(matches)}")
        key, response = matches[0]
        request, schema_class, normalization = normalize_cache_request(key, schemas)
        case = {
            "case_id": selection["case_id"],
            "phase": selection["phase"],
            "group": selection["group"],
            "assessment": selection["assessment"],
            "request": request,
            "original_response": response,
            "provenance": {
                "cache": selection["cache"],
                "response_id": response["id"],
                "response_model": response.get("model"),
                "cache_key_sha256": hashlib.sha256(key.encode("utf-8")).hexdigest(),
                "request_sha256": digest(request),
                "response_sha256": digest(response),
                "sdk_schema_class": schema_class,
                "normalization": normalization,
                "source_cache_key": key,
            },
        }
        validate_case(case)
        cases.append(case)
        print(f"EXPORTED {case['case_id']} ({len(json.dumps(request))} request characters)")
    ids = [case["case_id"] for case in cases]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate case IDs.")
    path = output / "cases.jsonl"
    path.write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases),
                    encoding="utf-8")
    sections = []
    for case in cases:
        text = case["original_response"]["choices"][0]["message"].get("content", "")
        sections.append(
            f"<details><summary>{html.escape(case['case_id'])} — "
            f"{html.escape(case['assessment']['label'])}</summary>"
            f"<p>{html.escape(case['assessment']['finding'])}</p>"
            f"<p><b>Evaluate:</b> {html.escape(case['assessment']['criterion'])}</p>"
            f"<h3>Complete original output</h3><pre>{html.escape(text or '')}</pre>"
            f"<h3>Complete replay request</h3><pre>"
            f"{html.escape(json.dumps(case['request'], ensure_ascii=False, indent=2))}</pre>"
            "</details>"
        )
    page = (
        "<!doctype html><meta charset='utf-8'><title>Standalone model cases</title>"
        "<style>body{font:16px/1.5 system-ui;max-width:1100px;margin:32px auto}"
        "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f4f4;padding:16px}"
        "summary{cursor:pointer;font-weight:bold}details{margin:18px 0}</style>"
        f"<h1>Standalone model cases</h1><p>{len(cases)} curated calls. These are "
        "diagnostic examples, not a representative benchmark. Group-level concerns do "
        "not make an individual negative preference incorrect. Prompts are preserved "
        "exactly; transport/schema normalization is recorded in JSONL provenance.</p>"
        + "".join(sections)
    )
    (output / "cases.html").write_text(page, encoding="utf-8")
    print(f"SAVED {len(cases)} cases to {path}")


def run_cases(corpus, conditions_path, output, selected, repeats, timeout, execute):
    """Run explicit conditions sequentially, recording full responses or explicit errors."""
    if repeats <= 0 or timeout <= 0:
        raise ValueError("Repeats and timeout must be positive.")
    cases = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()
             if line.strip()]
    for case in cases:
        validate_case(case)
    ids = {case["case_id"] for case in cases}
    if len(ids) != len(cases):
        raise ValueError("Corpus case IDs must be unique.")
    if selected and not set(selected) <= ids:
        raise ValueError(f"Unknown cases: {set(selected) - ids}")
    cases = [case for case in cases if not selected or case["case_id"] in selected]
    conditions = json.loads(conditions_path.read_text(encoding="utf-8"))
    if not conditions or not cases:
        raise ValueError("Select at least one case and condition.")
    names = [condition["id"] for condition in conditions]
    if len(set(names)) != len(names):
        raise ValueError("Condition IDs must be unique.")
    if any(not c.get("model", "").startswith(("gpt-", "o1", "o3", "o4")) for c in conditions):
        raise ValueError("Only explicit OpenAI model IDs are supported.")
    count = len(cases) * len(conditions) * repeats
    print(f"PLAN: {len(cases)} cases x {len(conditions)} conditions x {repeats} repeats = {count} calls.")
    for case in cases:
        for condition in conditions:
            replay_body(case, condition)
    if not execute:
        print("DRY RUN ONLY: no API calls. Add --execute to spend API credits.")
        return
    if output.exists():
        raise FileExistsError("Use a new result path; existing study results are never overwritten.")
    from openai import OpenAI

    client = OpenAI(timeout=timeout, max_retries=0)
    failures = 0
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8") as stream:
        for case in cases:
            for condition in conditions:
                body = replay_body(case, condition)
                for replicate in range(repeats):
                    started = time.monotonic()
                    result = {
                        "case_id": case["case_id"], "condition_id": condition["id"],
                        "replicate": replicate, "started_at": datetime.now(timezone.utc).isoformat(),
                        "request": body, "request_sha256": digest(body),
                        "source_request_sha256": case["provenance"]["request_sha256"],
                    }
                    try:
                        response = client.chat.completions.create(**body)
                        result["response"] = response.model_dump(mode="json")
                        choices = response.choices
                        refusal = choices[0].message.refusal if choices else None
                        result["status"] = (
                            "completed" if choices and choices[0].finish_reason == "stop"
                            and not refusal else "incomplete_or_refused"
                        )
                    except Exception as exc:
                        # Every failed API attempt stays visible; never substitute an answer.
                        result["status"] = "error"
                        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
                    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
                    failures += result["status"] != "completed"
                    stream.write(json.dumps(result, ensure_ascii=False) + "\n")
                    stream.flush()
                    print(f"{case['case_id']} {condition['id']} #{replicate}: "
                          f"{result['status']} {result['elapsed_seconds']}s")
    if failures:
        raise SystemExit(f"{failures} calls failed, were incomplete or refused; see saved results.")


def main():
    """Default to an explicit no-spend plan for standalone comparisons."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export")
    export.add_argument("--manifest", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    replay = commands.add_parser("replay")
    replay.add_argument("--corpus", type=Path, required=True)
    replay.add_argument("--conditions", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--case", action="append", default=[])
    replay.add_argument("--repeats", type=int, default=1)
    replay.add_argument("--timeout", type=float, default=120)
    replay.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.command == "export":
        export_cases(args.manifest, args.output)
    else:
        run_cases(args.corpus, args.conditions, args.output, args.case,
                  args.repeats, args.timeout, args.execute)


if __name__ == "__main__":
    main()
