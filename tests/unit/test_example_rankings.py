"""Regression coverage for the child-product examples' ranking tables."""

import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest


pytestmark = pytest.mark.core


@pytest.fixture(params=[
    "AI-enabled Children Story Telling Market Research.ipynb",
    "AI-enabled Children Story Telling Market Research 2.ipynb",
])
def example_sources(request):
    """Load the actual notebook cells without executing their LLM simulation."""
    path = Path(__file__).resolve().parents[2] / "examples" / request.param
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return ["".join(cell["source"]) for cell in notebook["cells"]]


@pytest.fixture
def ranking_cell(example_sources):
    """Select the notebook's real ranking-integrity guard."""
    return next(
        source for source in example_sources
        if "df = pd.DataFrame(filtered_results)" in source
    )


@pytest.mark.parametrize("response,expected", [
    ("B-D-A-E-C", "B-D-A-E-C"),
    ("OPTION_B-OPTION_E-OPTION_C-OPTION_A-OPTION_D", "B-E-C-A-D"),
    ("N/A", "N/A"),
])
def test_ranking_labels_preserve_preference_order(ranking_cell, response, expected):
    """Representation repair must not reorder preferences or invent responses."""
    namespace = {
        "pd": pd,
        "filtered_results": [{"name": "Parent", "response": response}],
        "population_size": 1,
    }
    exec(ranking_cell, namespace)
    assert namespace["df"]["response"].tolist() == [expected]


@pytest.mark.parametrize("response", [
    None,
    "B-B-A-E-C",
    "B-D-A-E",
    "B-D-A-E-F",
    "OPTION_1-OPTION_2-OPTION_3-OPTION_4-OPTION_5",
])
def test_invalid_rankings_fail_explicitly(ranking_cell, response):
    """Incomplete or ambiguous options cannot silently corrupt survey statistics."""
    namespace = {
        "pd": pd,
        "filtered_results": [{"name": "Parent", "response": response}],
        "population_size": 1,
    }
    with pytest.raises(ValueError, match="one complete A-E ranking"):
        exec(ranking_cell, namespace)


def test_missing_respondents_fail_explicitly(ranking_cell):
    """A successful-looking result must not silently omit sampled respondents."""
    namespace = {
        "pd": pd,
        "filtered_results": [{"name": "Parent", "response": "B-D-A-E-C"}],
        "population_size": 2,
    }
    with pytest.raises(ValueError, match="per sampled person"):
        exec(ranking_cell, namespace)


class RecordingExtractor:
    """Record orchestration calls without invoking or approximating an LLM."""

    def __init__(self, results, retry_result):
        self.results = results
        self.retry_result = retry_result
        self.default_fields_hints = {"response": "Preserve the public A-E order."}
        self.calls = []

    def extract_results_from_agents(self, people, **kwargs):
        """Return supplied parser results and record how the caller retries."""
        self.calls.append((people, kwargs))
        return self.results if len(self.calls) == 1 else [self.retry_result]


@pytest.mark.parametrize("invalid_result", [None, {}, {"response": None}])
def test_retry_preserves_defaults_and_valid_responses(
    example_sources, invalid_result, capsys
):
    """Retry only the failed person without overriding objective or situation."""
    people = [SimpleNamespace(name="First parent"), SimpleNamespace(name="Second parent")]
    valid_result = {"name": "First parent", "response": "N/A"}
    corrected = {"name": "Second parent", "response": "B-D-E-A-C"}
    extractor = RecordingExtractor([valid_result, invalid_result], corrected)
    namespace = {"people": people, "results_extractor": extractor}
    source = next(s for s in example_sources if "Retrying invalid ranking extraction" in s)

    exec(source, namespace)

    assert namespace["results"] == [valid_result, corrected]
    assert namespace["results"][0] is valid_result
    assert extractor.calls[0] == (people, {})
    assert len(extractor.calls) == 2
    retry_people, retry_kwargs = extractor.calls[1]
    assert retry_people == [people[1]]
    assert set(retry_kwargs) == {"fields_hints"}
    assert "properly closed string values" in retry_kwargs["fields_hints"]["response"]
    assert extractor.default_fields_hints == {"response": "Preserve the public A-E order."}
    assert "Retrying invalid ranking extraction for Second parent" in capsys.readouterr().out


def test_valid_extractions_are_not_retried(example_sources, capsys):
    """A public nonresponse is valid and must not be forced into a preference."""
    people = [SimpleNamespace(name="Parent")]
    result = {"name": "Parent", "response": "N/A"}
    extractor = RecordingExtractor([result], None)
    namespace = {"people": people, "results_extractor": extractor}
    source = next(s for s in example_sources if "Retrying invalid ranking extraction" in s)

    exec(source, namespace)

    assert extractor.calls == [(people, {})]
    assert namespace["results"] == [result]
    assert capsys.readouterr().out == ""


def test_persistently_invalid_extraction_fails_after_one_retry(example_sources):
    """A retry cannot conceal a missing ranking or loop until a desired answer."""
    people = [SimpleNamespace(name="First parent"), SimpleNamespace(name="Second parent")]
    extractor = RecordingExtractor([{"name": "First parent", "response": "B-D-E-A-C"}, {}], {})
    namespace = {
        "people": people,
        "results_extractor": extractor,
        "population_size": 2,
        "pd": pd,
    }
    for source in example_sources:
        if any(marker in source for marker in (
            "Retrying invalid ranking extraction",
            "filtered_results =",
        )):
            exec(source, namespace)
    ranking_source = next(
        s for s in example_sources if "df = pd.DataFrame(filtered_results)" in s
    )

    with pytest.raises(ValueError, match="one complete A-E ranking"):
        exec(ranking_source, namespace)
    assert len(extractor.calls) == 2
