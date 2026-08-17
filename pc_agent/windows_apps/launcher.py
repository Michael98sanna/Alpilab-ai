"""Structured process launcher — never uses shell=True."""

from __future__ import annotations

import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class ProcessLauncher(Protocol):
    def start_executable(self, executable_path: str) -> "LaunchResult":
        ...


@dataclass(frozen=True)
class LaunchResult:
    started: bool
    already_running: bool = False
    pid: int | None = None


class SubprocessLauncher:
    """Launch executables via subprocess.Popen without shell invocation."""

    def start_executable(self, executable_path: str) -> LaunchResult:
        exe = Path(executable_path)
        cwd = str(exe.parent)

        popen_kwargs: dict = {
            "args": [executable_path],
            "shell": False,
            "cwd": cwd,
        }

        if sys.platform == "win32":
            # GUI apps (e.g. 3uTools): detach from console, run from install directory.
            popen_kwargs["creationflags"] = (
                subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            popen_kwargs["stdin"] = subprocess.DEVNULL
            popen_kwargs["stdout"] = subprocess.DEVNULL
            popen_kwargs["stderr"] = subprocess.DEVNULL

        try:
            process = subprocess.Popen(**popen_kwargs)  # noqa: S603
        except OSError as exc:
            logger.exception("Failed to start executable: %s", executable_path)
            raise RuntimeError(f"process start failed: {exc}") from exc

        return LaunchResult(started=True, pid=process.pid)


class MockProcessLauncher:
    """Test double that records launches without starting processes."""

    def __init__(self) -> None:
        self.launches: list[str] = []

    def start_executable(self, executable_path: str) -> LaunchResult:
        self.launches.append(executable_path)
        return LaunchResult(started=True, pid=99999)
