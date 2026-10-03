import configparser
import logging
import os
import queue
import sys
import tempfile
import threading
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener
from pathlib import Path

################################################################################
# Config and startup utilities
################################################################################
_config = None
_log_file_path = None
_console_handler = None
_file_handler = None
_file_queue_listener = None
_file_delegate_handler = None
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
    if _file_delegate_handler is not None:
        _file_delegate_handler.setFormatter(logging.Formatter(_LOG_FORMAT_NO_THREAD))

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


def _get_writable_base_dir():
    """Return a writable directory for logs/cache. Tries: cwd, project root, ~/.tinytroupe, temp."""
    candidates = [
        Path.cwd(),
        Path(__file__).resolve().parent.parent.parent,
        Path.home() / ".tinytroupe",
        Path(tempfile.gettempdir()) / "tinytroupe",
    ]
    for base in candidates:
        try:
            test_dir = base / "logs"
            test_dir.mkdir(parents=True, exist_ok=True)
            (test_dir / ".write_test").write_text("ok")
            (test_dir / ".write_test").unlink()
            return base
        except (OSError, PermissionError):
            continue
    return Path.cwd()  # last resort


def _ensure_log_file_path():
    global _log_file_path
    if _log_file_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = _get_writable_base_dir()
        log_dir = base / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            _log_file_path = log_dir / f"tinytroupe.{timestamp}.log"
        except OSError:
            _log_file_path = None
    return _log_file_path


class _NoFormatQueueHandler(QueueHandler):
    """QueueHandler that skips format() in prepare() to avoid RecursionError in main thread."""

    def prepare(self, record):
        import copy
        r = copy.copy(record)
        r.msg = r.msg if not r.args else (r.msg % r.args)
        r.args = None
        r.exc_info = None
        r.exc_text = None
        r.stack_info = None
        return r


def _create_file_handler():
    """Create QueueHandler + QueueListener so file I/O runs in background thread, avoiding RecursionError."""
    path = _ensure_log_file_path()
    if path is None:
        return None
    try:
        delegate = ThreadSafeFileHandler(path, encoding="utf-8")
        delegate.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        q = queue.Queue(-1)
        queue_handler = _NoFormatQueueHandler(q)
        listener = QueueListener(q, delegate, respect_handler_level=True)
        listener.start()
        return queue_handler, listener, delegate
    except OSError:
        return None


def _apply_logging_levels():
    root_logger = logging.getLogger()
    root_logger.setLevel(_effective_root_level())

    if _console_handler is not None:
        _console_handler.setLevel(
            _console_level if isinstance(_console_level, int) else logging.INFO
        )

    if _file_delegate_handler is not None:
        _file_delegate_handler.setLevel(
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

        # Override with custom config: TINYTROUPE_CONFIG env (e.g. tests/config_ollama.ini)
        # takes precedence over cwd/config.ini
        config_file_path = None
        env_path = os.environ.get("TINYTROUPE_CONFIG")
        if env_path:
            p = Path(env_path)
            if not p.is_absolute():
                p = Path.cwd() / p
            if p.exists():
                config_file_path = p
        if config_file_path is None:
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
    Thread-safe file handler used as delegate for QueueListener. Bypasses
    super().emit() and overrides handleError to avoid recursion (handleError
    calls logging.error which would re-enqueue).
    """
    _in_emit = threading.local()

    def __init__(self, filename, mode="a", encoding=None, delay=False):
        self._emit_failed = False
        super().__init__(filename, mode, encoding, delay)
        self._lock = threading.Lock()

    def handleError(self, record):
        """Avoid recursion: do not call logging.error (would re-enqueue)."""
        if self._emit_failed:
            return
        self._emit_failed = True
        try:
            print(
                "Logging to file failed. Continuing without file logging.",
                file=sys.stderr,
            )
        except Exception:
            pass

    def emit(self, record):
        if self._emit_failed:
            return
        if getattr(ThreadSafeFileHandler._in_emit, "value", False):
            return
        ThreadSafeFileHandler._in_emit.value = True
        try:
            with self._lock:
                try:
                    # Bypass self.format() and record.getMessage() to avoid RecursionError
                    ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
                    m = record.msg % record.args if record.args else record.msg
                    msg = f"{ts} - {record.name} - {record.levelname} - {m}{self.terminator}"
                    if self.stream:
                        self.stream.write(msg)
                        self.flush()
                except Exception as e:
                    self._emit_failed = True
                    try:
                        print(
                            f"Logging to file failed ({type(e).__name__}: {e}). Continuing without file logging.",
                            file=sys.stderr,
                        )
                    except Exception:
                        pass
        finally:
            try:
                ThreadSafeFileHandler._in_emit.value = False
            except Exception:
                pass


def start_logger(config: configparser.ConfigParser):
    global _log_file_path, _console_handler, _file_handler, _file_queue_listener, _file_delegate_handler, _console_level, _file_level, _include_thread_info

    logging.raiseExceptions = False  # avoid --- Logging error --- spam when file handler fails

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
        old_listener = _file_queue_listener
        old_delegate = _file_delegate_handler

        new_console = None
        if _console_level is not None:
            new_console = logging.StreamHandler(stream=sys.stdout)
            _apply_formatter(new_console)

        _file_result = _create_file_handler() if _file_level is not None else None
        if _file_result is not None:
            new_file, new_listener, new_delegate = _file_result
        else:
            new_file, new_listener, new_delegate = None, None, None

        # Assign new handlers (still under lock but have not touched root logger yet)
        _console_handler = new_console
        _file_handler = new_file
        _file_queue_listener = new_listener
        _file_delegate_handler = new_delegate

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
    # Stop old file queue listener and close delegate
    if old_listener is not None:
        try:
            old_listener.stop()
        except Exception:
            pass
    if old_delegate is not None:
        try:
            old_delegate.close()
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
    global _file_level, _file_handler, _file_queue_listener, _file_delegate_handler
    level = _coerce_level(log_level)
    with _logging_lock:
        old_handler = _file_handler
        old_listener = _file_queue_listener
        old_delegate = _file_delegate_handler
        if level is None:
            _file_level = None
            _file_handler = None
            _file_queue_listener = None
            _file_delegate_handler = None
            new_handler = None
        else:
            _file_level = level
            if _file_handler is None:
                result = _create_file_handler()
                if result is not None:
                    _file_handler, _file_queue_listener, _file_delegate_handler = result
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
    if old_listener is not None and old_listener is not _file_queue_listener:
        try:
            old_listener.stop()
        except Exception:
            pass
    if old_delegate is not None and old_delegate is not _file_delegate_handler:
        try:
            old_delegate.close()
        except Exception:
            pass

    if new_handler is None:
        _apply_logging_levels()
        return

    if new_handler not in root_logger.handlers:
        root_logger.addHandler(new_handler)
    if isinstance(level, int) and _file_delegate_handler is not None:
        _file_delegate_handler.setLevel(level)

    _apply_logging_levels()


def get_log_file_path():
    """Return the path of the TinyTroupe log file, if initialized."""
    return _log_file_path


def get_writable_data_dir():
    """Return a writable directory for cache/data files."""
    return _get_writable_base_dir()


def set_include_thread_info(include_thread_info: bool):
    """Enable or disable thread identifiers in log output."""
    global _include_thread_info
    with _logging_lock:
        _include_thread_info = bool(include_thread_info)
        _refresh_handler_formatters_locked()
