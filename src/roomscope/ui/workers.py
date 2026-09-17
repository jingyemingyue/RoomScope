"""Worker threads so that analysis and playback never block the UI."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from roomscope.core.pipeline import Reference, analyze
from roomscope.errors import RoomScopeError
from roomscope.models.audio import AudioSignal, FloatArray
from roomscope.models.configuration import AnalysisSettings


class AnalysisWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        recording: AudioSignal,
        reference: Reference,
        settings: AnalysisSettings,
    ) -> None:
        super().__init__()
        self._recording = recording
        self._reference = reference
        self._settings = settings

    def run(self) -> None:
        try:
            result = analyze(self._recording, self._reference, self._settings)
        except RoomScopeError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"unexpected error: {exc!r}")
        else:
            self.succeeded.emit(result)


class MeasureWorker(QThread):
    succeeded = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        signal: FloatArray,
        sample_rate: int,
        *,
        input_device: int | None,
        output_device: int | None,
        input_channel: int,
        output_channel: int,
        level_dbfs: float,
    ) -> None:
        super().__init__()
        self._signal = signal
        self._sample_rate = sample_rate
        self._input_device = input_device
        self._output_device = output_device
        self._input_channel = input_channel
        self._output_channel = output_channel
        self._level_dbfs = level_dbfs

    def run(self) -> None:
        from roomscope.audio.playrec import play_and_record

        try:
            recording = play_and_record(
                self._signal,
                self._sample_rate,
                input_device=self._input_device,
                output_device=self._output_device,
                input_channel=self._input_channel,
                output_channel=self._output_channel,
                level_dbfs=self._level_dbfs,
            )
        except RoomScopeError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:
            self.failed.emit(f"unexpected error: {exc!r}")
        else:
            self.succeeded.emit(recording)
