"""Application entry point for the GUI."""

from __future__ import annotations

import sys


def run_app(argv: list[str] | None = None) -> int:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from roomscope.i18n import activate
    from roomscope.ui.main_window import MainWindow

    activate(None)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    app.setDesktopFileName("roomscope")
    window = MainWindow()
    window.show()
    return int(app.exec())


def main() -> None:
    raise SystemExit(run_app())
