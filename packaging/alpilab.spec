# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ALPILAB AI.exe — run from repo root on Windows."""

from PyInstaller.utils.hooks import collect_submodules

hidden = []
for pkg in ("app", "pc_agent", "ai", "hub", "local_hub", "uvicorn", "fastapi", "starlette", "zeroconf"):
    hidden += collect_submodules(pkg)

a = Analysis(
    ["local_hub/__main__.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("frontend/dist", "frontend/dist"),
        ("pc_agent/windows_apps.json.example", "pc_agent"),
    ],
    hiddenimports=hidden + ["webview", "uvicorn.logging", "uvicorn.protocols.http.auto"],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
