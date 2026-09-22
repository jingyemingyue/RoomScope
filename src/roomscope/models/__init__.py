"""Data models: settings, analysis results and the measurement session."""

from __future__ import annotations

from roomscope.models.calibration import CalibrationRecord
from roomscope.models.comparison import (
    CompareSettings,
    ComparisonResult,
    FrequencyResponseDelta,
    MetricDelta,
    ReflectionMatch,
    ResonanceMatch,
)
from roomscope.models.configuration import (
    DEFAULT_SAMPLE_RATE,
    SUPPORTED_SAMPLE_RATES,
    AnalysisSettings,
    SweepSettings,
)
from roomscope.models.project import PositionEntry, Project
from roomscope.models.result import (
    AnalysisResult,
    BandDecay,
    BoundaryCandidate,
    DecayMetric,
    DecayResult,
    FrequencyResponseResult,
    HumCandidate,
    ImpulseResponseResult,
    LoopbackResult,
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
    "CalibrationRecord",
    "CompareSettings",
    "ComparisonResult",
    "DecayMetric",
    "DecayResult",
    "FrequencyResponseDelta",
    "FrequencyResponseResult",
    "HumCandidate",
    "ImpulseResponseResult",
    "LoopbackResult",
    "MeasurementSession",
    "MetricDelta",
    "NoiseResult",
    "PlacementLength",
    "PlacementResult",
    "PositionEntry",
    "Project",
    "Reflection",
    "ReflectionMatch",
    "ReflectionsResult",
    "ResonanceCandidate",
    "ResonanceMatch",
    "ResonanceResult",
    "SweepSettings",
    "Validity",
]
