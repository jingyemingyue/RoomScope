"""List bundled native libraries and license files (ARCHITECTURE_V1.md §6.2).

Inspects installed distributions, or a downloaded ``.whl``. Used to close the
DEPENDENCIES.md §6 Linux/Windows wheel-content note before a bundle ships.
"""

from __future__ import annotations

import argparse
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path

REQUIRED = (
    "numpy",
    "scipy",
    "soundfile",
    "sounddevice",
    "matplotlib",
    "pillow",
)

_NATIVE_SUFFIXES = (".so", ".dll", ".dylib", ".pyd")
_LICENSE_NAMES = ("license", "copying", "notice", "authors")


@dataclass(frozen=True)
class PackageAudit:
    name: str
    version: str
    natives: tuple[str, ...]
    licenses: tuple[str, ...]
    asio: tuple[str, ...]
    ttconv: tuple[str, ...]


def _is_native(name: str) -> bool:
    low = name.replace("\\", "/").lower()
    return low.endswith(_NATIVE_SUFFIXES) or ".so." in Path(low).name


def _is_license(name: str) -> bool:
    base = Path(name.replace("\\", "/")).name.lower()
    return any(token in base for token in _LICENSE_NAMES)


def _from_names(name: str, version: str, names: Iterable[str]) -> PackageAudit:
    files = [n.replace("\\", "/") for n in names]
    natives = tuple(sorted(n for n in files if _is_native(n)))
    licenses = tuple(sorted(n for n in files if _is_license(n)))
    asio = tuple(n for n in natives if "asio" in n.lower())
    ttconv = tuple(n for n in files if "ttconv" in n.lower())
    return PackageAudit(name, version, natives, licenses, asio, ttconv)


def audit_installed(name: str) -> PackageAudit:
    dist = distribution(name)
    files = [str(item) for item in (dist.files or ())]
    return _from_names(name, dist.version, files)


def audit_wheel(path: Path) -> PackageAudit:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
    stem = path.name.split("-", 1)[0]
    version = path.name.split("-")[1] if "-" in path.name else ""
    return _from_names(stem, version, names)


def audit_required() -> list[PackageAudit]:
    found: list[PackageAudit] = []
    for name in REQUIRED:
        try:
            found.append(audit_installed(name))
        except PackageNotFoundError:
            continue
    return found


def bundled_shared_libs(audit: PackageAudit) -> tuple[str, ...]:
    """Shared libraries next to the package (``.libs``, ``_soundfile_data``, …)."""
    interesting: list[str] = []
    for name in audit.natives:
        low = name.lower()
        if any(
            part in low
            for part in (
                ".libs/",
                ".dylibs/",
                "_soundfile_data/",
                "_sounddevice_data/",
                "/qt/lib/",
            )
        ):
            interesting.append(name)
    return tuple(interesting)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path, help="inspect a downloaded .whl instead")
    args = parser.parse_args(argv)
    reports = [audit_wheel(args.wheel)] if args.wheel else audit_required()
    for item in reports:
        print(f"{item.name} {item.version}")
        print(f"  natives: {len(item.natives)}")
        for name in bundled_shared_libs(item):
            print(f"    {name}")
        if item.asio:
            print("  ASIO:")
            for name in item.asio:
                print(f"    {name}")
        if item.ttconv:
            print("  ttconv:")
            for name in item.ttconv:
                print(f"    {name}")
        print(f"  license files: {len(item.licenses)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
