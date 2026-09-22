"""Results page: Overview, Impulse Response, Frequency Response, Decay, Noise, Early Reflections."""

from __future__ import annotations

from pathlib import Path

from roomscope.ui.qt import ensure_pyside6

ensure_pyside6()

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from roomscope.cli.report import format_report
from roomscope.errors import RoomScopeError
from roomscope.io.recent import remember_session
from roomscope.io.session_store import save_measurement
from roomscope.io.wav import write_wav
from roomscope.ui.plots import (
    decay_table_rows,
    plot_decay,
    plot_frequency_response,
    plot_impulse_response,
    plot_noise,
    plot_reflections,
)
from roomscope.ui.state import MeasurementState


class _PlotTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(7.0, 4.5), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)

    def redraw(self) -> None:
        self.canvas.draw_idle()


class ResultsPage(QWidget):
    new_measurement = Signal()

    def __init__(self, state: MeasurementState, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.state = state
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        overview = QWidget()
        ov_layout = QVBoxLayout(overview)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Band", "EDT", "T20", "T30", "RT60 estimate"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        ov_layout.addWidget(
            QLabel(
                "Reverberation (extrapolated to 60 dB). 'insufficient range' means the decay is not clean enough for that metric."
            )
        )
        ov_layout.addWidget(self.table, 1)
        ov_layout.addWidget(self.text, 2)
        self.tabs.addTab(overview, "Overview")

        self.ir_tab = _PlotTab()
        self.fr_tab = _PlotTab()
        self.decay_tab = _PlotTab()
        self.noise_tab = _PlotTab()
        self.refl_tab = _PlotTab()
        self.tabs.addTab(self.ir_tab, "Impulse Response")
        self.tabs.addTab(self.fr_tab, "Frequency Response")
        self.tabs.addTab(self.decay_tab, "Decay")
        self.tabs.addTab(self.noise_tab, "Noise")
        self.tabs.addTab(self.refl_tab, "Early Reflections")
        layout.addWidget(self.tabs, 1)

        row = QHBoxLayout()
        self.new_button = QPushButton("New Measurement")
        self.new_button.clicked.connect(self.new_measurement.emit)
        self.save_button = QPushButton("Save Session...")
        self.save_button.clicked.connect(self._choose_save_directory)
        row.addWidget(self.new_button)
        row.addStretch(1)
        row.addWidget(self.save_button)
        layout.addLayout(row)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def refresh(self) -> None:
        result = self.state.result
        if result is None:
            return
        rows = decay_table_rows(result)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, item)
        self.table.resizeColumnsToContents()
        self.text.setPlainText(format_report(result, self.state.findings))
        plot_impulse_response(self.ir_tab.figure, result)
        plot_frequency_response(self.fr_tab.figure, result)
        plot_decay(self.decay_tab.figure, result)
        plot_noise(self.noise_tab.figure, result)
        plot_reflections(self.refl_tab.figure, result)
        for tab in (self.ir_tab, self.fr_tab, self.decay_tab, self.noise_tab, self.refl_tab):
            tab.redraw()
        self.status.setText("")

    def _choose_save_directory(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Choose a folder for the session")
        if directory:
            self.save_to(Path(directory))

    def save_to(self, directory: Path) -> None:
        result = self.state.result
        if result is None:
            return
        try:
            if self.state.recording is not None and self.state.recording_path is None:
                path = write_wav(
                    directory / "recording.wav",
                    self.state.recording.samples,
                    result.sample_rate,
                    subtype="FLOAT",
                )
                self.state.session.recording_path = str(path)
            session_path = save_measurement(directory, self.state.session, result)
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Cannot save session", str(exc))
            return
        remember_session(directory)
        self.status.setText(f"Session saved to {session_path.parent}")
