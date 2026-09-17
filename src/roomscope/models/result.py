"""Analysis result models.

Every metric carries its unit in the field name (``_s``, ``_hz``, ``_db``,
``_dbfs``, ``_ms``) and a :class:`Validity` so that front ends can never show a
number without knowing whether it is trustworthy. Curves are kept as NumPy
arrays in memory; :meth:`AnalysisResult.to_dict` converts them for JSON export.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]

RESULT_SCHEMA_VERSION = 1


class Validity(StrEnum):
    """Whether a metric may be shown as a measured value."""

    VALID = "valid"
    INSUFFICIENT_RANGE = "insufficient_decay_range"
    UNRELIABLE = "unreliable"
    NOT_COMPUTED = "not_computed"


def _array_to_list(values: FloatArray | None, decimals: int = 4) -> list[float] | None:
    if values is None:
        return None
    return [float(v) for v in np.round(values, decimals)]


@dataclass(frozen=True)
class DecayMetric:
    """One reverberation-time estimate (EDT, T20 or T30) extrapolated to 60 dB."""

    name: str
    seconds: float | None
    validity: Validity
    #: Evaluation range on the Schroeder curve (dB, e.g. (-5, -25) for T20).
    evaluation_range_db: tuple[float, float]
    #: ISO 3382-1 "degree of non-linearity" in permille: 1000 * (1 - r^2).
    nonlinearity_permille: float | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "seconds": self.seconds,
            "validity": str(self.validity),
            "evaluation_range_db": list(self.evaluation_range_db),
            "nonlinearity_permille": self.nonlinearity_permille,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class BandDecay:
    """Decay analysis of one frequency band (or the broadband IR)."""

    band_label: str
    center_hz: float | None
    low_hz: float | None
    high_hz: float | None
    #: Level of the noise floor relative to the Schroeder curve start (dB).
    noise_floor_db: float
    #: Dynamic range available for decay evaluation (dB above the noise floor).
    peak_to_noise_db: float
    #: Truncation point of the Schroeder integration (s from IR start).
    truncation_time_s: float
    edt: DecayMetric
    t20: DecayMetric
    t30: DecayMetric
    #: Estimated RT60 and which metric it is based on ("T30" preferred, then "T20").
    rt60_estimate_s: float | None
    rt60_basis: str | None
    #: ISO 3382-1 curvature C = 100 * (T30 / T20 - 1) in percent.
    curvature_percent: float | None
    #: Bandwidth-time product B*T of the band filter; low values mean the filter
    #: ringing dominates (Jacobsen & Rindel 1987).
    filter_bt_product: float | None
    filter_warning: str | None
    #: Decimated Schroeder decay curve for display and export.
    edc_time_s: FloatArray = field(repr=False)
    edc_db: FloatArray = field(repr=False)

    def to_dict(self, include_curves: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "band_label": self.band_label,
            "center_hz": self.center_hz,
            "low_hz": self.low_hz,
            "high_hz": self.high_hz,
            "noise_floor_db": self.noise_floor_db,
            "peak_to_noise_db": self.peak_to_noise_db,
            "truncation_time_s": self.truncation_time_s,
            "edt": self.edt.to_dict(),
            "t20": self.t20.to_dict(),
            "t30": self.t30.to_dict(),
            "rt60_estimate_s": self.rt60_estimate_s,
            "rt60_basis": self.rt60_basis,
            "curvature_percent": self.curvature_percent,
            "filter_bt_product": self.filter_bt_product,
            "filter_warning": self.filter_warning,
        }
        if include_curves:
            data["edc_time_s"] = _array_to_list(self.edc_time_s)
            data["edc_db"] = _array_to_list(self.edc_db, 2)
        return data


@dataclass(frozen=True)
class DecayResult:
    method: str
    broadband: BandDecay
    bands: tuple[BandDecay, ...]

    def to_dict(self, include_curves: bool = True) -> dict[str, Any]:
        return {
            "method": self.method,
            "broadband": self.broadband.to_dict(include_curves),
            "bands": [b.to_dict(include_curves) for b in self.bands],
        }


@dataclass(frozen=True)
class ImpulseResponseResult:
    sample_rate: int
    #: Impulse response samples (linear amplitude, relative units). The first
    #: sample is ``pre_delay_samples`` before the detected direct sound.
    samples: FloatArray = field(repr=False)
    direct_sound_index: int
    pre_delay_samples: int
    peak_value: float
    #: Length of IR that is fully supported by the recording (s).
    valid_length_s: float
    #: Ratio (dB) between the direct-sound peak and the strongest content before
    #: it (harmonic distortion pre-responses, noise). High is good.
    pre_peak_margin_db: float
    direct_sound_confidence: str
    #: Estimated start of the sweep in the recording (s).
    sweep_start_in_recording_s: float
    notes: tuple[str, ...] = ()

    @property
    def direct_sound_time_s(self) -> float:
        return self.direct_sound_index / self.sample_rate

    def to_dict(self, include_curves: bool = False) -> dict[str, Any]:
        data: dict[str, Any] = {
            "sample_rate": self.sample_rate,
            "length_samples": int(self.samples.shape[0]),
            "direct_sound_index": self.direct_sound_index,
            "direct_sound_time_s": self.direct_sound_time_s,
            "pre_delay_samples": self.pre_delay_samples,
            "peak_value": self.peak_value,
            "valid_length_s": self.valid_length_s,
            "pre_peak_margin_db": self.pre_peak_margin_db,
            "direct_sound_confidence": self.direct_sound_confidence,
            "sweep_start_in_recording_s": self.sweep_start_in_recording_s,
            "notes": list(self.notes),
        }
        if include_curves:
            data["samples"] = _array_to_list(self.samples, 8)
        return data


@dataclass(frozen=True)
class FrequencyResponseResult:
    frequencies_hz: FloatArray = field(repr=False)
    #: Unsmoothed magnitude (dB, relative). Always preserved.
    magnitude_db_raw: FloatArray = field(repr=False)
    #: Smoothed magnitude (dB, relative) or ``None`` when smoothing is disabled.
    magnitude_db_smoothed: FloatArray | None = field(repr=False)
    smoothing_fraction: int
    window_s: float
    reference: str = "relative dB (0 dB = flat loopback of the reference sweep)"

    def to_dict(self, include_curves: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "smoothing_fraction": self.smoothing_fraction,
            "window_s": self.window_s,
            "reference": self.reference,
            "points": int(self.frequencies_hz.shape[0]),
        }
        if include_curves:
            data["frequencies_hz"] = _array_to_list(self.frequencies_hz, 3)
            data["magnitude_db_raw"] = _array_to_list(self.magnitude_db_raw, 2)
            data["magnitude_db_smoothed"] = _array_to_list(self.magnitude_db_smoothed, 2)
        return data


@dataclass(frozen=True)
class HumCandidate:
    base_hz: float
    #: (frequency_hz, prominence_db) for each detected harmonic.
    harmonics: tuple[tuple[float, float], ...]
    strongest_prominence_db: float | None
    detected: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_hz": self.base_hz,
            "harmonics": [list(h) for h in self.harmonics],
            "strongest_prominence_db": self.strongest_prominence_db,
            "detected": self.detected,
        }


@dataclass(frozen=True)
class NoiseResult:
    #: Where the quiet segment came from ("pre-sweep", "tail") or None.
    segment_source: str | None
    segment_start_s: float | None
    segment_duration_s: float | None
    #: RMS level in dBFS (AES17 convention: a full-scale sine reads 0 dBFS).
    rms_dbfs: float | None
    peak_dbfs: float | None
    #: (center_hz, level_dbfs) per octave band.
    band_levels_dbfs: tuple[tuple[float, float], ...]
    psd_frequencies_hz: FloatArray | None = field(repr=False)
    psd_db: FloatArray | None = field(repr=False)
    hum: tuple[HumCandidate, ...] = ()
    calibration: str = "uncalibrated: levels are dBFS, not dB SPL"
    notes: tuple[str, ...] = ()

    def to_dict(self, include_curves: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "segment_source": self.segment_source,
            "segment_start_s": self.segment_start_s,
            "segment_duration_s": self.segment_duration_s,
            "rms_dbfs": self.rms_dbfs,
            "peak_dbfs": self.peak_dbfs,
            "band_levels_dbfs": [list(b) for b in self.band_levels_dbfs],
            "hum": [h.to_dict() for h in self.hum],
            "calibration": self.calibration,
            "notes": list(self.notes),
        }
        if include_curves:
            data["psd_frequencies_hz"] = _array_to_list(self.psd_frequencies_hz, 3)
            data["psd_db"] = _array_to_list(self.psd_db, 2)
        return data


@dataclass(frozen=True)
class Reflection:
    delay_ms: float
    relative_db: float

    def to_dict(self) -> dict[str, Any]:
        return {"delay_ms": self.delay_ms, "relative_db": self.relative_db}


@dataclass(frozen=True)
class ReflectionsResult:
    direct_sound_time_s: float
    direct_sound_confidence: str
    window_ms: tuple[float, float]
    threshold_db: float
    reflections: tuple[Reflection, ...]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "direct_sound_time_s": self.direct_sound_time_s,
            "direct_sound_confidence": self.direct_sound_confidence,
            "window_ms": list(self.window_ms),
            "threshold_db": self.threshold_db,
            "reflections": [r.to_dict() for r in self.reflections],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ResonanceCandidate:
    frequency_hz: float
    level_above_baseline_db: float
    #: Time for the narrow-band envelope to fall 20 dB (s), or None.
    narrowband_decay_20db_s: float | None
    #: Same measure for the analysis filter alone (its ringing), for comparison.
    filter_ringing_20db_s: float | None
    #: True only when the measured decay is clearly longer than the filter ringing.
    decay_distinguishable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "frequency_hz": self.frequency_hz,
            "level_above_baseline_db": self.level_above_baseline_db,
            "narrowband_decay_20db_s": self.narrowband_decay_20db_s,
            "filter_ringing_20db_s": self.filter_ringing_20db_s,
            "decay_distinguishable": self.decay_distinguishable,
        }


@dataclass(frozen=True)
class ResonanceResult:
    max_frequency_hz: float
    candidates: tuple[ResonanceCandidate, ...]
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_frequency_hz": self.max_frequency_hz,
            "candidates": [c.to_dict() for c in self.candidates],
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class AnalysisResult:
    """Complete output of :func:`roomscope.core.pipeline.analyze`."""

    created_at: str
    sample_rate: int
    sweep_settings: dict[str, Any]
    analysis_settings: dict[str, Any]
    impulse_response: ImpulseResponseResult
    decay: DecayResult
    frequency_response: FrequencyResponseResult
    noise: NoiseResult
    reflections: ReflectionsResult
    resonances: ResonanceResult
    warnings: tuple[str, ...] = ()
    schema_version: int = RESULT_SCHEMA_VERSION

    def to_dict(self, include_curves: bool = True) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "sample_rate": self.sample_rate,
            "sweep_settings": self.sweep_settings,
            "analysis_settings": self.analysis_settings,
            "impulse_response": self.impulse_response.to_dict(include_curves=False),
            "decay": self.decay.to_dict(include_curves),
            "frequency_response": self.frequency_response.to_dict(include_curves),
            "noise": self.noise.to_dict(include_curves),
            "reflections": self.reflections.to_dict(),
            "resonances": self.resonances.to_dict(),
            "warnings": list(self.warnings),
        }
