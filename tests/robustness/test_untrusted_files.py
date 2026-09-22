"""Untrusted session, sidecar and WAV files raise RoomScopeError only."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from roomscope.errors import InvalidAudioError, RoomScopeError, SessionError
from roomscope.io.jsonutil import MAX_JSON_BYTES
from roomscope.io.session_store import load_measurement, load_session
from roomscope.io.wav import read_sweep_sidecar, read_wav
from roomscope.models.audio import AudioSignal


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


def test_src_does_not_use_pickle_or_eval() -> None:
    banned = ("import pickle", "pickle.loads", "numpy.load(", "eval(")
    root = Path("src/roomscope")
    hits: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            if token in text:
                hits.append(f"{path}: {token}")
    assert hits == []
