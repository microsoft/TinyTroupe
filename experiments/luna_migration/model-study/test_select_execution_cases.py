"""Offline tests for bounded exact-case review exports."""

import json

import pytest

from model_case_study import digest
from select_execution_cases import select


def corpus(tmp_path):
    cases = []
    for i, phase in enumerate(["agent_action", "extraction", "extraction"]):
        request = {"model": "gpt-6-luna", "messages": [{"role": "user", "content": "<exact>"}]}
        response = {"id": f"r{i}", "choices": [{"finish_reason": "stop",
                     "message": {"content": '{"value":"<unmodified>"}'}}]}
        cases.append({
            "case_id": f"c{i}", "phase": phase, "group": "scenario",
            "request": request, "original_response": response,
            "assessment": {"label": "unreviewed", "criterion": "Public evidence only."},
            "selection": {"split": "optimization" if i < 2 else "validation"},
            "provenance": {"request_sha256": digest(request), "response_sha256": digest(response)},
        })
    path = tmp_path / "cases.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in cases), encoding="utf-8")
    return path, cases


def test_filters_preserve_exact_payloads_and_escape_html(tmp_path):
    path, cases = corpus(tmp_path)
    out = tmp_path / "out"
    selected = select(path, out, ["extraction"], "optimization", limit=1)
    assert selected == [cases[1]]
    assert json.loads((out / "selected.jsonl").read_text(encoding="utf-8")) == cases[1]
    html = (out / "review.html").read_text(encoding="utf-8")
    assert "&lt;unmodified&gt;" in html and "<unmodified>" not in html
    assert "unreviewed" in (out / "review-queue.csv").read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        select(path, out)


def test_unknown_ids_empty_filters_and_explicit_limit_fail(tmp_path):
    path, _ = corpus(tmp_path)
    for kwargs in [{"case_ids": ["unknown"]}, {"phases": ["absent"]},
                   {"case_ids": ["c0", "c1"], "limit": 1}, {"limit": 0}]:
        with pytest.raises(ValueError):
            select(path, tmp_path / "out", **kwargs)
    assert not (tmp_path / "out").exists()
