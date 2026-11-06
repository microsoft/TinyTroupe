"""Verify large-list semantic partition composition cannot lose or duplicate chunk membership."""

import json

import pytest

from model_case_study import digest
from prepare_partition_pipeline import assemble, assignments, plans
from test_select_execution_cases import corpus


def test_pipeline_restores_duplicate_occurrences_and_rejects_missing_chunks(tmp_path):
    source_path, rows = corpus(tmp_path)
    source = rows[0]
    source["phase"] = "normalization"
    source["provenance"]["normalization"] = []
    source["request"]["messages"] = [
        {"role": "user", "content": "Produce UP TO 2 categories.\nINPUT ELEMENTS:\n  - first\n  - second\n  - first\n"}
    ]
    source["provenance"]["request_sha256"] = digest(source["request"])
    source_path.write_text(json.dumps(source)+"\n", encoding="utf-8")
    instruction = tmp_path / "instruction.txt"
    instruction.write_text("Return JSON", encoding="utf-8")
    plans(source_path, instruction, tmp_path / "plans", "test")
    plan = json.loads((tmp_path / "plans" / "cases.jsonl").read_text(encoding="utf-8"))
    response = {"id": "plan-response", "choices": [{"message": {"content": json.dumps({"groups": {
        "1": {"label": "Repeated", "scope": "First"}, "2": {"label": "Other", "scope": "Second"}
    }})}}]}
    results = tmp_path / "plan-results.jsonl"
    results.write_text(json.dumps({"case_id": plan["case_id"], "request": plan["request"],
                                  "status": "completed", "response": response})+"\n", encoding="utf-8")
    assignments(tmp_path / "plans", results, instruction, tmp_path / "chunks", "assign", 2)
    chunks = [json.loads(s) for s in (tmp_path / "chunks" / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(chunks) == 2
    runs = []
    for i, chunk in enumerate(chunks):
        selected = {k: 2 if k == "2" else 1 for k in chunk["experiment"]["chunk_ids"]}
        runs.append({"case_id": chunk["case_id"], "request": chunk["request"], "status": "completed",
                     "response": {"id": f"chunk-{i}", "choices": [{"message": {
                         "content": json.dumps({"assignments": selected})}}]}})
    chunk_results = tmp_path / "chunk-results.jsonl"
    chunk_results.write_text("".join(json.dumps(r)+"\n" for r in runs), encoding="utf-8")
    partitions = assemble(tmp_path / "chunks", chunk_results, tmp_path / "assembled")
    assert partitions[0]["reconstructed"] == {"Repeated": ["first", "first"], "Other": ["second"]}
    chunk_results.write_text(json.dumps(runs[0])+"\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing"):
        assemble(tmp_path / "chunks", chunk_results, tmp_path / "missing")
