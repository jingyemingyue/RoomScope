"""Saving and loading measurement sessions.

A session directory contains::

    session.json            metadata + analysis summary (MeasurementSession)
    result.json             full AnalysisResult (metrics and curves)
    impulse_response.wav    raw impulse response, 32-bit float

Raw sweep and recording files are referenced by path (relative when they are
inside the session directory) and never modified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from roomscope.errors import SessionError
from roomscope.io.wav import write_wav
from roomscope.models.result import AnalysisResult, Validity
from roomscope.models.session import MeasurementSession

SESSION_FILE = "session.json"
RESULT_FILE = "result.json"
IR_FILE = "impulse_response.wav"


def _relative(path: str | Path | None, base: Path) -> str | None:
    if path is None:
        return None
    p = Path(path).resolve()
    try:
        return str(p.relative_to(base.resolve()))
    except ValueError:
        return str(p)


def _metric_value(metric: dict[str, Any]) -> float | None:
    return metric["seconds"] if metric.get("validity") == str(Validity.VALID) else None


def result_summary(result: AnalysisResult) -> dict[str, Any]:
    """Scalar summary of a result for listings and the session file."""
    broadband = result.decay.broadband
    bands = {
        band.band_label: {
            "rt60_estimate_s": band.rt60_estimate_s,
            "rt60_basis": band.rt60_basis,
            "t20_s": band.t20.seconds if band.t20.validity is Validity.VALID else None,
            "t30_s": band.t30.seconds if band.t30.validity is Validity.VALID else None,
            "edt_s": band.edt.seconds if band.edt.validity is Validity.VALID else None,
        }
        for band in result.decay.bands
    }
    return {
        "created_at": result.created_at,
        "sample_rate": result.sample_rate,
        "broadband_rt60_estimate_s": broadband.rt60_estimate_s,
        "broadband_rt60_basis": broadband.rt60_basis,
        "broadband_edt_s": broadband.edt.seconds
        if broadband.edt.validity is Validity.VALID
        else None,
        "broadband_peak_to_noise_db": broadband.peak_to_noise_db,
        "bands": bands,
        "noise_rms_dbfs": result.noise.rms_dbfs,
        "hum_detected": [h.base_hz for h in result.noise.hum if h.detected],
        "early_reflections": [r.to_dict() for r in result.reflections.reflections[:5]],
        "resonance_candidates_hz": [c.frequency_hz for c in result.resonances.candidates],
        "direct_sound_confidence": result.impulse_response.direct_sound_confidence,
        "warnings": list(result.warnings),
    }


def save_measurement(
    directory: str | Path,
    session: MeasurementSession,
    result: AnalysisResult,
    *,
    include_curves: bool = True,
) -> Path:
    """Write session.json, result.json and impulse_response.wav into ``directory``."""
    base = Path(directory)
    base.mkdir(parents=True, exist_ok=True)
    ir_path = write_wav(
        base / IR_FILE, result.impulse_response.samples, result.sample_rate, subtype="FLOAT"
    )
    result_path = base / RESULT_FILE
    try:
        result_path.write_text(
            json.dumps(result.to_dict(include_curves), indent=1), encoding="utf-8"
        )
    except (OSError, TypeError, ValueError) as exc:
        raise SessionError(f"cannot write {result_path}: {exc}") from exc
    session.sample_rate = result.sample_rate
    session.impulse_response_path = _relative(ir_path, base)
    session.result_path = _relative(result_path, base)
    session.sweep_path = _relative(session.sweep_path, base)
    session.recording_path = _relative(session.recording_path, base)
    session.analysis_summary = result_summary(result)
    session_path = base / SESSION_FILE
    try:
        session_path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
    except (OSError, TypeError, ValueError) as exc:
        raise SessionError(f"cannot write {session_path}: {exc}") from exc
    return session_path


def load_session(path: str | Path) -> MeasurementSession:
    """Load a session from ``session.json`` or from its directory."""
    p = Path(path)
    if p.is_dir():
        p = p / SESSION_FILE
    if not p.is_file():
        raise SessionError(f"session file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SessionError(f"cannot read {p}: {exc}") from exc
    return MeasurementSession.from_dict(data)
