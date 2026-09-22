"""Audio-backend protocol, device record and backend selection.

``core`` never imports this module. Front ends call :func:`get_backend` so
Standalone Mode can run against PortAudio or the synthetic ``fake`` backend.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np

from roomscope.errors import ConfigurationError
from roomscope.models.audio import AudioSignal, FloatArray
from roomscope.models.configuration import SUPPORTED_SAMPLE_RATES

SAFETY_MESSAGE = (
    "Start with your monitor/interface output at a low level. RoomScope will play a "
    "sine sweep at a conservative digital level; raise the level gradually between "
    "measurements only if the recording is too quiet."
)
#: Levels above this need an explicit acknowledgement in the front end.
SAFE_MAX_LEVEL_DBFS = -12.0
DEFAULT_STANDALONE_LEVEL_DBFS = -20.0
#: Block size used by the fake backend and as the PortAudio callback period
#: that Stop must silence within.
CALLBACK_BLOCK = 256
ENV_BACKEND = "ROOMSCOPE_AUDIO_BACKEND"


@dataclass(frozen=True)
class DeviceInfo:
    index: int
    name: str
    host_api: str
    max_input_channels: int
    max_output_channels: int
    default_sample_rate: float
    is_default_input: bool
    is_default_output: bool

    @property
    def is_input(self) -> bool:
        return self.max_input_channels > 0

    @property
    def is_output(self) -> bool:
        return self.max_output_channels > 0


class AudioBackend(Protocol):
    """Play a sweep and record one or more input channels."""

    name: str

    def list_devices(self) -> list[DeviceInfo]: ...

    def check_sample_rate(self, device: int, sample_rate: int, *, kind: str) -> None: ...

    def play_and_record(
        self,
        playback: FloatArray,
        sample_rate: int,
        *,
        input_device: int | None,
        output_device: int | None,
        input_channels: Sequence[int],
        output_channel: int,
        level_dbfs: float,
        extra_record_s: float = 0.0,
        progress: Callable[[float], None] | None = None,
        cancel: threading.Event | None = None,
    ) -> AudioSignal: ...


def scale_to_level(signal: FloatArray, level_dbfs: float) -> FloatArray:
    """Return ``signal`` peak-normalised to ``level_dbfs``."""
    if level_dbfs > 0.0:
        raise ConfigurationError("playback level must be <= 0 dBFS")
    peak = float(np.max(np.abs(signal)))
    if peak <= 0.0:
        raise ConfigurationError("signal is silent")
    scale = float(10.0 ** (level_dbfs / 20.0) / peak)
    return np.asarray(np.asarray(signal, dtype=np.float64) * scale, dtype=np.float64)


def prepare_playback(
    signal: FloatArray, sample_rate: int, level_dbfs: float, extra_record_s: float
) -> FloatArray:
    """Peak-normalise and optionally pad trailing silence."""
    playback = scale_to_level(signal, level_dbfs)
    if extra_record_s > 0.0:
        playback = np.concatenate(
            [playback, np.zeros(int(extra_record_s * sample_rate), dtype=np.float64)]
        )
    return np.asarray(playback, dtype=np.float64)


def get_backend(name: str | None = None) -> AudioBackend:
    """Return the named backend, settings, ``ROOMSCOPE_AUDIO_BACKEND``, or PortAudio."""
    chosen = name or os.environ.get(ENV_BACKEND)
    if not chosen:
        try:
            from roomscope.settings import load_settings

            chosen = load_settings().audio_backend
        except Exception:
            chosen = ""
    chosen = (chosen or "portaudio").strip().lower()
    if chosen == "fake":
        from roomscope.audio.fake import FakeBackend

        return FakeBackend()
    if chosen in {"portaudio", "sounddevice"}:
        from roomscope.audio.portaudio import PortAudioBackend

        return PortAudioBackend()
    raise ConfigurationError(f"unknown audio backend {chosen!r}; available: portaudio, fake")


def supported_sample_rate(sample_rate: int) -> None:
    if sample_rate not in SUPPORTED_SAMPLE_RATES:
        raise ConfigurationError(f"sample rate {sample_rate} Hz is not in {SUPPORTED_SAMPLE_RATES}")
