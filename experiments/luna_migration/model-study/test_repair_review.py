"""Verify repair reporting retains invalid assignments as explicit failures."""

import json

from model_case_study import digest
from normalization_assignments import indexed_request
from review_repair_study import review
from test_select_execution_cases import corpus


def test_invalid_assignment_response_remains_visible_and_raw_response_is_unchanged(tmp_path):
    from test_study_report import CostTests

    source_path, rows = corpus(tmp_path)
    source = rows[0]
    source["phase"] = "normalization"
    source["request"]["messages"] = [
        {"role": "user", "content": "Produce UP TO 2 categories.\nINPUT ELEMENTS:\n  - first\n  - second\n"}
    ]
    source["provenance"]["request_sha256"] = digest(source["request"])
    source_path = tmp_path / "sources.jsonl"
    source_path.write_text(json.dumps(source) + "\n", encoding="utf-8")
    case = json.loads(json.dumps(source))
    case["case_id"] += "::indexed"
    messages, fmt = indexed_request(source, "Return JSON")
    case["request"]["messages"], case["request"]["response_format"] = messages, fmt
    case["provenance"]["request_sha256"] = digest(case["request"])
    case["experiment"] = {"source_case_id": source["case_id"], "stage": "dev",
                          "variant": "indexed", "adapter": "indexed_normalization"}
    cases = tmp_path / "cases.jsonl"
    cases.write_text(json.dumps(case) + "\n", encoding="utf-8")
    fixture = CostTests()
    fixture.setUp()
    response = fixture.response
    response["id"] = "test-response"
    response["choices"] = [{"message": {"content": '{"labels":{"1":"First","2":"Second"},"assignments":{"1":1}}'}}]
    run = {"case_id": case["case_id"], "request": case["request"],
           "request_sha256": digest(case["request"]), "status": "completed",
           "elapsed_seconds": 1, "response": response}
    result = tmp_path / "results.jsonl"
    result.write_text(json.dumps(run) + "\n", encoding="utf-8")
    before = result.read_bytes()
    prices = tmp_path / "prices.json"
    prices.write_text(json.dumps(fixture.prices), encoding="utf-8")
    report = review([cases], [result], [source_path], prices, tmp_path / "out")
    assert not report["records"][0]["checks"]["reconstruction_valid"]
    assert "reconstructed" not in report["records"][0]
    assert result.read_bytes() == before
