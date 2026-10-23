import json
import tempfile

import pytest

from tinytroupe.control import Simulation


@pytest.fixture
def checkpoint_simulation(tmp_path, monkeypatch):
    """Record a cache entry without making an LLM call."""
    system_temp = tmp_path / "system_temp"
    system_temp.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(system_temp))
    simulation = Simulation()
    simulation.cache_path = str(tmp_path / "simulation.cache.json")
    simulation._add_to_cache_trace(
        state={"name": "建筑师 🚀"}, event_hash=123, event_output="saved output"
    )
    return simulation


@pytest.mark.core
@pytest.mark.parametrize("relative_path", [False, True])
def test_checkpoint_persists_and_reloads_trace(
    checkpoint_simulation, tmp_path, monkeypatch, relative_path
):
    """A checkpoint replaces the old cache with a complete, readable trace."""
    simulation = checkpoint_simulation
    cache_path = tmp_path / "simulation.cache.json"
    cache_path.write_text("[]", encoding="utf-8")
    if relative_path:
        monkeypatch.chdir(tmp_path)
        simulation.cache_path = cache_path.name

    simulation.checkpoint()

    saved = json.loads(cache_path.read_text(encoding="utf-8"))
    assert saved == [[None, 123, "saved output", {"name": "建筑师 🚀"}]]
    restored = Simulation()
    restored._load_cache_file(str(cache_path))
    assert restored.cached_trace == saved
    assert not simulation.has_unsaved_cache_changes
    assert list((tmp_path / "system_temp").iterdir()) == []


@pytest.mark.core
@pytest.mark.parametrize("failure", ["missing_parent", "target_directory"])
def test_checkpoint_can_retry_after_filesystem_error(
    checkpoint_simulation, tmp_path, failure
):
    """Fixing the destination lets the next checkpoint save pending changes."""
    simulation = checkpoint_simulation
    cache_path = tmp_path / "output" / "simulation.cache.json"
    simulation.cache_path = str(cache_path)
    if failure == "target_directory":
        cache_path.mkdir(parents=True)

    simulation.checkpoint()

    if failure == "target_directory":
        cache_path.rmdir()
    else:
        cache_path.parent.mkdir()
    simulation.checkpoint()

    assert json.loads(cache_path.read_text(encoding="utf-8")) == [
        [None, 123, "saved output", {"name": "建筑师 🚀"}]
    ]
    assert not simulation.has_unsaved_cache_changes
    assert list((tmp_path / "system_temp").iterdir()) == []
    assert list(cache_path.parent.iterdir()) == [cache_path]


@pytest.mark.core
def test_checkpoint_serialization_error_keeps_cache_and_cleans_up(
    checkpoint_simulation, tmp_path
):
    """A partial JSON write preserves the old cache and can be retried."""
    simulation = checkpoint_simulation
    cache_path = tmp_path / "simulation.cache.json"
    previous_contents = '[{"previous": "complete checkpoint"}]'
    cache_path.write_text(previous_contents, encoding="utf-8")
    simulation.cached_trace.append(object())

    simulation.checkpoint()

    assert cache_path.read_text(encoding="utf-8") == previous_contents
    assert simulation.has_unsaved_cache_changes
    assert list((tmp_path / "system_temp").iterdir()) == []
    assert set(tmp_path.iterdir()) == {cache_path, tmp_path / "system_temp"}

    simulation.cached_trace.pop()
    simulation.checkpoint()
    assert json.loads(cache_path.read_text(encoding="utf-8")) == [
        [None, 123, "saved output", {"name": "建筑师 🚀"}]
    ]
    assert not simulation.has_unsaved_cache_changes
