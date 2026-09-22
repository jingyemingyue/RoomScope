"""Error model for RoomScope.

Every error raised by RoomScope derives from :class:`RoomScopeError` so that
front ends (CLI, GUI) can distinguish expected failures (bad input, missing
device, insufficient data) from programming errors.
"""

from __future__ import annotations


class RoomScopeError(Exception):
    """Base class for all RoomScope errors."""


class ConfigurationError(RoomScopeError, ValueError):
    """A setting or parameter is invalid (wrong range, unsupported value)."""


class InvalidAudioError(RoomScopeError):
    """An audio file or signal cannot be used (unreadable, empty, silent, wrong format)."""


class SampleRateMismatchError(InvalidAudioError):
    """Reference and recording sample rates differ and cannot be reconciled."""


class AnalysisError(RoomScopeError):
    """The analysis pipeline could not produce a result."""


class InsufficientDataError(AnalysisError):
    """The data does not contain enough information for the requested metric."""


class AudioDeviceError(RoomScopeError):
    """An audio device operation (enumeration, playback, recording) failed."""


class AudioBackendUnavailableError(AudioDeviceError):
    """The optional audio backend (sounddevice / PortAudio) is not available."""


class MeasurementCancelledError(RoomScopeError):
    """Stop was pressed during playback; the output was silenced."""


class SessionError(RoomScopeError):
    """A measurement session could not be saved or loaded."""
