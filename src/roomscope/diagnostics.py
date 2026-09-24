"""Environment report for bug reports and debugging (``roomscope doctor``).

Everything a maintainer asks first: RoomScope's version, edition and build
(the commit a desktop bundle was built from), the Python and platform, the
versions of the libraries that carry the measurement (NumPy, SciPy,
libsndfile, PortAudio, Qt), the settings that change a measurement, where
RoomScope keeps its files, and which host APIs and devices PortAudio sees,
optionally with the sample rates each device accepts (probed; nothing is
played).

Nothing leaves the machine: the report is printed, or copied by the user.
Paths under the home folder are shown as ``~`` so the account name does not
end up in a public issue. Device names are kept because they identify the
hardware; they can contain a person's name ("Anna's AirPods"), and the report
says so.
"""

from __future__ import annotations

import json
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

#: Distribution name -> import name. A desktop bundle usually carries no
#: package metadata (PyInstaller copies it only when a hook asks), so the
#: module's own ``__version__`` is the fallback.
PACKAGES = {
    "numpy": "numpy",
    "scipy": "scipy",
    "soundfile": "soundfile",
    "sounddevice": "sounddevice",
    "matplotlib": "matplotlib",
    "PySide6_Essentials": "PySide6",
    "shiboken6": "shiboken6",
}

#: Written next to this module by packaging/roomscope.spec (desktop bundles only).
BUILD_INFO_FILENAME = "build_info.json"

PRIVACY_NOTE = (
    "Review before posting: device names can contain personal names; "
    "paths under your home folder are shown as ~."
)

#: Settings that change what a measurement does or how the app behaves.
#: ``output_dir`` is reported as set / not set, never as a path.
_SETTINGS_KEYS = (
    "language",
    "default_profile",
    "audio_backend",
    "copy_recording",
    "theme",
    "developer_tools",
)


def _package_version(name: str, module: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        pass
    try:
        found = getattr(_import(module), "__version__", None)
    except Exception:  # not installed, or its native library is missing
        return None
    return str(found) if found else None


def _import(module: str) -> Any:
    """Import one of :data:`PACKAGES` by its literal name (no computed imports)."""
    if module == "numpy":
        import numpy

        return numpy
    if module == "scipy":
        import scipy

        return scipy
    if module == "soundfile":
        import soundfile

        return soundfile
    if module == "sounddevice":
        import sounddevice

        return sounddevice
    if module == "matplotlib":
        import matplotlib

        return matplotlib
    if module == "PySide6":
        import PySide6

        return PySide6
    if module == "shiboken6":
        import shiboken6

        return shiboken6
    raise ImportError(module)


def _libsndfile_version() -> str | None:
    try:
        import soundfile

        return str(soundfile.__libsndfile_version__)
    except Exception:
        return None


def build_info(path: Path | None = None) -> dict[str, str] | None:
    """The commit (and CI run) a desktop bundle was built from; None otherwise."""
    path = path or Path(__file__).resolve().parent / BUILD_INFO_FILENAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    info = {key: str(data[key]) for key in ("commit", "ci_run") if data.get(key)}
    return info or None


def redact_home(path: str | Path, home: str | Path | None = None) -> str:
    """``path`` with the home folder replaced by ``~`` (the account name hidden)."""
    text = str(path)
    prefix = str(home if home is not None else Path.home()).rstrip("/\\")
    if not prefix:
        return text
    # Windows paths compare case-insensitively (C:\Users\Anna == c:\users\anna).
    fold = "\\" in prefix
    folded = text.casefold() if fold else text
    wanted = prefix.casefold() if fold else prefix
    if folded == wanted:
        return "~"
    for sep in ("/", "\\"):
        if folded.startswith(wanted + sep):
            return "~" + text[len(prefix) :]
    return text


def _settings_summary() -> dict[str, Any]:
    try:
        from roomscope.settings import load_settings

        settings = load_settings().to_dict()
    except Exception as exc:  # a broken settings file must not stop the report
        return {"error": str(exc)}
    summary = {key: settings.get(key) for key in _SETTINGS_KEYS}
    summary["output_dir_set"] = bool(settings.get("output_dir"))
    return summary


def environment_report(
    backend_name: str | None = None, *, probe_rates: bool = False
) -> dict[str, Any]:
    """The report as a JSON-ready dict; ``probe_rates`` asks every device for its rates."""
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
        "build": build_info(),
        "python": sys.version.split()[0],
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "language": current_locale(),
        "packages": {name: _package_version(name, module) for name, module in PACKAGES.items()},
        "libsndfile": _libsndfile_version(),
        "settings": _settings_summary(),
        "paths": {
            "roomscope_home": redact_home(roomscope_home()),
            "settings": redact_home(settings_path()),
            "log": redact_home(roomscope_home() / LOG_FILENAME),
        },
    }
    try:
        from roomscope.audio.backend import get_backend
        from roomscope.audio.inventory import build_inventory

        inventory = build_inventory(get_backend(backend_name), probe_rates=probe_rates)
    except Exception as exc:  # the report must print even without audio
        report["audio"] = {"error": str(exc)}
    else:
        report["audio"] = inventory.to_dict()
    return report


def _rates(rates: list[int]) -> str:
    return ", ".join(str(rate) for rate in rates) or "none"


def _format_devices(audio: dict[str, Any]) -> list[str]:
    probed = bool(audio.get("rates_probed"))
    lines = [
        "Devices (* default; sample rates accepted for 1 channel, nothing was played):"
        if probed
        else "Devices (* default; sample rates not probed, use roomscope doctor --probe):"
    ]
    for probe in audio.get("devices", []):
        device = probe["device"]
        star = " *" if device.get("is_default_input") or device.get("is_default_output") else ""
        lines.append(
            f"  [{device['index']:>2}] {device['name']}{star} | {device['host_api']} | "
            f"in {device['max_input_channels']} / out {device['max_output_channels']} | "
            f"default {device['default_sample_rate']:.0f} Hz"
        )
        details = []
        if probed and device["max_input_channels"] > 0:
            details.append(f"record {_rates(probe['input_rates'])}")
        if probed and device["max_output_channels"] > 0:
            details.append(f"play {_rates(probe['output_rates'])}")
        recommended = [
            name
            for name, flag in (
                ("input", probe.get("recommended_input")),
                ("output", probe.get("recommended_output")),
            )
            if flag
        ]
        if recommended:
            details.append("recommended " + " + ".join(recommended))
        if details:
            lines.append("       " + "; ".join(details))
    return lines


def format_environment_report(report: dict[str, Any]) -> str:
    build = report.get("build") or {}
    lines = [
        f"RoomScope {report['roomscope']} ({report['edition']} edition"
        + (", desktop bundle)" if report.get("frozen_bundle") else ")"),
        f"Build: {build.get('commit') or 'no commit recorded (source or pip install)'}",
    ]
    if build.get("ci_run"):
        lines.append(f"CI run: {build['ci_run']}")
    lines += [
        f"Python {report['python']} ({report['implementation']}) on {report['platform']} "
        f"[{report['machine']}]",
        f"Language: {report['language']}",
        "Packages:",
    ]
    for name, found in report["packages"].items():
        lines.append(f"  {name:<20} {found or 'not installed'}")
    lines.append(f"  {'libsndfile':<20} {report.get('libsndfile') or 'unknown'}")
    lines.append("Settings:")
    for key, value in report.get("settings", {}).items():
        lines.append(f"  {key:<20} {'-' if value in ('', None) else value}")
    lines.append("Paths:")
    for key, value in report["paths"].items():
        lines.append(f"  {key:<20} {value}")
    audio = report.get("audio", {})
    lines.append("Audio:")
    if "error" in audio:
        lines.append(f"  unavailable: {audio['error']}")
    else:
        devices = audio.get("devices", [])
        default_in = next(
            (p["device"]["name"] for p in devices if p["device"].get("is_default_input")), None
        )
        default_out = next(
            (p["device"]["name"] for p in devices if p["device"].get("is_default_output")), None
        )
        apis = ", ".join(
            f"{api['name']} ({api['device_count']})" for api in audio.get("host_apis", [])
        )
        lines.append(f"  backend              {audio.get('backend')}")
        lines.append(f"  PortAudio            {audio.get('portaudio_version') or '-'}")
        lines.append(f"  host APIs            {apis or '-'}")
        lines.append(f"  devices              {len(devices)}")
        lines.append(f"  default input        {default_in or '-'}")
        lines.append(f"  default output       {default_out or '-'}")
        for note in audio.get("notes", []):
            lines.append(f"  note: {note}")
        lines.extend(_format_devices(audio))
    lines.append("")
    lines.append(PRIVACY_NOTE)
    return "\n".join(lines)
