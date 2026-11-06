"""Regression coverage for public-only travel-survey evidence."""

import json
from pathlib import Path

import pytest


@pytest.mark.core
def test_travel_product_extraction_requires_public_justifications():
    """Bare decisions must not become invented explanations from private thoughts."""
    path = (
        Path(__file__).resolve().parents[2] / "examples"
        / "Travel Product Market Research.ipynb"
    )
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = next(
        "".join(cell["source"]) for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and "results_extractor = ResultsExtractor(" in "".join(cell["source"])
    )
    calls = []

    def record_extractor(**kwargs):
        calls.append(kwargs)

    exec(source, {"ResultsExtractor": record_extractor})
    assert len(calls) == 1
    settings = calls[0]
    assert settings["fields"] == ["response", "justification"]
    hint = settings["fields_hints"]["justification"]
    assert "public TALK actions" in hint
    assert "Do not infer reasons from private THINK actions" in hint
    assert "No public justification provided." in hint
