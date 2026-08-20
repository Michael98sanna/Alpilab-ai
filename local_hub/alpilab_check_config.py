"""Opt-in local Alpilab Check config under ~/.alpilab (not compiled into the EXE)."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import MutableMapping

logger = logging.getLogger("alpilab.local_hub")

CAP_ENV = "ALPILAB_CAP_ALPILAB_CHECK"
SECRET_PATH_ENV = "ALPILAB_CHECK_BRIDGE_SECRET_PATH"
DEFAULT_EXECUTABLE = "AlpilabCheck.exe"


@dataclass(frozen=True)
class AlpilabCheckLauncherSettings:
    """Launcher fields from ~/.alpilab/alpilab_check.json (never from UI)."""

    enabled: bool
    executable: str
    executable_path: str
    dry_run: bool


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


def _read_config_object(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        logger.warning(
            "Alpilab Check local config is invalid or unreadable; capability left disabled"
        )
        return None
    if not isinstance(data, dict):
        logger.warning(
            "Alpilab Check local config must be a JSON object; capability left disabled"
        )
        return None
    return data


def load_alpilab_check_launcher_settings(
    config_path: Path | None = None,
) -> AlpilabCheckLauncherSettings | None:
    """
    Read launcher settings from alpilab_check.json.

    Returns None when the file is missing/invalid or executable_path is absent.
    Does not require bridge_secret_path (bridge and launcher are independent).
    Never logs secrets.
    """
    path = config_path if config_path is not None else alpilab_check_config_path()
    data = _read_config_object(path)
    if data is None:
        return None

    path_raw = data.get("executable_path")
    if not isinstance(path_raw, str) or not path_raw.strip():
        return None

    executable_raw = data.get("executable")
    executable = (
        executable_raw.strip()
        if isinstance(executable_raw, str) and executable_raw.strip()
        else DEFAULT_EXECUTABLE
    )

    dry_run = data.get("dry_run") is True
    # Launch is allowed when path is present; honor enabled=false explicitly.
    enabled = data.get("enabled") is not False

    return AlpilabCheckLauncherSettings(
        enabled=enabled,
        executable=executable,
        executable_path=path_raw.strip(),
        dry_run=dry_run,
    )


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

    data = _read_config_object(path)
    if data is None:
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
