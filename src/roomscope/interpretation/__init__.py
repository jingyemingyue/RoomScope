"""Interpretation layer: turns measured numbers into recording-oriented advice.

Strictly separate from the DSP layer: it only reads an :class:`AnalysisResult`
and never changes it. Recording profiles (vocal, drums, ...) plug in through
:class:`RecordingProfile`; pick one with :func:`interpret`'s ``profile_name``.
"""

from __future__ import annotations

from roomscope.interpretation.interpreter import Finding, Severity, interpret, interpret_comparison
from roomscope.interpretation.profiles import (
    AcousticGuitarProfile,
    ChoirProfile,
    DrumsProfile,
    GenericProfile,
    ProfileBase,
    RecordingProfile,
    RoomMicProfile,
    VocalProfile,
    VoiceOverProfile,
    available_profiles,
)

__all__ = [
    "AcousticGuitarProfile",
    "ChoirProfile",
    "DrumsProfile",
    "Finding",
    "GenericProfile",
    "ProfileBase",
    "RecordingProfile",
    "RoomMicProfile",
    "Severity",
    "VocalProfile",
    "VoiceOverProfile",
    "available_profiles",
    "interpret",
    "interpret_comparison",
]
