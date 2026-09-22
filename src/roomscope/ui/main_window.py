"""Main window: a stacked layout of Home -> Mode page -> Results."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QStackedWidget

from roomscope import __version__
from roomscope.errors import RoomScopeError
from roomscope.i18n import _
from roomscope.interpretation import interpret
from roomscope.io.recent import remember_session
from roomscope.io.session_store import load_measurement
from roomscope.ui.compare_view import ComparePage
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
        self.compare = ComparePage()
        for page in (self.home, self.daw, self.standalone, self.results, self.compare):
            self.stack.addWidget(page)

        self.home.choose_mode.connect(self.show_mode)
        self.home.open_session.connect(self.choose_session)
        self.home.open_recent.connect(self.open_session_path)
        self.home.compare_requested.connect(self.show_compare)
        self.daw.analysis_finished.connect(self.show_results)
        self.standalone.analysis_finished.connect(self.show_results)
        self.daw.back.connect(self.show_home)
        self.standalone.back.connect(self.show_home)
        self.results.new_measurement.connect(self.show_home)
        self.compare.back.connect(self.show_home)

        file_menu = self.menuBar().addMenu(_("&File"))
        new_action = QAction(_("&New Measurement"), self)
        new_action.triggered.connect(self.show_home)
        open_action = QAction(_("&Open Session..."), self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.choose_session)
        compare_action = QAction(_("&Compare Sessions..."), self)
        compare_action.triggered.connect(self.show_compare)
        settings_action = QAction(_("&Settings..."), self)
        settings_action.triggered.connect(self.show_settings)
        quit_action = QAction(_("&Quit"), self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(compare_action)
        file_menu.addSeparator()
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        help_menu = self.menuBar().addMenu(_("&Help"))
        about_action = QAction(_("&About RoomScope"), self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)
        self.show_home()

    def show_home(self) -> None:
        self.state.reset()
        self.home.refresh_recent()
        self.stack.setCurrentWidget(self.home)

    def choose_session(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open session",
            "",
            "Session files (session.json);;JSON files (*.json);;All files (*)",
        )
        if path:
            self.open_session_path(path)

    def open_session_path(self, path: str | Path) -> None:
        try:
            loaded = load_measurement(path)
        except RoomScopeError as exc:
            QMessageBox.critical(self, "Cannot open session", str(exc))
            return
        self.state.session = loaded.session
        self.state.result = loaded.result
        self.state.mode = loaded.session.mode
        profile = loaded.session.recording_profile or "generic"
        try:
            findings = interpret(loaded.result, profile)
        except RoomScopeError:
            profile = "generic"
            findings = interpret(loaded.result, profile)
        self.state.profile = profile
        self.state.findings = findings
        remember_session(loaded.directory)
        self.show_results()

    def show_mode(self, mode: str) -> None:
        if mode == "demo":
            self.state.mode = "standalone"
            self.standalone.demo_mode = True
            self.standalone.refresh_devices()
            self.stack.setCurrentWidget(self.standalone)
            return
        self.state.mode = mode
        self.standalone.demo_mode = False
        if mode == "standalone":
            self.standalone.refresh_devices()
            self.stack.setCurrentWidget(self.standalone)
        else:
            self.stack.setCurrentWidget(self.daw)

    def show_results(self) -> None:
        self.results.refresh()
        self.stack.setCurrentWidget(self.results)

    def show_compare(self) -> None:
        self.compare.browser.refresh_recent()
        selected = self.home.browser.selected_paths()
        if len(selected) == 2:
            self.compare.set_paths(selected[0], selected[1])
        self.stack.setCurrentWidget(self.compare)

    def show_settings(self) -> None:
        from roomscope.ui.settings_dialog import SettingsDialog

        SettingsDialog(self).exec()

    def _about(self) -> None:
        QMessageBox.about(self, _("About RoomScope"), ABOUT_TEXT)
