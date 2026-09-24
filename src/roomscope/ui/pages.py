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

from roomscope.audio.backend import ChannelPlan, DeviceInfo, plan_input_channels
from roomscope.audio.playrec import (
    DEFAULT_STANDALONE_LEVEL_DBFS,
    SAFE_MAX_LEVEL_DBFS,
    SAFETY_MESSAGE,
)
from roomscope.core.pipeline import Reference
from roomscope.core.sweep import measurement_signal
from roomscope.errors import RoomScopeError
from roomscope.i18n import N_, _
from roomscope.interpretation import available_profiles, interpret
from roomscope.io.wav import load_reference, read_wav, write_sweep_file
from roomscope.models.audio import AudioSignal
from roomscope.models.configuration import SUPPORTED_SAMPLE_RATES, AnalysisSettings, SweepSettings
from roomscope.models.result import AnalysisResult
from roomscope.models.session import MeasurementSession
from roomscope.ui.browser import SessionBrowser
from roomscope.ui.state import MeasurementState
from roomscope.ui.workers import AnalysisWorker, MeasureWorker

DAW_INSTRUCTIONS = N_(
    "1. Import the test-signal WAV on a new track of your DAW project.\n"
    "2. Route that track to the monitors (or the loudspeaker you want to test).\n"
    "3. Arm a second track with the measurement microphone and record while the test signal plays.\n"
    "4. Export / bounce the recorded track as a WAV file at the project sample rate.\n"
    "   Do not trim it - RoomScope finds the sweep automatically.\n"
    "Start with a low monitor level; the sweep should be clearly audible but not loud."
)


class HomePage(QWidget):
    choose_mode = Signal(str)
    open_session = Signal()
    open_recent = Signal(str)
    compare_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("RoomScope")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        subtitle = QLabel(_("An open-source, DAW-independent recording environment analyzer"))
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addSpacing(16)
        layout.addWidget(QLabel(_("New Measurement")))
        daw = QPushButton(_("Universal DAW Mode"))
        daw.setToolTip(
            "Generate a test signal, play and record it in any DAW, import the recording."
        )
        standalone = QPushButton(_("Standalone Mode"))
        standalone.setToolTip(
            "RoomScope plays the sweep and records the microphone through your audio interface."
        )
        demo = QPushButton(_("Demo (no interface)"))
        demo.setToolTip(
            "Run Standalone Mode on the fake backend. Nothing is sent to a loudspeaker."
        )
        daw.clicked.connect(lambda: self.choose_mode.emit("universal_daw"))
        standalone.clicked.connect(lambda: self.choose_mode.emit("standalone"))
        demo.clicked.connect(lambda: self.choose_mode.emit("demo"))
        layout.addWidget(daw)
        layout.addWidget(standalone)
        layout.addWidget(demo)
        layout.addSpacing(16)
        layout.addWidget(QLabel(_("Saved sessions")))
        session_row = QHBoxLayout()
        open_button = QPushButton(_("Open Session..."))
        open_button.setToolTip("Open a session.json or a folder that contains one.")
        open_button.clicked.connect(self.open_session.emit)
        compare_button = QPushButton(_("Compare two sessions..."))
        compare_button.setToolTip("Pick two saved sessions and compare their metrics.")
        compare_button.clicked.connect(self.compare_requested.emit)
        session_row.addWidget(open_button)
        session_row.addWidget(compare_button)
        layout.addLayout(session_row)
        self.browser = SessionBrowser()
        self.browser.open_session.connect(self.open_recent.emit)
        self.recent = self.browser.list
        layout.addWidget(self.browser, 1)

    def refresh_recent(self) -> None:
        self.browser.refresh_recent()

    def list_folder(self, root: Path) -> None:
        self.browser.list_folder(root)


def _metadata_form(state: MeasurementState) -> tuple[QGroupBox, QLineEdit, QLineEdit, QLineEdit]:
    box = QGroupBox(_("Measurement metadata (optional)"))
    form = QFormLayout(box)
    room = QLineEdit(state.session.room_name)
    position = QLineEdit(state.session.measurement_position)
    mic = QLineEdit(state.session.microphone_name)
    form.addRow(_("Room"), room)
    form.addRow(_("Position"), position)
    form.addRow(_("Microphone"), mic)
    return box, room, position, mic


def _profile_combo(state: MeasurementState) -> QComboBox:
    combo = QComboBox()
    for name in available_profiles():
        combo.addItem(name, name)
    combo.setCurrentText(state.profile)
    return combo


class PlacementInputs(QGroupBox):
    """Optional tape measurements that raise the placement tier (S5)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(_("Tape measurements (optional)"))
        form = QFormLayout(self)
        self.distance = QDoubleSpinBox()
        self.distance.setRange(0.0, 15.0)
        self.distance.setDecimals(2)
        self.distance.setSingleStep(0.01)
        self.distance.setSuffix(" m")
        self.distance.setSpecialValueText(_("not measured"))
        self.distance.setValue(0.0)
        self.distance.setToolTip(_("Straight line from the loudspeaker to the microphone capsule."))
        self.mic_height = QDoubleSpinBox()
        self.mic_height.setRange(0.0, 5.0)
        self.mic_height.setDecimals(2)
        self.mic_height.setSingleStep(0.01)
        self.mic_height.setSuffix(" m")
        self.mic_height.setSpecialValueText(_("not measured"))
        self.mic_height.setValue(0.0)
        self.mic_height.setEnabled(False)
        self.mic_height.setToolTip(
            _("Capsule above the first solid horizontal surface below it. Needs the distance.")
        )
        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(-20.0, 50.0)
        self.temperature.setDecimals(1)
        self.temperature.setValue(20.0)
        self.temperature.setSuffix(" C")
        self.temperature.setEnabled(False)
        self.temperature_measured = QCheckBox(_("air temperature measured"))
        self.temperature_measured.toggled.connect(self.temperature.setEnabled)
        self.distance.valueChanged.connect(self._sync_height)
        form.addRow(_("Loudspeaker distance"), self.distance)
        form.addRow(_("Microphone height"), self.mic_height)
        form.addRow(self.temperature_measured, self.temperature)

    def _sync_height(self, value: float) -> None:
        allowed = value >= 0.20
        self.mic_height.setEnabled(allowed)
        if not allowed:
            self.mic_height.setValue(0.0)

    def analysis_kwargs(self) -> dict[str, float | None]:
        distance = self.distance.value()
        height = self.mic_height.value()
        distance_m = distance if distance >= 0.20 else None
        mic_height_m = height if distance_m is not None and height >= 0.02 else None
        temperature_c = self.temperature.value() if self.temperature_measured.isChecked() else None
        return {
            "placement_distance_m": distance_m,
            "placement_mic_height_m": mic_height_m,
            "placement_temperature_c": temperature_c,
        }


class DawModePage(QWidget):
    analysis_finished = Signal()
    back = Signal()

    def __init__(self, state: MeasurementState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self._worker: AnalysisWorker | None = None
        layout = QVBoxLayout(self)

        # Step 1
        step1 = QGroupBox(_("Step 1 - Generate Test Signal"))
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
        form1.addRow(_("Sample rate"), self.sample_rate)
        form1.addRow(_("Sweep duration"), self.duration)
        form1.addRow(_("Peak level"), self.level)
        self.save_sweep_button = QPushButton(_("Save Test Signal WAV..."))
        self.save_sweep_button.clicked.connect(self._choose_sweep_target)
        self.sweep_label = QLabel(_("No test signal written yet."))
        self.sweep_label.setWordWrap(True)
        form1.addRow(self.save_sweep_button)
        form1.addRow(self.sweep_label)
        layout.addWidget(step1)

        # Step 2
        step2 = QGroupBox(_("Step 2 - Record Through Your DAW"))
        v2 = QVBoxLayout(step2)
        instructions = QLabel(_(DAW_INSTRUCTIONS))
        instructions.setWordWrap(True)
        v2.addWidget(instructions)
        layout.addWidget(step2)

        # Step 3
        step3 = QGroupBox(_("Step 3 - Import Recording"))
        form3 = QFormLayout(step3)
        self.recording_button = QPushButton(_("Choose Recording WAV..."))
        self.recording_button.clicked.connect(self._choose_recording)
        self.recording_label = QLabel(_("No recording selected."))
        self.recording_label.setWordWrap(True)
        self.reference_button = QPushButton(_("Choose Reference Sweep..."))
        self.reference_button.clicked.connect(self._choose_reference)
        self.reference_label = QLabel(
            _("Reference: the test signal from Step 1 (or choose a file).")
        )
        self.reference_label.setWordWrap(True)
        self.channel = QComboBox()
        self.channel.addItem(_("Auto (highest level)"), None)
        self.loopback_channel = QComboBox()
        self.loopback_channel.addItem(_("None"), None)
        form3.addRow(self.recording_button, self.recording_label)
        form3.addRow(self.reference_button, self.reference_label)
        form3.addRow(_("Microphone channel"), self.channel)
        form3.addRow(_("Loopback channel"), self.loopback_channel)
        layout.addWidget(step3)

        # Step 4
        step4 = QGroupBox(_("Step 4 - Analyze"))
        v4 = QVBoxLayout(step4)
        meta, self.room, self.position, self.mic = _metadata_form(state)
        v4.addWidget(meta)
        self.placement = PlacementInputs()
        v4.addWidget(self.placement)
        profile_form = QFormLayout()
        self.profile = _profile_combo(state)
        profile_form.addRow(_("Recording profile"), self.profile)
        v4.addLayout(profile_form)
        row = QHBoxLayout()
        self.analyze_button = QPushButton(_("Analyze"))
        self.analyze_button.setShortcut("Ctrl+Return")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.back_button = QPushButton(_("Back"))
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
        path, _filter = QFileDialog.getSaveFileName(
            self, _("Save test signal"), "roomscope_sweep.wav", _("WAV files (*.wav)")
        )
        if path:
            self.generate_sweep_to(Path(path))

    def generate_sweep_to(self, path: Path) -> None:
        try:
            settings = self.current_sweep_settings()
            wav_path, sidecar = write_sweep_file(settings, path)
        except RoomScopeError as exc:
            QMessageBox.critical(self, _("Cannot write test signal"), str(exc))
            return
        self.state.sweep_settings = settings
        self.state.sweep_path = wav_path
        self.state.reference = Reference.from_settings(settings)
        self.sweep_label.setText(
            _("Written: {wav} (+ {sidecar}). Keep both files together.").format(
                wav=wav_path.name, sidecar=sidecar.name
            )
        )
        self.reference_label.setText(_("Reference: {name}").format(name=wav_path.name))

    # --- step 3 -----------------------------------------------------------------
    def _choose_recording(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            _("Choose recording"),
            "",
            _("Audio files (*.wav *.flac *.aif *.aiff)"),
        )
        if path:
            self.set_recording(Path(path))

    def set_recording(self, path: Path) -> None:
        try:
            recording = read_wav(path)
        except RoomScopeError as exc:
            QMessageBox.critical(self, _("Cannot read recording"), str(exc))
            return
        self.state.recording = recording
        self.state.recording_path = path
        self.channel.clear()
        self.channel.addItem(_("Auto (highest level)"), None)
        self.loopback_channel.clear()
        self.loopback_channel.addItem(_("None"), None)
        for index in range(recording.n_channels):
            label = _("Channel {n}").format(n=index + 1)
            self.channel.addItem(label, index)
            self.loopback_channel.addItem(label, index)
        self.recording_label.setText(
            _("{name}: {seconds:.1f} s, {rate} Hz, {channels} channel(s)").format(
                name=path.name,
                seconds=recording.duration_s,
                rate=recording.sample_rate,
                channels=recording.n_channels,
            )
        )

    def _choose_reference(self) -> None:
        path, _filter = QFileDialog.getOpenFileName(
            self,
            _("Choose reference sweep"),
            "",
            _("Sweep files (*.wav *.json);;All files (*)"),
        )
        if path:
            self.set_reference(Path(path))

    def set_reference(self, path: Path) -> None:
        try:
            self.state.reference = load_reference(path)
        except RoomScopeError as exc:
            QMessageBox.critical(self, _("Cannot read reference sweep"), str(exc))
            return
        self.state.sweep_path = path
        if self.state.reference.settings is not None:
            self.state.sweep_settings = self.state.reference.settings
        self.reference_label.setText(_("Reference: {name}").format(name=path.name))

    # --- step 4 -----------------------------------------------------------------
    def start_analysis(self, *, blocking: bool = False) -> None:
        if self.state.recording is None:
            QMessageBox.warning(
                self, _("No recording"), _("Choose the recorded WAV file first (Step 3).")
            )
            return
        if self.state.reference is None:
            QMessageBox.warning(
                self,
                _("No reference"),
                _("Generate the test signal (Step 1) or choose the sweep file."),
            )
            return
        channel = self.channel.currentData()
        loopback = self.loopback_channel.currentData()
        self.state.profile = str(self.profile.currentData())
        place = self.placement.analysis_kwargs()
        self.state.analysis_settings = AnalysisSettings(
            channel=None if channel is None else int(channel),
            loopback_channel=None if loopback is None else int(loopback),
            placement_distance_m=place["placement_distance_m"],
            placement_mic_height_m=place["placement_mic_height_m"],
            placement_temperature_c=place["placement_temperature_c"],
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
            recording_profile=self.state.profile,
        )
        self._set_busy(True, _("Analyzing..."))
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
        self.state.findings = interpret(result, self.state.profile)
        self._set_busy(False, _("Done."))
        self.analysis_finished.emit()

    def _on_failure(self, message: str) -> None:
        self._set_busy(False, _("Analysis failed: {message}").format(message=message))
        QMessageBox.critical(self, _("Analysis failed"), message)


class StandalonePage(QWidget):
    analysis_finished = Signal()
    back = Signal()

    def __init__(self, state: MeasurementState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        self.demo_mode = False
        self._devices: list[DeviceInfo] = []
        self._measure_worker: MeasureWorker | None = None
        self._analysis_worker: AnalysisWorker | None = None
        self._channel_plan: ChannelPlan | None = None
        layout = QVBoxLayout(self)

        self.demo_banner = QLabel(
            _("Demo mode: the fake backend synthesises a room. Nothing is sent to a loudspeaker.")
        )
        self.demo_banner.setWordWrap(True)
        self.demo_banner.setStyleSheet("font-weight: bold;")
        self.demo_banner.hide()
        layout.addWidget(self.demo_banner)

        safety = QLabel(_(SAFETY_MESSAGE))
        safety.setWordWrap(True)
        safety.setStyleSheet("font-weight: bold;")
        layout.addWidget(safety)

        devices = QGroupBox(_("Audio devices"))
        form = QFormLayout(devices)
        self.input_device = QComboBox()
        self.output_device = QComboBox()
        self.refresh_button = QPushButton(_("Refresh devices"))
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.sample_rate = QComboBox()
        for sr in SUPPORTED_SAMPLE_RATES:
            self.sample_rate.addItem(f"{sr} Hz", sr)
        self.sample_rate.setCurrentIndex(
            list(SUPPORTED_SAMPLE_RATES).index(state.sweep_settings.sample_rate)
        )
        self.input_channel = QSpinBox()
        self.input_channel.setRange(1, 64)
        self.loopback_channel = QSpinBox()
        self.loopback_channel.setRange(0, 64)
        self.loopback_channel.setSpecialValueText(_("unused"))
        self.output_channel = QSpinBox()
        self.output_channel.setRange(1, 64)
        self.device_rate = QLabel(_("Device rate: unknown"))
        self.device_rate.setWordWrap(True)
        self.input_device.currentIndexChanged.connect(self._update_device_rate)
        self.output_device.currentIndexChanged.connect(self._update_device_rate)
        self.sample_rate.currentIndexChanged.connect(self._update_device_rate)
        form.addRow(_("Input device"), self.input_device)
        form.addRow(_("Output device"), self.output_device)
        form.addRow(self.refresh_button)
        form.addRow(_("Sample rate"), self.sample_rate)
        form.addRow(self.device_rate)
        form.addRow(_("Input channel (mic)"), self.input_channel)
        form.addRow(_("Loopback channel (1-based)"), self.loopback_channel)
        form.addRow(_("Output channel (speaker)"), self.output_channel)
        layout.addWidget(devices)

        sweep = QGroupBox(_("Test signal"))
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
            _("I have set the monitor level low (required above {level:g} dBFS)").format(
                level=SAFE_MAX_LEVEL_DBFS
            )
        )
        form2.addRow(_("Sweep duration"), self.duration)
        form2.addRow(_("Playback level"), self.level)
        form2.addRow(self.acknowledge)
        self.profile = _profile_combo(state)
        form2.addRow(_("Recording profile"), self.profile)
        layout.addWidget(sweep)

        meta, self.room, self.position, self.mic = _metadata_form(state)
        layout.addWidget(meta)
        self.placement = PlacementInputs()
        layout.addWidget(self.placement)

        row = QHBoxLayout()
        self.back_button = QPushButton(_("Back"))
        self.back_button.clicked.connect(self.back.emit)
        self.run_button = QPushButton(_("Run Measurement"))
        self.run_button.setShortcut("Ctrl+Return")
        self.run_button.clicked.connect(self.start_measurement)
        self.stop_button = QPushButton(_("Stop"))
        self.stop_button.setShortcut("Esc")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_measurement)
        row.addWidget(self.back_button)
        row.addStretch(1)
        row.addWidget(self.stop_button)
        row.addWidget(self.run_button)
        layout.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.progress)
        layout.addWidget(self.status)
        layout.addStretch(1)
        self.refresh_devices()

    def refresh_devices(self) -> None:
        from roomscope.audio.backend import get_backend

        self.demo_banner.setVisible(self.demo_mode)
        self.input_device.clear()
        self.output_device.clear()
        self.input_device.addItem(_("System default"), None)
        self.output_device.addItem(_("System default"), None)
        try:
            backend = get_backend("fake" if self.demo_mode else None)
            devices = backend.list_devices()
        except RoomScopeError as exc:
            self._devices = []
            self._update_device_rate()
            self.status.setText(f"Audio backend unavailable: {exc}")
            self.run_button.setEnabled(False)
            return
        self._devices = list(devices)
        for d in devices:
            label = f"[{d.index}] {d.name} ({d.host_api})"
            if d.is_input:
                self.input_device.addItem(label + f" - {d.max_input_channels} in", d.index)
            if d.is_output:
                self.output_device.addItem(label + f" - {d.max_output_channels} out", d.index)
        self._update_device_rate()
        self.run_button.setEnabled(True)
        if self.demo_mode:
            self.status.setText(_("Demo mode: fake backend, no loudspeaker."))
        else:
            self.status.setText(_("{n} audio device(s) found.").format(n=len(devices)))

    def _device_for(self, combo: QComboBox, *, kind: str) -> DeviceInfo | None:
        index = combo.currentData()
        for device in self._devices:
            if index is None:
                if kind == "input" and device.is_default_input:
                    return device
                if kind == "output" and device.is_default_output:
                    return device
            elif device.index == index:
                return device
        return None

    def _update_device_rate(self) -> None:
        requested = self.sample_rate.currentData()
        requested_hz = int(requested) if requested is not None else 0
        inp = self._device_for(self.input_device, kind="input")
        out = self._device_for(self.output_device, kind="output")
        parts: list[str] = []
        if inp is not None:
            parts.append(f"in {inp.default_sample_rate:.0f} Hz")
        if out is not None and (
            inp is None
            or out.index != inp.index
            or abs(out.default_sample_rate - inp.default_sample_rate) > 0.5
        ):
            parts.append(f"out {out.default_sample_rate:.0f} Hz")
        device_txt = ", ".join(parts) if parts else _("unknown")
        text = _("Device rate: {device}  (requested {requested} Hz)").format(
            device=device_txt, requested=requested_hz
        )
        mismatch = False
        for device in (inp, out):
            if (
                device is not None
                and requested_hz
                and abs(device.default_sample_rate - requested_hz) > 1.0
            ):
                mismatch = True
        if mismatch:
            text += _(" — rates differ; the interface may resample")
        self.device_rate.setText(text)

    def _check_selected_rates(self, sample_rate: int) -> None:
        from roomscope.audio.backend import get_backend

        backend = get_backend("fake" if self.demo_mode else None)
        for kind, combo in (("input", self.input_device), ("output", self.output_device)):
            device = self._device_for(combo, kind=kind)
            if device is not None:
                backend.check_sample_rate(device.index, sample_rate, kind=kind)

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
            QMessageBox.critical(self, _("Invalid settings"), str(exc))
            return
        if settings.level_dbfs > SAFE_MAX_LEVEL_DBFS and not self.acknowledge.isChecked():
            QMessageBox.warning(
                self,
                _("Level too high"),
                _(
                    "Levels above {level:g} dBFS need the acknowledgement checkbox. "
                    "Set the monitor level low first."
                ).format(level=SAFE_MAX_LEVEL_DBFS),
            )
            return
        try:
            self._check_selected_rates(settings.sample_rate)
        except RoomScopeError as exc:
            QMessageBox.critical(self, _("Sample rate not supported"), str(exc))
            return
        self.state.mode = "standalone"
        self.state.sweep_settings = settings
        self.state.reference = Reference.from_settings(settings)
        hardware_loopback = int(self.loopback_channel.value())
        try:
            # 1-based interface inputs → 0-based recording columns, checked
            # before anything is played (#13).
            plan = plan_input_channels(
                [int(self.input_channel.value())],
                hardware_loopback if hardware_loopback > 0 else None,
            )
        except RoomScopeError as exc:
            QMessageBox.critical(self, _("Invalid settings"), str(exc))
            return
        self._channel_plan = plan
        place = self.placement.analysis_kwargs()
        self.state.analysis_settings = AnalysisSettings(
            channel=plan.analysis_channel,
            loopback_channel=plan.analysis_loopback_channel,
            placement_distance_m=place["placement_distance_m"],
            placement_mic_height_m=place["placement_mic_height_m"],
            placement_temperature_c=place["placement_temperature_c"],
        )
        self.state.profile = str(self.profile.currentData())
        self._set_busy(True, _("Playing the sweep and recording..."))
        self._measure_worker = MeasureWorker(
            measurement_signal(settings),
            settings.sample_rate,
            input_device=self.input_device.currentData(),
            output_device=self.output_device.currentData(),
            input_channels=list(plan.input_channels),
            output_channel=int(self.output_channel.value()),
            level_dbfs=settings.level_dbfs,
            backend="fake" if self.demo_mode else None,
        )
        self._measure_worker.succeeded.connect(self._on_recorded)
        self._measure_worker.failed.connect(self._on_failure)
        self._measure_worker.progress.connect(self._on_progress)
        self._measure_worker.stopped.connect(self._on_stopped)
        self._measure_worker.start()

    def stop_measurement(self) -> None:
        if self._measure_worker is not None:
            self._measure_worker.request_stop()

    def _on_progress(self, fraction: float) -> None:
        self.progress.setValue(int(fraction * 100.0))

    def _on_stopped(self) -> None:
        self._set_busy(False, _("Stopped."))

    def _on_recorded(self, recording: AudioSignal) -> None:
        self.state.recording = recording
        self.state.recording_path = None
        plan = self._channel_plan
        assert plan is not None
        # The session stores the 1-based interface channels of the take.
        self.state.session = MeasurementSession(
            mode="standalone",
            room_name=self.room.text(),
            measurement_position=self.position.text(),
            microphone_name=self.mic.text(),
            input_channel=plan.microphone_channel,
            loopback_channel=plan.loopback_channel,
            output_channel=int(self.output_channel.value()),
            sweep_settings=self.state.sweep_settings,
            analysis_settings=self.state.analysis_settings,
            recording_profile=self.state.profile,
        )
        assert self.state.reference is not None
        self.status.setText(_("Recorded. Analyzing..."))
        self._analysis_worker = AnalysisWorker(
            recording, self.state.reference, self.state.analysis_settings
        )
        self._analysis_worker.succeeded.connect(self._on_success)
        self._analysis_worker.failed.connect(self._on_failure)
        self._analysis_worker.start()

    def _set_busy(self, busy: bool, text: str = "") -> None:
        self.run_button.setEnabled(not busy)
        if hasattr(self, "stop_button"):
            self.stop_button.setEnabled(busy)
        self.progress.setVisible(busy)
        if not busy and hasattr(self, "progress") and self.progress.maximum() == 100:
            self.progress.setValue(0)
        self.status.setText(text)

    def _on_success(self, result: AnalysisResult) -> None:
        self.state.result = result
        self.state.findings = interpret(result, self.state.profile)
        self._set_busy(False, _("Done."))
        self.analysis_finished.emit()

    def _on_failure(self, message: str) -> None:
        self._set_busy(False, _("Measurement failed: {message}").format(message=message))
        QMessageBox.critical(self, _("Measurement failed"), message)
