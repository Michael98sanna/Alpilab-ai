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


@dataclass(frozen=True)
class ResolvedLaunchTarget:
    """Concrete process to start after optional .lnk resolution."""

    executable_path: Path
    working_directory: Path
    image_name: str


def is_image_running(image_name: str) -> bool:
    """True if a process with this image name is running (Windows tasklist; no shell)."""
    name = Path(image_name).name
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        return False
    if sys.platform != "win32":
        return False
    try:
        from pc_agent.win_no_console import windows_no_console_kwargs

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
            **windows_no_console_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    out = (completed.stdout or "").strip().lower()
    if not out or out.startswith("info:"):
        return False
    return name.lower() in out


def resolve_launch_target(executable_path: str | Path) -> ResolvedLaunchTarget:
    """
    Resolve a configured path to the real executable + working directory.

    For .lnk shortcuts, resolve TargetPath/WorkingDirectory so apps like Borneo
    start from their install folder (required for saved login session) and so
    already-running detection uses the real .exe image name.
    """
    path = Path(executable_path)
    if not path.is_file():
        raise RuntimeError(f"executable not found: {executable_path}")

    resolved = path.resolve()
    if resolved.suffix.lower() != ".lnk":
        return ResolvedLaunchTarget(
            executable_path=resolved,
            working_directory=resolved.parent,
            image_name=resolved.name,
        )

    target, working_directory = _resolve_windows_shortcut(resolved)
    if target is None or not target.is_file():
        # Last resort: open the .lnk itself, but do not force Desktop as cwd.
        logger.warning(
            "Could not resolve shortcut target; opening .lnk without forced cwd path=%s",
            resolved,
        )
        return ResolvedLaunchTarget(
            executable_path=resolved,
            working_directory=resolved.parent,
            image_name=resolved.name,
        )

    work = working_directory if working_directory and working_directory.is_dir() else target.parent
    return ResolvedLaunchTarget(
        executable_path=target,
        working_directory=work,
        image_name=target.name,
    )


def _resolve_windows_shortcut(lnk_path: Path) -> tuple[Path | None, Path | None]:
    """Read TargetPath / WorkingDirectory from a .lnk via PowerShell COM (no shell)."""
    if sys.platform != "win32":
        return None, None

    import os

    script = (
        "$s = New-Object -ComObject WScript.Shell; "
        "$k = $s.CreateShortcut($env:ALPILAB_LNK_PATH); "
        "Write-Output $k.TargetPath; "
        "Write-Output $k.WorkingDirectory"
    )
    env = os.environ.copy()
    env["ALPILAB_LNK_PATH"] = str(lnk_path)
    try:
        from pc_agent.win_no_console import windows_no_console_kwargs

        completed = subprocess.run(  # noqa: S603
            [
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            text=True,
            shell=False,
            check=False,
            timeout=10,
            env=env,
            **windows_no_console_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("Shortcut resolve failed path=%s error=%s", lnk_path, exc)
        return None, None

    if completed.returncode != 0:
        logger.warning(
            "Shortcut resolve non-zero path=%s code=%s stderr=%s",
            lnk_path,
            completed.returncode,
            (completed.stderr or "").strip()[:200],
        )
        return None, None

    lines = [line.strip() for line in (completed.stdout or "").splitlines() if line.strip()]
    if not lines:
        return None, None

    target = Path(lines[0]) if lines[0] else None
    work = Path(lines[1]) if len(lines) > 1 and lines[1] else None
    return target, work


class SubprocessLauncher:
    """Launch executables with platform-appropriate safe APIs."""

    def start_executable(self, executable_path: str) -> LaunchResult:
        target = resolve_launch_target(executable_path)

        if is_image_running(target.image_name):
            logger.info("Executable already running: %s", target.image_name)
            return LaunchResult(started=False, already_running=True)

        if sys.platform == "win32":
            return self._start_windows(target)

        return self._start_subprocess(target)

    def _start_windows(self, target: ResolvedLaunchTarget) -> LaunchResult:
        """Use ShellExecuteW with the resolved install directory."""
        import ctypes

        # For unresolved .lnk fallback, pass NULL directory so Windows uses
        # the shortcut's own WorkingDirectory (critical for Borneo login).
        use_null_cwd = target.executable_path.suffix.lower() == ".lnk"
        cwd = None if use_null_cwd else str(target.working_directory)
        exe_path = str(target.executable_path)

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
            return self._start_subprocess(target)

        logger.info(
            "Started via ShellExecuteW: %s cwd=%s image=%s",
            exe_path,
            cwd or "(shortcut-default)",
            target.image_name,
        )
        return LaunchResult(started=True)

    def _start_subprocess(self, target: ResolvedLaunchTarget) -> LaunchResult:
        cwd = str(target.working_directory)
        popen_kwargs: dict = {
            "args": [str(target.executable_path)],
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
            logger.exception("Failed to start executable: %s", target.executable_path)
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
