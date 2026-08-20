"""Tests for V0.6 Windows auto-start and single-instance behavior."""

from __future__ import annotations

import socket
import sys
from pathlib import Path
from types import SimpleNamespace

from local_hub.single_instance import (
    acquire_single_instance_lock,
    release_single_instance_lock,
)
from local_hub.user_config import DEFAULT_CONFIG
from local_hub.windows_startup import ensure_windows_autostart


def test_default_config_includes_start_with_windows() -> None:
    assert DEFAULT_CONFIG["start_with_windows"] is True


def test_single_instance_lock_reentrant_same_process() -> None:
    try:
        assert acquire_single_instance_lock() is True
        # Same process should behave idempotently.
        assert acquire_single_instance_lock() is True
    finally:
        release_single_instance_lock()


def test_single_instance_lock_detects_existing_instance() -> None:
    holder = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    holder.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    holder.bind(("127.0.0.1", 45879))
    holder.listen(1)
    try:
        assert acquire_single_instance_lock() is False
    finally:
        holder.close()
        release_single_instance_lock()


def test_windows_autostart_noop_on_non_windows(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "linux")
    ensure_windows_autostart(True)  # no exception


def test_windows_autostart_enable_disable(monkeypatch) -> None:
    monkeypatch.setattr(sys, "platform", "win32")
    calls: list[tuple] = []
    values: dict[str, str] = {}

    class _FakeKey:
        def __enter__(self):  # noqa: D401
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001, D401
            return False

    def open_key(*_args, **_kwargs):
        return _FakeKey()

    def query_value(_key, name):
        if name not in values:
            raise FileNotFoundError()
        return values[name], 1

    def set_value(_key, name, *_args):
        value = _args[-1]
        values[name] = value
        calls.append(("set", name, value))

    def delete_value(_key, name):
        if name not in values:
            raise FileNotFoundError()
        values.pop(name)
        calls.append(("del", name))

    fake_winreg = SimpleNamespace(
        HKEY_CURRENT_USER=1,
        KEY_ALL_ACCESS=1,
        REG_SZ=1,
        OpenKey=open_key,
        QueryValueEx=query_value,
        SetValueEx=set_value,
        DeleteValue=delete_value,
    )
    monkeypatch.setitem(sys.modules, "winreg", fake_winreg)

    ensure_windows_autostart(True)
    assert calls and calls[0][0] == "set"
    command = calls[0][2]
    assert command.startswith('"') and command.endswith('"')

    # Idempotent second call should not write again.
    calls.clear()
    ensure_windows_autostart(True)
    assert calls == []

    ensure_windows_autostart(False)
    assert ("del", "ALPILAB AI") in calls


def test_launcher_disables_access_log_to_avoid_token_leaks() -> None:
    src = (
        Path(__file__).resolve().parent.parent / "local_hub" / "launcher.py"
    ).read_text(encoding="utf-8")
    assert "access_log=False" in src
