"""Load trusted Windows application configuration from env and local file."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pc_agent.windows_apps.models import WindowsApplicationConfig

DEFAULT_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".alpilab", "windows_apps.json")

KNOWN_APPS: dict[str, dict[str, str]] = {
    "3utools": {
        "name": "3uTools",
        "executable": "3uTools.exe",
        "env_prefix": "ALPILAB_WINAPP_3UTOOLS",
    },
}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes"}


def _load_json_config(path: str) -> dict[str, Any]:
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    apps = data.get("windows_apps", data)
    return apps if isinstance(apps, dict) else {}


def load_windows_apps_config(
    config_path: str | None = None,
) -> dict[str, WindowsApplicationConfig]:
    """Merge file config with environment overrides."""
    path = config_path or os.getenv("ALPILAB_WINDOWS_APPS_CONFIG", DEFAULT_CONFIG_PATH)
    file_data = _load_json_config(path)
    configs: dict[str, WindowsApplicationConfig] = {}

    for app_id, defaults in KNOWN_APPS.items():
        prefix = defaults["env_prefix"]
        file_entry = file_data.get(app_id, {})
        if not isinstance(file_entry, dict):
            file_entry = {}

        enabled = _env_bool(
            f"{prefix}_ENABLED",
            bool(file_entry.get("enabled", False)),
        )
        dry_run = _env_bool(
            f"{prefix}_DRY_RUN",
            bool(file_entry.get("dry_run", True)),
        )
        executable_path = os.getenv(f"{prefix}_PATH", "").strip() or str(
            file_entry.get("executable_path", "")
        ).strip()
        executable = str(file_entry.get("executable", defaults["executable"])).strip()

        if app_id == "3utools" and not executable_path:
            from pc_agent.windows_apps.discover import discover_3utools_path

            discovered = discover_3utools_path()
            if discovered:
                executable_path = discovered

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

    return configs
