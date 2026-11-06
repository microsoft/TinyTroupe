"""Offline tests for reusable prompt recipe composition."""

import json

import pytest

from compose_prompt_study import compile_manifest


def test_import_and_compose_operations(tmp_path):
    (tmp_path / "replacement.txt").write_text("new instruction", encoding="utf-8")
    base = {"variants": [{"id": "base", "operations": [
        {"kind": "replace", "old": "old", "new_file": "replacement.txt"}
    ]}]}
    (tmp_path / "base.json").write_text(json.dumps(base), encoding="utf-8")
    spec = {"imports": [{"path": "base.json", "variants": ["base"]}], "variants": [
        {"id": "child", "operations_from": ["base"], "operations": [{"kind": "append", "text": "tail"}]}
    ]}
    path = tmp_path / "study.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    compiled = compile_manifest(path)
    assert compiled["variants"][1]["operations"] == [
        {"kind": "replace", "old": "old", "new": "new instruction"},
        {"kind": "append", "text": "tail"},
    ]
    assert len(compiled["variants"][0]["operations"]) == 1


def test_duplicate_recipe_rejected(tmp_path):
    path = tmp_path / "study.json"
    path.write_text(json.dumps({"variants": [{"id": "x", "operations": []}] * 2}), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate recipe"):
        compile_manifest(path)


def test_ambiguous_text_source_rejected(tmp_path):
    path = tmp_path / "study.json"
    path.write_text(json.dumps({"variants": [{"id": "x", "operations": [
        {"new": "x", "new_file": "x.txt"}
    ]}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="not both"):
        compile_manifest(path)
