"""Application entry point for the GUI."""

from __future__ import annotations

import sys


def run_app(argv: list[str] | None = None) -> int:
    from PySide6.QtWidgets import QApplication

    from roomscope.ui.main_window import MainWindow

    app = QApplication.instance() or QApplication(argv if argv is not None else sys.argv)
    window = MainWindow()
    window.show()
    return int(app.exec())
