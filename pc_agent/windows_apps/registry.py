"""Local registry of authorized Windows applications."""

from __future__ import annotations

from pc_agent.windows_apps.config import load_windows_apps_config
from pc_agent.windows_apps.models import WindowsApplicationConfig

TOOL_ID_TO_APP_ID: dict[str, str] = {
    "windows.3utools.open": "3utools",
}


class LocalAppRegistry:
    """Maps tool IDs to locally configured Windows applications."""

    def __init__(self) -> None:
        self._apps: dict[str, WindowsApplicationConfig] = {}
        self.reload()

    def reload(self, config_path: str | None = None) -> None:
        self._apps = load_windows_apps_config(config_path)

    def set_apps(self, apps: dict[str, WindowsApplicationConfig]) -> None:
        self._apps = dict(apps)

    def get(self, app_id: str) -> WindowsApplicationConfig | None:
        return self._apps.get(app_id)

    def resolve_tool(self, tool_id: str) -> WindowsApplicationConfig | None:
        app_id = TOOL_ID_TO_APP_ID.get(tool_id)
        if app_id is None:
            return None
        return self.get(app_id)

    def list_apps(self) -> list[WindowsApplicationConfig]:
        return list(self._apps.values())


local_app_registry = LocalAppRegistry()
