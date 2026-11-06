"""Verify usage-bearing failures are charged and duplicate canonical evidence is rejected."""

import copy
import json

import pytest

from model_case_study import digest
from summarize_repair_study import summarize
from test_select_execution_cases import corpus


def fixture(tmp_path):
    from test_study_report import CostTests

    source_path, rows = corpus(tmp_path)
    case = rows[0]
    case["request"]["model"] = "gpt-6-luna"
    case["request"]["reasoning_effort"] = "xhigh"
    case["provenance"]["request_sha256"] = digest(case["request"])
    case["experiment"] = {"source_case_id": case["case_id"]}
    source_path.write_text(json.dumps(case) + "\n", encoding="utf-8")
    costs = CostTests()
    costs.setUp()
    costs.response["id"] = "unique-response"
    run = {"case_id": case["case_id"], "request": case["request"],
           "request_sha256": digest(case["request"]), "status": "incomplete_or_refused",
           "elapsed_seconds": 1, "response": costs.response}
    (tmp_path / "results.jsonl").write_text(json.dumps(run) + "\n", encoding="utf-8")
    (tmp_path / "prices.json").write_text(json.dumps(costs.prices), encoding="utf-8")
    config = {"model": "gpt-6-luna", "reasoning_effort": "xhigh", "prices": "prices.json",
              "batches": [{"name": "first", "cases": source_path.name, "results": "results.jsonl"}]}
    return config, run


def test_incomplete_usage_and_unknown_error_charges_are_not_dropped(tmp_path):
    config, run = fixture(tmp_path)
    error = copy.deepcopy(run)
    error.pop("response")
    error.update(status="error", error={"message": "Service error"})
    (tmp_path / "error.jsonl").write_text(json.dumps(error) + "\n", encoding="utf-8")
    config["batches"].append({**config["batches"][0], "name": "second", "results": "error.jsonl"})
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    result = summarize(path, tmp_path / "summary.json")
    assert result["canonical_attempts"] == 2
    assert result["statuses"] == {"incomplete_or_refused": 1, "error": 1}
    assert result["attempts_without_usage_unknown_charge"] == 1
    assert float(result["usage_list_price_bounds_usd"][0]) > 0


def test_repeated_api_response_cannot_be_counted_as_a_fresh_attempt(tmp_path):
    config, _ = fixture(tmp_path)
    config["batches"].append({**config["batches"][0], "name": "duplicate"})
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    with pytest.raises(ValueError, match="same API response"):
        summarize(path, tmp_path / "summary.json")
