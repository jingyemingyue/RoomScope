"""Untrusted session, sidecar and WAV files raise RoomScopeError only."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.errors import InvalidAudioError, RoomScopeError, SessionError
from roomscope.io.jsonutil import MAX_JSON_BYTES, MAX_JSON_DEPTH, read_json_object
from roomscope.io.project_store import load_project
from roomscope.io.session_store import load_comparison, load_measurement, load_session
from roomscope.io.wav import read_sweep_sidecar, read_wav
from roomscope.models.audio import AudioSignal
from roomscope.models.configuration import SweepSettings
from tests.conftest import make_rir


def test_malformed_session_json_is_roomscope_error(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SessionError):
        load_session(path)


def test_oversized_session_json_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    path.write_bytes(b"{" + b" " * (MAX_JSON_BYTES + 1) + b"}")
    with pytest.raises(SessionError, match="refused"):
        load_session(path)


def test_session_json_array_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(SessionError, match="not a JSON object"):
        load_session(path)


def test_truncated_wav_is_invalid_audio(tmp_path: Path) -> None:
    path = tmp_path / "broken.wav"
    path.write_bytes(b"RIFF\x00\x00\x00\x00WAVE")
    with pytest.raises(InvalidAudioError):
        read_wav(path)


def test_nan_audio_is_invalid() -> None:
    with pytest.raises(InvalidAudioError, match="NaN"):
        AudioSignal(samples=np.array([0.0, np.nan]), sample_rate=48000)


def test_sidecar_must_be_an_object(tmp_path: Path) -> None:
    path = tmp_path / "sweep.roomscope-sweep.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(RoomScopeError):
        read_sweep_sidecar(path)


def test_missing_result_json_is_session_error(tmp_path: Path) -> None:
    session = tmp_path / "session.json"
    session.write_text(json.dumps({"schema_version": 1, "room_name": "X"}), encoding="utf-8")
    with pytest.raises(SessionError):
        load_measurement(tmp_path)


def test_deeply_nested_json_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "session.json"
    depth = MAX_JSON_DEPTH + 8
    path.write_text("{" * depth + "}" * depth, encoding="utf-8")
    with pytest.raises(SessionError, match="deeper"):
        read_json_object(path, kind="session")


def test_deeply_nested_project_is_session_error(tmp_path: Path) -> None:
    path = tmp_path / "project.json"
    depth = MAX_JSON_DEPTH + 2
    path.write_text("{" * depth + "}" * depth, encoding="utf-8")
    with pytest.raises(SessionError, match="deeper"):
        load_project(tmp_path)


def test_infinite_audio_is_invalid() -> None:
    with pytest.raises(InvalidAudioError, match="infinite"):
        AudioSignal(samples=np.array([0.0, np.inf]), sample_rate=48000)


def test_garbage_wav_is_invalid_audio(tmp_path: Path) -> None:
    path = tmp_path / "garbage.wav"
    path.write_bytes(b"this is not a RIFF wave file at all")
    with pytest.raises(InvalidAudioError):
        read_wav(path)


def test_oversized_sidecar_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "sweep.roomscope-sweep.json"
    path.write_bytes(b"{" + b" " * 1_000_001 + b"}")
    with pytest.raises(RoomScopeError):
        read_sweep_sidecar(path)


def test_malformed_project_json_is_session_error(tmp_path: Path) -> None:
    (tmp_path / "project.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(SessionError):
        load_project(tmp_path)


def test_malformed_result_json_is_session_error(tmp_path: Path) -> None:
    (tmp_path / "session.json").write_text(
        json.dumps({"schema_version": 1, "room_name": "X"}), encoding="utf-8"
    )
    (tmp_path / "result.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(SessionError):
        load_measurement(tmp_path)


def test_malformed_comparison_json_is_session_error(tmp_path: Path) -> None:
    path = tmp_path / "comparison.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(SessionError):
        load_comparison(path)


def test_comparison_json_array_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "comparison.json"
    path.write_text("[]", encoding="utf-8")
    with pytest.raises(SessionError, match="not a JSON object"):
        load_comparison(path)


def test_oversized_comparison_json_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "comparison.json"
    path.write_bytes(b"{" + b" " * (MAX_JSON_BYTES + 1) + b"}")
    with pytest.raises(SessionError, match="refused"):
        load_comparison(path)


def test_deeply_nested_comparison_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "comparison.json"
    depth = MAX_JSON_DEPTH + 4
    path.write_text("{" * depth + "}" * depth, encoding="utf-8")
    with pytest.raises(SessionError, match="deeper"):
        load_comparison(path)


def test_loopback_that_is_a_microphone_does_not_raise(
    short_sweep: SweepSettings,
) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.4, reflections=[(0.018, 0.35)])
    rec = synthetic_recording(short_sweep, ir, noise_rms=1e-5)
    result = analyze(rec, Reference.from_settings(short_sweep), loopback=rec)
    assert result.impulse_response.loopback is not None
    assert result.impulse_response.loopback.compensation_applied is False
    assert result.impulse_response.loopback.reason is not None


def test_src_does_not_use_pickle_eval_or_shell() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "check_src_safety", Path("scripts") / "check_src_safety.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.check(Path("src")) == []
