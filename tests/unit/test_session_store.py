from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.io.session_store import (
    IR_FILE,
    RESULT_FILE,
    SESSION_FILE,
    load_session,
    save_measurement,
)
from roomscope.io.wav import read_wav
from roomscope.models.configuration import SweepSettings
from roomscope.models.session import MeasurementSession
from tests.conftest import make_rir


def test_save_and_load_measurement(tmp_path: Path, short_sweep: SweepSettings) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.3)
    rec = synthetic_recording(short_sweep, ir, noise_rms=1e-5)
    result = analyze(rec, Reference.from_settings(short_sweep))
    session = MeasurementSession(
        room_name="Booth", sweep_settings=short_sweep, recording_path=str(tmp_path / "rec.wav")
    )
    out = tmp_path / "session"
    session_path = save_measurement(out, session, result, include_curves=False)
    assert session_path == out / SESSION_FILE
    assert (out / RESULT_FILE).is_file() and (out / IR_FILE).is_file()

    loaded = load_session(out)
    assert loaded.room_name == "Booth"
    assert loaded.impulse_response_path == IR_FILE
    assert loaded.result_path == RESULT_FILE
    assert loaded.recording_path == str(tmp_path / "rec.wav")
    assert loaded.analysis_summary["broadband_rt60_estimate_s"] is not None
    assert loaded.analysis_summary["bands"]["1 kHz"]["t30_s"] is not None

    stored_ir = read_wav(out / IR_FILE)
    assert np.allclose(stored_ir.samples, result.impulse_response.samples, atol=1e-6)
    payload = json.loads((out / RESULT_FILE).read_text())
    assert payload["schema_version"] == 1
    assert "edc_db" not in payload["decay"]["broadband"]
