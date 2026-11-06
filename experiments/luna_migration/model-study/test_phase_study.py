"""Offline safeguards for phase-balanced, append-only paired comparisons."""

import json

import pytest

import run_parallel_study
from model_case_study import digest
from prepare_phase_study import prepare
from review_phase_study import checks, cost_with_bounds
from test_select_execution_cases import corpus


def fixture(tmp_path):
    source, cases = corpus(tmp_path)
    for case in cases:
        case["provenance"].update(cache=case["case_id"], normalization=[])
    source.write_text("".join(json.dumps(c) + "\n" for c in cases), encoding="utf-8")
    spec = {
        "variant": "revision", "selection_seed": 1, "execution_order_seed": 2,
        "stages": {"dev": {"split": "optimization", "order_offset": 0,
                           "counts": {"extraction": 1}}},
        "instructions": {"extraction": "Use public evidence for public answers."},
        "hypotheses": {"extraction": "Preserve attribution"},
    }
    protocol = tmp_path / "protocol.json"
    protocol.write_text(json.dumps(spec), encoding="utf-8")
    # Exclude reserved data: accidental mixing must fail, not silently select around it.
    source.write_text("".join(json.dumps(c) + "\n" for c in cases[:2]), encoding="utf-8")
    return source, protocol, cases


def test_pairs_preserve_exact_originals_and_hashes(tmp_path):
    source, protocol, originals = fixture(tmp_path)
    result = prepare(source, protocol, tmp_path / "out", "dev")
    pair = {c["experiment"]["variant"]: c for c in result}
    assert pair["baseline"]["request"] == originals[1]["request"]
    revised = pair["revision"]
    assert revised["request"]["messages"][:-1] == originals[1]["request"]["messages"]
    assert revised["original_response"] == originals[1]["original_response"]
    assert revised["provenance"]["request_sha256"] == digest(revised["request"])
    assert (tmp_path / "out" / "prompt-audit.json").exists()
    with pytest.raises(FileExistsError):
        prepare(source, protocol, tmp_path / "out", "dev")


def test_wrong_split_and_missing_phase_fail_before_writing(tmp_path):
    source, protocol, originals = fixture(tmp_path)
    source.write_text(json.dumps(originals[2]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Unexpected split"):
        prepare(source, protocol, tmp_path / "out", "dev")
    assert not (tmp_path / "out").exists()
    source.write_text(json.dumps(originals[0]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Need 1"):
        prepare(source, protocol, tmp_path / "out", "dev")


def test_sharding_dry_run_never_executes(tmp_path, monkeypatch):
    source, _, _ = fixture(tmp_path)
    conditions = tmp_path / "conditions.json"
    conditions.write_text('[{"id":"test","model":"gpt-6-luna"}]', encoding="utf-8")

    def forbidden(*args):
        raise AssertionError("Dry run called paid runner")

    monkeypatch.setattr(run_parallel_study, "run_cases", forbidden)
    run_parallel_study.run(source, conditions, tmp_path / "result")
    assert not (tmp_path / "result").exists()


def test_shards_preserve_attempts_and_surface_failure(tmp_path, monkeypatch):
    source, _, _ = fixture(tmp_path)
    conditions = tmp_path / "conditions.json"
    conditions.write_text('[{"id":"test","model":"gpt-6-luna"}]', encoding="utf-8")

    def replay(corpus_path, settings, output, *args):
        rows = [json.loads(line) for line in corpus_path.read_text(encoding="utf-8").splitlines()]
        output.write_text("".join(json.dumps({"case_id": c["case_id"], "status": "error"})
                                  + "\n" for c in rows), encoding="utf-8")
        raise SystemExit("Deliberate saved failure")

    monkeypatch.setattr(run_parallel_study, "run_cases", replay)
    with pytest.raises(RuntimeError, match="2/2 attempts"):
        run_parallel_study.run(source, conditions, tmp_path / "result", execute=True)
    rows = (tmp_path / "result" / "results.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 2


def test_normalization_checks_occurrences_not_just_set_members():
    case = {"phase": "normalization", "request": {"messages": [{
        "role": "user", "content": "Produce UP TO 2 categories.\nINPUT ELEMENTS:\n  - first\n  - second\n  - first\n"
    }]}}
    valid = checks(case, '{"group":["first","second","first"]}')
    assert valid["membership_multiset_preserved"]
    invalid = checks(case, '{"group":["first","second"]}')
    assert not invalid["membership_multiset_preserved"]
    assert invalid["missing_members"] == ["first"]


def test_length_check_measures_actual_source_not_entire_request():
    case = {"phase": "content_enrichment", "request": {"messages": [{
        "role": "user", "content": "At least 5 times".lower() + "\n## CONTENT TO ENRICH\n```\n12345\n```"
    }]}}
    assert checks(case, "x" * 25)["minimum_expansion_met"]
    assert not checks(case, "x" * 24)["minimum_expansion_met"]


def test_sampling_plan_checks_arithmetic_and_enforced_dimensions():
    case = {"phase": "sampling_plan", "request": {"messages": [{
        "role": "user", "content": "## Named parameters\n" + json.dumps({
            "N": 2, "enforce_usage_of_all_dimensions": True, "max_quantity_per_sample_directive": 2,
            "sampling_dimensions": {"dimensions": [{"name": "age", "range": [18, 30]}]}
        })
    }]}}
    measured = checks(case, '{"sample_plan":[{"quantity":3,"sampled_values":{"unknown":25}}]}')
    assert not measured["exact_total"]
    assert not measured["max_quantity_per_sample_directive_satisfied"]
    assert measured["unknown_dimensions"] == ["unknown"]
    assert measured["missing_dimensions_by_directive"] == [["age"]]


def test_missing_write_usage_gets_explicit_bounds_without_mutating_response():
    from test_study_report import CostTests

    fixture = CostTests()
    fixture.setUp()
    del fixture.response["usage"]["prompt_tokens_details"]["cache_write_tokens"]
    result = cost_with_bounds(fixture.response, fixture.prices)
    assert result["total_usd"] is None
    assert result["cache_write_tokens"] is None
    assert result["minimum_usd"] == "0.0131"
    assert result["maximum_usd"] == "0.0151"
    assert "cache_write_tokens" not in fixture.response["usage"]["prompt_tokens_details"]


def test_sampling_plan_rejects_rewritten_values_and_out_of_range_numbers():
    case = {"phase": "sampling_plan", "request": {"messages": [{
        "role": "user", "content": "## Named parameters\n" + json.dumps({
            "N": 2, "sampling_dimensions": {"dimensions": [
                {"name": "age", "range": [18, 30]},
                {"name": "place", "values": {"Rural community": 0.5, "City": 0.5}}
            ]}
        })
    }]}}
    measured = checks(case, json.dumps({"sample_plan": [{
        "id": 1, "quantity": 2, "sampled_values": {"age": [18, 31], "place": "Rural"}
    }]}))
    assert measured["exact_total"]
    assert [v["dimension"] for v in measured["invalid_or_rewritten_sampled_values"]] == ["age", "place"]
    measured = checks(case, json.dumps({"sample_plan": [{
        "id": 1, "quantity": 2, "sampled_values": {"age": [18, 30], "place": ["Rural community"]}
    }]}))
    assert measured["invalid_or_rewritten_sampled_values"] == []
