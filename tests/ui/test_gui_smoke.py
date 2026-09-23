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


def test_reopen_saved_session(
    app: QApplication, tmp_path: Path, short_sweep: SweepSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ROOMSCOPE_HOME", str(tmp_path / "home"))
    window = MainWindow()
    window.show()
    window.show_mode("universal_daw")
    page = window.daw
    page.sample_rate.setCurrentIndex(page.sample_rate.findData(short_sweep.sample_rate))
    page.duration.setValue(short_sweep.duration_s)
    page.generate_sweep_to(tmp_path / "sweep.wav")
    ir = make_rir(
        short_sweep.sample_rate, rt60_s=0.35, reflections=[(0.018, 0.35)], diffuse_level=0.01
    )
    recording = synthetic_recording(window.state.sweep_settings, ir, noise_rms=1e-5)
    rec_path = write_wav(
        tmp_path / "recording.wav", recording.samples, recording.sample_rate, subtype="FLOAT"
    )
    page.set_recording(rec_path)
    page.room.setText("Booth A")
    page.profile.setCurrentText("vocal")
    page.start_analysis(blocking=True)
    app.processEvents()
    out = tmp_path / "session"
    window.results.save_to(out)
    saved_rt60 = window.state.result.decay.broadband.rt60_estimate_s
    assert window.state.session.recording_profile == "vocal"

    window.show_home()
    assert window.state.result is None
    window.home.refresh_recent()
    assert window.home.recent.count() == 1
    assert "Booth A" in window.home.recent.item(0).text()

    window.home.list_folder(tmp_path)
    assert window.home.recent.count() == 1
    assert "Booth A" in window.home.recent.item(0).text()

    window.open_session_path(out)
    app.processEvents()
    assert window.stack.currentWidget() is window.results
    assert window.state.result is not None
    assert window.state.session.room_name == "Booth A"
    assert window.state.profile == "vocal"
    assert window.state.result.decay.broadband.rt60_estimate_s == saved_rt60
    assert window.state.result.impulse_response.samples.size > 0
    assert "RoomScope analysis" in window.results.text.toPlainText()
    assert "Interpretation (vocal profile):" in window.results.text.toPlainText()
    window.close()


def test_standalone_page_builds(app: QApplication) -> None:
    window = MainWindow()
    window.show_mode("standalone")
    assert window.stack.currentWidget() is window.standalone
    # Either devices were listed or the backend is reported unavailable; both are acceptable.
    assert window.standalone.status.text()
    window.close()


def test_demo_mode_uses_fake_backend(app: QApplication) -> None:
    window = MainWindow()
    window.show()
    window.show_mode("demo")
    app.processEvents()
    assert window.stack.currentWidget() is window.standalone
    assert window.standalone.demo_mode is True
    assert not window.standalone.demo_banner.isHidden()
    assert window.standalone.stop_button is not None
    assert "fake" in window.standalone.status.text().lower()
    window.close()


def test_compare_two_saved_sessions(
    app: QApplication, tmp_path: Path, short_sweep: SweepSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ROOMSCOPE_HOME", str(tmp_path / "home"))
    window = MainWindow()
    window.show()
    window.show_mode("universal_daw")
    page = window.daw
    page.sample_rate.setCurrentIndex(page.sample_rate.findData(short_sweep.sample_rate))
    page.duration.setValue(short_sweep.duration_s)
    page.generate_sweep_to(tmp_path / "sweep.wav")
    ir = make_rir(
        short_sweep.sample_rate, rt60_s=0.35, reflections=[(0.018, 0.35)], diffuse_level=0.01
    )
    recording = synthetic_recording(window.state.sweep_settings, ir, noise_rms=1e-5)
    rec_path = write_wav(
        tmp_path / "recording.wav", recording.samples, recording.sample_rate, subtype="FLOAT"
    )
    page.set_recording(rec_path)
    page.start_analysis(blocking=True)
    app.processEvents()
    first = tmp_path / "session-a"
    window.results.save_to(first)
    window.show_home()
    window.show_mode("universal_daw")
    page = window.daw
    page.sample_rate.setCurrentIndex(page.sample_rate.findData(short_sweep.sample_rate))
    page.duration.setValue(short_sweep.duration_s)
    page.generate_sweep_to(tmp_path / "sweep2.wav")
    page.set_recording(rec_path)
    page.start_analysis(blocking=True)
    app.processEvents()
    second = tmp_path / "session-b"
    window.results.save_to(second)

    window.show_compare()
    assert window.stack.currentWidget() is window.compare
    window.compare.set_paths(first, second)
    window.compare.same_gain.setChecked(True)
    window.compare.run_compare()
    app.processEvents()
    assert "RoomScope comparison" in window.compare.text.toPlainText()
    assert window.compare.table.rowCount() > 0
    assert window.compare._comparison is not None
    assert all(item.validity is not None for item in window.compare._comparison.decay)
    window.close()
