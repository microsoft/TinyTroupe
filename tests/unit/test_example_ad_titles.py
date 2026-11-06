"""Regression coverage for travel-ad sampling and canonical metadata."""

import json
from pathlib import Path

import pytest


@pytest.mark.core
@pytest.mark.parametrize("ad_id,expected", [
    (1, "Tailor-Made Tours Of Europe - Nat'l Geographic Award Winner"),
    (2, "Europe all-inclusive Packages - Europe Vacation Packages"),
    (3, "Travel Packages - Great Vacation Deals"),
    (4, "Europe Luxury Private Tours"),
])
def test_travel_ad_headlines_come_from_supplied_copy(ad_id, expected):
    """Both extraction surfaces resolve exact headlines without changing votes."""
    path = (
        Path(__file__).resolve().parents[2] / "examples"
        / "Online Advertisement for Travel.ipynb"
    )
    notebook = json.loads(path.read_text(encoding="utf-8"))
    sources = [
        "".join(cell["source"]) for cell in notebook["cells"]
        if cell["cell_type"] == "code"
    ]
    namespace = {}
    exec(next(source for source in sources if "ad_titles = {" in source), namespace)
    extraction_sources = [
        source for source in sources
        if "extractor.extract_results_from_agent(" in source
    ]
    assert len(extraction_sources) == 2

    class Extractor:
        def extract_results_from_agent(self, person, **kwargs):
            return {"ad_id": ad_id, "justification": "Original rationale"}

    for source in extraction_sources:
        namespace.update({
            "people": [object()],
            "extractor": Extractor(),
            "ResultsExtractor": Extractor,
            "extraction_objective": "Extract the selected ad.",
            "situation": "Planning travel.",
            "choices": [],
        })
        exec(source, namespace)
        assert namespace["choices"] == [{
            "ad_id": ad_id,
            "ad_title": expected,
            "justification": "Original rationale",
        }]


@pytest.mark.core
def test_travel_ad_sampling_receives_the_declared_audience():
    """The sampling plan receives the same seven criteria as persona generation."""
    path = (
        Path(__file__).resolve().parents[2] / "examples"
        / "Online Advertisement for Travel.ipynb"
    )
    notebook = json.loads(path.read_text(encoding="utf-8"))
    source = next(
        "".join(cell["source"]) for cell in notebook["cells"]
        if cell["cell_type"] == "code"
        and "factory = TinyPersonFactory(" in "".join(cell["source"])
    )
    calls = []

    def record_factory(**kwargs):
        calls.append(kwargs)

    exec(source, {"TinyPersonFactory": record_factory})
    assert len(calls) == 1
    settings = calls[0]
    assert settings["total_population_size"] == 100
    assert settings["sampling_space_description"] == settings["context"]
    description = settings["sampling_space_description"]
    assert "Americans" in description and "Europe" in description
    for dimension in (
        "partner status", "financial situation", "luxury preferences",
        "security concerns", "hotel amenities", "travel planning",
        "social confirmation",
    ):
        assert dimension in description
