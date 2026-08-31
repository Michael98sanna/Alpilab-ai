"""Load trusted Windows application configuration from env and local file."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from pc_agent.windows_apps.models import WindowsApplicationConfig

logger = logging.getLogger("alpilab.pc_agent")

DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".alpilab", "windows_apps.json")

KNOWN_APPS: dict[str, dict[str, str]] = {
    "3utools": {
        "name": "3uTools",
        "executable": "3uTools.exe",
        "env_prefix": "ALPILAB_WINAPP_3UTOOLS",
    },
    "alpilab_check": {
        "name": "Alpilab Check",
        "executable": "AlpilabCheck.exe",
        "env_prefix": "ALPILAB_WINAPP_ALPILAB_CHECK",
    },
    "thermal_camera": {
        "name": "Termocamera",
        "executable": "MIIR.exe",
        "env_prefix": "ALPILAB_WINAPP_THERMAL_CAMERA",
    },
    "microscope": {
        "name": "Microscopio",
        "executable": "Mosaic2.3.exe",
        "env_prefix": "ALPILAB_WINAPP_MICROSCOPE",
    },
    "borneo": {
        "name": "Borneo",
        "executable": "Borneo Schematics.lnk",
        "env_prefix": "ALPILAB_WINAPP_BORNEO",
    },
}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes"}


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    raw = str(value).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes"}


def _decode_config_bytes(raw: bytes) -> str:
    """Decode user JSON written by Python (UTF-8) or PowerShell (UTF-8 BOM / UTF-16)."""
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        return raw.decode("utf-16")
    return raw.decode("utf-8-sig")


def _load_json_config(path: str) -> dict[str, Any]:
    if not os.path.isfile(path):
        logger.info("windows_apps config missing path=%s", path)
        return {}
    try:
        text = _decode_config_bytes(Path(path).read_bytes())
        data = json.loads(text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        logger.warning("windows_apps config unreadable path=%s error=%s", path, exc)
        return {}
    if not isinstance(data, dict):
        logger.warning("windows_apps config is not an object path=%s", path)
        return {}
    apps = data.get("windows_apps", data)
    if not isinstance(apps, dict):
        logger.warning("windows_apps config has invalid windows_apps object path=%s", path)
        return {}
    return apps


def _field_from_file_or_env(
    file_entry: dict[str, Any],
    key: str,
    env_name: str,
    default: bool,
) -> bool:
    """User JSON is source of truth when the key is present; env fills gaps only."""
    if key in file_entry:
        return _coerce_bool(file_entry.get(key), default)
    return _env_bool(env_name, default)


def load_windows_apps_config(
    config_path: str | None = None,
) -> dict[str, WindowsApplicationConfig]:
    """Load `%USERPROFILE%\\.alpilab\\windows_apps.json`, then fill missing fields from env."""
    path = config_path or os.getenv("ALPILAB_WINDOWS_APPS_CONFIG", DEFAULT_CONFIG_PATH)
    file_data = _load_json_config(path)
    configs: dict[str, WindowsApplicationConfig] = {}

    logger.info("windows_apps config path=%s apps=%s", path, ",".join(sorted(file_data)) or "-")

    for app_id, defaults in KNOWN_APPS.items():
        prefix = defaults["env_prefix"]
        file_entry = file_data.get(app_id, {})
        if not isinstance(file_entry, dict):
            file_entry = {}

        enabled = _field_from_file_or_env(
            file_entry, "enabled", f"{prefix}_ENABLED", False
        )
        dry_run = _field_from_file_or_env(
            file_entry, "dry_run", f"{prefix}_DRY_RUN", True
        )
        file_path = str(file_entry.get("executable_path", "")).strip()
        executable_path = file_path or os.getenv(f"{prefix}_PATH", "").strip()
        executable = str(file_entry.get("executable", defaults["executable"])).strip()

        if app_id == "3utools" and not executable_path:
            from pc_agent.windows_apps.discover import discover_3utools_path

            discovered = discover_3utools_path()
            if discovered:
                executable_path = discovered

        if app_id == "alpilab_check" and not executable_path:
            from local_hub.alpilab_check_config import load_alpilab_check_launcher_settings

            launcher = load_alpilab_check_launcher_settings()
            if launcher is not None:
                executable_path = launcher.executable_path
                if "enabled" not in file_entry:
                    enabled = launcher.enabled
                if "dry_run" not in file_entry:
                    dry_run = launcher.dry_run
                if "executable" not in file_entry and launcher.executable:
                    executable = launcher.executable

        if not executable_path and not enabled:
            continue

        configs[app_id] = WindowsApplicationConfig(
            app_id=app_id,
            name=str(file_entry.get("name", defaults["name"])),
            executable=executable or defaults["executable"],
            executable_path=executable_path,
            enabled=enabled,
            dry_run=dry_run,
        )
        logger.info(
            "windows_apps loaded app=%s enabled=%s dry_run=%s executable=%s executable_path=%s",
            app_id,
            enabled,
            dry_run,
            executable or defaults["executable"],
            executable_path,
        )

    return configs
