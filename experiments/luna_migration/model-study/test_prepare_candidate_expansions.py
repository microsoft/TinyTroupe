"""Candidate draws are reproducible, auditable and never silently repaired."""

import json
import copy

import pytest

from model_case_study import digest
from prepare_candidate_expansions import build


def fixture(tmp_path):
    request = {"model": "test", "messages": [
        {"role": "system", "content": "System"},
        {"role": "user", "content": "Fixed particulars.\n## Generation Rules\nFull record."},
    ]}
    response = {"id": "plan-0", "choices": [{
        "finish_reason": "stop",
        "message": {"content": json.dumps({"candidates": [
            {"particulars": {"name": "Fixed"}, "life": f"Life {i}"} for i in range(4)
        ]})},
    }]}
    case = {
        "case_id": "sample::base", "phase": "persona_generation", "request": request,
        "original_response": response, "assessment": {},
        "experiment": {"source_case_id": "sample", "variant": "base"},
        "provenance": {"request_sha256": digest(request), "response_sha256": digest(response)},
    }
    for name in ["base", "plan"]:
        (tmp_path / f"{name}.jsonl").write_text(json.dumps(case) + "\n", encoding="utf-8")
    run = {"case_id": case["case_id"], "condition_id": "test", "replicate": 0,
           "request": request, "request_sha256": digest(request),
           "status": "completed", "response": response}
    (tmp_path / "results.jsonl").write_text(json.dumps(run) + "\n", encoding="utf-8")
    (tmp_path / "instruction.txt").write_text("Develop this candidate:", encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({
        "candidate_count": 4, "selection_seed": 123,
        "required_candidate_fields": ["particulars", "life"],
        "expansion_instruction": "instruction.txt",
    }), encoding="utf-8")
    return run


def invoke(tmp_path, name="out"):
    build(tmp_path / "base.jsonl", tmp_path / "plan.jsonl", tmp_path / "results.jsonl",
          tmp_path / "config.json", tmp_path / name, "expanded")


def test_reproducible_draw_preserves_input_and_provenance(tmp_path):
    run = fixture(tmp_path)
    invoke(tmp_path)
    invoke(tmp_path, "again")
    assert (tmp_path / "out/selected.jsonl").read_bytes() == (tmp_path / "again/selected.jsonl").read_bytes()
    case = json.loads((tmp_path / "out/selected.jsonl").read_text(encoding="utf-8"))
    original = run["request"]
    assert case["request"]["messages"][0] == original["messages"][0]
    assert case["request"]["messages"][1]["content"].startswith(original["messages"][1]["content"])
    audit = case["experiment"]["selection"]
    assert audit["response_sha256"] == digest(run["response"])
    assert audit["candidate_sha256"] == digest(audit["selected_candidate"])
    assert 0 <= audit["selected_index_zero_based"] < 4
    with pytest.raises(FileExistsError):
        invoke(tmp_path)


@pytest.mark.parametrize("failure", ["duplicate", "bad_hash", "error", "truncated", "wrong_count", "missing_field"])
def test_bad_plan_fails_before_writing(tmp_path, failure):
    run = fixture(tmp_path)
    if failure == "bad_hash":
        run["request_sha256"] = "modified"
    elif failure == "error":
        run["status"] = "error"
    elif failure == "truncated":
        run["response"]["choices"][0]["finish_reason"] = "length"
    elif failure in ("wrong_count", "missing_field"):
        candidates = [{"particulars": {"name": "Fixed"}, "life": "A life"} for _ in range(4)]
        if failure == "wrong_count":
            candidates.pop()
        else:
            del candidates[0]["life"]
        run["response"]["choices"][0]["message"]["content"] = json.dumps({"candidates": candidates})
    rows = [run, run] if failure == "duplicate" else [run]
    (tmp_path / "results.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
    )
    with pytest.raises(ValueError):
        invoke(tmp_path)
    assert not (tmp_path / "out").exists()


def test_draws_do_not_depend_on_file_order(tmp_path):
    first = fixture(tmp_path)
    second = copy.deepcopy(first)
    second["replicate"] = 1
    second["response"]["id"] = "plan-1"
    results = tmp_path / "results.jsonl"
    results.write_text("\n".join(map(json.dumps, [first, second])) + "\n", encoding="utf-8")
    invoke(tmp_path)
    results.write_text("\n".join(map(json.dumps, [second, first])) + "\n", encoding="utf-8")
    invoke(tmp_path, "reversed")
    assert (tmp_path / "out/selected.jsonl").read_bytes() == (tmp_path / "reversed/selected.jsonl").read_bytes()
