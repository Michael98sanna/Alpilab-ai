"""Generic WindowsAppTool — open registered local applications."""

from __future__ import annotations

import logging
from pathlib import Path

from pc_agent.windows_apps.launcher import LaunchResult, ProcessLauncher, SubprocessLauncher
from pc_agent.windows_apps.models import WindowsApplicationConfig
from pc_agent.windows_apps.registry import LocalAppRegistry, local_app_registry

logger = logging.getLogger("alpilab.pc_agent")


class WindowsAppToolError(Exception):
    def __init__(self, code: str, message: str = "") -> None:
        super().__init__(message or code)
        self.code = code


class WindowsAppTool:
    """Validate and open/register Windows applications from local config only."""

    def __init__(
        self,
        registry: LocalAppRegistry | None = None,
        launcher: ProcessLauncher | None = None,
    ) -> None:
        self._registry = registry or local_app_registry
        self._launcher = launcher or SubprocessLauncher()

    def execute(self, tool_id: str) -> dict:
        app = self._registry.resolve_tool(tool_id)
        if app is None:
            logger.warning("windows app tool_id=%s APP_NOT_REGISTERED", tool_id)
            raise WindowsAppToolError("APP_NOT_REGISTERED")

        logger.info(
            "windows app tool_id=%s app_id=%s enabled=%s dry_run=%s executable_path=%s",
            tool_id,
            app.app_id,
            app.enabled,
            app.dry_run,
            app.executable_path,
        )
        if not app.enabled:
            raise WindowsAppToolError("TOOL_DISABLED")

        validated_path = self._validate_executable(app)

        if app.dry_run:
            return {
                "mode": "dry_run",
                "app_id": app.app_id,
                "executable": app.executable,
                "validated": True,
                "would_execute": True,
            }

        try:
            launch = self._launcher.start_executable(validated_path)
        except (OSError, RuntimeError) as exc:
            raise WindowsAppToolError("PROCESS_START_FAILED", str(exc)) from exc

        return {
            "mode": "execution",
            "app_id": app.app_id,
            "started": launch.started,
            "already_running": launch.already_running,
        }

    def _validate_executable(self, app: WindowsApplicationConfig) -> str:
        if not app.executable_path:
            raise WindowsAppToolError("EXECUTABLE_NOT_FOUND")

        path = Path(app.executable_path)
        if not path.is_file():
            raise WindowsAppToolError("EXECUTABLE_NOT_FOUND")

        resolved = path.resolve()
        if not resolved.is_file():
            raise WindowsAppToolError("EXECUTABLE_NOT_FOUND")

        if resolved.name.lower() != app.executable.lower():
            raise WindowsAppToolError("EXECUTABLE_NOT_FOUND")

        return str(resolved)


def execute_windows_app(tool_id: str) -> dict:
    return WindowsAppTool().execute(tool_id)
