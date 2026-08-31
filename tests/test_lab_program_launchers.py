"""Authorized launcher coverage for MIIR and Mosaic lab applications."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agent.payloads import AgentCapabilities
from app.main import app
from app.security.tool_authorization import authorize_tool_execution
from app.tools.executable import (
    WINDOWS_BORNEO_OPEN_TOOL,
    WINDOWS_MICROSCOPE_OPEN_TOOL,
    WINDOWS_THERMAL_CAMERA_OPEN_TOOL,
    validate_tool_arguments,
)
from app.tools.registry import default_tool_registry
from pc_agent.windows_apps.launcher import MockProcessLauncher
from pc_agent.windows_apps.models import WindowsApplicationConfig
from pc_agent.windows_apps.registry import LocalAppRegistry
from pc_agent.windows_apps.tool import WindowsAppTool, WindowsAppToolError


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.parametrize(
    "tool_id",
    [
        "windows.thermal_camera.open",
        "windows.microscope.open",
        "windows.borneo.open",
    ],
)
def test_lab_programs_are_explicitly_registered(tool_id: str) -> None:
    assert default_tool_registry.get_executable(tool_id) is not None


@pytest.mark.parametrize(
    "spec",
    [
        WINDOWS_THERMAL_CAMERA_OPEN_TOOL,
        WINDOWS_MICROSCOPE_OPEN_TOOL,
        WINDOWS_BORNEO_OPEN_TOOL,
    ],
)
def test_lab_programs_require_authorized_windows_apps(spec) -> None:
    assert authorize_tool_execution(spec, AgentCapabilities(windows_apps=True)).allowed
    assert not authorize_tool_execution(spec, AgentCapabilities(windows_apps=False)).allowed
    assert validate_tool_arguments(spec, {"path": r"C:\\untrusted.exe"}) == "INVALID_ARGUMENTS"


@pytest.mark.parametrize(
    ("tool_id", "app_id", "exe_name"),
    [
        ("windows.thermal_camera.open", "thermal_camera", "MIIR.exe"),
        ("windows.microscope.open", "microscope", "Mosaic2.3.exe"),
        ("windows.borneo.open", "borneo", "Borneo Schematics.lnk"),
    ],
)
def test_lab_program_launches_only_registered_local_executable(
    tmp_path: Path, tool_id: str, app_id: str, exe_name: str
) -> None:
    executable = tmp_path / exe_name
    executable.write_bytes(b"MZ")
    app_cfg = WindowsApplicationConfig(
        app_id=app_id,
        name=app_id,
        executable=exe_name,
        executable_path=str(executable),
        enabled=True,
        dry_run=False,
    )
    registry = LocalAppRegistry()
    registry.set_apps({app_id: app_cfg})
    launcher = MockProcessLauncher()

    result = WindowsAppTool(registry=registry, launcher=launcher).execute(tool_id)

    assert result["started"] is True
    assert launcher.launches == [str(executable)]


def test_lab_program_executable_missing_returns_real_error() -> None:
    registry = LocalAppRegistry()
    registry.set_apps(
        {
            "thermal_camera": WindowsApplicationConfig(
                app_id="thermal_camera",
                name="Termocamera",
                executable="MIIR.exe",
                executable_path=r"C:\\missing\\MIIR.exe",
                enabled=True,
                dry_run=False,
            )
        }
    )

    with pytest.raises(WindowsAppToolError, match="EXECUTABLE_NOT_FOUND"):
        WindowsAppTool(registry=registry, launcher=MockProcessLauncher()).execute(
            "windows.thermal_camera.open"
        )


@pytest.mark.parametrize(
    "tool_id",
    [
        "windows.thermal_camera.open",
        "windows.microscope.open",
        "windows.borneo.open",
    ],
)
def test_rest_execute_routes_exist_for_lab_programs(
    client: TestClient, tool_id: str
) -> None:
    """Missing POST routes previously returned HTTP 405 from the UI."""
    resp = client.post(
        f"/api/v1/sessions/repair-x/agents/missing/tools/{tool_id}/execute"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["tool_id"] == tool_id
    assert body["error"]
