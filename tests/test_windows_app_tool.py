"""WindowsAppTool and windows.3utools.open tests — V0.3."""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from app.agent.execution_store import tool_execution_store
from app.agent.registry import agent_registry
from app.agent.payloads import AgentCapabilities
from app.security.tool_authorization import authorize_tool_execution
from app.tools.executable import (
    FORBIDDEN_REMOTE_ARGUMENT_KEYS,
    WINDOWS_3UTOOLS_OPEN_TOOL,
    validate_tool_arguments,
)
from app.tools.registry import default_tool_registry
from app.main import app
from pc_agent.commands import configure_dispatcher, handle_command
from pc_agent.tools.windows_handlers import configure_windows_app_tool
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


def _agent_connect(client: TestClient, session_id: str, agent_id: str = "agent-test-01"):
    return client.websocket_connect(
        f"/ws/agent/{session_id}?agent_id={agent_id}"
    )


def _register(ws, agent_id: str = "agent-test-01", *, windows_apps: bool = True) -> dict:
    ws.send_json(
        {
            "type": "register",
            "agent_id": agent_id,
            "agent_name": "ALPILAB-PC",
            "platform": "windows",
            "agent_version": "0.3.0",
            "capabilities": {
                "safe_test": True,
                "windows_apps": windows_apps,
                "alpilab_check": False,
                "microscope": False,
                "thermal_camera": False,
                "multimeter": False,
                "power_supply": False,
            },
            "status": "ONLINE",
        }
    )
    return ws.receive_json()


def _sample_app_config(tmp_path, *, dry_run: bool = True) -> WindowsApplicationConfig:
    exe = tmp_path / "3uTools.exe"
    exe.write_text("stub", encoding="utf-8")
    return WindowsApplicationConfig(
        app_id="3utools",
        name="3uTools",
        executable="3uTools.exe",
        executable_path=str(exe),
        enabled=True,
        dry_run=dry_run,
    )


# --- Server registry / authorization ---


def test_windows_3utools_open_registered() -> None:
    spec = default_tool_registry.get_executable("windows.3utools.open")
    assert spec is not None
    assert spec.tool_id == "windows.3utools.open"
    assert spec.enabled is True


def test_tool_lookup() -> None:
    assert default_tool_registry.resolve_executable("windows.3utools.open") is not None


def test_authorization_windows_apps_capability() -> None:
    auth = authorize_tool_execution(
        WINDOWS_3UTOOLS_OPEN_TOOL,
        AgentCapabilities(windows_apps=True),
    )
    assert auth.allowed is True


def test_authorization_missing_capability() -> None:
    auth = authorize_tool_execution(
        WINDOWS_3UTOOLS_OPEN_TOOL,
        AgentCapabilities(windows_apps=False),
    )
    assert auth.allowed is False
    assert auth.metadata.get("error") == "CAPABILITY_MISSING"


def test_disabled_tool_server() -> None:
    disabled = WINDOWS_3UTOOLS_OPEN_TOOL.model_copy(update={"enabled": False})
    default_tool_registry.register_executable(disabled)
    assert default_tool_registry.resolve_executable("windows.3utools.open") is None


def test_invalid_arguments_extra_keys() -> None:
    assert validate_tool_arguments(WINDOWS_3UTOOLS_OPEN_TOOL, {"foo": "bar"}) == "INVALID_ARGUMENTS"


def test_remote_path_rejected() -> None:
    for key in ("path", "executable", "executable_path", "shell_command", "command", "args"):
        assert (
            validate_tool_arguments(WINDOWS_3UTOOLS_OPEN_TOOL, {key: "evil"})
            == "INVALID_ARGUMENTS"
        )


def test_valid_empty_arguments() -> None:
    assert validate_tool_arguments(WINDOWS_3UTOOLS_OPEN_TOOL, {}) is None


def test_forbidden_keys_documented() -> None:
    assert "path" in FORBIDDEN_REMOTE_ARGUMENT_KEYS
    assert "executable_path" in FORBIDDEN_REMOTE_ARGUMENT_KEYS


def test_list_tools_includes_3utools(client: TestClient) -> None:
    tools = client.get("/api/v1/tools").json()["tools"]
    assert any(t["tool_id"] == "windows.3utools.open" for t in tools)


# --- PC Agent local ---


def test_local_app_registry_config_parsing(tmp_path, monkeypatch) -> None:
    config_file = tmp_path / "windows_apps.json"
    exe = tmp_path / "3uTools.exe"
    exe.write_text("stub", encoding="utf-8")
    config_file.write_text(
        f'{{"windows_apps": {{"3utools": {{"enabled": true, "executable_path": "{exe.as_posix()}", "dry_run": true}}}}}}',
        encoding="utf-8",
    )
    registry = LocalAppRegistry()
    registry.reload(str(config_file))
    app = registry.get("3utools")
    assert app is not None
    assert app.enabled is True
    assert app.dry_run is True


def test_app_disabled_local(tmp_path) -> None:
    app_cfg = _sample_app_config(tmp_path)
    disabled = WindowsApplicationConfig(
        app_id=app_cfg.app_id,
        name=app_cfg.name,
        executable=app_cfg.executable,
        executable_path=app_cfg.executable_path,
        enabled=False,
        dry_run=True,
    )
    registry = LocalAppRegistry()
    registry.set_apps({"3utools": disabled})
    tool = WindowsAppTool(registry=registry)
    with pytest.raises(WindowsAppToolError) as exc:
        tool.execute("windows.3utools.open")
    assert exc.value.code == "TOOL_DISABLED"


def test_missing_path(tmp_path) -> None:
    registry = LocalAppRegistry()
    registry.set_apps(
        {
            "3utools": WindowsApplicationConfig(
                app_id="3utools",
                name="3uTools",
                executable="3uTools.exe",
                executable_path="",
                enabled=True,
                dry_run=True,
            )
        }
    )
    tool = WindowsAppTool(registry=registry)
    with pytest.raises(WindowsAppToolError) as exc:
        tool.execute("windows.3utools.open")
    assert exc.value.code == "EXECUTABLE_NOT_FOUND"


def test_path_validation_missing_file(tmp_path) -> None:
    registry = LocalAppRegistry()
    registry.set_apps(
        {
            "3utools": WindowsApplicationConfig(
                app_id="3utools",
                name="3uTools",
                executable="3uTools.exe",
                executable_path=str(tmp_path / "missing.exe"),
                enabled=True,
                dry_run=True,
            )
        }
    )
    tool = WindowsAppTool(registry=registry)
    with pytest.raises(WindowsAppToolError) as exc:
        tool.execute("windows.3utools.open")
    assert exc.value.code == "EXECUTABLE_NOT_FOUND"


def test_dry_run_does_not_launch(tmp_path) -> None:
    launcher = MockProcessLauncher()
    registry = LocalAppRegistry()
    registry.set_apps({"3utools": _sample_app_config(tmp_path, dry_run=True)})
    tool = WindowsAppTool(registry=registry, launcher=launcher)
    result = tool.execute("windows.3utools.open")
    assert result["mode"] == "dry_run"
    assert result["validated"] is True
    assert result["would_execute"] is True
    assert result["app_id"] == "3utools"
    assert launcher.launches == []


def test_execution_mode_uses_mock_launcher(tmp_path) -> None:
    launcher = MockProcessLauncher()
    registry = LocalAppRegistry()
    registry.set_apps({"3utools": _sample_app_config(tmp_path, dry_run=False)})
    tool = WindowsAppTool(registry=registry, launcher=launcher)
    result = tool.execute("windows.3utools.open")
    assert result["mode"] == "execution"
    assert result["started"] is True
    assert len(launcher.launches) == 1


def test_unknown_app_tool_id() -> None:
    registry = LocalAppRegistry()
    registry.set_apps({})
    tool = WindowsAppTool(registry=registry)
    with pytest.raises(WindowsAppToolError) as exc:
        tool.execute("windows.borneo.open")
    assert exc.value.code == "APP_NOT_REGISTERED"


def test_pc_agent_capability_missing() -> None:
    configure_dispatcher({"windows_apps": False, "safe_test": True})
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-cap-win",
            "command_id": "cmd-cap-win",
            "payload": {"tool_id": "windows.3utools.open", "arguments": {}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "CAPABILITY_MISSING"


def test_pc_agent_invalid_arguments(tmp_path) -> None:
    configure_dispatcher({"windows_apps": True, "safe_test": True})
    local_app_registry.set_apps({"3utools": _sample_app_config(tmp_path)})
    configure_windows_app_tool(WindowsAppTool(registry=local_app_registry))
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-bad-win",
            "command_id": "cmd-bad-win",
            "payload": {"tool_id": "windows.3utools.open", "arguments": {"path": "C:\\evil.exe"}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "INVALID_ARGUMENTS"


def test_pc_agent_dry_run_via_handle_command(tmp_path) -> None:
    configure_dispatcher({"windows_apps": True, "safe_test": True})
    local_app_registry.set_apps({"3utools": _sample_app_config(tmp_path, dry_run=True)})
    configure_windows_app_tool(
        WindowsAppTool(registry=local_app_registry, launcher=MockProcessLauncher())
    )
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-dry-win",
            "command_id": "cmd-dry-win",
            "payload": {"tool_id": "windows.3utools.open", "arguments": {}},
        },
        "agent-local",
    )
    assert result is not None
    assert result["success"] is True
    assert result["result"]["mode"] == "dry_run"
    assert result["result"]["would_execute"] is True


# --- E2E ---


def _run_tool_pipeline(
    client: TestClient,
    ws_agent,
    session_id: str,
    tool_id: str,
    agent_id: str = "agent-test-01",
) -> dict:
    import asyncio

    from app.agent.gateway import agent_gateway

    async def send() -> None:
        await agent_gateway.send_tool_execute(
            session_id,
            agent_id,
            tool_id,
            {},
        )

    asyncio.run(send())
    cmd_msg = ws_agent.receive_json()
    assert cmd_msg["command"]["type"] == "TOOL_EXECUTE"
    assert cmd_msg["command"]["payload"]["tool_id"] == tool_id
    local = handle_command(cmd_msg["command"], agent_id)
    ws_agent.send_json(local)
    return local


def test_e2e_3utools_dry_run(client: TestClient, tmp_path) -> None:
    configure_dispatcher({"windows_apps": True, "safe_test": True})
    local_app_registry.set_apps({"3utools": _sample_app_config(tmp_path, dry_run=True)})
    configure_windows_app_tool(
        WindowsAppTool(registry=local_app_registry, launcher=MockProcessLauncher())
    )

    session_id = "repair-3utools-dry"
    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent, windows_apps=True)
        local = _run_tool_pipeline(
            client,
            ws_agent,
            session_id,
            "windows.3utools.open",
        )
        assert local["success"] is True
        assert local["result"]["mode"] == "dry_run"
        assert local["result"]["validated"] is True


def test_e2e_3utools_smartphone_broadcast(client: TestClient, tmp_path) -> None:
    configure_dispatcher({"windows_apps": True, "safe_test": True})
    local_app_registry.set_apps({"3utools": _sample_app_config(tmp_path, dry_run=True)})
    configure_windows_app_tool(
        WindowsAppTool(registry=local_app_registry, launcher=MockProcessLauncher())
    )

    session_id = "repair-3utools-rt"
    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent, windows_apps=True)
        with client.websocket_connect(
            f"/ws/sessions/{session_id}?device_id=phone-01&device_type=phone&device_name=Phone"
        ) as ws_phone:
            ws_phone.receive_json()
            _run_tool_pipeline(client, ws_agent, session_id, "windows.3utools.open")

            event_types: set[str] = set()
            for _ in range(3):
                msg = ws_phone.receive_json()
                if msg.get("type") == "event":
                    event_types.add(msg["event"]["event_type"])

            assert "TOOL_EXECUTION_STARTED" in event_types
            assert "TOOL_EXECUTION_COMPLETED" in event_types
            assert "TOOL_EXECUTE_RESULT" in event_types


def test_repair_session_audit_events(client: TestClient, tmp_path) -> None:
    from app.realtime.session_manager import realtime_manager

    configure_dispatcher({"windows_apps": True, "safe_test": True})
    local_app_registry.set_apps({"3utools": _sample_app_config(tmp_path, dry_run=True)})
    configure_windows_app_tool(
        WindowsAppTool(registry=local_app_registry, launcher=MockProcessLauncher())
    )

    session_id = "repair-3utools-audit"
    with _agent_connect(client, session_id) as ws_agent:
        _register(ws_agent, windows_apps=True)
        _run_tool_pipeline(client, ws_agent, session_id, "windows.3utools.open")
        types = {e.event_type.value for e in realtime_manager.events_for_session(session_id)}
        assert "TOOL_EXECUTION_STARTED" in types
        assert "TOOL_EXECUTE_RESULT" in types
