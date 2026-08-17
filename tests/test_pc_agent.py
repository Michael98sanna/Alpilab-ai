"""Unit tests for PC Agent client logic (no Windows required)."""

import json
import os
import tempfile

import pytest

from pc_agent.commands import ALLOWED_COMMANDS, handle_command, is_allowed_command
from pc_agent.config import AgentConfig
from pc_agent.identity import load_or_create_agent_id


def test_allowlist_only_agent_test() -> None:
    assert ALLOWED_COMMANDS == frozenset({"AGENT_TEST"})
    assert is_allowed_command("AGENT_TEST")
    assert not is_allowed_command("OPEN_APPLICATION")
    assert not is_allowed_command("EXECUTE_PROCESS")


def test_agent_test_response() -> None:
    result = handle_command(
        {
            "type": "AGENT_TEST",
            "request_id": "req-1",
            "command_id": "cmd-1",
        },
        "agent-abc",
    )
    assert result is not None
    assert result["type"] == "agent_test_result"
    assert result["success"] is True
    assert result["agent_id"] == "agent-abc"
    assert result["request_id"] == "req-1"


def test_unknown_command_rejection() -> None:
    result = handle_command(
        {"type": "RUN_COMMAND", "request_id": "req-2"},
        "agent-abc",
    )
    assert result is not None
    assert result["success"] is False
    assert result["error"] == "COMMAND_NOT_ALLOWED"


def test_malformed_command_no_request_id() -> None:
    result = handle_command({"type": "AGENT_TEST"}, "agent-abc")
    assert result is None


def test_persistent_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "identity.json")
        id1 = load_or_create_agent_id(path)
        id2 = load_or_create_agent_id(path)
        assert id1 == id2
        assert id1.startswith("agent-")


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALPILAB_WS_URL", "ws://localhost:9000")
    monkeypatch.setenv("ALPILAB_SESSION_ID", "repair-test")
    monkeypatch.setenv("ALPILAB_AGENT_NAME", "TEST-PC")
    cfg = AgentConfig.from_env()
    assert cfg.ws_url == "ws://localhost:9000"
    assert cfg.session_id == "repair-test"
    assert cfg.agent_name == "TEST-PC"
    assert "repair-test" in cfg.websocket_url("agent-x")


def test_registration_payload_shape() -> None:
    cfg = AgentConfig.from_env()
    payload = {
        "type": "register",
        "agent_id": "agent-test",
        "agent_name": cfg.agent_name,
        "capabilities": {
            "windows_apps": cfg.capabilities_windows_apps,
            "alpilab_check": cfg.capabilities_alpilab_check,
        },
    }
    assert payload["type"] == "register"
    assert json.dumps(payload)
