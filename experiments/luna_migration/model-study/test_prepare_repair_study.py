"""Verify evidence preservation and explicit scope for reusable prompt repair preparation."""

import json

import pytest

from model_case_study import digest
from prepare_repair_study import prepare
from test_select_execution_cases import corpus


def test_repair_preparation_preserves_inputs_and_records_independent_repetitions(tmp_path):
    source, originals = corpus(tmp_path)
    chosen = originals[0]
    chosen["provenance"]["normalization"] = []
    source.write_text(json.dumps(chosen) + "\n", encoding="utf-8")
    (tmp_path / "instruction.txt").write_text("A readable instruction.", encoding="utf-8")
    config = {"stage": "dev", "corpora": [source.name], "repetitions": 2, "recipes": [{
        "id": "candidate", "instruction_file": "instruction.txt", "cases": [chosen["case_id"]],
        "hypothesis": "Improve instruction clarity."
    }]}
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    rows = prepare(config_path, tmp_path / "out")
    assert len(rows) == 2 and rows[0]["case_id"] != rows[1]["case_id"]
    for row in rows:
        assert row["request"]["messages"][:-1] == chosen["request"]["messages"]
        assert row["original_response"] == chosen["original_response"]
        assert row["provenance"]["request_sha256"] == digest(row["request"])
    with pytest.raises(FileExistsError):
        prepare(config_path, tmp_path / "out")
