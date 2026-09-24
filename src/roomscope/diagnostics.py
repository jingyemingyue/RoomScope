"""Environment report for bug reports and debugging (``roomscope doctor``).

Everything a maintainer asks first: RoomScope's version and edition, the
Python and platform, the versions of the libraries that carry the
measurement (NumPy, SciPy, libsndfile, PortAudio, Qt), where RoomScope keeps
its files, and which host APIs and devices PortAudio sees. Nothing leaves the
machine; the report is printed.
"""

from __future__ import annotations

import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

PACKAGES = (
    "numpy",
    "scipy",
    "soundfile",
    "sounddevice",
    "matplotlib",
    "PySide6_Essentials",
    "shiboken6",
)


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def _libsndfile_version() -> str | None:
    try:
        import soundfile

        return str(soundfile.__libsndfile_version__)
    except Exception:
        return None


def environment_report(backend_name: str | None = None) -> dict[str, Any]:
    from roomscope import __version__
    from roomscope.edition import edition
    from roomscope.i18n import current_locale
    from roomscope.io.recent import roomscope_home
    from roomscope.logging_config import LOG_FILENAME
    from roomscope.settings import settings_path

    report: dict[str, Any] = {
        "roomscope": __version__,
        "edition": edition(),
        "frozen_bundle": bool(getattr(sys, "frozen", False)),
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "language": current_locale(),
        "packages": {name: _package_version(name) for name in PACKAGES},
        "libsndfile": _libsndfile_version(),
        "paths": {
            "roomscope_home": str(roomscope_home()),
            "settings": str(settings_path()),
            "log": str(roomscope_home() / LOG_FILENAME),
        },
    }
    try:
        from roomscope.audio.backend import get_backend
        from roomscope.audio.inventory import build_inventory

        inventory = build_inventory(get_backend(backend_name), probe_rates=False)
    except Exception as exc:  # the report must print even without audio
        report["audio"] = {"error": str(exc)}
    else:
        report["audio"] = {
            "backend": inventory.backend,
            "portaudio": inventory.portaudio_version,
            "host_apis": [
                {"name": api.name, "devices": api.device_count} for api in inventory.host_apis
            ],
            "devices": len(inventory.devices),
            "default_input": next(
                (p.device.name for p in inventory.devices if p.device.is_default_input), None
            ),
            "default_output": next(
                (p.device.name for p in inventory.devices if p.device.is_default_output), None
            ),
        }
    return report


def format_environment_report(report: dict[str, Any]) -> str:
    lines = [
        f"RoomScope {report['roomscope']} ({report['edition']} edition"
        + (", desktop bundle)" if report.get("frozen_bundle") else ")"),
        f"Python {report['python']} ({report['implementation']}) on {report['platform']} "
        f"[{report['machine']}]",
        f"Language: {report['language']}",
        "Packages:",
    ]
    for name, found in report["packages"].items():
        lines.append(f"  {name:<20} {found or 'not installed'}")
    lines.append(f"  {'libsndfile':<20} {report.get('libsndfile') or 'unknown'}")
    lines.append("Paths:")
    for key, value in report["paths"].items():
        lines.append(f"  {key:<20} {value}")
    audio = report.get("audio", {})
    lines.append("Audio:")
    if "error" in audio:
        lines.append(f"  unavailable: {audio['error']}")
    else:
        lines.append(f"  backend              {audio.get('backend')}")
        lines.append(f"  PortAudio            {audio.get('portaudio') or '-'}")
        apis = ", ".join(f"{api['name']} ({api['devices']})" for api in audio.get("host_apis", []))
        lines.append(f"  host APIs            {apis or '-'}")
        lines.append(f"  devices              {audio.get('devices')}")
        lines.append(f"  default input        {audio.get('default_input') or '-'}")
        lines.append(f"  default output       {audio.get('default_output') or '-'}")
    return "\n".join(lines)
