"""Measurement session model.

A session records everything needed to re-analyse a measurement later: the
sweep definition, the file paths of the raw audio, the equipment metadata and
the analysis summary. Raw audio is never embedded in the JSON; it stays in WAV
files next to the session file so that the measurement can be repeated.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field, fields
from datetime import UTC, datetime
from typing import Any

from roomscope.errors import SessionError
from roomscope.models.configuration import AnalysisSettings, SweepSettings

SESSION_SCHEMA_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


@dataclass
class MeasurementSession:
    """One measurement of one position in one room."""

    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: str = field(default_factory=utc_now_iso)
    mode: str = "universal_daw"  # or "standalone"
    room_name: str = ""
    measurement_position: str = ""
    microphone_name: str = ""
    microphone_type: str = ""
    microphone_calibration: str = "uncalibrated"
    audio_interface: str = ""
    input_channel: int | None = None
    output_channel: int | None = None
    loudspeaker: str = ""
    sample_rate: int | None = None
    bit_depth: str | None = None
    sweep_settings: SweepSettings = field(default_factory=SweepSettings)
    analysis_settings: AnalysisSettings = field(default_factory=AnalysisSettings)
    #: Paths are stored relative to the session directory when possible.
    sweep_path: str | None = None
    recording_path: str | None = None
    impulse_response_path: str | None = None
    result_path: str | None = None
    #: Scalar summary of the analysis (no curves) for quick listing.
    analysis_summary: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    #: Recording profile used when the result was last interpreted.
    recording_profile: str = "generic"
    schema_version: int = SESSION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["sweep_settings"] = self.sweep_settings.to_dict()
        data["analysis_settings"] = self.analysis_settings.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MeasurementSession:
        if not isinstance(data, dict):
            raise SessionError("session data must be a JSON object")
        version = data.get("schema_version", SESSION_SCHEMA_VERSION)
        if version != SESSION_SCHEMA_VERSION:
            raise SessionError(f"unsupported session schema version {version}")
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise SessionError(f"unknown session fields: {sorted(unknown)}")
        payload = dict(data)
        if "sweep_settings" in payload:
            payload["sweep_settings"] = SweepSettings.from_dict(payload["sweep_settings"])
        if "analysis_settings" in payload:
            payload["analysis_settings"] = AnalysisSettings.from_dict(payload["analysis_settings"])
        return cls(**payload)
