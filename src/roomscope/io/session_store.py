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
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from roomscope.errors import SessionError
from roomscope.io.wav import read_wav, write_wav
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
    return MeasurementSession.from_dict(_read_json(_session_file(path)))


def load_result(path: str | Path) -> AnalysisResult:
    """Load an :class:`AnalysisResult` from ``result.json``."""
    return AnalysisResult.from_dict(_read_json(Path(path)))


@dataclass(frozen=True)
class LoadedMeasurement:
    """A session directory after :func:`load_measurement`."""

    directory: Path
    session: MeasurementSession
    result: AnalysisResult


@dataclass(frozen=True)
class SessionListing:
    """One ``session.json`` found by :func:`list_sessions``."""

    path: Path
    session: MeasurementSession

    @property
    def label(self) -> str:
        room = self.session.room_name or "(unnamed room)"
        created = self.session.created_at
        rt60 = self.session.analysis_summary.get("broadband_rt60_estimate_s")
        rt60_text = f"RT60 {rt60:.2f} s" if isinstance(rt60, (int, float)) else "RT60 n/a"
        return f"{room}  ·  {created}  ·  {rt60_text}"


def load_measurement(path: str | Path) -> LoadedMeasurement:
    """Load session metadata, ``result.json`` and the IR WAV from a directory."""
    session_file = _session_file(path)
    directory = session_file.parent
    session = MeasurementSession.from_dict(_read_json(session_file))
    result_path = _resolve_member(directory, session.result_path, RESULT_FILE)
    if not result_path.is_file():
        raise SessionError(f"result.json not found next to {session_file}")
    result = load_result(result_path)
    ir_path = _resolve_member(directory, session.impulse_response_path, IR_FILE)
    if ir_path.is_file():
        ir = read_wav(ir_path)
        samples = ir.samples if ir.samples.ndim == 1 else ir.samples[:, 0]
        result = replace(
            result,
            impulse_response=replace(
                result.impulse_response, samples=samples, sample_rate=ir.sample_rate
            ),
        )
    elif result.impulse_response.samples.size == 0:
        raise SessionError(
            f"impulse_response.wav not found next to {session_file} and result.json "
            "has no IR samples"
        )
    return LoadedMeasurement(directory=directory, session=session, result=result)


def list_sessions(root: str | Path, *, max_depth: int = 2) -> list[SessionListing]:
    """Find ``session.json`` files under ``root``, newest ``created_at`` first."""
    base = Path(root)
    if not base.is_dir():
        raise SessionError(f"not a directory: {base}")
    found: list[SessionListing] = []
    for candidate in base.rglob(SESSION_FILE):
        try:
            rel = candidate.relative_to(base)
        except ValueError:
            continue
        if len(rel.parts) - 1 > max_depth:
            continue
        if any(part.startswith(".") for part in rel.parts[:-1]):
            continue
        try:
            found.append(SessionListing(path=candidate.parent, session=load_session(candidate)))
        except SessionError:
            continue
    found.sort(key=lambda item: item.session.created_at, reverse=True)
    return found


def _session_file(path: str | Path) -> Path:
    p = Path(path)
    if p.is_dir():
        p = p / SESSION_FILE
    if not p.is_file():
        raise SessionError(f"session file not found: {p}")
    return p


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SessionError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SessionError(f"{path} is not a JSON object")
    return data


def _resolve_member(directory: Path, stored: str | None, default_name: str) -> Path:
    if not stored:
        return directory / default_name
    candidate = Path(stored)
    if candidate.is_absolute():
        return candidate
    return directory / candidate
