"""Backend presets and environment validation helpers.

This module provides a small helper layer around TinyTroupe's LLM backend
selection. It exposes presets for the three supported modes—OpenAI, Azure, and
Ollama—and a warning helper that surfaces missing environment variables early
so users can avoid confusing runtime errors.
"""

from __future__ import annotations

import configparser
import logging
import os
from pathlib import Path
from typing import Dict, Iterable

logger = logging.getLogger("tinytroupe")

BACKEND_PRESETS: Dict[str, Dict[str, object]] = {
    "openai": {
        "api_type": "openai",
        "required_env": ["OPENAI_API_KEY"],
        "description": "Hosted OpenAI Chat Completions with the OPENAI_API_KEY secret.",
    },
    "azure": {
        "api_type": "azure",
        "required_env": ["AZURE_OPENAI_ENDPOINT"],
        "optional_env": ["AZURE_OPENAI_KEY"],
        "description": "Azure OpenAI Service using endpoint + key or Entra ID auth.",
    },
    "ollama": {
        "api_type": "ollama",
        "required_env": [],
        "optional_env": ["OLLAMA_BASE_URL", "OLLAMA_API_KEY"],
        "description": "Local Ollama server exposed via the OpenAI-compatible API.",
    },
}


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.ini"


def warn_missing_env_vars(api_type: str) -> None:
    """Log warnings when required/expected environment variables are absent."""

    preset = BACKEND_PRESETS.get(api_type)
    if not preset:
        logger.warning("No backend preset found for '%s'.", api_type)
        return

    missing_required = _missing_env(preset.get("required_env", []))
    missing_optional = _missing_env(preset.get("optional_env", []))

    if missing_required:
        logger.warning(
            "[%s backend] Missing required environment variables: %s.",
            api_type,
            ", ".join(sorted(missing_required)),
        )

    if missing_optional and not missing_required:
        logger.info(
            "[%s backend] Optional environment variables not set: %s.",
            api_type,
            ", ".join(sorted(missing_optional)),
        )


def apply_backend_preset(api_type: str, config_path: Path = DEFAULT_CONFIG_PATH) -> Path:
    """Persist the given backend preset into ``config.ini``.

    Only updates the OpenAI section keys involved in backend selection so users
    can quickly switch between local Ollama, hosted OpenAI, or Azure OpenAI
    without editing the file manually.
    """

    preset = BACKEND_PRESETS.get(api_type)
    if not preset:
        raise ValueError(f"Unknown backend preset '{api_type}'.")

    parser = configparser.ConfigParser()
    parser.read(config_path)

    if "OpenAI" not in parser:
        parser["OpenAI"] = {}

    parser["OpenAI"]["API_TYPE"] = str(preset["api_type"])

    # Ensure reasonable defaults are present for optional endpoints.
    if api_type == "ollama":
        parser["OpenAI"].setdefault("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    elif api_type == "azure":
        parser["OpenAI"].setdefault("AZURE_API_VERSION", "2023-05-15")

    with open(config_path, "w", encoding="utf-8", errors="replace") as config_file:
        parser.write(config_file)

    logger.info("Applied backend preset '%s' to %s", api_type, config_path)
    warn_missing_env_vars(api_type)

    return config_path


def _missing_env(expected: Iterable[str]) -> set[str]:
    return {name for name in expected if not os.getenv(name)}

