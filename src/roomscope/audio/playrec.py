"""Simultaneous playback of the sweep and recording of the microphone.

Safety rules (docs/PROJECT_BRIEF.zh-CN.md, section 12): the default level is
conservative, the caller must show :data:`SAFETY_MESSAGE` before the first
measurement, and this module never changes system volume, device settings or
anything outside the stream it opens.
"""

from __future__ import annotations

import numpy as np

from roomscope.audio.devices import sounddevice_module
from roomscope.errors import AudioDeviceError, ConfigurationError
from roomscope.models.audio import AudioSignal, FloatArray

SAFETY_MESSAGE = (
    "Start with your monitor/interface output at a low level. RoomScope will play a "
    "sine sweep at a conservative digital level; raise the level gradually between "
    "measurements only if the recording is too quiet."
)
#: Levels above this need an explicit acknowledgement in the front end.
SAFE_MAX_LEVEL_DBFS = -12.0
DEFAULT_STANDALONE_LEVEL_DBFS = -20.0


def scale_to_level(signal: FloatArray, level_dbfs: float) -> FloatArray:
    """Return ``signal`` peak-normalised to ``level_dbfs``."""
    if level_dbfs > 0.0:
        raise ConfigurationError("playback level must be <= 0 dBFS")
    peak = float(np.max(np.abs(signal)))
    if peak <= 0.0:
        raise ConfigurationError("signal is silent")
    scale = float(10.0 ** (level_dbfs / 20.0) / peak)
    return np.asarray(np.asarray(signal, dtype=np.float64) * scale, dtype=np.float64)


def play_and_record(
    signal: FloatArray,
    sample_rate: int,
    *,
    input_device: int | None,
    output_device: int | None,
    input_channel: int = 1,
    output_channel: int = 1,
    level_dbfs: float = DEFAULT_STANDALONE_LEVEL_DBFS,
    extra_record_s: float = 0.0,
) -> AudioSignal:
    """Play ``signal`` on ``output_channel`` (1-based) while recording
    ``input_channel`` (1-based). Returns the mono recording.

    The stream is opened only for the duration of the measurement.
    """
    sd = sounddevice_module()
    if input_channel < 1 or output_channel < 1:
        raise ConfigurationError("channels are 1-based and must be >= 1")
    playback = scale_to_level(signal, level_dbfs)
    if extra_record_s > 0.0:
        playback = np.concatenate([playback, np.zeros(int(extra_record_s * sample_rate))])
    frames = np.ascontiguousarray(playback[:, np.newaxis], dtype=np.float32)
    try:
        recorded = sd.playrec(
            frames,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            input_mapping=[input_channel],
            output_mapping=[output_channel],
            device=(input_device, output_device),
            blocking=True,
        )
    except Exception as exc:
        raise AudioDeviceError(f"playback/recording failed: {exc}") from exc
    data = np.asarray(recorded, dtype=np.float64)
    if data.ndim == 2:
        data = data[:, 0]
    return AudioSignal(
        samples=np.ascontiguousarray(data), sample_rate=sample_rate, source="standalone"
    )
