"""Structured process launcher — never uses shell=True or cmd.exe strings."""

from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)

# ShellExecuteW return values <= 32 indicate failure (Windows).
_SHELL_EXECUTE_SUCCESS_THRESHOLD = 32


class ProcessLauncher(Protocol):
    def start_executable(self, executable_path: str) -> "LaunchResult":
        ...


@dataclass(frozen=True)
class LaunchResult:
    started: bool
    already_running: bool = False
    pid: int | None = None


def is_image_running(image_name: str) -> bool:
    """True if a process with this image name is running (Windows tasklist; no shell)."""
    name = Path(image_name).name
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        return False
    if sys.platform != "win32":
        return False
    try:
        completed = subprocess.run(  # noqa: S603
            [
                "tasklist",
                "/FI",
                f"IMAGENAME eq {name}",
                "/FO",
                "CSV",
                "/NH",
            ],
            capture_output=True,
            text=True,
            shell=False,
            check=False,
            timeout=8,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    out = (completed.stdout or "").strip().lower()
    if not out or out.startswith("info:"):
        return False
    return name.lower() in out


class SubprocessLauncher:
    """Launch executables with platform-appropriate safe APIs."""

    def start_executable(self, executable_path: str) -> LaunchResult:
        exe = Path(executable_path)
        if not exe.is_file():
            raise RuntimeError(f"executable not found: {executable_path}")

        if is_image_running(exe.name):
            logger.info("Executable already running: %s", exe.name)
            return LaunchResult(started=False, already_running=True)

        if sys.platform == "win32":
            return self._start_windows(exe)

        return self._start_subprocess(exe)

    def _start_windows(self, exe: Path) -> LaunchResult:
        """Use ShellExecuteW with install directory — standard for Windows GUI apps."""
        import ctypes

        cwd = str(exe.resolve().parent)
        exe_path = str(exe.resolve())
        result = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None,
            "open",
            exe_path,
            None,
            cwd,
            1,  # SW_SHOWNORMAL
        )
        if int(result) <= _SHELL_EXECUTE_SUCCESS_THRESHOLD:
            logger.warning(
                "ShellExecuteW failed code=%s exe=%s cwd=%s",
                result,
                exe_path,
                cwd,
            )
            return self._start_subprocess(exe)

        logger.info("Started via ShellExecuteW: %s", exe_path)
        return LaunchResult(started=True)

    def _start_subprocess(self, exe: Path) -> LaunchResult:
        cwd = str(exe.resolve().parent)
        popen_kwargs: dict = {
            "args": [str(exe.resolve())],
            "shell": False,
            "cwd": cwd,
        }

        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            popen_kwargs["startupinfo"] = startupinfo
        else:
            popen_kwargs["stdin"] = subprocess.DEVNULL
            popen_kwargs["stdout"] = subprocess.DEVNULL
            popen_kwargs["stderr"] = subprocess.DEVNULL

        try:
            process = subprocess.Popen(**popen_kwargs)  # noqa: S603
        except OSError as exc:
            logger.exception("Failed to start executable: %s", exe)
            raise RuntimeError(f"process start failed: {exc}") from exc

        return LaunchResult(started=True, pid=process.pid)


class MockProcessLauncher:
    """Test double that records launches without starting processes."""

    def __init__(self, *, already_running: bool = False) -> None:
        self.launches: list[str] = []
        self.already_running = already_running

    def start_executable(self, executable_path: str) -> LaunchResult:
        self.launches.append(executable_path)
        if self.already_running:
            return LaunchResult(started=False, already_running=True)
        return LaunchResult(started=True, pid=99999)
