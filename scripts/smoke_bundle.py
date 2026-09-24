"""Smoke-test a desktop bundle or an on-PATH ``roomscope`` (ARCHITECTURE_V1.md §6.2).

Runs ``--version``, a fake-backend Standalone measurement, and ``gui --smoke``
offscreen, then ``gui --smoke`` through the windowed ``roomscope-gui``
launcher when the bundle has one (Windows, Linux), and starts that launcher
without arguments, as a double-click does, requiring the GUI to stay open.
Nothing is sent to a loudspeaker.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from pathlib import Path


def find_binary(root: Path | None, explicit: Path | None) -> Path:
    if explicit is not None:
        return explicit
    if root is not None:
        for name in ("roomscope", "roomscope.exe"):
            candidate = root / name
            if candidate.is_file():
                return candidate
        for app in (
            root / "RoomScope.app" / "Contents" / "MacOS" / "roomscope",
            root.parent / "RoomScope.app" / "Contents" / "MacOS" / "roomscope",
        ):
            if app.is_file():
                return app
    from shutil import which

    found = which("roomscope")
    if found:
        return Path(found)
    raise SystemExit("roomscope binary not found; pass --root or --roomscope")


def smoke_gui_argv(binary: Path) -> list[str]:
    return [str(binary), "gui", "--smoke"]


def find_gui_launcher(binary: Path) -> Path | None:
    """The windowed ``roomscope-gui`` next to the console binary, if any."""
    for name in ("roomscope-gui", "roomscope-gui.exe"):
        candidate = binary.parent / name
        if candidate.is_file():
            return candidate
    return None


#: A desktop launch (no arguments) must still be running after this long:
#: the GUI's event loop, not a usage message that exits at once.
DESKTOP_LAUNCH_WAIT_S = 6.0


def check_stays_open(
    argv: list[str], env: dict[str, str], *, seconds: float = DESKTOP_LAUNCH_WAIT_S
) -> None:
    """Start ``argv`` like a double-click does and require it to keep running."""
    with subprocess.Popen(argv, env=env) as process:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise SystemExit(
                    f"desktop launch of {argv[0]} exited at once (code {process.returncode}); "
                    "a launch without arguments must open the GUI"
                )
            time.sleep(0.2)
        process.terminate()
        try:
            process.wait(timeout=15)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def smoke(binary: Path, out: Path, *, gui: bool = True, require_gui_launcher: bool = False) -> None:
    version = subprocess.run([str(binary), "--version"], check=True, capture_output=True, text=True)
    if "roomscope" not in version.stdout.lower() and "roomscope" not in version.stderr.lower():
        raise SystemExit(f"--version did not name roomscope: {version.stdout!r}")
    subprocess.run(
        [
            str(binary),
            "--backend",
            "fake",
            "measure",
            "--out",
            str(out),
            "--duration",
            "2",
            "--post-silence",
            "1.5",
            "--level",
            "-20",
        ],
        check=True,
    )
    if not (out / "session.json").is_file() and not any(out.rglob("session.json")):
        raise SystemExit(f"fake measure did not write session.json under {out}")
    if gui:
        env = os.environ.copy()
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        subprocess.run(smoke_gui_argv(binary), check=True, env=env, timeout=120)
        launcher = find_gui_launcher(binary)
        if launcher is None and require_gui_launcher:
            raise SystemExit(f"no roomscope-gui launcher next to {binary}")
        if launcher is not None:
            subprocess.run(smoke_gui_argv(launcher), check=True, env=env, timeout=120)
            # What Explorer, the Start menu, AppRun and the desktop file do.
            check_stays_open([str(launcher)], env)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="bundle directory (dist/roomscope)")
    parser.add_argument("--roomscope", type=Path, help="path to the roomscope binary")
    parser.add_argument("--out", type=Path, help="session output directory")
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="skip the offscreen GUI smoke (CLI-only binaries)",
    )
    parser.add_argument(
        "--require-gui-launcher",
        action="store_true",
        help="fail when the windowed roomscope-gui launcher is missing (Windows, Linux)",
    )
    args = parser.parse_args(argv)
    binary = find_binary(args.root, args.roomscope)
    out = args.out or Path("smoke-session")
    out.mkdir(parents=True, exist_ok=True)
    smoke(binary, out, gui=not args.no_gui, require_gui_launcher=args.require_gui_launcher)
    print(f"smoke ok: {binary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
