"""Tests for opt-in Alpilab Check local launcher config."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from local_hub.alpilab_check_config import (
    CAP_ENV,
    SECRET_PATH_ENV,
    apply_alpilab_check_env,
)


def _write_config(path: Path, payload: dict | str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload), encoding="utf-8")


def test_config_absent_does_not_set_capability(tmp_path: Path) -> None:
    env: dict[str, str] = {}
    ok = apply_alpilab_check_env(config_path=tmp_path / "missing.json", environ=env)
    assert ok is False
    assert CAP_ENV not in env
    assert SECRET_PATH_ENV not in env


def test_enabled_false_does_not_set_capability(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("bridge-secret-value", encoding="utf-8")
    cfg = tmp_path / "alpilab_check.json"
    _write_config(
        cfg,
        {"enabled": False, "bridge_secret_path": str(secret)},
    )
    env: dict[str, str] = {}
    ok = apply_alpilab_check_env(config_path=cfg, environ=env)
    assert ok is False
    assert CAP_ENV not in env
    assert SECRET_PATH_ENV not in env


def test_enabled_true_with_valid_secret_sets_env(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("bridge-secret-value", encoding="utf-8")
    cfg = tmp_path / "alpilab_check.json"
    _write_config(
        cfg,
        {"enabled": True, "bridge_secret_path": str(secret)},
    )
    env: dict[str, str] = {}
    ok = apply_alpilab_check_env(config_path=cfg, environ=env)
    assert ok is True
    assert env[CAP_ENV] == "true"
    assert env[SECRET_PATH_ENV] == str(secret)


def test_setdefault_preserves_existing_env(tmp_path: Path) -> None:
    secret = tmp_path / "secret.txt"
    secret.write_text("bridge-secret-value", encoding="utf-8")
    other_secret = tmp_path / "other-secret.txt"
    other_secret.write_text("other", encoding="utf-8")
    cfg = tmp_path / "alpilab_check.json"
    _write_config(
        cfg,
        {"enabled": True, "bridge_secret_path": str(secret)},
    )
    env = {
        CAP_ENV: "false",
        SECRET_PATH_ENV: str(other_secret),
    }
    ok = apply_alpilab_check_env(config_path=cfg, environ=env)
    assert ok is True
    assert env[CAP_ENV] == "false"
    assert env[SECRET_PATH_ENV] == str(other_secret)


def test_invalid_json_does_not_crash(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    cfg = tmp_path / "alpilab_check.json"
    _write_config(cfg, "{not-json")
    env: dict[str, str] = {}
    with caplog.at_level(logging.WARNING, logger="alpilab.local_hub"):
        ok = apply_alpilab_check_env(config_path=cfg, environ=env)
    assert ok is False
    assert CAP_ENV not in env
    assert any("invalid" in r.message.lower() for r in caplog.records)


def test_missing_secret_path_disables_capability(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    cfg = tmp_path / "alpilab_check.json"
    _write_config(cfg, {"enabled": True})
    env: dict[str, str] = {}
    with caplog.at_level(logging.WARNING, logger="alpilab.local_hub"):
        ok = apply_alpilab_check_env(config_path=cfg, environ=env)
    assert ok is False
    assert CAP_ENV not in env
    assert SECRET_PATH_ENV not in env
    assert any("bridge_secret_path" in r.message for r in caplog.records)


def test_nonexistent_secret_file_disables_capability(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    cfg = tmp_path / "alpilab_check.json"
    _write_config(
        cfg,
        {
            "enabled": True,
            "bridge_secret_path": str(tmp_path / "does-not-exist.txt"),
        },
    )
    env: dict[str, str] = {}
    with caplog.at_level(logging.WARNING, logger="alpilab.local_hub"):
        ok = apply_alpilab_check_env(config_path=cfg, environ=env)
    assert ok is False
    assert CAP_ENV not in env
    assert SECRET_PATH_ENV not in env
    assert any("missing or unreadable" in r.message for r in caplog.records)


def test_secret_content_never_appears_in_logs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    secret_value = "SUPER-SECRET-TOKEN-DO-NOT-LEAK"
    secret = tmp_path / "secret.txt"
    secret.write_text(secret_value, encoding="utf-8")
    cfg = tmp_path / "alpilab_check.json"
    _write_config(
        cfg,
        {"enabled": True, "bridge_secret_path": str(secret)},
    )
    env: dict[str, str] = {}
    with caplog.at_level(logging.DEBUG, logger="alpilab.local_hub"):
        apply_alpilab_check_env(config_path=cfg, environ=env)
        bad = tmp_path / "bad.json"
        _write_config(bad, "{broken")
        apply_alpilab_check_env(config_path=bad, environ={})
    joined = "\n".join(r.getMessage() for r in caplog.records)
    assert secret_value not in joined


def test_configure_local_env_invokes_apply_alpilab_check_env() -> None:
    """Launcher wires opt-in config into _configure_local_env without env side effects."""
    import inspect

    from local_hub import launcher as launcher_mod

    source = inspect.getsource(launcher_mod._configure_local_env)
    assert "apply_alpilab_check_env()" in source

