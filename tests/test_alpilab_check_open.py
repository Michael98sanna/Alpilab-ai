"""V0.7.3: windows.alpilab_check.open launcher via WindowsAppTool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.agent.execution_store import tool_execution_store
from app.agent.registry import agent_registry
from app.main import app
from app.security.tool_authorization import authorize_tool_execution
from app.tools.executable import (
    FORBIDDEN_REMOTE_ARGUMENT_KEYS,
    WINDOWS_ALPILAB_CHECK_OPEN_TOOL,
    validate_tool_arguments,
)
from app.tools.registry import default_tool_registry
from local_hub.alpilab_check_config import load_alpilab_check_launcher_settings
from pc_agent.commands import configure_dispatcher, handle_command
from pc_agent.tools.windows_handlers import configure_windows_app_tool
from pc_agent.windows_apps.config import load_windows_apps_config
from pc_agent.windows_apps.launcher import MockProcessLauncher
from pc_agent.windows_apps.models import WindowsApplicationConfig
from pc_agent.windows_apps.registry import LocalAppRegistry, local_app_registry
from pc_agent.windows_apps.tool import WindowsAppTool, WindowsAppToolError


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    agent_registry.clear()
    tool_execution_store.clear()
    from app.realtime import session_manager as sm

    sm.realtime_manager._sessions.clear()
    sm.realtime_manager._ws_connections.clear()
    sm.realtime_manager._event_log.clear()
    local_app_registry.set_apps({})


def _register(ws, agent_id: str = "agent-check-open-01") -> None:
    ws.send_json(
        {
            "type": "register",
            "agent_id": agent_id,
            "agent_name": "ALPILAB-PC",
            "platform": "windows",
            "agent_version": "0.7.3",
            "capabilities": {
                "safe_test": True,
                "windows_apps": True,
                "alpilab_check": True,
                "microscope": False,
                "thermal_camera": False,
                "multimeter": False,
                "power_supply": False,
            },
            "status": "ONLINE",
        }
    )
    ws.receive_json()


def _check_app(tmp_path: Path, *, dry_run: bool = False) -> WindowsApplicationConfig:
    exe = tmp_path / "AlpilabCheck.exe"
    exe.write_text("stub", encoding="utf-8")
    return WindowsApplicationConfig(
        app_id="alpilab_check",
        name="Alpilab Check",
        executable="AlpilabCheck.exe",
        executable_path=str(exe),
        enabled=True,
        dry_run=dry_run,
    )


def test_windows_alpilab_check_open_registered() -> None:
    spec = default_tool_registry.get_executable("windows.alpilab_check.open")
    assert spec is not None
    assert spec.tool_id == "windows.alpilab_check.open"
    assert spec.enabled is True
    assert "windows_apps" in spec.required_capabilities


def test_authorization_required_for_open() -> None:
    from app.agent.payloads import AgentCapabilities

    decision = authorize_tool_execution(
        WINDOWS_ALPILAB_CHECK_OPEN_TOOL,
        AgentCapabilities(windows_apps=True),
    )
    assert decision.allowed is True

    denied = authorize_tool_execution(
        WINDOWS_ALPILAB_CHECK_OPEN_TOOL,
        AgentCapabilities(windows_apps=False, alpilab_check=True),
    )
    assert denied.allowed is False


def test_no_arbitrary_path_arguments() -> None:
    assert validate_tool_arguments(
        WINDOWS_ALPILAB_CHECK_OPEN_TOOL,
        {"path": "C:\\evil.exe"},
    ) == "INVALID_ARGUMENTS"
    for key in FORBIDDEN_REMOTE_ARGUMENT_KEYS:
        assert (
            validate_tool_arguments(WINDOWS_ALPILAB_CHECK_OPEN_TOOL, {key: "x"})
            == "INVALID_ARGUMENTS"
        )


def test_launcher_settings_from_alpilab_check_json(tmp_path: Path) -> None:
    exe = tmp_path / "AlpilabCheck.exe"
    exe.write_bytes(b"MZ")
    cfg = tmp_path / "alpilab_check.json"
    cfg.write_text(
        json.dumps(
            {
                "enabled": True,
                "executable": "AlpilabCheck.exe",
                "executable_path": str(exe),
                "dry_run": False,
            }
        ),
        encoding="utf-8",
    )
    settings = load_alpilab_check_launcher_settings(config_path=cfg)
    assert settings is not None
    assert settings.executable_path == str(exe)
    assert settings.enabled is True


def test_launcher_settings_missing_path(tmp_path: Path) -> None:
    cfg = tmp_path / "alpilab_check.json"
    cfg.write_text(json.dumps({"enabled": True}), encoding="utf-8")
    assert load_alpilab_check_launcher_settings(config_path=cfg) is None


def test_config_loads_from_alpilab_check_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    exe = tmp_path / "AlpilabCheck.exe"
    exe.write_bytes(b"MZ")
    check_cfg = tmp_path / "alpilab_check.json"
    check_cfg.write_text(
        json.dumps(
            {
                "enabled": True,
                "executable_path": str(exe),
                "executable": "AlpilabCheck.exe",
                "dry_run": False,
            }
        ),
        encoding="utf-8",
    )
    win_cfg = tmp_path / "windows_apps.json"
    win_cfg.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("ALPILAB_WINDOWS_APPS_CONFIG", str(win_cfg))

    import local_hub.alpilab_check_config as acc

    monkeypatch.setattr(acc, "alpilab_check_config_path", lambda: check_cfg)

    apps = load_windows_apps_config(str(win_cfg))
    assert "alpilab_check" in apps
    assert apps["alpilab_check"].executable_path == str(exe)
    assert apps["alpilab_check"].enabled is True
    assert apps["alpilab_check"].dry_run is False


def test_exe_missing_raises() -> None:
    registry = LocalAppRegistry()
    registry.set_apps(
        {
            "alpilab_check": WindowsApplicationConfig(
                app_id="alpilab_check",
                name="Alpilab Check",
                executable="AlpilabCheck.exe",
                executable_path="C:\\missing\\AlpilabCheck.exe",
                enabled=True,
                dry_run=False,
            )
        }
    )
    tool = WindowsAppTool(registry=registry, launcher=MockProcessLauncher())
    with pytest.raises(WindowsAppToolError) as exc:
        tool.execute("windows.alpilab_check.open")
    assert exc.value.code == "EXECUTABLE_NOT_FOUND"


def test_app_not_registered() -> None:
    registry = LocalAppRegistry()
    registry.set_apps({})
    tool = WindowsAppTool(registry=registry, launcher=MockProcessLauncher())
    with pytest.raises(WindowsAppToolError) as exc:
        tool.execute("windows.alpilab_check.open")
    assert exc.value.code == "APP_NOT_REGISTERED"


def test_launch_success(tmp_path: Path) -> None:
    app = _check_app(tmp_path)
    registry = LocalAppRegistry()
    registry.set_apps({"alpilab_check": app})
    launcher = MockProcessLauncher()
    tool = WindowsAppTool(registry=registry, launcher=launcher)
    result = tool.execute("windows.alpilab_check.open")
    assert result["started"] is True
    assert result["already_running"] is False
    assert launcher.launches == [app.executable_path]


def test_already_running(tmp_path: Path) -> None:
    app = _check_app(tmp_path)
    registry = LocalAppRegistry()
    registry.set_apps({"alpilab_check": app})
    launcher = MockProcessLauncher(already_running=True)
    tool = WindowsAppTool(registry=registry, launcher=launcher)
    result = tool.execute("windows.alpilab_check.open")
    assert result["already_running"] is True
    assert result["started"] is False


def test_e2e_open_via_pc_agent_command(tmp_path: Path) -> None:
    app = _check_app(tmp_path, dry_run=False)
    configure_dispatcher({"windows_apps": True, "safe_test": True, "alpilab_check": True})
    local_app_registry.set_apps({"alpilab_check": app})
    launcher = MockProcessLauncher()
    configure_windows_app_tool(
        WindowsAppTool(registry=local_app_registry, launcher=launcher)
    )
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-check-open",
            "command_id": "cmd-check-open",
            "payload": {"tool_id": "windows.alpilab_check.open", "arguments": {}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is True
    assert result["result"]["started"] is True
    assert launcher.launches == [app.executable_path]


def test_rest_execute_rejects_without_agent(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/sessions/repair-x/agents/missing"
        "/tools/windows.alpilab_check.open/execute"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is False
    assert body["error"]
