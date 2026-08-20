"""Windows no-console subprocess helpers for discovery / ADB / tasklist."""

from __future__ import annotations

import subprocess
import sys
from unittest.mock import patch

import pytest

from app.hub import discovery as discovery_mod
from pc_agent.win_no_console import windows_no_console_kwargs
from pc_agent.windows_apps.launcher import is_image_running


def test_windows_no_console_kwargs_shape() -> None:
    flags = windows_no_console_kwargs()
    if sys.platform == "win32":
        assert flags["creationflags"] == subprocess.CREATE_NO_WINDOW
        assert flags["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW
        assert flags["startupinfo"].wShowWindow == 0
    else:
        assert flags == {}


def test_enumerate_windows_hides_powershell() -> None:
    if sys.platform != "win32":
        pytest.skip("Windows only")

    captured: dict = {}

    def fake_run(cmd, **kwargs):  # noqa: ANN001
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs

        class _R:
            returncode = 0
            stdout = "[]"
            stderr = ""

        return _R()

    with patch("subprocess.run", side_effect=fake_run):
        discovery_mod._enumerate_windows()

    assert captured["cmd"][0].lower() == "powershell"
    assert "-WindowStyle" in captured["cmd"]
    assert captured["kwargs"].get("creationflags") == subprocess.CREATE_NO_WINDOW
    assert "startupinfo" in captured["kwargs"]
    assert captured["kwargs"]["startupinfo"].wShowWindow == 0


def test_is_image_running_hides_tasklist() -> None:
    if sys.platform != "win32":
        pytest.skip("Windows only")

    captured: dict = {}

    def fake_run(cmd, **kwargs):  # noqa: ANN001
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs

        class _R:
            returncode = 0
            stdout = ""
            stderr = ""

        return _R()

    with patch("subprocess.run", side_effect=fake_run):
        assert is_image_running("AlpilabCheck.exe") is False

    assert captured["cmd"][0].lower() == "tasklist"
    assert captured["kwargs"].get("creationflags") == subprocess.CREATE_NO_WINDOW
    assert "startupinfo" in captured["kwargs"]
