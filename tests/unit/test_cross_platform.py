"""Regressions found by the 2026-09 cross-platform audit (Windows / macOS paths
that the Linux CI does not exercise). Each test emulates the platform
behaviour it guards against."""

from __future__ import annotations

import io
import json
import logging
import os
import sys
from pathlib import Path

import pytest

from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.errors import SessionError
from roomscope.i18n import normalize_lang
from roomscope.io.project_store import (
    add_session,
    list_project_sessions,
    project_file,
    save_project,
)
from roomscope.io.session_store import _copy_into, bundle_session, save_measurement
from roomscope.models.configuration import SweepSettings
from roomscope.models.project import Project
from roomscope.models.session import MeasurementSession
from tests.conftest import make_rir


@pytest.fixture(scope="module")
def result(short_sweep: SweepSettings):  # type: ignore[no-untyped-def]
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.3)
    return analyze(
        synthetic_recording(short_sweep, ir, noise_rms=1e-5), Reference.from_settings(short_sweep)
    )


def test_project_stores_forward_slashes_and_reads_backslashes(tmp_path: Path, result) -> None:  # type: ignore[no-untyped-def]
    project_dir = tmp_path / "room"
    save_project(project_dir, Project(name="Booth"))
    session = project_dir / "sessions" / "pos-a"
    save_measurement(session, MeasurementSession(room_name="Booth"), result, include_curves=False)
    add_session(project_dir, session, position="desk")
    raw = json.loads(project_file(project_dir).read_text(encoding="utf-8"))
    stored = raw["positions"][0]["session_dirs"][0]
    assert stored == "sessions/pos-a"

    # A project written on Windows: the same entry with a backslash.
    raw["positions"][0]["session_dirs"] = ["sessions\\pos-a"]
    project_file(project_dir).write_text(json.dumps(raw), encoding="utf-8")
    items = list_project_sessions(project_dir)
    assert items[0] == ("desk", items[0][1])
    assert items[0][1].resolve() == session.resolve()
    assert len(items) == 1

    # Adding the same session again (the path spelled the other way) is a no-op.
    add_session(project_dir, session, position="desk")
    raw = json.loads(project_file(project_dir).read_text(encoding="utf-8"))
    assert len(raw["positions"][0]["session_dirs"]) == 1


def test_bundle_inside_the_session_folder_is_refused(tmp_path: Path, result) -> None:  # type: ignore[no-untyped-def]
    out = tmp_path / "session"
    save_measurement(out, MeasurementSession(room_name="Booth"), result, include_curves=False)
    with pytest.raises(SessionError, match="outside the session folder"):
        bundle_session(out, out)
    with pytest.raises(SessionError, match="outside the session folder"):
        bundle_session(out, out / "report.zip")
    assert not (out / "session.zip").exists()


def test_copy_onto_the_same_file_is_a_no_op(tmp_path: Path) -> None:
    """On a case-insensitive file system Recording.wav and recording.wav are one
    file; a hard link emulates that on Linux."""
    src = tmp_path / "Recording.wav"
    src.write_bytes(b"RIFF")
    dest = tmp_path / "recording.wav"
    os.link(src, dest)
    assert _copy_into(src, dest) == dest
    assert src.read_bytes() == b"RIFF"


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("zh-Hans-CN", "zh_CN"),
        ("zh-Hans", "zh_CN"),
        ("Chinese (Simplified)_China", "zh_CN"),
        (["zh_CN", "UTF-8"][0], "zh_CN"),
        ("en-US", "en_US"),
    ],
)
def test_os_language_tags_are_normalised(tag: str, expected: str) -> None:
    assert normalize_lang(tag) == expected


def test_session_list_survives_dates_windows_cannot_convert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("PySide6")
    from datetime import datetime

    from roomscope.ui import browser

    def refuse(self: datetime, tz: object = None) -> datetime:
        raise OSError(22, "Invalid argument")

    class Moment(datetime):
        astimezone = refuse  # type: ignore[assignment]

    monkeypatch.setattr(browser, "_when", browser._when)
    import datetime as datetime_module

    monkeypatch.setattr(datetime_module, "datetime", Moment)
    assert browser._when("1900-01-01T00:00:00+00:00") == "1900-01-01T00:00:00+00:00"
    assert browser._when("not a date") == "not a date"


def test_log_rotation_keeps_logging_when_the_file_is_locked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from logging.handlers import RotatingFileHandler

    from roomscope.logging_config import _SharedRotatingFileHandler

    def locked(self: RotatingFileHandler) -> None:
        raise PermissionError(32, "The process cannot access the file")

    monkeypatch.setattr(RotatingFileHandler, "doRollover", locked)
    handler = _SharedRotatingFileHandler(tmp_path / "roomscope.log", maxBytes=10, backupCount=1)
    logger = logging.getLogger("roomscope-test-rotation")
    logger.propagate = False
    logger.addHandler(handler)
    errors = io.StringIO()
    monkeypatch.setattr(sys, "stderr", errors)
    try:
        for index in range(5):
            logger.warning("record %d is longer than the limit", index)
    finally:
        logger.removeHandler(handler)
        handler.close()
    assert "Logging error" not in errors.getvalue()
    assert "record 4" in (tmp_path / "roomscope.log").read_text(encoding="utf-8")


def test_default_devices_are_marked(monkeypatch: pytest.MonkeyPatch) -> None:
    """sounddevice returns the defaults as an indexable _InputOutputPair."""
    from roomscope.audio import devices

    class Pair:
        def __init__(self, a: int, b: int) -> None:
            self._items = [a, b]

        def __getitem__(self, index: int) -> int:
            return self._items[index]

    class FakeSd:
        class default:  # noqa: N801 - mirrors sounddevice.default
            device = Pair(1, 0)

        @staticmethod
        def query_devices() -> list[dict[str, object]]:
            return [
                {
                    "name": "Speakers",
                    "hostapi": 0,
                    "max_input_channels": 0,
                    "max_output_channels": 2,
                    "default_samplerate": 48000.0,
                },
                {
                    "name": "Mic",
                    "hostapi": 0,
                    "max_input_channels": 1,
                    "max_output_channels": 0,
                    "default_samplerate": 48000.0,
                },
            ]

        @staticmethod
        def query_hostapis() -> list[dict[str, object]]:
            return [
                {
                    "name": "Windows WASAPI",
                    "devices": [0, 1],
                    "default_input_device": 1,
                    "default_output_device": 0,
                }
            ]

    monkeypatch.setattr(devices, "sounddevice_module", lambda: FakeSd)
    listed = devices.list_devices()
    assert listed[1].is_default_input and not listed[1].is_default_output
    assert listed[0].is_default_output and not listed[0].is_default_input


def test_cli_output_to_a_pipe_is_utf8(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib

    cli = importlib.import_module("roomscope.cli.main")

    raw = io.BytesIO()
    stream = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
    monkeypatch.delenv("PYTHONIOENCODING", raising=False)
    monkeypatch.setattr(sys, "stdout", stream)
    cli._utf8_when_redirected()
    sys.stdout.write("Δ → 录音棚\n")
    sys.stdout.flush()
    assert raw.getvalue().decode("utf-8").strip() == "Δ → 录音棚"
