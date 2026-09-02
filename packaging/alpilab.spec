# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ALPILAB AI.exe.

PyInstaller executes this file with CWD = packaging/. All script/data/pathex
entries MUST be resolved from SPECPATH (this directory), not from ".".
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

_ROOT = Path(SPECPATH).resolve().parent


def _collect(pkg: str) -> list[str]:
    try:
        return collect_submodules(pkg)
    except Exception:
        return [pkg]


hidden = []
for pkg in (
    "app",
    "pc_agent",
    "ai",
    "local_hub",
    "uvicorn",
    "fastapi",
    "starlette",
    "zeroconf",
    "webview",
    "aiosqlite",
):
    hidden += _collect(pkg)

hidden += [
    "uvicorn.logging",
    "uvicorn.lifespan.on",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "app.realtime",
    "app.realtime.session_manager",
    "app.realtime.events",
    "app.realtime.payloads",
    "app.realtime.session_state",
    "app.realtime.state_sync",
    "app.realtime.persistence",
    "app.conversation",
    "app.conversation.engine",
    "app.conversation.natural_language_service",
    "app.conversation.user_messages",
]

datas = [
    (str(_ROOT / "frontend" / "dist"), "frontend/dist"),
    (str(_ROOT / "pc_agent" / "windows_apps.json.example"), "pc_agent"),
    (str(_ROOT / "config" / "llm_providers.yaml"), "config"),
]

a = Analysis(
    [str(_ROOT / "local_hub" / "__main__.py")],
    pathex=[str(_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=sorted(set(hidden)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ALPILAB AI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Windowed GUI (no black console). stdio may be None; launcher log_config
    # must not use uvicorn DefaultFormatter / isatty().
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
