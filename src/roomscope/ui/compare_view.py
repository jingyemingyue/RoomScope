"""Compare two saved sessions: side-by-side deltas and a difference curve."""

from __future__ import annotations

from pathlib import Path

from roomscope.ui.qt import ensure_pyside6

ensure_pyside6()

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from roomscope.cli.report import format_comparison_report
from roomscope.core.compare import compare
from roomscope.errors import RoomScopeError
from roomscope.interpretation import interpret_comparison
from roomscope.interpretation.interpreter import Finding
from roomscope.io.session_store import load_measurement, save_comparison
from roomscope.models.comparison import CompareSettings, ComparisonResult
from roomscope.ui.browser import SessionBrowser


class ComparePage(QWidget):
    back = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._comparison: ComparisonResult | None = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Compare two sessions. Select two rows, or pick each path."))
        self.browser = SessionBrowser(multi_select=True)
        self.browser.open_session.connect(self._fill_next_path)
        layout.addWidget(self.browser, 1)

        paths = QHBoxLayout()
        self.baseline_path = QLineEdit()
        self.baseline_path.setPlaceholderText("Baseline session")
        self.candidate_path = QLineEdit()
        self.candidate_path.setPlaceholderText("Candidate session")
        pick_a = QPushButton("Baseline...")
        pick_b = QPushButton("Candidate...")
        pick_a.clicked.connect(lambda: self._pick_into(self.baseline_path))
        pick_b.clicked.connect(lambda: self._pick_into(self.candidate_path))
        paths.addWidget(self.baseline_path)
        paths.addWidget(pick_a)
        paths.addWidget(self.candidate_path)
        paths.addWidget(pick_b)
        layout.addLayout(paths)

        self.same_gain = QCheckBox("Input gain unchanged")
        self.same_gain.setToolTip(
            "Required for a VALID noise delta. Leave unchecked if the preamp gain may have changed."
        )
        layout.addWidget(self.same_gain)

        buttons = QHBoxLayout()
        run = QPushButton("Compare")
        run.clicked.connect(self.run_compare)
        save = QPushButton("Save comparison.json...")
        save.clicked.connect(self._save)
        back = QPushButton("Back")
        back.clicked.connect(self.back.emit)
        buttons.addWidget(run)
        buttons.addWidget(save)
        buttons.addStretch(1)
        buttons.addWidget(back)
        layout.addLayout(buttons)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Metric", "Baseline", "Candidate", "Delta", "%", "Validity"]
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table, 1)

        self.figure = Figure(figsize=(7.0, 3.2), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
        layout.addWidget(self.canvas)

        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text, 1)
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def set_paths(self, baseline: Path, candidate: Path) -> None:
        self.baseline_path.setText(str(baseline))
        self.candidate_path.setText(str(candidate))

    def run_compare(self) -> None:
        selected = self.browser.selected_paths()
        baseline = self.baseline_path.text().strip()
        candidate = self.candidate_path.text().strip()
        if (not baseline or not candidate) and len(selected) == 2:
            baseline, candidate = str(selected[0]), str(selected[1])
            self.set_paths(Path(baseline), Path(candidate))
        if not baseline or not candidate:
            QMessageBox.information(self, "Compare", "Choose two sessions first.")
            return
        try:
            left = load_measurement(baseline)
            right = load_measurement(candidate)
            comparison = compare(
                left.result,
                right.result,
                settings=CompareSettings(same_input_gain=self.same_gain.isChecked()),
            )
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Cannot compare", str(exc))
            return
        profile = right.session.recording_profile or "generic"
        try:
            findings = interpret_comparison(comparison, profile)
        except RoomScopeError:
            findings = interpret_comparison(comparison, "generic")
            profile = "generic"
        self._comparison = comparison
        self._show(comparison, findings, profile)
        self.status.setText(f"{left.directory}  vs  {right.directory}")

    def _show(self, comparison: ComparisonResult, findings: list[Finding], profile: str) -> None:
        rows = list(comparison.decay) + list(comparison.noise) + list(comparison.placement)
        self.table.setRowCount(len(rows))
        for r, item in enumerate(rows):
            values = [
                item.name,
                "" if item.baseline is None else f"{item.baseline:.3f}",
                "" if item.candidate is None else f"{item.candidate:.3f}",
                "" if item.delta is None else f"{item.delta:+.3f}",
                "" if item.delta_percent is None else f"{item.delta_percent:+.1f}",
                str(item.validity),
            ]
            for c, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setFlags(cell.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(r, c, cell)
        self.table.resizeColumnsToContents()
        self.text.setPlainText(format_comparison_report(comparison, findings, profile))
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        fr = comparison.frequency_response
        if fr is not None and fr.frequencies_hz.size:
            axes.semilogx(fr.frequencies_hz, fr.difference_db)
            axes.set_xlabel("Hz")
            axes.set_ylabel("Δ dB")
            axes.set_title("Frequency-response difference (candidate − baseline)")
            axes.grid(True, which="both", alpha=0.3)
        else:
            axes.text(0.5, 0.5, "No difference curve", ha="center", va="center")
            axes.set_axis_off()
        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _save(self) -> None:
        if self._comparison is None:
            QMessageBox.information(self, "Save comparison", "Run a comparison first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save comparison.json", "comparison.json", "JSON files (*.json)"
        )
        if not path:
            return
        try:
            save_comparison(path, self._comparison)
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Cannot save", str(exc))
            return
        self.status.setText(f"Wrote {path}")

    def _pick_into(self, field: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open session",
            "",
            "Session files (session.json);;JSON files (*.json);;All files (*)",
        )
        if path:
            field.setText(path)

    def _fill_next_path(self, path: str) -> None:
        if not self.baseline_path.text().strip():
            self.baseline_path.setText(path)
        else:
            self.candidate_path.setText(path)
