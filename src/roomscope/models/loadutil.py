"""Lenient JSON loading: unknown keys are ignored, schema versions are gated.

Readers accept every 1.x file they understand. A *higher* ``schema_version``
is refused with the running RoomScope version in the message. Unknown keys
are dropped and logged at INFO. Writers stay strict: ``to_dict`` output is
validated against the shipped schemas in the test suite, never at runtime.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from roomscope.errors import ConfigurationError, SessionError
from roomscope.version import __version__

log = logging.getLogger("roomscope.models")


def read_schema_version(data: Mapping[str, Any], known: int, kind: str) -> int:
    """Return the file's schema version, or raise if it is newer than ``known``."""
    raw = data.get("schema_version", known)
    try:
        version = int(raw)
    except (TypeError, ValueError) as exc:
        raise SessionError(f"{kind} schema_version is not an integer") from exc
    if version > known:
        raise SessionError(
            f"{kind} schema version {version} cannot be read by RoomScope {__version__}; "
            f"this version reads schema {known} and below. Open the file in a newer RoomScope."
        )
    return version


def drop_unknown(data: Mapping[str, Any], known: set[str], *, kind: str) -> dict[str, Any]:
    """Copy known keys only; log the rest at INFO."""
    unknown = sorted(set(data) - known)
    if unknown:
        log.info("ignoring unknown %s fields: %s", kind, unknown)
    return {key: data[key] for key in data if key in known}


def settings_payload(data: Mapping[str, Any], known: set[str], *, kind: str) -> dict[str, Any]:
    """Lenient payload for settings dataclasses (``ConfigurationError`` on bad types)."""
    if not isinstance(data, Mapping):
        raise ConfigurationError(f"{kind} must be a JSON object")
    return drop_unknown(data, known, kind=kind)


def record_payload(data: object, known: set[str], *, kind: str) -> dict[str, Any]:
    """:func:`drop_unknown` for a nested record read from a file.

    Raises :class:`SessionError` when ``data`` is not a JSON object.
    """
    if not isinstance(data, Mapping):
        raise SessionError(f"{kind} must be a JSON object")
    return drop_unknown(data, known, kind=kind)


def build_record[T](cls: type[T], payload: Mapping[str, Any], *, kind: str) -> T:
    """``cls(**payload)`` for data read from a file.

    A missing required field (``TypeError``) or a value the class rejects
    (``ValueError``) becomes :class:`SessionError`, so an untrusted file never
    surfaces a bare Python exception (#11).
    """
    try:
        return cls(**payload)
    except SessionError:
        raise
    except (TypeError, ValueError) as exc:
        raise SessionError(f"invalid {kind} in file: {exc}") from exc
