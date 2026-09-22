"""User settings stored under ``$ROOMSCOPE_HOME/settings.json``.

Plain JSON written by this module so the CLI does not depend on Qt and no
configuration library is added (ARCHITECTURE_V1.md §5.10). Level
acknowledgements are never persisted.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from roomscope.errors import SessionError
from roomscope.io.recent import roomscope_home
from roomscope.models.loadutil import drop_unknown, read_schema_version

log = logging.getLogger("roomscope.settings")

SETTINGS_FILENAME = "settings.json"
SETTINGS_SCHEMA_VERSION = 1


@dataclass
class UserSettings:
    """Preferences that apply across sessions.

    ``language`` and ``audio_backend`` empty means "follow the environment /
    system default". ``copy_recording`` defaults to True (the GUI default).
    """

    schema_version: int = SETTINGS_SCHEMA_VERSION
    language: str = ""
    default_profile: str = "generic"
    audio_backend: str = ""
    output_dir: str = ""
    copy_recording: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserSettings:
        if not isinstance(data, dict):
            raise SessionError("settings data must be a JSON object")
        version = read_schema_version(data, SETTINGS_SCHEMA_VERSION, "settings")
        payload = drop_unknown(data, {f.name for f in fields(cls)}, kind="settings")
        payload["schema_version"] = version
        if "copy_recording" in payload:
            payload["copy_recording"] = bool(payload["copy_recording"])
        return cls(**payload)


def settings_path() -> Path:
    return roomscope_home() / SETTINGS_FILENAME


def load_settings() -> UserSettings:
    """Read settings, or the defaults when the file is missing or unreadable."""
    path = settings_path()
    if not path.is_file():
        return UserSettings()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        log.info("ignoring unreadable settings file %s: %s", path, exc)
        return UserSettings()
    if not isinstance(payload, dict):
        log.info("ignoring settings file %s: not a JSON object", path)
        return UserSettings()
    try:
        return UserSettings.from_dict(payload)
    except SessionError as exc:
        log.info("ignoring settings file %s: %s", path, exc)
        return UserSettings()


def save_settings(settings: UserSettings) -> Path:
    """Write ``settings.json``. Never stores a level acknowledgement."""
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = settings.to_dict()
    payload.pop("acknowledge_level", None)
    try:
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise SessionError(f"cannot write {path}: {exc}") from exc
    return path
