"""Main window: a stacked layout of Home -> Mode page -> Results."""

from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from roomscope import __version__
from roomscope.ui.pages import DawModePage, HomePage, StandalonePage
from roomscope.ui.results import ResultsPage
from roomscope.ui.state import MeasurementState

ABOUT_TEXT = (
    f"<b>RoomScope {__version__}</b><br>"
    "An open-source, DAW-independent recording environment analyzer.<br><br>"
    "Licensed under the Apache License, Version 2.0.<br>"
    "This program uses Qt and PySide6 (Copyright The Qt Company Ltd. and contributors) under the "
    "GNU Lesser General Public License v3; the Qt libraries are loaded as separate shared libraries "
    "and may be replaced by interface-compatible versions. NumPy, SciPy, matplotlib, soundfile "
    "(libsndfile, LGPL-2.1) and sounddevice (PortAudio) are used under their respective licenses; "
    "see docs/DEPENDENCIES.md.<br><br>"
    "Levels are digital (dBFS) unless a calibration is provided; RoomScope never reports dB SPL."
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"RoomScope {__version__}")
        self.resize(900, 720)
        self.state = MeasurementState()
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.home = HomePage()
        self.daw = DawModePage(self.state)
        self.standalone = StandalonePage(self.state)
        self.results = ResultsPage(self.state)
        for page in (self.home, self.daw, self.standalone, self.results):
            self.stack.addWidget(page)

        self.home.choose_mode.connect(self.show_mode)
        self.daw.analysis_finished.connect(self.show_results)
        self.standalone.analysis_finished.connect(self.show_results)
        self.daw.back.connect(self.show_home)
        self.standalone.back.connect(self.show_home)
        self.results.new_measurement.connect(self.show_home)

        file_menu = self.menuBar().addMenu("&File")
        new_action = QAction("&New Measurement", self)
        new_action.triggered.connect(self.show_home)
        quit_action = QAction("&Quit", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(new_action)
        file_menu.addAction(quit_action)
        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About RoomScope", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)
        self.show_home()

    def show_home(self) -> None:
        self.state.reset()
        self.stack.setCurrentWidget(self.home)

    def show_mode(self, mode: str) -> None:
        self.state.mode = mode
        if mode == "standalone":
            self.stack.setCurrentWidget(self.standalone)
        else:
            self.stack.setCurrentWidget(self.daw)

    def show_results(self) -> None:
        self.results.refresh()
        self.stack.setCurrentWidget(self.results)

    def _about(self) -> None:
        QMessageBox.about(self, "About RoomScope", ABOUT_TEXT)
