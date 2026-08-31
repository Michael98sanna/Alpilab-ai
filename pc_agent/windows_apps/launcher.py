"""Structured process launcher — never uses shell=True or cmd.exe strings."""

from __future__ import annotations

import logging
import os
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
class LaunchPlan:
    """
    How to open a configured Windows app.

    For .lnk configs (or .exe with a matching Desktop shortcut), launch the
    shortcut itself with no forced cwd — same as Explorer double-click.
    That preserves WorkingDirectory and any app identity used for saved login
    (important for WebView2 apps like Borneo).

    already-running detection always uses the real .exe image name.
    """

    launch_path: Path
    image_name: str
    working_directory: Path | None
    launch_via_shortcut: bool


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


def resolve_launch_target(executable_path: str | Path) -> LaunchPlan:
    """Build a launch plan from a trusted local config path (.exe or .lnk)."""
    path = Path(executable_path)
    if not path.is_file():
        raise RuntimeError(f"executable not found: {executable_path}")

    configured = path.resolve()

    if configured.suffix.lower() == ".lnk":
        target, work = _resolve_windows_shortcut(configured)
        image = target.name if target is not None and target.is_file() else configured.name
        work_dir = None  # Explorer uses the shortcut's own WorkingDirectory
        return LaunchPlan(
            launch_path=configured,
            image_name=image,
            working_directory=work_dir,
            launch_via_shortcut=True,
        )

    # Prefer a same-stem Desktop shortcut when present (Borneo login/profile).
    desktop_shortcut = Path.home() / "Desktop" / f"{configured.stem}.lnk"
    if desktop_shortcut.is_file():
        target, _work = _resolve_windows_shortcut(desktop_shortcut)
        # Only use the shortcut if it points at this same executable.
        if target is not None and target.resolve() == configured:
            logger.info(
                "Preferring Desktop shortcut for launch exe=%s shortcut=%s",
                configured,
                desktop_shortcut,
            )
            return LaunchPlan(
                launch_path=desktop_shortcut.resolve(),
                image_name=configured.name,
                working_directory=None,
                launch_via_shortcut=True,
            )

    return LaunchPlan(
        launch_path=configured,
        image_name=configured.name,
        working_directory=configured.parent,
        launch_via_shortcut=False,
    )


def _resolve_windows_shortcut(lnk_path: Path) -> tuple[Path | None, Path | None]:
    """Read TargetPath / WorkingDirectory from a .lnk via PowerShell COM (no shell)."""
    if sys.platform != "win32":
        return None, None

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
        plan = resolve_launch_target(executable_path)

        if is_image_running(plan.image_name):
            logger.info("Executable already running: %s", plan.image_name)
            return LaunchResult(started=False, already_running=True)

        if sys.platform == "win32":
            return self._start_windows(plan)

        return self._start_subprocess(plan)

    def _start_windows(self, plan: LaunchPlan) -> LaunchResult:
        """
        Open like Explorer double-click.

        For shortcuts: use os.startfile / ShellExecute on the .lnk with no cwd
        override so Borneo keeps its normal login/session behavior.
        """
        launch_path = str(plan.launch_path)

        if plan.launch_via_shortcut:
            try:
                # Closest equivalent to double-clicking the shortcut in Explorer.
                os.startfile(launch_path)  # noqa: S606
                logger.info(
                    "Started via os.startfile shortcut=%s image=%s",
                    launch_path,
                    plan.image_name,
                )
                return LaunchResult(started=True)
            except OSError as exc:
                logger.warning(
                    "os.startfile failed shortcut=%s error=%s; falling back to ShellExecuteW",
                    launch_path,
                    exc,
                )

        import ctypes

        cwd = None if plan.launch_via_shortcut else (
            str(plan.working_directory) if plan.working_directory else None
        )
        result = ctypes.windll.shell32.ShellExecuteW(  # type: ignore[attr-defined]
            None,
            "open",
            launch_path,
            None,
            cwd,
            1,  # SW_SHOWNORMAL
        )
        if int(result) <= _SHELL_EXECUTE_SUCCESS_THRESHOLD:
            logger.warning(
                "ShellExecuteW failed code=%s path=%s cwd=%s",
                result,
                launch_path,
                cwd,
            )
            if plan.launch_via_shortcut:
                raise RuntimeError(f"failed to open shortcut: {launch_path}")
            return self._start_subprocess(plan)

        logger.info(
            "Started via ShellExecuteW: %s cwd=%s image=%s shortcut=%s",
            launch_path,
            cwd or "(default)",
            plan.image_name,
            plan.launch_via_shortcut,
        )
        return LaunchResult(started=True)

    def _start_subprocess(self, plan: LaunchPlan) -> LaunchResult:
        if plan.launch_via_shortcut:
            raise RuntimeError("subprocess fallback cannot open .lnk shortcuts safely")

        exe = plan.launch_path
        cwd = str(plan.working_directory or exe.parent)
        popen_kwargs: dict = {
            "args": [str(exe)],
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
