"""Spatial average of reverberation-time values (SHOULD, ARCHITECTURE_V1 §5.3.4).

Averages EDT, T20 and T30 per band over the VALID metrics only. Decay curves
are never averaged. The output names the ISO 3382-2 accuracy class that the
number of source and microphone positions reaches.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from roomscope.errors import ConfigurationError
from roomscope.models.result import AnalysisResult, DecayMetric, Validity

# ISO 3382-2:2008 Table 1, transcribed from secondary sources (see
# MEASUREMENT_METHODOLOGY.md §3a). Confirmation status: not verified against a
# purchased copy of the standard. The class is a label, not a claim of
# compliance.
ISO_3382_2_TABLE1 = {
    "survey": {"n_source": 1, "n_microphone": 2, "n_combinations": 2},
    "engineering": {"n_source": 2, "n_microphone": 3, "n_combinations": 6},
    "precision": {"n_source": 2, "n_microphone": 6, "n_combinations": 12},
}


@dataclass(frozen=True)
class AveragedMetric:
    """Arithmetic mean of one VALID decay metric across sessions."""

    name: str
    seconds: float | None
    count: int
    spread_s: float | None
    contributing: tuple[str, ...]
    validity: Validity
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "seconds": self.seconds,
            "count": self.count,
            "spread_s": self.spread_s,
            "contributing": list(self.contributing),
            "validity": str(self.validity),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class AveragedBand:
    band_label: str
    edt: AveragedMetric
    t20: AveragedMetric
    t30: AveragedMetric
    rt60_estimate_s: float | None
    rt60_basis: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "band_label": self.band_label,
            "edt": self.edt.to_dict(),
            "t20": self.t20.to_dict(),
            "t30": self.t30.to_dict(),
            "rt60_estimate_s": self.rt60_estimate_s,
            "rt60_basis": self.rt60_basis,
        }


@dataclass(frozen=True)
class AveragedDecay:
    """Spatial average of T values. No decay curve is stored."""

    bands: tuple[AveragedBand, ...]
    n_sessions: int
    n_source_positions: int
    n_microphone_positions: int
    iso_3382_2_class: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_sessions": self.n_sessions,
            "n_source_positions": self.n_source_positions,
            "n_microphone_positions": self.n_microphone_positions,
            "iso_3382_2_class": self.iso_3382_2_class,
            "notes": list(self.notes),
            "bands": [band.to_dict() for band in self.bands],
            "iso_3382_2_table1": ISO_3382_2_TABLE1,
            "confirmation_status": (
                "ISO 3382-2:2008 Table 1 transcribed from secondary sources; "
                "not verified against a purchased copy of the standard"
            ),
        }


def iso_3382_2_class(n_source: int, n_microphone: int) -> str:
    """Name the accuracy class reached by the position counts."""
    combinations = n_source * n_microphone
    if (
        n_source >= ISO_3382_2_TABLE1["precision"]["n_source"]
        and n_microphone >= ISO_3382_2_TABLE1["precision"]["n_microphone"]
        and combinations >= ISO_3382_2_TABLE1["precision"]["n_combinations"]
    ):
        return "precision"
    if (
        n_source >= ISO_3382_2_TABLE1["engineering"]["n_source"]
        and combinations >= ISO_3382_2_TABLE1["engineering"]["n_combinations"]
    ):
        return "engineering"
    if (
        n_source >= ISO_3382_2_TABLE1["survey"]["n_source"]
        and n_microphone >= ISO_3382_2_TABLE1["survey"]["n_microphone"]
    ):
        return "survey"
    return "below_survey"


def average_decay(
    results: Sequence[AnalysisResult],
    *,
    n_source_positions: int | None = None,
    n_microphone_positions: int | None = None,
    session_labels: Sequence[str] | None = None,
) -> AveragedDecay:
    """Arithmetic mean of VALID EDT / T20 / T30 per band.

    ``n_source_positions`` defaults to 1 (RoomScope measures one source).
    ``n_microphone_positions`` defaults to the number of results.
    """
    if not results:
        raise ConfigurationError("average_decay needs at least one AnalysisResult")
    labels = (
        list(session_labels)
        if session_labels is not None and len(session_labels) == len(results)
        else [f"session-{index}" for index in range(len(results))]
    )
    n_source = 1 if n_source_positions is None else int(n_source_positions)
    n_mic = len(results) if n_microphone_positions is None else int(n_microphone_positions)
    if n_source < 1 or n_mic < 1:
        raise ConfigurationError("source and microphone position counts must be >= 1")

    band_labels = _band_labels(results)
    bands = tuple(_average_band(results, labels, band_label) for band_label in band_labels)
    notes = [
        "Decay curves are never averaged; only VALID T values enter the mean.",
        (
            "ISO 3382-2 class from Table 1 transcribed from secondary sources "
            f"({iso_3382_2_class(n_source, n_mic)})."
        ),
    ]
    return AveragedDecay(
        bands=bands,
        n_sessions=len(results),
        n_source_positions=n_source,
        n_microphone_positions=n_mic,
        iso_3382_2_class=iso_3382_2_class(n_source, n_mic),
        notes=tuple(notes),
    )


def _band_labels(results: Sequence[AnalysisResult]) -> list[str]:
    seen: list[str] = []
    for result in results:
        for band in (result.decay.broadband, *result.decay.bands):
            if band.band_label not in seen:
                seen.append(band.band_label)
    return seen


def _average_band(
    results: Sequence[AnalysisResult], labels: Sequence[str], band_label: str
) -> AveragedBand:
    edt = _average_metric(results, labels, band_label, "edt")
    t20 = _average_metric(results, labels, band_label, "t20")
    t30 = _average_metric(results, labels, band_label, "t30")
    if t30.seconds is not None:
        rt60, basis = t30.seconds, "T30"
    elif t20.seconds is not None:
        rt60, basis = t20.seconds, "T20"
    else:
        rt60, basis = None, None
    return AveragedBand(
        band_label=band_label,
        edt=edt,
        t20=t20,
        t30=t30,
        rt60_estimate_s=rt60,
        rt60_basis=basis,
    )


def _average_metric(
    results: Sequence[AnalysisResult],
    labels: Sequence[str],
    band_label: str,
    attr: str,
) -> AveragedMetric:
    values: list[float] = []
    contributing: list[str] = []
    for result, label in zip(results, labels, strict=True):
        band = _band(result, band_label)
        if band is None:
            continue
        metric: DecayMetric = getattr(band, attr)
        if metric.validity is Validity.VALID and metric.seconds is not None:
            values.append(float(metric.seconds))
            contributing.append(label)
    name = f"{band_label}.{attr}"
    if not values:
        return AveragedMetric(
            name=name,
            seconds=None,
            count=0,
            spread_s=None,
            contributing=(),
            validity=Validity.NOT_COMPUTED,
            reason="no VALID values to average",
        )
    mean = statistics.fmean(values)
    spread = max(values) - min(values) if len(values) > 1 else 0.0
    return AveragedMetric(
        name=name,
        seconds=mean,
        count=len(values),
        spread_s=spread,
        contributing=tuple(contributing),
        validity=Validity.VALID,
    )


def _band(result: AnalysisResult, band_label: str) -> Any:
    if result.decay.broadband.band_label == band_label:
        return result.decay.broadband
    for band in result.decay.bands:
        if band.band_label == band_label:
            return band
    return None
