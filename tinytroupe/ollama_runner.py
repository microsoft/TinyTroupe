"""
Start and manage Ollama instances for TinyTroupe.

TinyTroupe uses dedicated ports (11444, 11445) for its own Ollama instances;
no reliance on the default 11434. Supports dual-agent setups with round-robin.
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import time

import requests

logger = logging.getLogger("tinytroupe")

DEFAULT_PORTS = [11444, 11445]
DEFAULT_MODEL = "gemma3:1b"
READY_TIMEOUT = 120
READY_POLL_INTERVAL = 1.0


def _ollama_bin() -> str | None:
    """Return path to ollama binary, or None if not found."""
    return shutil.which("ollama")


def _wait_until_ready(url: str, timeout: float = READY_TIMEOUT) -> bool:
    """Poll until Ollama responds at url. Returns True when ready."""
    base = url.rstrip("/").replace("/v1", "")
    health_url = f"{base}/api/tags"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = requests.get(health_url, timeout=2)
            if r.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(READY_POLL_INTERVAL)
    return False


def start_instances(
    ports: list[int] | None = None,
    model: str | None = None,
    wait: bool = True,
) -> list[subprocess.Popen]:
    """
    Start Ollama on the given ports. TinyTroupe uses 11444 and 11445 by default.

    Args:
        ports: Ports to use (default [11444, 11445]).
        model: Model to pull after start (e.g. gemma3:1b). If None, skips pull.
        wait: If True, block until each instance responds. Otherwise return immediately.

    Returns:
        List of Popen processes. Call stop_instances(procs) or terminate() when done.

    Raises:
        FileNotFoundError: If ollama binary is not in PATH.
    """
    bin_path = _ollama_bin()
    if not bin_path:
        raise FileNotFoundError(
            "ollama not found in PATH. Install from https://ollama.com"
        )

    ports = ports or DEFAULT_PORTS
    procs: list[subprocess.Popen] = []

    for port in ports:
        env = os.environ.copy()
        env["OLLAMA_HOST"] = f"127.0.0.1:{port}"

        proc = subprocess.Popen(
            [bin_path, "serve"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        procs.append(proc)
        logger.info(f"Started Ollama on port {port} (pid={proc.pid})")

    if wait:
        for port in ports:
            url = f"http://127.0.0.1:{port}/v1"
            if not _wait_until_ready(url):
                stop_instances(procs)
                raise TimeoutError(
                    f"Ollama on port {port} did not become ready within {READY_TIMEOUT}s"
                )

        if model:
            host = f"127.0.0.1:{ports[0]}"
            env = os.environ.copy()
            env["OLLAMA_HOST"] = host
            logger.info(f"Pulling model {model}...")
            subprocess.run(
                [bin_path, "pull", model],
                env=env,
                capture_output=True,
                timeout=300,
                check=False,
            )

    return procs


def stop_instances(procs: list[subprocess.Popen]) -> None:
    """Terminate Ollama processes started by start_instances."""
    for proc in procs:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                proc.kill()
            except ProcessLookupError:
                pass


class OllamaInstances:
    """
    Context manager to run TinyTroupe's Ollama instances.
    Starts on 11444 and 11445 by default; stops on exit.
    """

    def __init__(
        self,
        ports: list[int] | None = None,
        model: str | None = DEFAULT_MODEL,
    ):
        self.ports = ports or DEFAULT_PORTS
        self.model = model
        self._procs: list[subprocess.Popen] | None = None

    def __enter__(self) -> "OllamaInstances":
        self._procs = start_instances(ports=self.ports, model=self.model, wait=True)
        return self

    def __exit__(self, *args) -> None:
        if self._procs:
            stop_instances(self._procs)
            self._procs = None

    @property
    def base_urls(self) -> list[str]:
        """Base URLs for the running instances (for OLLAMA_BASE_URLS)."""
        return [f"http://127.0.0.1:{p}/v1" for p in self.ports]
