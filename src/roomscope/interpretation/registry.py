"""Recording-profile registry: built-ins plus ``roomscope.profiles`` entry points."""

from __future__ import annotations

import logging
from typing import Any

from roomscope.errors import ConfigurationError
from roomscope.interpretation.profiles import (
    AcousticGuitarProfile,
    ChoirProfile,
    DrumsProfile,
    GenericProfile,
    RecordingProfile,
    RoomMicProfile,
    VocalProfile,
    VoiceOverProfile,
)

log = logging.getLogger("roomscope.interpretation")

_BUILTINS: dict[str, RecordingProfile] = {
    "generic": GenericProfile(),
    "vocal": VocalProfile(),
    "voiceover": VoiceOverProfile(),
    "acoustic_guitar": AcousticGuitarProfile(),
    "drums": DrumsProfile(),
    "room_mic": RoomMicProfile(),
    "choir": ChoirProfile(),
}


def _entry_points() -> dict[str, RecordingProfile]:
    found: dict[str, RecordingProfile] = {}
    try:
        from importlib.metadata import entry_points
    except ImportError:  # pragma: no cover
        return found
    for item in entry_points().select(group="roomscope.profiles"):
        if item.name in _BUILTINS or item.name in found:
            log.warning("ignoring third-party profile %r; name collides with a built-in", item.name)
            continue
        try:
            loaded = item.load()
        except Exception as exc:
            log.warning("profile %r failed to import: %s", item.name, exc)
            continue
        profile = loaded() if isinstance(loaded, type) else loaded
        found[item.name] = profile
    return found


def profile_origins() -> dict[str, str]:
    origins = {name: "builtin" for name in _BUILTINS}
    origins.update({name: "entry_point" for name in _entry_points()})
    return origins


def available_profiles() -> list[str]:
    return sorted({*_BUILTINS, *_entry_points()})


def get_profile(name: str) -> RecordingProfile:
    table: dict[str, Any] = {**_entry_points(), **_BUILTINS}
    try:
        return table[name]
    except KeyError as exc:
        raise ConfigurationError(
            f"unknown recording profile '{name}'; available: {available_profiles()}"
        ) from exc
