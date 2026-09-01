"""PC Agent handler tests for iPhone panic tools."""

from __future__ import annotations

import pytest

from pc_agent.commands import configure_dispatcher, handle_command
from pc_agent.tools.iphone_panic.handlers import handle_panic_analyze, handle_panic_check


@pytest.fixture(autouse=True)
def _configure_capabilities() -> None:
    configure_dispatcher({"iphone_panic": True, "safe_test": True})


def test_handle_check_registered_via_dispatcher() -> None:
    result = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-check-1",
            "command_id": "cmd-1",
            "payload": {
                "tool_id": "iphone.panic_log.check",
                "arguments": {},
            },
        },
        "agent-test",
    )
    assert result is not None
    assert result["tool_id"] == "iphone.panic_log.check"
    assert "success" in result


def test_handle_analyze_requires_force_flag() -> None:
    rejected = handle_command(
        {
            "type": "TOOL_EXECUTE",
            "request_id": "req-analyze-bad",
            "command_id": "cmd-2",
            "payload": {
                "tool_id": "iphone.panic_log.analyze",
                "arguments": {},
            },
        },
        "agent-test",
    )
    assert rejected is not None
    assert rejected["success"] is False
    assert rejected["error"] == "INVALID_ARGUMENTS"


def test_handle_analyze_direct() -> None:
    result = handle_panic_analyze({"force_reanalyze": False})
    assert isinstance(result, dict)
    assert result["status"] in {"success", "no_device", "no_panic", "error"}


def test_handle_check_direct() -> None:
    result = handle_panic_check({})
    assert isinstance(result, dict)
    assert result["status"] in {"success", "no_device", "no_panic", "error"}
