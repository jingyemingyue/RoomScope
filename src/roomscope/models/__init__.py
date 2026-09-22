"""Data models: settings, analysis results and the measurement session."""

from __future__ import annotations

from roomscope.models.configuration import (
    DEFAULT_SAMPLE_RATE,
    SUPPORTED_SAMPLE_RATES,
    AnalysisSettings,
    SweepSettings,
)
from roomscope.models.result import (
    AnalysisResult,
    BandDecay,
    BoundaryCandidate,
    DecayMetric,
    DecayResult,
    FrequencyResponseResult,
    HumCandidate,
    ImpulseResponseResult,
    NoiseResult,
    PlacementLength,
    PlacementResult,
    Reflection,
    ReflectionsResult,
    ResonanceCandidate,
    ResonanceResult,
    Validity,
)
from roomscope.models.session import MeasurementSession

__all__ = [
    "DEFAULT_SAMPLE_RATE",
    "SUPPORTED_SAMPLE_RATES",
    "AnalysisResult",
    "AnalysisSettings",
    "BandDecay",
    "BoundaryCandidate",
    "DecayMetric",
    "DecayResult",
    "FrequencyResponseResult",
    "HumCandidate",
    "ImpulseResponseResult",
    "MeasurementSession",
    "NoiseResult",
    "PlacementLength",
    "PlacementResult",
    "Reflection",
    "ReflectionsResult",
    "ResonanceCandidate",
    "ResonanceResult",
    "SweepSettings",
    "Validity",
]
