"""Opt-in local Alpilab Check config under ~/.alpilab (not compiled into the EXE)."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import MutableMapping

logger = logging.getLogger("alpilab.local_hub")

CAP_ENV = "ALPILAB_CAP_ALPILAB_CHECK"
SECRET_PATH_ENV = "ALPILAB_CHECK_BRIDGE_SECRET_PATH"


def alpilab_check_config_path() -> Path:
    return Path.home() / ".alpilab" / "alpilab_check.json"


def _secret_file_is_usable(path: Path) -> bool:
    """True when path exists, is a file, and contains non-empty secret text."""
    try:
        if not path.is_file():
            return False
        return bool(path.read_text(encoding="utf-8").strip())
    except OSError:
        return False


def apply_alpilab_check_env(
    config_path: Path | None = None,
    environ: MutableMapping[str, str] | None = None,
) -> bool:
    """
    Optionally enable Alpilab Check capability from local JSON config.

    Returns True only when capability env was set (or already present) after
    a valid enabled=true config with a usable secret path.

    Never logs secret contents. Invalid/missing config is a no-op.
    """
    env: MutableMapping[str, str] = os.environ if environ is None else environ
    path = config_path if config_path is not None else alpilab_check_config_path()

    if not path.is_file():
        return False

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        logger.warning(
            "Alpilab Check local config is invalid or unreadable; capability left disabled"
        )
        return False

    if not isinstance(data, dict):
        logger.warning(
            "Alpilab Check local config must be a JSON object; capability left disabled"
        )
        return False

    if data.get("enabled") is not True:
        return False

    secret_path_raw = data.get("bridge_secret_path")
    if not isinstance(secret_path_raw, str) or not secret_path_raw.strip():
        logger.warning(
            "Alpilab Check enabled but bridge_secret_path is missing; capability left disabled"
        )
        return False

    secret_path = Path(secret_path_raw.strip())
    if not _secret_file_is_usable(secret_path):
        logger.warning(
            "Alpilab Check enabled but bridge secret file is missing or unreadable; "
            "capability left disabled"
        )
        return False

    env.setdefault(CAP_ENV, "true")
    env.setdefault(SECRET_PATH_ENV, str(secret_path))
    logger.info("Alpilab Check local config enabled (secret path configured)")
    return True
