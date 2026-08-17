"""Structured process launcher — never uses shell=True."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Protocol


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
        process = subprocess.Popen(  # noqa: S603
            [executable_path],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return LaunchResult(started=True, pid=process.pid)


class MockProcessLauncher:
    """Test double that records launches without starting processes."""

    def __init__(self) -> None:
        self.launches: list[str] = []

    def start_executable(self, executable_path: str) -> LaunchResult:
        self.launches.append(executable_path)
        return LaunchResult(started=True, pid=99999)
