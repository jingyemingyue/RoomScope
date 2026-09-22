"""Offscreen smoke test of the GUI: build the window, run a DAW-mode analysis, save a session."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from roomscope.core.pipeline import synthetic_recording
from roomscope.io.wav import write_wav
from roomscope.models.configuration import SweepSettings
from roomscope.ui.main_window import MainWindow
from tests.conftest import make_rir

pytestmark = pytest.mark.gui


def test_pyside6_version_is_visible_to_matplotlib() -> None:
    from roomscope.ui.qt import ensure_pyside6

    ensure_pyside6()
    import PySide6

    assert PySide6.__version__
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

    assert FigureCanvasQTAgg is not None


@pytest.fixture(scope="module")
def app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_daw_mode_end_to_end(app: QApplication, tmp_path: Path, short_sweep: SweepSettings) -> None:
    window = MainWindow()
    window.show()
    window.show_mode("universal_daw")
    assert window.stack.currentWidget() is window.daw

    page = window.daw
    page.sample_rate.setCurrentIndex(page.sample_rate.findData(short_sweep.sample_rate))
    page.duration.setValue(short_sweep.duration_s)
    page.generate_sweep_to(tmp_path / "sweep.wav")
    assert (tmp_path / "sweep.roomscope-sweep.json").is_file()
    assert window.state.reference is not None

    ir = make_rir(
        short_sweep.sample_rate, rt60_s=0.35, reflections=[(0.018, 0.35)], diffuse_level=0.01
    )
    recording = synthetic_recording(window.state.sweep_settings, ir, noise_rms=1e-5)
    rec_path = write_wav(
        tmp_path / "recording.wav", recording.samples, recording.sample_rate, subtype="FLOAT"
    )
    page.set_recording(rec_path)
    assert page.channel.count() == 2
    page.room.setText("Booth A")

    page.start_analysis(blocking=True)
    app.processEvents()
    assert window.state.result is not None
    assert window.stack.currentWidget() is window.results
    assert "RoomScope analysis" in window.results.text.toPlainText()
    assert window.results.table.rowCount() == 1 + len(window.state.result.decay.bands)
    assert window.state.findings

    out = tmp_path / "session"
    window.results.save_to(out)
    assert (out / "session.json").is_file()
    assert (out / "impulse_response.wav").is_file()
    assert "saved" in window.results.status.text()

    window.show_home()
    assert window.state.result is None
    window.close()


def test_standalone_page_builds(app: QApplication) -> None:
    window = MainWindow()
    window.show_mode("standalone")
    assert window.stack.currentWidget() is window.standalone
    # Either devices were listed or the backend is reported unavailable; both are acceptable.
    assert window.standalone.status.text()
    window.close()
