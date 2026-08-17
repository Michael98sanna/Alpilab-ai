"""Windows application tool infrastructure for PC Agent."""

from pc_agent.windows_apps.registry import TOOL_ID_TO_APP_ID, LocalAppRegistry, local_app_registry
from pc_agent.windows_apps.tool import WindowsAppTool, WindowsAppToolError, execute_windows_app

__all__ = [
    "LocalAppRegistry",
    "TOOL_ID_TO_APP_ID",
    "WindowsAppTool",
    "WindowsAppToolError",
    "execute_windows_app",
    "local_app_registry",
]
