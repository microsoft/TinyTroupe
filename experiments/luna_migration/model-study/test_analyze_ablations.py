"""Checks must distinguish public answers from private simulated thoughts."""

import json
import csv
import unittest
from pathlib import Path

import pytest

from analyze_ablations import analyze, output_checks, result_labels
from model_case_study import digest


class ObservationTests(unittest.TestCase):
    def check_actions(self, actions):
        return output_checks({"phase": "agent_action", "request": {}}, {
            "choices": [{"message": {"content": json.dumps({"actions": actions})}}],
        })

    def test_private_number_is_not_a_public_answer(self):
        checks = self.check_actions([
            {"type": "THINK", "content": "My answer would be 2."},
            {"type": "DONE", "content": "Waiting."},
        ])
        self.assertFalse(checks["public_answer_present"])
        self.assertNotIn("first_public_number_1_to_5", checks)

    def test_ranking_must_be_a_permutation(self):
        checks = self.check_actions([{"type": "TALK", "content": "Ranking: A, B, C, D, A"}])
        self.assertFalse(checks["ranking_is_permutation"])

    def test_bare_decision_is_not_a_reason(self):
        checks = self.check_actions([{"type": "TALK", "content": "No."}])
        self.assertEqual(checks["decision"], "no")
        self.assertFalse(checks["public_reason_present"])

    def test_invalid_json_is_visible(self):
        checks = output_checks({"phase": "extraction", "request": {}}, {
            "choices": [{"message": {"content": "Not JSON"}}],
        })
        self.assertFalse(checks["json_valid"])
        self.assertIn("parse_error", checks)

    def test_same_basename_in_separate_rounds_is_unambiguous(self):
        a = Path("round1") / "results.jsonl"
        b = Path("round2") / "results.jsonl"
        self.assertEqual(result_labels([a, b]), {
            a: "round1/results.jsonl", b: "round2/results.jsonl",
        })

    def test_single_file_keeps_short_label(self):
        path = Path("round1") / "results.jsonl"
        self.assertEqual(result_labels([path]), {path: "results.jsonl"})


def test_combined_round_report_retains_both_observations_and_reviews(tmp_path):
    request = {"model": "test", "messages": [{"role": "user", "content": "Question"}]}
    response = {
        "id": "test-response", "model": "test", "service_tier": "default",
        "choices": [{"finish_reason": "stop", "message": {"content": '{"response":"No"}'}}],
        "usage": {
            "prompt_tokens": 10, "completion_tokens": 5,
            "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 2},
        },
    }
    case = {
        "case_id": "sample", "request": request, "original_response": response,
        "phase": "extraction", "assessment": {},
        "experiment": {"source_case_id": "source", "variant": "variant"},
        "provenance": {"request_sha256": digest(request), "response_sha256": digest(response)},
    }
    corpus = tmp_path / "cases.jsonl"
    corpus.write_text(json.dumps(case) + "\n", encoding="utf-8")
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps({"models": {"test": {
        "input": "1", "cached_input": ".05", "cache_write": "1.25", "output": "5",
        "long_context_threshold": 272000, "long_input_multiplier": "2", "long_output_multiplier": "1.5",
    }}}), encoding="utf-8")
    paths = []
    for folder in ["round1", "round2"]:
        path = tmp_path / folder / "results.jsonl"
        path.parent.mkdir()
        path.write_text(json.dumps({
            "case_id": "sample", "condition_id": "condition", "replicate": 0,
            "request": request, "request_sha256": digest(request), "response": response,
            "status": "completed", "elapsed_seconds": 1, "started_at": "2026-01-01T00:00:00Z",
        }) + "\n", encoding="utf-8")
        paths.append(path)
    review = tmp_path / "review.json"
    review.write_text(json.dumps({
        "summary": "Reviewed", "limitations": ["Small sample"],
        "case_reviews": [{"case": "sample", "status": "Reviewed", "evidence": "Exact output"}],
    }), encoding="utf-8")
    output = tmp_path / "report"
    analyze(corpus, paths, prices, output, review)
    saved = json.loads((output / "analysis.json").read_text(encoding="utf-8"))
    assert saved["totals"]["test"]["calls"] == 2
    assert {row["result_file"] for row in saved["observations"]} == {
        "round1/results.jsonl", "round2/results.jsonl",
    }
    page = (output / "report.html").read_text(encoding="utf-8")
    assert "Exact output" in page
    assert "Terra" not in page
    failed = tmp_path / "rejected" / "results.jsonl"
    failed.parent.mkdir()
    failed.write_text(json.dumps({
        "case_id": "sample", "condition_id": "condition", "replicate": 0,
        "request": request, "request_sha256": digest(request),
        "status": "error", "error": {"message": "API rejected request; no usage"},
        "elapsed_seconds": 1, "started_at": "2026-01-01T00:00:00Z",
    }) + "\n", encoding="utf-8")
    paths.append(failed)
    from assemble_prompt_report import assemble
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"experiments": [
        {"name": path.parent.name, "role": "development", "corpus": "cases.jsonl",
         "results": path.relative_to(tmp_path).as_posix()}
        for path in paths
    ]}), encoding="utf-8")
    combined_output = tmp_path / "combined"
    assemble(index, prices, review, combined_output)
    with (combined_output / "stage-costs.csv").open(encoding="utf-8") as stream:
        stage = next(csv.DictReader(stream))
    assert stage["calls"] == "3"
    assert stage["completed"] == "2"
    assert stage["calls_without_usage"] == "1"
    with pytest.raises(FileExistsError):
        assemble(index, prices, review, combined_output)
    duplicate = json.loads(index.read_text(encoding="utf-8"))
    duplicate["experiments"].append(duplicate["experiments"][0])
    index.write_text(json.dumps(duplicate), encoding="utf-8")
    with pytest.raises(ValueError, match="Repeated result file"):
        assemble(index, prices, review, tmp_path / "duplicate")


if __name__ == "__main__":
    unittest.main()
