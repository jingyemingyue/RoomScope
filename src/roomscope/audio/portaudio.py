"""PortAudio backend: callback stream with progress and immediate Stop."""

from __future__ import annotations

import threading
from collections.abc import Callable, Sequence

import numpy as np

from roomscope.audio.backend import CALLBACK_BLOCK, DeviceInfo, prepare_playback
from roomscope.audio.devices import check_sample_rate, list_devices, sounddevice_module
from roomscope.errors import AudioDeviceError, ConfigurationError, MeasurementCancelledError
from roomscope.models.audio import AudioSignal, FloatArray


class PortAudioBackend:
    """sounddevice / PortAudio implementation of :class:`AudioBackend`."""

    name = "portaudio"

    def list_devices(self) -> list[DeviceInfo]:
        return list_devices()

    def check_sample_rate(self, device: int, sample_rate: int, *, kind: str) -> None:
        check_sample_rate(device, sample_rate, kind=kind)

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
    ) -> AudioSignal:
        if not input_channels:
            raise ConfigurationError("at least one input channel is required")
        if any(ch < 1 for ch in input_channels) or output_channel < 1:
            raise ConfigurationError("channels are 1-based and must be >= 1")
        sd = sounddevice_module()
        signal = prepare_playback(playback, sample_rate, level_dbfs, extra_record_s)
        n_in = max(input_channels)
        n_out = output_channel
        frames_total = int(signal.shape[0])
        recorded = np.zeros((frames_total, len(input_channels)), dtype=np.float64)
        play_idx = 0
        finished = threading.Event()
        callback_error: list[BaseException] = []

        def callback(
            indata: np.ndarray,
            outdata: np.ndarray,
            frames: int,
            _time: object,
            _status: object,
        ) -> None:
            nonlocal play_idx
            # Silence first: Stop must zero the output in this callback period.
            outdata.fill(0)
            if cancel is not None and cancel.is_set():
                raise sd.CallbackStop
            remaining = frames_total - play_idx
            if remaining <= 0:
                raise sd.CallbackStop
            n = min(frames, remaining)
            outdata[:n, output_channel - 1] = signal[play_idx : play_idx + n]
            for i, channel in enumerate(input_channels):
                recorded[play_idx : play_idx + n, i] = np.asarray(
                    indata[:n, channel - 1], dtype=np.float64
                )
            play_idx += n
            if progress is not None:
                progress(min(1.0, play_idx / frames_total))
            if play_idx >= frames_total:
                raise sd.CallbackStop

        def on_finished() -> None:
            finished.set()

        try:
            with sd.Stream(
                samplerate=sample_rate,
                channels=(n_in, n_out),
                dtype="float32",
                device=(input_device, output_device),
                blocksize=CALLBACK_BLOCK,
                callback=callback,
                finished_callback=on_finished,
            ):
                timeout = frames_total / max(sample_rate, 1) + 5.0
                if not finished.wait(timeout=timeout):
                    raise AudioDeviceError("playback/recording timed out")
        except Exception as exc:
            if cancel is not None and cancel.is_set():
                raise MeasurementCancelledError("measurement stopped") from exc
            if isinstance(exc, MeasurementCancelledError):
                raise
            raise AudioDeviceError(f"playback/recording failed: {exc}") from exc
        if callback_error:
            raise AudioDeviceError(
                f"playback/recording failed: {callback_error[0]}"
            ) from callback_error[0]
        if cancel is not None and cancel.is_set():
            raise MeasurementCancelledError("measurement stopped")
        samples = recorded[:, 0] if len(input_channels) == 1 else recorded
        return AudioSignal(
            samples=np.ascontiguousarray(samples),
            sample_rate=sample_rate,
            source="standalone",
        )
