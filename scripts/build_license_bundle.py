"""Build THIRD_PARTY_LICENSES/ for a desktop bundle (ARCHITECTURE_V1.md §6.2).

Copies license files from installed distributions, adds notices that the
wheels omit (Qt/PySide6, PortAudio, FreeType), and fails if a required
package still has no license text. matplotlib's old ``ttconv`` module is
treated as resolved: it is not present in matplotlib 3.8+.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

REQUIRED = [
    "numpy",
    "scipy",
    "soundfile",
    "sounddevice",
    "matplotlib",
    "cffi",
    "pycparser",
    "pillow",
    "contourpy",
    "cycler",
    "fonttools",
    "kiwisolver",
    "packaging",
    "pyparsing",
    "python-dateutil",
    "six",
]

OPTIONAL = ["PySide6_Essentials", "shiboken6", "PySide6"]

KNOWN_NOTICES = {
    "portaudio": (
        "PortAudio Portable Real-Time Audio Library\n"
        "Copyright (c) 1999-2011 Ross Bencina and Phil Burk\n\n"
        "Permission is hereby granted, free of charge, to any person obtaining\n"
        "a copy of this software and associated documentation files (the\n"
        "\"Software\"), to deal in the Software without restriction, including\n"
        "without limitation the rights to use, copy, modify, merge, publish,\n"
        "distribute, sublicense, and/or sell copies of the Software.\n\n"
        "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND.\n"
        "Source: http://www.portaudio.com/license.html\n"
    ),
    "freetype": (
        "This software uses FreeType (https://www.freetype.org/) under the\n"
        "FreeType License (FTL). FreeType appears in matplotlib, Pillow and Qt.\n"
        "Credit: Portions of this software are copyright (c) The FreeType Project\n"
        "(www.freetype.org). All rights reserved.\n"
    ),
    "qhull": (
        "Qhull (http://www.qhull.org/) is used by SciPy and matplotlib.\n"
        "Qhull is copyright (c) C.B. Barber and The Geometry Center.\n"
        "See the Qhull license shipped with SciPy / matplotlib.\n"
    ),
    "agg": (
        "Anti-Grain Geometry (AGG) is used by matplotlib.\n"
        "Copyright (c) 2002-2005 Maxim Shemanarev (McSeem).\n"
    ),
    "pyside6": (
        "This program uses Qt and PySide6 under the GNU Lesser General Public\n"
        "License version 3 (LGPL-3.0). Qt libraries are loaded as separate shared\n"
        "libraries and may be replaced by interface-compatible versions.\n\n"
        "Qt source: https://download.qt.io/official_releases/qt/\n"
        "PySide6 source: https://code.qt.io/cgit/pyside/pyside-setup.git/\n"
        "LGPL-3.0: https://www.gnu.org/licenses/lgpl-3.0.html\n"
        "GPL-3.0: https://www.gnu.org/licenses/gpl-3.0.html\n"
    ),
    "ttconv": (
        "matplotlib's historical ttconv TrueType converter is not present in\n"
        "matplotlib 3.8 and later (fonttools is used instead). RoomScope requires\n"
        "matplotlib>=3.8, so ttconv is not bundled. Status: resolved.\n"
    ),
}


def _license_files(name: str) -> list[tuple[str, bytes]]:
    try:
        dist = distribution(name)
    except PackageNotFoundError:
        return []
    found: list[tuple[str, bytes]] = []
    for file in dist.files or []:
        upper = file.name.upper()
        if file.parent.name.endswith(".dist-info") and any(
            token in upper for token in ("LICENSE", "LICENCE", "COPYING", "NOTICE")
        ):
            try:
                found.append((file.name, Path(file.locate()).read_bytes()))
            except OSError:
                continue
    return found


def build(out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    unresolved: list[str] = []
    for name in REQUIRED:
        files = _license_files(name)
        if not files:
            unresolved.append(name)
            continue
        dest = out / name
        dest.mkdir(exist_ok=True)
        for filename, data in files:
            (dest / filename).write_bytes(data)
    for name in OPTIONAL:
        files = _license_files(name)
        dest = out / name.replace(" ", "_")
        dest.mkdir(exist_ok=True)
        for filename, data in files:
            (dest / filename).write_bytes(data)
        if name.lower().startswith("pyside") or name == "shiboken6":
            (dest / "LGPL-NOTICE.txt").write_text(KNOWN_NOTICES["pyside6"], encoding="utf-8")
    extras = out / "_notices"
    extras.mkdir(exist_ok=True)
    for key, text in KNOWN_NOTICES.items():
        (extras / f"{key}.txt").write_text(text, encoding="utf-8")
    root = Path(__file__).resolve().parents[1]
    for name in ("LICENSE", "NOTICE"):
        src = root / name
        if src.is_file():
            (out / name).write_bytes(src.read_bytes())
    summary = out / "INDEX.txt"
    lines = [
        "RoomScope third-party license bundle",
        f"unresolved: {', '.join(unresolved) if unresolved else 'none'}",
        "ttconv: resolved (not present in matplotlib>=3.8)",
        "ASIO: Windows sounddevice ASIO DLLs must be stripped by check_bundle_contents.py",
    ]
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return unresolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="THIRD_PARTY_LICENSES directory")
    args = parser.parse_args(argv)
    unresolved = build(args.out)
    if unresolved:
        print("unresolved packages: " + ", ".join(unresolved), file=sys.stderr)
        return 1
    print(f"wrote {args.out} (no unresolved packages)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
