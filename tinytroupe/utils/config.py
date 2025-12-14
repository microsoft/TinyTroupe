import configparser
import logging
import sys
import threading
from datetime import datetime
from pathlib import Path

################################################################################
# Config and startup utilities
################################################################################
_config = None
_log_file_path = None
_console_handler = None
_file_handler = None
_root_level = None
_console_level = None
_file_level = None
_include_thread_info = False
_logging_lock = threading.RLock()

_LOG_FORMAT_WITH_THREAD = (
    "%(asctime)s - %(threadName)s(%(thread)d) - %(name)s - %(levelname)s - %(message)s"
)
_LOG_FORMAT_NO_THREAD = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def _current_formatter():
    fmt = _LOG_FORMAT_WITH_THREAD if _include_thread_info else _LOG_FORMAT_NO_THREAD
    return logging.Formatter(fmt)


def _apply_formatter(handler):
    if handler is not None:
        handler.setFormatter(_current_formatter())


def _refresh_handler_formatters_locked():
    if _console_handler is not None:
        _console_handler.setFormatter(_current_formatter())
    if _file_handler is not None:
        _file_handler.setFormatter(_current_formatter())

_DISABLED_LEVEL_TOKENS = {"NONE", "OFF"}


def _coerce_level(level):
    """Convert a log level (string/int) into a numeric level understood by logging."""
    if isinstance(level, int):
        return level

    if isinstance(level, str):
        candidate = level.strip().upper()
        if candidate in _DISABLED_LEVEL_TOKENS or candidate == "":
            return None
        attr = getattr(logging, candidate, None)
        if isinstance(attr, int):
            return attr
        try:
            return int(candidate)
        except ValueError:
            pass

    return logging.INFO


def _effective_root_level():
    levels = [
        level
        for level in (_root_level, _console_level, _file_level)
        if isinstance(level, int)
    ]
    return min(levels) if levels else logging.INFO


def _ensure_log_file_path():
    global _log_file_path
    if _log_file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        _log_file_path = Path.cwd() / f"tinytroupe.{timestamp}.log"
    return _log_file_path


def _create_file_handler():
    handler = ThreadSafeFileHandler(_ensure_log_file_path(), encoding="utf-8")
    _apply_formatter(handler)
    return handler


def _apply_logging_levels():
    root_logger = logging.getLogger()
    root_logger.setLevel(_effective_root_level())

    if _console_handler is not None:
        _console_handler.setLevel(
            _console_level if isinstance(_console_level, int) else logging.INFO
        )

    if _file_handler is not None:
        _file_handler.setLevel(
            _file_level if isinstance(_file_level, int) else logging.INFO
        )

    project_logger = logging.getLogger("tinytroupe")
    project_logger.setLevel(_effective_root_level())
    project_logger.propagate = True


def read_config_file(use_cache=True, verbose=True) -> configparser.ConfigParser:
    global _config
    if use_cache and _config is not None:
        # if we have a cached config and accept that, return it
        return _config

    else:
        config = configparser.ConfigParser()

        # Read the default values in the module directory.
        config_file_path = Path(__file__).parent.absolute() / "../config.ini"
        print(f"Looking for default config on: {config_file_path}") if verbose else None
        if config_file_path.exists():
            config.read(config_file_path)
            _config = config
        else:
            raise ValueError(f"Failed to find default config on: {config_file_path}")

        # Now, let's override any specific default value, if there's a custom .ini config.
        # Try the directory of the current main program
        config_file_path = Path.cwd() / "config.ini"
        if config_file_path.exists():
            print(f"Found custom config on: {config_file_path}") if verbose else None
            config.read(
                config_file_path
            )  # this only overrides the values that are present in the custom config
            _config = config
            return config
        else:
            if verbose:
                (
                    print(f"Failed to find custom config on: {config_file_path}")
                    if verbose
                    else None
                )
                (
                    print(
                        "Will use only default values. IF THINGS FAIL, TRY CUSTOMIZING MODEL, API TYPE, etc."
                    )
                    if verbose
                    else None
                )

        return config


def pretty_print_config(config):
    print()
    print("=================================")
    print("Current TinyTroupe configuration ")
    print("=================================")
    for section in config.sections():
        print(f"[{section}]")
        for key, value in config.items(section):
            print(f"{key} = {value}")
        print()


def pretty_print_datetime():
    from datetime import datetime, timezone

    now = datetime.now()
    now_utc = now.astimezone(timezone.utc)
    print(f"Current date and time (local): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Current date and time (UTC):   {now_utc.strftime('%Y-%m-%d %H:%M:%S')}")


def pretty_print_tinytroupe_version():
    try:
        import importlib.metadata

        version = importlib.metadata.version("tinytroupe")
    except Exception:
        version = "unknown"
    print(f"TinyTroupe version: {version}")


class ThreadSafeFileHandler(logging.FileHandler):
    """
    A thread-safe file handler that uses a lock to prevent reentrant calls
    when multiple threads are logging simultaneously.
    """

    def __init__(self, filename, mode="a", encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)
        self._lock = threading.Lock()

    def emit(self, record):
        """
        Thread-safe emit method that prevents reentrant calls to the file buffer.
        """
        with self._lock:
            try:
                super().emit(record)
            except Exception:
                # If we can't log to file, continue to avoid breaking the application
                # This is better than crashing on logging issues.
                # But print to stderr so we know something went wrong.
                print(
                    "Logging to file failed. Continuing without file logging.",
                    file=sys.stderr,
                )


def start_logger(config: configparser.ConfigParser):
    global _log_file_path, _console_handler, _file_handler, _console_level, _file_level, _include_thread_info

    # Collect changes under lock, but avoid calling logging APIs while holding it.
    with _logging_lock:
        default_level = config["Logging"].get("LOGLEVEL", "INFO")
        _root_level = _coerce_level(default_level)

        _include_thread_info = config["Logging"].getboolean(
            "LOG_INCLUDE_THREAD_ID", fallback=False
        )

        _console_level = _coerce_level(
            config["Logging"].get("LOGLEVEL_CONSOLE", default_level)
        )
        _file_level = _coerce_level(
            config["Logging"].get("LOGLEVEL_FILE", default_level)
        )

        # Cache old handlers to remove outside lock
        old_console = _console_handler
        old_file = _file_handler

        new_console = None
        if _console_level is not None:
            new_console = logging.StreamHandler(stream=sys.stdout)
            _apply_formatter(new_console)

        new_file = _create_file_handler() if _file_level is not None else None

        # Assign new handlers (still under lock but have not touched root logger yet)
        _console_handler = new_console
        _file_handler = new_file

    _refresh_handler_formatters_locked()

    # From here on, no module lock held; operate on logging (avoids lock inversion risks).
    root_logger = logging.getLogger()

    if old_console is not None:
        root_logger.removeHandler(old_console)
        try:
            old_console.close()
        except Exception:
            pass

    if old_file is not None:
        root_logger.removeHandler(old_file)
        try:
            old_file.close()
        except Exception:
            pass

    if _console_handler is not None:
        root_logger.addHandler(_console_handler)
    if _file_handler is not None:
        root_logger.addHandler(_file_handler)

    project_logger = logging.getLogger("tinytroupe")
    for handler in project_logger.handlers[:]:
        project_logger.removeHandler(handler)
    project_logger.propagate = True

    _apply_logging_levels()

    # Log AFTER initialization & lock release to avoid nested lock acquisition chains.
    project_logger.debug("TinyTroupe logging initialized")


def set_loglevel(log_level):
    """
    Sets both log levels (console and file) to the same value.
    Args:
        log_level (str | int): Desired logging level.
    """
    level = _coerce_level(log_level)
    global _root_level
    with _logging_lock:
        _root_level = level

    set_console_loglevel(log_level)
    set_file_loglevel(log_level)


def set_console_loglevel(log_level):
    """Update the console logging level without affecting the file level."""
    global _console_level, _console_handler
    level = _coerce_level(log_level)
    with _logging_lock:
        old_handler = _console_handler
        if level is None:
            _console_level = None
            _console_handler = None
            new_handler = None
        else:
            _console_level = level
            if _console_handler is None:
                handler = logging.StreamHandler(stream=sys.stdout)
                _apply_formatter(handler)
                _console_handler = handler
            new_handler = _console_handler

    root_logger = logging.getLogger()
    if (
        old_handler is not None
        and old_handler is not new_handler
        and old_handler in root_logger.handlers
    ):
        root_logger.removeHandler(old_handler)
        try:
            old_handler.close()
        except Exception:
            pass

    if new_handler is not None:
        if new_handler not in root_logger.handlers:
            root_logger.addHandler(new_handler)
        if isinstance(level, int):
            new_handler.setLevel(level)

    _apply_logging_levels()


def set_file_loglevel(log_level):
    """Update the file logging level without affecting the console level."""
    global _file_level, _file_handler
    level = _coerce_level(log_level)
    with _logging_lock:
        old_handler = _file_handler
        if level is None:
            _file_level = None
            _file_handler = None
            new_handler = None
        else:
            _file_level = level
            if _file_handler is None:
                _file_handler = _create_file_handler()
            new_handler = _file_handler

    root_logger = logging.getLogger()
    if (
        old_handler is not None
        and old_handler is not new_handler
        and old_handler in root_logger.handlers
    ):
        root_logger.removeHandler(old_handler)
        try:
            old_handler.close()
        except Exception:
            pass

    if new_handler is None:
        # File logging disabled; nothing else to attach.
        _apply_logging_levels()
        return

    if new_handler not in root_logger.handlers:
        root_logger.addHandler(new_handler)
    if isinstance(level, int):
        new_handler.setLevel(level)

    _apply_logging_levels()


def get_log_file_path():
    """Return the path of the TinyTroupe log file, if initialized."""
    return _log_file_path


def set_include_thread_info(include_thread_info: bool):
    """Enable or disable thread identifiers in log output."""
    global _include_thread_info
    with _logging_lock:
        _include_thread_info = bool(include_thread_info)
        _refresh_handler_formatters_locked()
