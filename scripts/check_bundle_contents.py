"""Fail a desktop bundle that contains GPL-only Qt modules or ASIO DLLs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

GPL_ONLY_QT = (
    "QtCharts",
    "QtDataVisualization",
    "QtGraphs",
    "QtLottie",
    "QtQuickTimeline",
    "QtVirtualKeyboard",
    "QtQuick3D",
    "QtHttpServer",
    "QtNetworkAuth",
    "QtShaderTools",
)

# LGPL Essentials modules that a frozen app may ship. The gate bans GPL-only
# modules, not every Qt library beyond QtCore/QtGui/QtWidgets.
ALLOWED_HINT = "QtCore, QtGui, QtWidgets, QtDBus (Linux) and other PySide6 Essentials LGPL modules"


def check(root: Path, *, require_licenses: bool = False) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"not a directory: {root}"]
    for path in root.rglob("*"):
        name = path.name
        if path.suffix.lower() == ".dll" and "asio" in name.lower():
            errors.append(f"ASIO DLL present: {path}")
        for banned in GPL_ONLY_QT:
            if banned.lower() in name.lower():
                errors.append(f"GPL-only Qt module present: {path}")
                break
    if require_licenses:
        licenses = root / "THIRD_PARTY_LICENSES"
        if not licenses.is_dir():
            errors.append("THIRD_PARTY_LICENSES/ is missing")
        else:
            index = licenses / "INDEX.txt"
            if index.is_file() and "unresolved: none" not in index.read_text(encoding="utf-8"):
                errors.append("THIRD_PARTY_LICENSES/INDEX.txt lists unresolved packages")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="bundle or site-packages tree")
    parser.add_argument(
        "--require-licenses",
        action="store_true",
        help="require THIRD_PARTY_LICENSES/ with no unresolved packages",
    )
    args = parser.parse_args(argv)
    errors = check(args.root, require_licenses=args.require_licenses)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"bundle gate passed for {args.root} ({ALLOWED_HINT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
