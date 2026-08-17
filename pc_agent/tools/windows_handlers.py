"""Handlers for WindowsAppTool-backed local tools."""

from __future__ import annotations

from typing import Any

from pc_agent.windows_apps.tool import WindowsAppTool, WindowsAppToolError

_windows_app_tool: WindowsAppTool | None = None


def configure_windows_app_tool(tool: WindowsAppTool | None = None) -> None:
    global _windows_app_tool
    _windows_app_tool = tool or WindowsAppTool()


def get_windows_app_tool() -> WindowsAppTool:
    if _windows_app_tool is None:
        configure_windows_app_tool()
    return _windows_app_tool


def make_windows_app_handler(tool_id: str):
    def handler(_arguments: dict[str, Any]) -> dict[str, Any]:
        return get_windows_app_tool().execute(tool_id)

    return handler
