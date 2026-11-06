"""Check protected-input and coverage guards without calling a model."""

import copy
import json

import pytest

from audit_prompt_revision import audit
from model_case_study import digest


def fixture_files(tmp_path, change=None):
    """Create one original and one candidate with a protected persona and safety section."""
    request = {"model": "gpt-6-luna", "messages": [{"role": "system", "content":
        "# Old rules\n## Additional Constraints (if any)\nKeep safe.\n"
        "## Persona\n{\"name\":\"Test\"}\n### Rules for interpreting your persona\nOld style."
    }]}
    response = {"choices": [{"finish_reason": "stop"}]}
    original = {
        "case_id": "sample", "phase": "agent_action", "request": request,
        "original_response": response, "assessment": {},
        "provenance": {"request_sha256": digest(request), "response_sha256": digest(response)},
    }
    candidate = copy.deepcopy(original)
    candidate["case_id"] = "sample::new"
    candidate["experiment"] = {"source_case_id": "sample"}
    if change:
        candidate["request"]["messages"][0]["content"] = change(candidate["request"]["messages"][0]["content"])
    candidate["provenance"]["request_sha256"] = digest(candidate["request"])
    source, corpus = tmp_path / "source.jsonl", tmp_path / "corpus.jsonl"
    source.write_text(json.dumps(original) + "\n", encoding="utf-8")
    corpus.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    return source, corpus


def test_instruction_changes_preserve_protected_sections(tmp_path):
    source, corpus = fixture_files(tmp_path, lambda text: text.replace("Old", "New"))
    output = tmp_path / "audit.json"
    audit(source, corpus, [], output)
    assert json.loads(output.read_text())["protected_inputs_preserved"]


def test_changed_persona_is_rejected(tmp_path):
    source, corpus = fixture_files(tmp_path, lambda text: text.replace('"Test"', '"Other"'))
    with pytest.raises(ValueError, match="Protected persona"):
        audit(source, corpus, [], tmp_path / "audit.json")


def test_missing_expected_runs_are_rejected(tmp_path):
    source, corpus = fixture_files(tmp_path)
    with pytest.raises(ValueError, match="Coverage differs"):
        audit(source, corpus, [], tmp_path / "audit.json", expected_repeats=3)


def test_same_basename_results_are_distinct_observations(tmp_path):
    source, corpus = fixture_files(tmp_path)
    case = json.loads(corpus.read_text(encoding="utf-8"))
    paths = []
    for folder in ["a", "b"]:
        path = tmp_path / folder / "results.jsonl"
        path.parent.mkdir()
        path.write_text(json.dumps({
            "case_id": case["case_id"], "replicate": 0, "condition_id": "same",
            "status": "completed", "request": case["request"],
            "request_sha256": digest(case["request"]),
            "response": {"choices": [{"message": {"content": '{"actions":[]}'}}]},
        }) + "\n", encoding="utf-8")
        paths.append(path)
    output = tmp_path / "audit.json"
    audit(source, corpus, paths, output, expected_repeats=2)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert {row["file"] for row in report["observations"]} == {"a/results.jsonl", "b/results.jsonl"}


@pytest.mark.parametrize("phase", ["persona_generation", "persona_generation_plan"])
def test_generation_stages_preserve_original_particulars(tmp_path, phase):
    source, corpus = fixture_files(tmp_path)
    original = json.loads(source.read_text(encoding="utf-8"))
    original["phase"] = "persona_generation"
    original["request"]["messages"].append({
        "role": "user", "content": "Age: 40\n## Generation Rules\nOriginal rules."
    })
    original["provenance"]["request_sha256"] = digest(original["request"])
    source.write_text(json.dumps(original) + "\n", encoding="utf-8")
    candidate = copy.deepcopy(original)
    candidate.update(case_id="sample::new", phase=phase, experiment={"source_case_id": "sample"})
    candidate["request"]["messages"][1]["content"] = "Age: 40\n## Generation Rules\nNew rules."
    candidate["provenance"]["request_sha256"] = digest(candidate["request"])
    corpus.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    audit(source, corpus, [], tmp_path / "valid.json")
    candidate["request"]["messages"][1]["content"] = "Age: 50\n## Generation Rules\nNew rules."
    candidate["provenance"]["request_sha256"] = digest(candidate["request"])
    corpus.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Generation constraints changed"):
        audit(source, corpus, [], tmp_path / "invalid.json")


def test_strict_plan_schema_requires_opt_in_and_does_not_allow_other_changes(tmp_path):
    source, corpus = fixture_files(tmp_path)
    original = json.loads(source.read_text(encoding="utf-8"))
    original["phase"] = "persona_generation"
    original["request"]["response_format"] = {"type": "json_object"}
    original["request"]["messages"].append({
        "role": "user", "content": "Age: 40\n## Generation Rules\nReturn JSON."
    })
    original["provenance"]["request_sha256"] = digest(original["request"])
    source.write_text(json.dumps(original) + "\n", encoding="utf-8")
    candidate = copy.deepcopy(original)
    candidate.update(case_id="sample::plan", phase="persona_generation_plan",
                     experiment={"source_case_id": "sample"})
    candidate["request"]["response_format"] = {"type": "json_schema", "json_schema": {
        "name": "test", "strict": True,
        "schema": {"type": "object", "properties": {}, "additionalProperties": False},
    }}
    candidate["provenance"]["request_sha256"] = digest(candidate["request"])
    corpus.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Non-message setting changed"):
        audit(source, corpus, [], tmp_path / "default.json")
    output = tmp_path / "allowed.json"
    audit(source, corpus, [], output, allow_plan_schema=True)
    assert json.loads(output.read_text())["explicit_plan_schema_changes"] == ["sample::plan"]
    candidate["request"]["model"] = "different-model"
    candidate["provenance"]["request_sha256"] = digest(candidate["request"])
    corpus.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Non-message setting changed"):
        audit(source, corpus, [], tmp_path / "invalid.json", allow_plan_schema=True)
