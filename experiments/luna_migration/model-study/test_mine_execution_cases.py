"""Offline tests for broad extraction, provenance, split boundaries and retained failures."""

import copy
import json
from pathlib import Path

import pytest

from mine_execution_cases import balanced_ids, classify, load_lines, mine, output_diagnostics
from model_case_study import digest, normalize_cache_request


def fixture(tmp_path):
    schema = {"type": "json_schema", "json_schema": {
        "name": "Answer", "strict": True,
        "schema": {"type": "object", "properties": {"value": {"type": "integer"}},
                   "required": ["value"], "additionalProperties": False},
    }}
    (tmp_path / "schemas.json").write_text(json.dumps({"test.Answer": schema}), encoding="utf-8")
    sources = []
    prior = None
    for i, family in enumerate(["known", "fresh-one", "fresh-two", "fresh-three", "fresh-four"]):
        folder = tmp_path / family
        folder.mkdir()
        request = {"model": "gpt-6-luna", "messages": [{"role": "system", "content": family}],
                   "reasoning_effort": "xhigh", "response_format": {"type": "json_object"}}
        response = {"id": f"response-{i}", "model": "gpt-6-luna",
                    "choices": [{"finish_reason": "stop",
                                 "message": {"content": json.dumps({"value": i})}}]}
        key = str(("gpt-6-luna", request))
        (folder / "api.cache.json").write_text(json.dumps({key: response}), encoding="utf-8")
        sources.append({"name": family, "folder": family, "execution_audit_passed": True})
        if i == 0:
            prior = {"case_id": "original", "phase": "agent_action", "group": family,
                     "assessment": {"label": "positive", "finding": "prior review", "criterion": "fidelity"},
                     "request": request, "original_response": response,
                     "provenance": {"request_sha256": digest(request),
                                    "response_sha256": digest(response)}}
    (tmp_path / "prior.jsonl").write_text(json.dumps(prior) + "\n", encoding="utf-8")
    (tmp_path / "audit.json").write_text(json.dumps({"runs": sources}), encoding="utf-8")
    spec = {"source_root": ".", "source_audit": "audit.json", "schemas": "schemas.json",
            "prior_corpus": "prior.jsonl", "cache_filename": "api.cache.json",
            "seed": 291029, "validation_fraction": 0.5,
            "subset_limits": {"optimization": 20, "validation": 20},
            "group_rules": [], "phase_rules": [], "criteria": {},
            "default_criterion": "review", "limitations": ["not semantic gold"]}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    return path, spec, sources


def test_normalization_preserves_messages_and_records_schema_reconstruction():
    messages = [{"role": "system", "content": '"unchanged encoded envelope"'}]
    key = str(("gpt-6-luna", {
        "model": "gpt-6-luna", "messages": messages, "response_format": None,
        "temperature": 0.8, "stream": False, "timeout": 12, "reasoning_effort": "xhigh",
    })).replace("'response_format': None", "'response_format': <class 'test.Answer'>")
    schema = {"type": "json_schema", "json_schema": {"name": "Answer"}}
    request, cls, notes = normalize_cache_request(key, {"test.Answer": schema})
    assert request["messages"] == messages and cls == "test.Answer"
    assert not {"temperature", "stream", "timeout"} & request.keys()
    assert request["response_format"] == schema and notes
    request["response_format"]["json_schema"]["name"] = "Changed"
    assert schema["json_schema"]["name"] == "Answer"


def test_classification_decodes_only_for_matching():
    request = {"messages": [{"content": json.dumps("# Results filter\nhello")}]}
    before = copy.deepcopy(request)
    assert classify(request, None, [
        {"system_contains": "# Results filter", "phase": "extraction"}
    ]) == "extraction"
    assert request == before
    assert classify(request, None, []) == "unclassified"


def test_observable_schema_failure_not_hidden():
    request = {"response_format": {"type": "json_schema", "json_schema": {
        "schema": {"type": "object", "required": ["value"]},
    }}}
    response = {"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
    checks = output_diagnostics(request, response)
    assert checks["json_valid"] and checks["schema_valid"] is False


def test_complete_export_pins_prior_and_is_reproducible(tmp_path):
    path, _, _ = fixture(tmp_path)
    first, second = tmp_path / "first", tmp_path / "second"
    report = mine(path, first)
    mine(path, second)
    cases = list(load_lines(first / "cases.jsonl"))
    assert report["distinct_completed_responses"] == 5
    assert report["new_responses_beyond_prior"] == 4
    assert cases[0]["prior_diagnostic"]["case_id"] == "original"
    assert cases[0]["selection"]["split"] == "optimization"
    assert all(c["assessment"]["label"] == "unreviewed" for c in cases)
    assert (first / "cases.jsonl").read_bytes() == (second / "cases.jsonl").read_bytes()
    assert not list(first.glob("mining-*"))
    with pytest.raises(FileExistsError):
        mine(path, first)


def test_duplicate_copy_merges_sources_and_retains_occurrences(tmp_path):
    path, _, sources = fixture(tmp_path)
    folder = tmp_path / "copy"
    folder.mkdir()
    (folder / "api.cache.json").write_bytes((tmp_path / "known" / "api.cache.json").read_bytes())
    sources.append({"name": "copy", "folder": "copy"})
    (tmp_path / "audit.json").write_text(json.dumps({"runs": sources}), encoding="utf-8")
    report = mine(path, tmp_path / "out")
    assert report["distinct_completed_responses"] == 5 and report["copied_entries_removed"] == 1
    assert len(list(load_lines(tmp_path / "out" / "occurrences.jsonl"))) == 6
    group = next(g for g in report["split_groups"] if "copy" in g["families"])
    assert group["families"] == ["copy", "known"] and group["split"] == "optimization"


def test_different_completions_same_request_stay_in_same_split(tmp_path):
    path, _, sources = fixture(tmp_path)
    first = json.loads((tmp_path / "known" / "api.cache.json").read_text(encoding="utf-8"))
    key, response = next(iter(first.items()))
    response["id"] = "extra-response"
    response["choices"][0]["message"]["content"] = '{"value":99}'
    (tmp_path / "fresh-one" / "api.cache.json").write_text(json.dumps({key: response}), encoding="utf-8")
    report = mine(path, tmp_path / "out")
    assert report["distinct_completed_responses"] == 5 and report["distinct_requests"] == 4
    cases = list(load_lines(tmp_path / "out" / "cases.jsonl"))
    same = [c for c in cases if c["provenance"]["request_sha256"] == digest(
        next(load_lines(tmp_path / "prior.jsonl"))["request"])]
    assert len(same) == 2 and {c["selection"]["split"] for c in same} == {"optimization"}


def test_conflicting_duplicate_is_rejected(tmp_path):
    path, _, _ = fixture(tmp_path)
    cache_path = tmp_path / "fresh-one" / "api.cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    next(iter(cache.values()))["id"] = "response-0"
    cache_path.write_text(json.dumps(cache), encoding="utf-8")
    with pytest.raises(ValueError, match="Prior diagnostic provenance differs|Conflicting duplicate"):
        mine(path, tmp_path / "out")


def test_incomplete_response_preserved_separately(tmp_path):
    path, _, _ = fixture(tmp_path)
    cache_path = tmp_path / "fresh-one" / "api.cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8"))
    next(iter(cache.values()))["choices"][0]["finish_reason"] = "length"
    cache_path.write_text(json.dumps(cache), encoding="utf-8")
    report = mine(path, tmp_path / "out")
    assert report["excluded_entries"] == 1 and report["distinct_completed_responses"] == 4
    excluded = list(load_lines(tmp_path / "out" / "excluded.jsonl"))
    assert excluded[0]["response"]["choices"][0]["finish_reason"] == "length"


def test_balancing_limits_and_input_order_independence():
    rows = [{"case_id": f"{phase}-{i}", "phase": phase, "split_group": "scenario"}
            for phase in ["a", "b"] for i in range(10)]
    ids = balanced_ids(rows, 5, 123)
    assert len(ids) == len(set(ids)) == 5
    assert ids == balanced_ids(list(reversed(rows)), 5, 123)
    assert sum(case.startswith("a-") for case in ids) == 3


def test_validation_group_count_uses_declared_fraction(tmp_path):
    path, _, _ = fixture(tmp_path)
    report = mine(path, tmp_path / "out")
    assert sum(group["split"] == "validation" for group in report["split_groups"]) == 3
    assert all(not group["prior_diagnostic_pinned"] for group in report["split_groups"]
               if group["split"] == "validation")


def test_insufficient_unexposed_groups_fail_explicitly(tmp_path):
    path, spec, _ = fixture(tmp_path)
    spec["group_rules"] = [{"pattern": ".*", "group": "all-connected"}]
    path.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(ValueError, match="only 0 remain"):
        mine(path, tmp_path / "out")
