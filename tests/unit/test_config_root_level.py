import configparser
import importlib.util
import logging
from pathlib import Path

import pytest

pytestmark = pytest.mark.core


@pytest.fixture
def isolated_logging_config(monkeypatch, tmp_path):
    """Load the stdlib-only utility without initializing the SDK's logging."""
    source = Path(__file__).resolve().parents[2] / "tinytroupe/utils/config.py"
    spec = importlib.util.spec_from_file_location("isolated_logging_config", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    root = logging.getLogger()
    project = logging.getLogger("tinytroupe")
    root_handlers, root_level = root.handlers[:], root.level
    project_handlers, project_level = project.handlers[:], project.level
    project_propagate = project.propagate
    monkeypatch.chdir(tmp_path)
    try:
        yield module
    finally:
        for handler in root.handlers[:]:
            if handler not in root_handlers:
                root.removeHandler(handler)
                handler.close()
        root.setLevel(root_level)
        project.handlers[:] = project_handlers
        project.setLevel(project_level)
        project.propagate = project_propagate


@pytest.mark.parametrize(
    "level, console, expected",
    [
        ("DEBUG", "WARNING", logging.DEBUG),
        ("ERROR", "OFF", logging.ERROR),
        ("INFO", "INFO", logging.INFO),
    ],
)
def test_start_logger_applies_root_level(
    isolated_logging_config, level, console, expected
):
    settings = configparser.ConfigParser()
    settings["Logging"] = {
        "LOGLEVEL": level,
        "LOGLEVEL_CONSOLE": console,
        "LOGLEVEL_FILE": "OFF",
    }
    isolated_logging_config.start_logger(settings)
    assert logging.getLogger().level == expected
    assert logging.getLogger("tinytroupe").level == expected


def test_start_logger_replaces_previous_root_level(isolated_logging_config):
    isolated_logging_config.set_loglevel("CRITICAL")
    settings = configparser.ConfigParser()
    settings["Logging"] = {
        "LOGLEVEL": "DEBUG",
        "LOGLEVEL_CONSOLE": "ERROR",
        "LOGLEVEL_FILE": "OFF",
    }
    isolated_logging_config.start_logger(settings)
    assert logging.getLogger().level == logging.DEBUG
    assert logging.getLogger("tinytroupe").level == logging.DEBUG
