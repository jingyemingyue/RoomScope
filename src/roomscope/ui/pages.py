"""Home, Universal DAW Mode and Standalone Mode pages."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from roomscope.audio.playrec import (
    DEFAULT_STANDALONE_LEVEL_DBFS,
    SAFE_MAX_LEVEL_DBFS,
    SAFETY_MESSAGE,
)
from roomscope.core.pipeline import Reference
from roomscope.core.sweep import measurement_signal
from roomscope.errors import RoomScopeError
from roomscope.interpretation import interpret
from roomscope.io.wav import load_reference, read_wav, write_sweep_file
from roomscope.models.audio import AudioSignal
from roomscope.models.configuration import SUPPORTED_SAMPLE_RATES, AnalysisSettings, SweepSettings
from roomscope.models.result import AnalysisResult
from roomscope.models.session import MeasurementSession
from roomscope.ui.state import MeasurementState
from roomscope.ui.workers import AnalysisWorker, MeasureWorker

DAW_INSTRUCTIONS = (
    "1. Import the test-signal WAV on a new track of your DAW project.\n"
    "2. Route that track to the monitors (or the loudspeaker you want to test).\n"
    "3. Arm a second track with the measurement microphone and record while the test signal plays.\n"
    "4. Export / bounce the recorded track as a WAV file at the project sample rate.\n"
    "   Do not trim it - RoomScope finds the sweep automatically.\n"
    "Start with a low monitor level; the sweep should be clearly audible but not loud."
)


class HomePage(QWidget):
    choose_mode = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("RoomScope")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        subtitle = QLabel("An open-source, DAW-independent recording environment analyzer")
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(16)
        layout.addWidget(QLabel("New Measurement"))
        daw = QPushButton("Universal DAW Mode")
        daw.setToolTip(
            "Generate a test signal, play and record it in any DAW, import the recording."
        )
        standalone = QPushButton("Standalone Mode")
        standalone.setToolTip(
            "RoomScope plays the sweep and records the microphone through your audio interface."
        )
        daw.clicked.connect(lambda: self.choose_mode.emit("universal_daw"))
        standalone.clicked.connect(lambda: self.choose_mode.emit("standalone"))
        layout.addWidget(daw)
        layout.addWidget(standalone)
        layout.addStretch(1)


def _metadata_form(state: MeasurementState) -> tuple[QGroupBox, QLineEdit, QLineEdit, QLineEdit]:
    box = QGroupBox("Measurement metadata (optional)")
    form = QFormLayout(box)
    room = QLineEdit(state.session.room_name)
    position = QLineEdit(state.session.measurement_position)
    mic = QLineEdit(state.session.microphone_name)
    form.addRow("Room", room)
    form.addRow("Position", position)
    form.addRow("Microphone", mic)
    return box, room, position, mic


class DawModePage(QWidget):
    analysis_finished = Signal()
    back = Signal()

    def __init__(self, state: MeasurementState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self._worker: AnalysisWorker | None = None
        layout = QVBoxLayout(self)

        # Step 1
        step1 = QGroupBox("Step 1 - Generate Test Signal")
        form1 = QFormLayout(step1)
        self.sample_rate = QComboBox()
        for sr in SUPPORTED_SAMPLE_RATES:
            self.sample_rate.addItem(f"{sr} Hz", sr)
        self.sample_rate.setCurrentIndex(
            list(SUPPORTED_SAMPLE_RATES).index(state.sweep_settings.sample_rate)
        )
        self.duration = QDoubleSpinBox()
        self.duration.setRange(1.0, 60.0)
        self.duration.setValue(state.sweep_settings.duration_s)
        self.duration.setSuffix(" s")
        self.level = QDoubleSpinBox()
        self.level.setRange(-40.0, 0.0)
        self.level.setValue(state.sweep_settings.level_dbfs)
        self.level.setSuffix(" dBFS")
        form1.addRow("Sample rate", self.sample_rate)
        form1.addRow("Sweep duration", self.duration)
        form1.addRow("Peak level", self.level)
        self.save_sweep_button = QPushButton("Save Test Signal WAV...")
        self.save_sweep_button.clicked.connect(self._choose_sweep_target)
        self.sweep_label = QLabel("No test signal written yet.")
        self.sweep_label.setWordWrap(True)
        form1.addRow(self.save_sweep_button)
        form1.addRow(self.sweep_label)
        layout.addWidget(step1)

        # Step 2
        step2 = QGroupBox("Step 2 - Record Through Your DAW")
        v2 = QVBoxLayout(step2)
        instructions = QLabel(DAW_INSTRUCTIONS)
        instructions.setWordWrap(True)
        v2.addWidget(instructions)
        layout.addWidget(step2)

        # Step 3
        step3 = QGroupBox("Step 3 - Import Recording")
        form3 = QFormLayout(step3)
        self.recording_button = QPushButton("Choose Recording WAV...")
        self.recording_button.clicked.connect(self._choose_recording)
        self.recording_label = QLabel("No recording selected.")
        self.recording_label.setWordWrap(True)
        self.reference_button = QPushButton("Choose Reference Sweep...")
        self.reference_button.clicked.connect(self._choose_reference)
        self.reference_label = QLabel("Reference: the test signal from Step 1 (or choose a file).")
        self.reference_label.setWordWrap(True)
        self.channel = QComboBox()
        self.channel.addItem("Auto (highest level)", None)
        form3.addRow(self.recording_button, self.recording_label)
        form3.addRow(self.reference_button, self.reference_label)
        form3.addRow("Channel", self.channel)
        layout.addWidget(step3)

        # Step 4
        step4 = QGroupBox("Step 4 - Analyze")
        v4 = QVBoxLayout(step4)
        meta, self.room, self.position, self.mic = _metadata_form(state)
        v4.addWidget(meta)
        row = QHBoxLayout()
        self.analyze_button = QPushButton("Analyze")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.back.emit)
        row.addWidget(self.back_button)
        row.addStretch(1)
        row.addWidget(self.analyze_button)
        v4.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.status = QLabel("")
        self.status.setWordWrap(True)
        v4.addWidget(self.progress)
        v4.addWidget(self.status)
        layout.addWidget(step4)
        layout.addStretch(1)

    # --- step 1 -----------------------------------------------------------------
    def current_sweep_settings(self) -> SweepSettings:
        return SweepSettings(
            sample_rate=int(self.sample_rate.currentData()),
            duration_s=float(self.duration.value()),
            level_dbfs=float(self.level.value()),
        )

    def _choose_sweep_target(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save test signal", "roomscope_sweep.wav", "WAV files (*.wav)"
        )
        if path:
            self.generate_sweep_to(Path(path))

    def generate_sweep_to(self, path: Path) -> None:
        try:
            settings = self.current_sweep_settings()
            wav_path, sidecar = write_sweep_file(settings, path)
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Cannot write test signal", str(exc))
            return
        self.state.sweep_settings = settings
        self.state.sweep_path = wav_path
        self.state.reference = Reference.from_settings(settings)
        self.sweep_label.setText(
            f"Written: {wav_path.name} (+ {sidecar.name}). Keep both files together."
        )
        self.reference_label.setText(f"Reference: {wav_path.name}")

    # --- step 3 -----------------------------------------------------------------
    def _choose_recording(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose recording", "", "Audio files (*.wav *.flac *.aif *.aiff)"
        )
        if path:
            self.set_recording(Path(path))

    def set_recording(self, path: Path) -> None:
        try:
            recording = read_wav(path)
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Cannot read recording", str(exc))
            return
        self.state.recording = recording
        self.state.recording_path = path
        self.channel.clear()
        self.channel.addItem("Auto (highest level)", None)
        for index in range(recording.n_channels):
            self.channel.addItem(f"Channel {index + 1}", index)
        self.recording_label.setText(
            f"{path.name}: {recording.duration_s:.1f} s, {recording.sample_rate} Hz, {recording.n_channels} channel(s)"
        )

    def _choose_reference(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose reference sweep", "", "Sweep files (*.wav *.json);;All files (*)"
        )
        if path:
            self.set_reference(Path(path))

    def set_reference(self, path: Path) -> None:
        try:
            self.state.reference = load_reference(path)
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Cannot read reference sweep", str(exc))
            return
        self.state.sweep_path = path
        if self.state.reference.settings is not None:
            self.state.sweep_settings = self.state.reference.settings
        self.reference_label.setText(f"Reference: {path.name}")

    # --- step 4 -----------------------------------------------------------------
    def start_analysis(self, *, blocking: bool = False) -> None:
        if self.state.recording is None:
            QMessageBox.warning(
                self, "No recording", "Choose the recorded WAV file first (Step 3)."
            )
            return
        if self.state.reference is None:
            QMessageBox.warning(
                self, "No reference", "Generate the test signal (Step 1) or choose the sweep file."
            )
            return
        channel = self.channel.currentData()
        self.state.analysis_settings = AnalysisSettings(
            channel=None if channel is None else int(channel)
        )
        self.state.session = MeasurementSession(
            mode="universal_daw",
            room_name=self.room.text(),
            measurement_position=self.position.text(),
            microphone_name=self.mic.text(),
            sweep_settings=self.state.sweep_settings,
            analysis_settings=self.state.analysis_settings,
            sweep_path=str(self.state.sweep_path) if self.state.sweep_path else None,
            recording_path=str(self.state.recording_path) if self.state.recording_path else None,
        )
        self._set_busy(True, "Analyzing...")
        self._worker = AnalysisWorker(
            self.state.recording, self.state.reference, self.state.analysis_settings
        )
        self._worker.succeeded.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        if blocking:
            self._worker.run()
        else:
            self._worker.start()

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.analyze_button.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.status.setText(text)

    def _on_success(self, result: AnalysisResult) -> None:
        self.state.result = result
        self.state.findings = interpret(result)
        self._set_busy(False, "Done.")
        self.analysis_finished.emit()

    def _on_failure(self, message: str) -> None:
        self._set_busy(False, f"Analysis failed: {message}")
        QMessageBox.critical(self, "Analysis failed", message)


class StandalonePage(QWidget):
    analysis_finished = Signal()
    back = Signal()

    def __init__(self, state: MeasurementState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self._measure_worker: MeasureWorker | None = None
        self._analysis_worker: AnalysisWorker | None = None
        layout = QVBoxLayout(self)

        safety = QLabel(SAFETY_MESSAGE)
        safety.setWordWrap(True)
        safety.setStyleSheet("font-weight: bold;")
        layout.addWidget(safety)

        devices = QGroupBox("Audio devices")
        form = QFormLayout(devices)
        self.input_device = QComboBox()
        self.output_device = QComboBox()
        self.refresh_button = QPushButton("Refresh devices")
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.sample_rate = QComboBox()
        for sr in SUPPORTED_SAMPLE_RATES:
            self.sample_rate.addItem(f"{sr} Hz", sr)
        self.sample_rate.setCurrentIndex(
            list(SUPPORTED_SAMPLE_RATES).index(state.sweep_settings.sample_rate)
        )
        self.input_channel = QSpinBox()
        self.input_channel.setRange(1, 64)
        self.output_channel = QSpinBox()
        self.output_channel.setRange(1, 64)
        form.addRow("Input device", self.input_device)
        form.addRow("Output device", self.output_device)
        form.addRow(self.refresh_button)
        form.addRow("Sample rate", self.sample_rate)
        form.addRow("Input channel (mic)", self.input_channel)
        form.addRow("Output channel (speaker)", self.output_channel)
        layout.addWidget(devices)

        sweep = QGroupBox("Test signal")
        form2 = QFormLayout(sweep)
        self.duration = QDoubleSpinBox()
        self.duration.setRange(1.0, 60.0)
        self.duration.setValue(state.sweep_settings.duration_s)
        self.duration.setSuffix(" s")
        self.level = QDoubleSpinBox()
        self.level.setRange(-40.0, 0.0)
        self.level.setValue(DEFAULT_STANDALONE_LEVEL_DBFS)
        self.level.setSuffix(" dBFS")
        self.acknowledge = QCheckBox(
            f"I have set the monitor level low (required above {SAFE_MAX_LEVEL_DBFS:g} dBFS)"
        )
        form2.addRow("Sweep duration", self.duration)
        form2.addRow("Playback level", self.level)
        form2.addRow(self.acknowledge)
        layout.addWidget(sweep)

        meta, self.room, self.position, self.mic = _metadata_form(state)
        layout.addWidget(meta)

        row = QHBoxLayout()
        self.back_button = QPushButton("Back")
        self.back_button.clicked.connect(self.back.emit)
        self.run_button = QPushButton("Run Measurement")
        self.run_button.clicked.connect(self.start_measurement)
        row.addWidget(self.back_button)
        row.addStretch(1)
        row.addWidget(self.run_button)
        layout.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.hide()
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addStretch(1)
        self.refresh_devices()

    def refresh_devices(self) -> None:
        from roomscope.audio.devices import list_devices

        self.input_device.clear()
        self.output_device.clear()
        self.input_device.addItem("System default", None)
        self.output_device.addItem("System default", None)
        try:
            devices = list_devices()
        except RoomScopeError as exc:
            self.status.setText(f"Audio backend unavailable: {exc}")
            self.run_button.setEnabled(False)
            return
        for d in devices:
            label = f"[{d.index}] {d.name} ({d.host_api})"
            if d.is_input:
                self.input_device.addItem(label + f" - {d.max_input_channels} in", d.index)
            if d.is_output:
                self.output_device.addItem(label + f" - {d.max_output_channels} out", d.index)
        self.run_button.setEnabled(True)
        self.status.setText(f"{len(devices)} audio device(s) found.")

    def current_sweep_settings(self) -> SweepSettings:
        return SweepSettings(
            sample_rate=int(self.sample_rate.currentData()),
            duration_s=float(self.duration.value()),
            level_dbfs=float(self.level.value()),
        )

    def start_measurement(self) -> None:
        try:
            settings = self.current_sweep_settings()
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Invalid settings", str(exc))
            return
        if settings.level_dbfs > SAFE_MAX_LEVEL_DBFS and not self.acknowledge.isChecked():
            QMessageBox.warning(
                self,
                "Level too high",
                f"Levels above {SAFE_MAX_LEVEL_DBFS:g} dBFS need the acknowledgement checkbox. "
                "Set the monitor level low first.",
            )
            return
        self.state.mode = "standalone"
        self.state.sweep_settings = settings
        self.state.reference = Reference.from_settings(settings)
        self.state.analysis_settings = AnalysisSettings()
        self._set_busy(True, "Playing the sweep and recording...")
        self._measure_worker = MeasureWorker(
            measurement_signal(settings),
            settings.sample_rate,
            input_device=self.input_device.currentData(),
            output_device=self.output_device.currentData(),
            input_channel=int(self.input_channel.value()),
            output_channel=int(self.output_channel.value()),
            level_dbfs=settings.level_dbfs,
        )
        self._measure_worker.succeeded.connect(self._on_recorded)
        self._measure_worker.failed.connect(self._on_failure)
        self._measure_worker.start()

    def _on_recorded(self, recording: AudioSignal) -> None:
        self.state.recording = recording
        self.state.recording_path = None
        self.state.session = MeasurementSession(
            mode="standalone",
            room_name=self.room.text(),
            measurement_position=self.position.text(),
            microphone_name=self.mic.text(),
            input_channel=int(self.input_channel.value()),
            output_channel=int(self.output_channel.value()),
            sweep_settings=self.state.sweep_settings,
            analysis_settings=self.state.analysis_settings,
        )
        assert self.state.reference is not None
        self.status.setText("Recorded. Analyzing...")
        self._analysis_worker = AnalysisWorker(
            recording, self.state.reference, self.state.analysis_settings
        )
        self._analysis_worker.succeeded.connect(self._on_success)
        self._analysis_worker.failed.connect(self._on_failure)
        self._analysis_worker.start()

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.run_button.setEnabled(not busy)
        self.progress.setVisible(busy)
        self.status.setText(text)

    def _on_success(self, result: AnalysisResult) -> None:
        self.state.result = result
        self.state.findings = interpret(result)
        self._set_busy(False, "Done.")
        self.analysis_finished.emit()

    def _on_failure(self, message: str) -> None:
        self._set_busy(False, f"Measurement failed: {message}")
        QMessageBox.critical(self, "Measurement failed", message)
