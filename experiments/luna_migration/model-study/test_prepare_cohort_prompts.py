"""Verify cohort context is explicit, traceable and does not overwrite prior artifacts."""

import json

import pytest

from model_case_study import digest
from prepare_cohort_prompts import build


@pytest.fixture
def inputs(tmp_path):
    request = {"model": "gpt-6-luna", "messages": [{"role": "user", "content": "Fixed constraints."}]}
    response = {"id": "test-response", "choices": [{"finish_reason": "stop", "message": {
        "content": json.dumps({"age": 30, "occupation": "Writer"})
    }}]}
    case = {"case_id": "sample::base", "request": request, "original_response": response,
            "assessment": {}, "provenance": {
                "request_sha256": digest(request), "response_sha256": digest(response),
            }, "experiment": {"source_case_id": "sample"}}
    corpus = tmp_path / "source.jsonl"
    corpus.write_text(json.dumps(case) + "\n", encoding="utf-8")
    history = tmp_path / "history.jsonl"
    history.write_text(json.dumps({"case_id": "sample::old", "replicate": 0,
                                  "status": "completed", "response": response}) + "\n", encoding="utf-8")
    (tmp_path / "instruction.txt").write_text("Prior drafts are alternatives:", encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text(json.dumps({
        "case_ids": ["sample::base"], "context_fields": ["occupation"],
        "instruction_file": "instruction.txt", "message": 0, "purpose": "Diversity test",
    }), encoding="utf-8")
    return corpus, config, history, case


def test_context_uses_matching_source_and_keeps_original_request(tmp_path, inputs):
    corpus, config, history, case = inputs
    output = tmp_path / "new"
    build(corpus, config, [history], output, "new")
    saved = json.loads((output / "selected.jsonl").read_text(encoding="utf-8"))
    assert saved["request"]["messages"][0]["content"].startswith("Fixed constraints.")
    assert "Writer" in saved["request"]["messages"][0]["content"]
    assert '"age"' not in saved["request"]["messages"][0]["content"]
    assert saved["experiment"]["diversity_seeking_not_population_sample"]
    source = saved["experiment"]["prior_candidate_provenance"][0]
    assert source["response_id"] == "test-response"
    assert source["response_sha256"] == digest(case["original_response"])
    assert json.loads(corpus.read_text(encoding="utf-8")) == case
    with pytest.raises(FileExistsError):
        build(corpus, config, [history], output, "new")


def test_failed_history_is_rejected_without_writing(tmp_path, inputs):
    corpus, config, history, _ = inputs
    history.write_text(json.dumps({"status": "error"}) + "\n", encoding="utf-8")
    output = tmp_path / "failed"
    with pytest.raises(ValueError, match="failed attempt"):
        build(corpus, config, [history], output, "bad")
    assert not output.exists()


def test_unrelated_history_is_not_used(tmp_path, inputs):
    corpus, config, history, _ = inputs
    run = json.loads(history.read_text(encoding="utf-8"))
    run["case_id"] = "unrelated::old"
    history.write_text(json.dumps(run) + "\n", encoding="utf-8")
    output = tmp_path / "unrelated"
    with pytest.raises(ValueError, match="No candidate history"):
        build(corpus, config, [history], output, "bad")
    assert not output.exists()


def test_missing_context_fields_fail_explicitly(tmp_path, inputs):
    corpus, config, history, _ = inputs
    run = json.loads(history.read_text(encoding="utf-8"))
    run["response"]["choices"][0]["message"]["content"] = "{}"
    history.write_text(json.dumps(run) + "\n", encoding="utf-8")
    output = tmp_path / "missing"
    with pytest.raises(ValueError, match="lacks context fields"):
        build(corpus, config, [history], output, "bad")
    assert not output.exists()
