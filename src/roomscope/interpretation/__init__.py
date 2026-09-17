"""Interpretation layer: turns measured numbers into recording-oriented advice.

Strictly separate from the DSP layer: it only reads an :class:`AnalysisResult`
and never changes it. Recording profiles (vocal, drums, ...) plug in through
:class:`RecordingProfile`; v0.1 ships only :class:`GenericProfile`.
"""

from __future__ import annotations

from roomscope.interpretation.interpreter import Finding, Severity, interpret
from roomscope.interpretation.profiles import GenericProfile, RecordingProfile, available_profiles

__all__ = [
    "Finding",
    "GenericProfile",
    "RecordingProfile",
    "Severity",
    "available_profiles",
    "interpret",
]
