"""Smoke-test a desktop bundle or an on-PATH ``roomscope`` (ARCHITECTURE_V1.md §6.2).

Runs ``--version`` and a fake-backend Standalone measurement. Nothing is sent
to a loudspeaker.
"""

from __future__ import annotations

import argparse
import subprocess
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


def smoke(binary: Path, out: Path) -> None:
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="bundle directory (dist/roomscope)")
    parser.add_argument("--roomscope", type=Path, help="path to the roomscope binary")
    parser.add_argument("--out", type=Path, help="session output directory")
    args = parser.parse_args(argv)
    binary = find_binary(args.root, args.roomscope)
    out = args.out or Path("smoke-session")
    out.mkdir(parents=True, exist_ok=True)
    smoke(binary, out)
    print(f"smoke ok: {binary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
