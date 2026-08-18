"""Windowed frozen EXE: uvicorn must not crash when stdio is None."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest
import uvicorn

from local_hub.launcher import (
    _configure_hub_logging,
    _writable_stdio,
    hub_uvicorn_log_config,
)


@pytest.fixture(autouse=True)
def _restore_logging():
    root = logging.getLogger()
    handlers = list(root.handlers)
    level = root.level
    yield
    for handler in list(root.handlers):
        root.removeHandler(handler)
        handler.close()
    for handler in handlers:
        root.addHandler(handler)
    root.setLevel(level)


def test_writable_stdio_none_when_windowed(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    assert _writable_stdio() is None


def test_writable_stdio_prefers_stderr(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stderr", sys.__stderr__)
    monkeypatch.setattr(sys, "stdout", sys.__stdout__)
    assert _writable_stdio() is sys.__stderr__


def test_default_uvicorn_config_crashes_without_stdio(monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    with pytest.raises(ValueError, match="Unable to configure formatter 'default'"):
        uvicorn.Config("app.main:app", host="127.0.0.1", port=18100, log_level="info")


def test_hub_log_config_allows_uvicorn_with_none_stdio(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    log_path = tmp_path / "logs" / "hub.log"
    cfg = hub_uvicorn_log_config(log_path)
    assert "uvicorn.logging.DefaultFormatter" not in str(cfg)
    assert "console" not in cfg["handlers"]
    assert cfg["formatters"]["default"]["()"] == "logging.Formatter"

    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=18101,
        log_level="info",
        log_config=cfg,
    )
    logging.getLogger("uvicorn.error").info("hub-started")
    text = log_path.read_text(encoding="utf-8")
    assert "hub-started" in text
    assert "token" not in text.lower()
    assert config.log_config is not None


def test_hub_log_config_keeps_console_when_stdio_exists(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sys, "stderr", sys.__stderr__)
    cfg = hub_uvicorn_log_config(tmp_path / "hub.log")
    assert "console" in cfg["handlers"]
    assert cfg["handlers"]["console"]["stream"] is sys.__stderr__


def test_configure_hub_logging_file_only_when_windowed(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    log_path = tmp_path / "hub.log"
    _configure_hub_logging(log_path)
    logging.getLogger("alpilab.local_hub").info("sqlite-ready")
    assert "sqlite-ready" in log_path.read_text(encoding="utf-8")


def test_wait_hub_ready_uses_health() -> None:
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from threading import Thread

    from local_hub.launcher import _wait_hub_ready

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status":"ok"}')
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    port = int(server.server_address[1])
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        _wait_hub_ready(port, timeout=3.0)
    finally:
        server.shutdown()
