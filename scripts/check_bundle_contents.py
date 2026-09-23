"""Fail a desktop bundle that contains GPL-only Qt modules or ASIO DLLs.

ARCHITECTURE_V1.md §6.2: a frozen tree must not ship GPL-only Qt modules or
``*asio*.dll``. PySide6 Essentials wheels still contain ``.pyi`` stubs and a
few QML / input plugins whose names match the ban list; those are ignored
only in ``--installed-essentials`` mode, which instead fails if Addons is
installed or a real GPL extension module is present.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, distribution
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

_BINARY_SUFFIXES = {".so", ".dll", ".dylib", ".pyd"}

# LGPL Essentials modules that a frozen app may ship. The gate bans GPL-only
# modules, not every Qt library beyond QtCore/QtGui/QtWidgets.
ALLOWED_HINT = "QtCore, QtGui, QtWidgets, QtDBus (Linux) and other PySide6 Essentials LGPL modules"


def _is_binary(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in _BINARY_SUFFIXES:
        return True
    # ``QtCharts.abi3.so`` uses suffix ``.so`` already; keep the extra check
    # for names like ``foo.abi3.so`` on case-insensitive volumes.
    return path.name.lower().endswith((".abi3.so", ".abi3.pyd"))


def _name_hits_gpl(name: str) -> str | None:
    lowered = name.lower()
    for banned in GPL_ONLY_QT:
        if banned.lower() in lowered:
            return banned
    return None


def _under_essentials_plugin_tree(path: Path, root: Path) -> bool:
    try:
        relative = path.relative_to(root).as_posix().lower()
    except ValueError:
        relative = path.as_posix().lower()
    return "/qt/plugins/" in f"/{relative}" or "/qt/qml/" in f"/{relative}"


def check(
    root: Path,
    *,
    require_licenses: bool = False,
    installed_essentials: bool = False,
) -> list[str]:
    errors: list[str] = []
    if not root.is_dir():
        return [f"not a directory: {root}"]
    if installed_essentials:
        try:
            distribution("PySide6_Addons")
        except PackageNotFoundError:
            pass
        else:
            errors.append("PySide6_Addons is installed; RoomScope must use PySide6_Essentials only")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name
        if path.suffix.lower() == ".dll" and "asio" in name.lower():
            errors.append(f"ASIO DLL present: {path}")
        if path.suffix.lower() == ".pyi":
            continue
        banned = _name_hits_gpl(name)
        if banned is None:
            continue
        if installed_essentials and not _is_binary(path):
            continue
        if installed_essentials and _under_essentials_plugin_tree(path, root):
            continue
        if not installed_essentials and not _is_binary(path) and path.suffix.lower() != ".py":
            continue
        errors.append(f"GPL-only Qt module present: {path}")
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
    parser.add_argument(
        "--installed-essentials",
        action="store_true",
        help="gate a PySide6_Essentials install (ignore wheel stubs and stock plugins)",
    )
    args = parser.parse_args(argv)
    errors = check(
        args.root,
        require_licenses=args.require_licenses,
        installed_essentials=args.installed_essentials,
    )
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"bundle gate passed for {args.root} ({ALLOWED_HINT})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
