"""The corrected gazpacho example must retain and report genuine nonresponses."""

import json
from pathlib import Path

import pandas as pd
import pytest


pytestmark = pytest.mark.core


@pytest.fixture
def score_cell():
    """Load the actual notebook's score statistics, not a copied implementation."""
    path = Path(__file__).resolve().parents[2] / "examples" / (
        "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb"
    )
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return next(
        "".join(cell["source"]) for cell in notebook["cells"]
        if "average_score =" in "".join(cell["source"])
    )


def test_nonresponses_do_not_become_scores(score_cell, capsys):
    """Missing speech cannot crash statistics or be imputed as a preference."""
    frame = pd.DataFrame({"response": ["1", "3", "5", "N/A"]})
    before = frame.copy(deep=True)
    namespace = {"pd": pd, "df": frame}
    exec(score_cell, namespace)
    assert namespace["average_score"] == 3
    assert namespace["std_score"] == 2
    pd.testing.assert_frame_equal(frame, before)
    assert "Rated respondents: 3/4" in capsys.readouterr().out


@pytest.mark.parametrize("response", ["6", "0", "2.5", "probably 2"])
def test_invalid_scores_fail_explicitly(score_cell, response):
    """Malformed or out-of-scale values cannot quietly become missing data."""
    with pytest.raises(ValueError):
        exec(score_cell, {"pd": pd, "df": pd.DataFrame({"response": [response]})})


def test_all_nonresponses_remain_undefined(score_cell, capsys):
    """An empty rated sample must not produce a success-shaped numeric mean."""
    namespace = {"pd": pd, "df": pd.DataFrame({"response": ["N/A", "N/A"]})}
    exec(score_cell, namespace)
    assert pd.isna(namespace["average_score"])
    assert pd.isna(namespace["std_score"])
    assert "Rated respondents: 0/2" in capsys.readouterr().out


def test_validation_cell_preserves_nonresponses():
    """A missing response must survive empirical-dataset import without imputation."""
    from tinytroupe.validation import SimulationExperimentEmpiricalValidator

    path = Path(__file__).resolve().parents[2] / "examples" / (
        "Bottled Gazpacho Market Research 5 (with behavior correction).ipynb"
    )
    notebook = json.loads(path.read_text(encoding="utf-8"))
    cell = next(
        "".join(cell["source"]) for cell in notebook["cells"]
        if 'dataset_name="Bottled Gazpacho Simulation Results"' in "".join(cell["source"])
    )
    frame = pd.DataFrame({
        "name": ["A", "B", "C", "D", "E"],
        "response": ["1", "2", "2", "3", "N/A"],
        "justification": ["one", "two", "two", "three", "no public score"],
    })
    before = frame.copy(deep=True)
    namespace = {
        "pd": pd,
        "df": frame,
        "SimulationExperimentEmpiricalValidator": SimulationExperimentEmpiricalValidator,
    }
    exec(cell, namespace)
    dataset = namespace["treatment_data"]
    assert dataset.key_results["Vote"] == [1.0, 2.0, 2.0, 3.0, None]
    assert dataset.agent_names == frame["name"].tolist()
    assert len(dataset.agent_justifications) == 5
    pd.testing.assert_frame_equal(frame, before)
