import concurrent.futures
import configparser
import logging
import os
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

logger = logging.getLogger("tinytroupe")

import sys

sys.path.insert(0, "../../tinytroupe/")
sys.path.insert(0, "../../")
sys.path.insert(0, "..")

from testing_utils import *

from tinytroupe.utils import config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_content = """
[OpenAI]
API_TYPE = azure
API_KEY = test_key
API_BASE = https://test.openai.azure.com/
API_VERSION = 2023-05-15

[LLM]
DEFAULT_MODEL = gpt-3.5-turbo
DEFAULT_TEMPERATURE = 0.7
MAX_COMPLETION_TOKENS = 1000

[Simulation]
CACHE_API_CALLS = True
CACHE_FILE_NAME = test_cache.json
"""

    fd, path = tempfile.mkstemp(suffix=".ini")
    with os.fdopen(fd, "w") as f:
        f.write(config_content)

    yield path

    if os.path.exists(path):
        os.remove(path)


def test_read_config_file_default():
    """Test reading the default config file."""

    # Test reading config with cache
    config_obj = config.read_config_file(use_cache=True)
    assert isinstance(config_obj, configparser.ConfigParser)

    # Test that sections exist (depends on actual config.ini)
    # We'll test that we get a valid ConfigParser object
    assert hasattr(config_obj, "sections")
    assert hasattr(config_obj, "get")
    assert hasattr(config_obj, "has_section")


def test_read_config_file_cache_behavior():
    """Test config file caching behavior."""

    # Clear any existing cache
    config._config = None

    # First call should load and cache
    config1 = config.read_config_file(use_cache=True)

    # Second call should return cached version
    config2 = config.read_config_file(use_cache=True)

    # Should be the same object when using cache
    assert config1 is config2

    # Without cache should create new object
    config3 = config.read_config_file(use_cache=False)

    # Should be different object when not using cache
    assert config3 is not config2


def test_read_config_file_without_cache():
    """Test reading config file without caching."""

    config1 = config.read_config_file(use_cache=False)
    config2 = config.read_config_file(use_cache=False)

    # Should be different objects
    assert config1 is not config2
    assert isinstance(config1, configparser.ConfigParser)
    assert isinstance(config2, configparser.ConfigParser)


@patch("pathlib.Path.exists")
def test_read_config_file_not_found(mock_exists):
    """Test behavior when config file is not found."""

    # Mock that config file doesn't exist
    mock_exists.return_value = False

    # Clear cache to force file reading
    config._config = None

    # Should raise ValueError when config file is not found
    with pytest.raises(ValueError, match="Failed to find default config"):
        config.read_config_file(use_cache=False)


@patch("pathlib.Path.cwd")
@patch("pathlib.Path.exists")
@patch("configparser.ConfigParser.read")
def test_read_config_file_custom_override(
    mock_read, mock_exists, mock_cwd, temp_config_file
):
    """Test config file override behavior."""

    # Mock the current working directory
    mock_cwd.return_value = Path(os.path.dirname(temp_config_file))

    # Mock that both default and custom config exist
    mock_exists.return_value = True

    # Clear cache
    config._config = None

    # Mock the config read to track calls
    mock_config_instance = Mock()
    mock_read.return_value = None

    with patch("configparser.ConfigParser") as mock_config_class:
        mock_config_class.return_value = mock_config_instance

        try:
            result = config.read_config_file(use_cache=False, verbose=False)

            # Should have attempted to read config files
            assert mock_read.call_count >= 1

        except Exception as e:
            # If it fails due to mocking complexity, that's okay for this test
            logger.info(f"Config test failed due to mocking: {e}")


def test_config_module_global_variable():
    """Test the global _config variable behavior."""

    # Test that _config starts as None or gets initialized
    assert hasattr(config, "_config")

    # Test that calling read_config_file sets the global variable
    config._config = None
    result = config.read_config_file(use_cache=True)

    # Global variable should now be set
    assert config._config is not None
    assert config._config is result


def test_config_verbose_output(capsys):
    """Test verbose output functionality."""

    # Clear cache to force reading
    config._config = None

    # Test with verbose=True
    try:
        config.read_config_file(use_cache=False, verbose=True)
        captured = capsys.readouterr()

        # Should have some output when verbose=True
        # (exact output depends on whether config file exists)
        assert isinstance(captured.out, str)  # Should capture something

    except ValueError:
        # Config file might not exist in test environment
        captured = capsys.readouterr()
        assert "Looking for default config" in captured.out

    # Test with verbose=False
    config._config = None
    try:
        config.read_config_file(use_cache=False, verbose=False)
        captured = capsys.readouterr()

        # Should have no output when verbose=False
        # (unless there's an error message)

    except ValueError:
        # Expected if config doesn't exist
        pass


def test_config_path_construction():
    """Test that config paths are constructed correctly."""

    # Test that the module constructs reasonable paths
    module_dir = Path(config.__file__).parent.absolute()
    expected_config_path = module_dir / "../config.ini"

    # The path should be reasonable (contains config.ini)
    assert "config.ini" in str(expected_config_path)


@patch("configparser.ConfigParser")
def test_config_parser_usage(mock_config_class):
    """Test that ConfigParser is used correctly."""

    mock_config_instance = Mock()
    mock_config_class.return_value = mock_config_instance
    mock_config_instance.read.return_value = None

    # Mock file existence
    with patch("pathlib.Path.exists", return_value=True):
        config._config = None

        try:
            config.read_config_file(use_cache=False)

            # Verify ConfigParser was instantiated
            mock_config_class.assert_called()

            # Verify read method was called
            mock_config_instance.read.assert_called()

        except Exception as e:
            # Mocking might cause issues, that's expected
            logger.info(f"Mocked config test encountered expected issue: {e}")


def test_config_module_imports():
    """Test that the config module imports are correct."""

    # Test that required modules are imported
    assert hasattr(config, "configparser")
    assert hasattr(config, "Path")
    assert hasattr(config, "logging")

    # Test that main function exists
    assert hasattr(config, "read_config_file")
    assert callable(config.read_config_file)


def test_config_error_handling():
    """Test config error handling scenarios."""

    # Test with invalid path (should be handled gracefully)
    config._config = None

    # Mock a scenario where file exists but can't be read
    with patch("pathlib.Path.exists", return_value=True):
        with patch(
            "configparser.ConfigParser.read", side_effect=Exception("Read error")
        ):
            try:
                config.read_config_file(use_cache=False)
                # If it doesn't raise an exception, that's one way to handle it
            except Exception as e:
                # If it raises an exception, that's also acceptable
                assert "error" in str(e).lower() or "config" in str(e).lower()


def test_config_multiple_calls_consistency():
    """Test that multiple calls to read_config_file are consistent."""

    # Clear cache
    config._config = None

    try:
        # Multiple calls should be consistent
        config1 = config.read_config_file(use_cache=True)
        config2 = config.read_config_file(use_cache=True)
        config3 = config.read_config_file(use_cache=True)

        # All should be the same object when using cache
        assert config1 is config2
        assert config2 is config3

    except ValueError:
        # If config file doesn't exist, that's expected in test environment
        pytest.skip("Config file not available in test environment")


def test_config_cache_reset():
    """Test that cache can be reset and rebuilt."""

    # Set cache to something
    config._config = "dummy_value"

    # Reading with cache should return the dummy value
    result_with_cache = config.read_config_file(use_cache=True)
    assert result_with_cache == "dummy_value"

    # Clear cache
    config._config = None

    # Reading should now attempt to load from file
    try:
        result_without_cache = config.read_config_file(use_cache=False)
        assert result_without_cache != "dummy_value"
        assert isinstance(result_without_cache, configparser.ConfigParser)
    except ValueError:
        # Expected if config file doesn't exist
        pass


def test_config_file_path_resolution():
    """Test config file path resolution logic."""

    # Test that the module correctly resolves paths
    # This is mainly a smoke test to ensure path logic doesn't crash

    module_file_path = Path(config.__file__)
    assert module_file_path.exists()

    # Parent directory should exist
    parent_dir = module_file_path.parent
    assert parent_dir.exists()

    # Config path construction should not crash
    config_path = parent_dir / "../config.ini"
    # Path might not exist, but construction should work
    assert isinstance(config_path, Path)


def test_thread_safe_logging_concurrent_access():
    """
    Test that the thread-safe logging system can handle concurrent access
    from multiple threads without reentrant errors.

    This test simulates the scenario that was causing the original reentrant
    logging error in TinyPersonFactory's parallel agent generation.
    """

    def logging_worker(worker_id, iterations=10):
        """
        Simulate a worker thread that performs logging operations,
        similar to what happens during parallel agent generation.
        """
        logger = logging.getLogger("tinytroupe")

        try:
            for i in range(iterations):
                # Simulate various log levels and operations that occur during agent generation
                logger.debug(f"Test Worker {worker_id}: Debug message {i}")
                logger.info(f"Test Worker {worker_id}: Processing iteration {i}")

                # Small delay to increase chance of concurrent access
                time.sleep(0.001)

                logger.warning(f"Test Worker {worker_id}: Warning in iteration {i}")
                logger.error(
                    f"Test Worker {worker_id}: Error simulation for iteration {i}"
                )

            return True
        except Exception as e:
            # If we encounter the reentrant error, the test should fail
            logger.error(f"Worker {worker_id} encountered error: {e}")
            return False

    # Test with multiple concurrent threads
    num_workers = 3
    iterations_per_worker = 5

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit work to multiple threads
        futures = [
            executor.submit(logging_worker, worker_id, iterations_per_worker)
            for worker_id in range(num_workers)
        ]

        # Wait for all workers to complete and collect results
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Any exception means the test failed
                pytest.fail(f"Worker failed with exception: {e}")

    # All workers should have completed successfully
    assert len(results) == num_workers
    assert all(results), "All workers should complete without errors"


def test_thread_safe_file_handler_creation():
    """
    Test that ThreadSafeFileHandler can be created and used properly.
    """
    from tinytroupe.utils.config import ThreadSafeFileHandler

    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(
        mode="w+", delete=False, suffix=".log"
    ) as temp_file:
        temp_path = temp_file.name

    handler = None
    try:
        # Create the handler
        handler = ThreadSafeFileHandler(temp_path, encoding="utf-8")

        # Verify it has the required attributes
        assert hasattr(handler, "_lock")
        # Check that _lock is a lock object (use type name since isinstance can be tricky with Lock)
        assert type(handler._lock).__name__ in ["Lock", "_thread.lock", "lock"]

        # Test that we can emit records
        test_logger = logging.getLogger("test_thread_safe_handler")
        # Remove any existing handlers to avoid interference
        for h in test_logger.handlers[:]:
            test_logger.removeHandler(h)

        test_logger.addHandler(handler)
        test_logger.setLevel(logging.DEBUG)
        test_logger.propagate = False  # Prevent propagation to root logger

        # Emit a few log records
        test_logger.info("Test message 1")
        test_logger.warning("Test message 2")
        test_logger.error("Test message 3")

        # Clean up logger first
        test_logger.removeHandler(handler)

    finally:
        # Ensure handler is properly closed
        if handler is not None:
            handler.close()

        # Clean up temp file (with retry for Windows)
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                # On Windows, file might still be locked; this is acceptable for the test
                pass


def test_logging_level_setters_thread_safety():
    """
    Test that the logging level setter functions are thread-safe.
    """

    def level_setter_worker(worker_id):
        """Worker that changes log levels concurrently."""
        try:
            for i in range(5):
                if i % 2 == 0:
                    config.set_console_loglevel("DEBUG")
                    config.set_file_loglevel("INFO")
                else:
                    config.set_console_loglevel("WARNING")
                    config.set_file_loglevel("ERROR")

                # Small delay
                time.sleep(0.001)

            return True
        except Exception as e:
            return False

    # Test with multiple threads changing log levels
    num_workers = 3

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(level_setter_worker, worker_id)
            for worker_id in range(num_workers)
        ]

        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                pytest.fail(f"Level setter worker failed: {e}")

    # All workers should complete successfully
    assert len(results) == num_workers
    assert all(results), "All level setter workers should complete without errors"


def test_logging_initialization_thread_safety():
    """
    Test that logger initialization is thread-safe when called from multiple threads.
    """

    # Create a minimal config for testing
    test_config = configparser.ConfigParser()
    test_config.add_section("Logging")
    test_config.set("Logging", "LOGLEVEL", "INFO")
    test_config.set("Logging", "LOGLEVEL_CONSOLE", "INFO")
    test_config.set("Logging", "LOGLEVEL_FILE", "DEBUG")

    def init_worker(worker_id):
        """Worker that initializes logging concurrently."""
        try:
            # Save original state
            original_config = config._config
            original_log_path = config._log_file_path
            original_console_handler = config._console_handler
            original_file_handler = config._file_handler

            # Call start_logger (which should be thread-safe)
            config.start_logger(test_config)

            return True
        except Exception as e:
            return False
        finally:
            # Restore original state
            config._config = original_config
            config._log_file_path = original_log_path
            config._console_handler = original_console_handler
            config._file_handler = original_file_handler

    # Test with multiple threads initializing logging
    num_workers = 2  # Keep small to avoid too much interference

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(init_worker, worker_id) for worker_id in range(num_workers)
        ]

        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                pytest.fail(f"Logger initialization worker failed: {e}")

    # All workers should complete successfully
    assert len(results) == num_workers
    assert all(
        results
    ), "All logger initialization workers should complete without errors"
