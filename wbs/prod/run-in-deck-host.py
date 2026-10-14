#!/usr/bin/env python3
"""World Builder Studio → ROM Launcher.

WBS is a Textual TUI, not a glass ROM. The launcher spawns this script with
no console (CREATE_NO_WINDOW), so we open a real console, then the studio
build / play chooser, then `python -m world_studio --textual`.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROD = Path(__file__).resolve().parent
WBS = PROD.parent
SRC = WBS / "src"
SCRIPT = Path(__file__).resolve()
TITLE = "World Builder Studio"


def _env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(SRC)
    prior = env.get("PYTHONPATH", "").strip()
    env["PYTHONPATH"] = src if not prior else src + os.pathsep + prior
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env["WBS_IN_CONSOLE"] = "1"
    return env


def _attached_tty() -> bool:
    out = getattr(sys, "stdout", None)
    if out is None:
        return False
    try:
        return bool(out.isatty())
    except Exception:
        return False


def _in_console_requested(argv: list[str]) -> bool:
    if os.environ.get("WBS_IN_CONSOLE", "").strip() in ("1", "true", "yes"):
        return True
    return "--in-console" in argv


def _mode_from(argv: list[str]) -> str | None:
    env_mode = os.environ.get("WBS_MODE", "").strip().lower()
    if env_mode in ("studio", "build", "play", "continue"):
        return "studio" if env_mode == "build" else env_mode
    if "--continue" in argv:
        return "continue"
    if "--play" in argv:
        return "play"
    if "--studio" in argv or "--build" in argv:
        return "studio"
    return None


def _tui_argv(mode: str) -> list[str]:
    cmd = [sys.executable, "-m", "world_studio", "--textual"]
    if mode == "play":
        cmd.append("--play")
    elif mode == "continue":
        cmd.extend(["--play", "--continue"])
    return cmd


def _choose_mode() -> str | None:
    print()
    print(TITLE)
    print("CO.WBS-001-STUDIO")
    print()
    print("  1  build      studio TUI")
    print("  2  play       new game (copy-on-play)")
    print("  3  continue   last play save")
    print("  q  quit")
    print()
    try:
        raw = input("› ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return None
    if raw in ("", "1", "b", "build", "studio"):
        return "studio"
    if raw in ("2", "p", "play"):
        return "play"
    if raw in ("3", "c", "continue"):
        return "continue"
    if raw in ("q", "quit", "exit"):
        return None
    print(f"unknown: {raw}")
    return _choose_mode()


def _set_console_title() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleTitleW(TITLE)
    except Exception:
        pass


def run_console(argv: list[str]) -> int:
    _set_console_title()
    if not SRC.is_dir():
        print(f"world_studio src missing: {SRC}", file=sys.stderr)
        return 1
    mode = _mode_from(argv)
    if mode is None:
        mode = _choose_mode()
    if mode is None:
        return 0
    cmd = _tui_argv(mode)
    code = subprocess.call(cmd, cwd=str(WBS), env=_env())
    if code != 0:
        try:
            input(f"exit {code} · enter to close ")
        except (EOFError, KeyboardInterrupt):
            pass
    return code


def spawn_console(argv: list[str]) -> int:
    """Open a visible console from a windowless ROM Launcher spawn.

    Do not use ``cmd /c start "title" …`` — ``start`` treats the first quoted
    token as the program name, which produced: cannot find '"World Builder Studio"'.
    CREATE_NEW_CONSOLE + close_fds gives the child its own conhost handles
    instead of inheriting the launcher's log pipe.
    """
    extra = [a for a in argv if a not in ("--in-console",)]
    flags = int(getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010))
    subprocess.Popen(
        [sys.executable, str(SCRIPT), "--in-console", *extra],
        cwd=str(WBS),
        env=_env(),
        creationflags=flags,
        close_fds=True,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if _in_console_requested(argv) or _attached_tty():
        return run_console(argv)
    if sys.platform == "win32":
        return spawn_console(argv)
    return run_console(argv)


if __name__ == "__main__":
    raise SystemExit(main())
