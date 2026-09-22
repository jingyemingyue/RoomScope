"""RoomScope: an open-source, DAW-independent recording environment analyzer.

The package is organised core-first:

* :mod:`roomscope.core` -- pure DSP functions (sweep, deconvolution, decay, ...).
* :mod:`roomscope.models` -- data models (settings, results, measurement session).
* :mod:`roomscope.io` -- WAV and session storage.
* :mod:`roomscope.audio` -- optional audio device access for Standalone Mode.
* :mod:`roomscope.interpretation` -- recording-engineer oriented explanations.
* :mod:`roomscope.cli` / :mod:`roomscope.ui` -- thin front ends over the core.

Tier 1 names are loaded through :func:`__getattr__` so ``import roomscope``
does not import SciPy, PortAudio or Qt. The list is locked against
``docs/ARCHITECTURE_V1.md`` §5.1.
"""

from __future__ import annotations

from typing import Any

from roomscope.errors import (
    AnalysisError as AnalysisError,
)
from roomscope.errors import (
    AudioBackendUnavailableError as AudioBackendUnavailableError,
)
from roomscope.errors import (
    AudioDeviceError as AudioDeviceError,
)
from roomscope.errors import (
    ConfigurationError as ConfigurationError,
)
from roomscope.errors import (
    InsufficientDataError as InsufficientDataError,
)
from roomscope.errors import (
    InvalidAudioError as InvalidAudioError,
)
from roomscope.errors import (
    RoomScopeError as RoomScopeError,
)
from roomscope.errors import (
    SampleRateMismatchError as SampleRateMismatchError,
)
from roomscope.errors import (
    SessionError as SessionError,
)
from roomscope.version import __version__ as __version__

# Names exported by roomscope/__init__.py (ARCHITECTURE_V1.md §5.1). Keep this
# tuple and the document in lockstep; tests/unit/test_public_api.py checks both.
TIER1_EXPORTS: tuple[str, ...] = (
    "__version__",
    "analyze",
    "analyze_impulse_response",
    "Reference",
    "compare",
    "ComparisonResult",
    "SweepSettings",
    "AnalysisSettings",
    "AnalysisResult",
    "Validity",
    "DecayResult",
    "BandDecay",
    "DecayMetric",
    "FrequencyResponseResult",
    "NoiseResult",
    "ReflectionsResult",
    "Reflection",
    "ResonanceResult",
    "PlacementResult",
    "LoopbackResult",
    "MeasurementSession",
    "Project",
    "interpret",
    "interpret_comparison",
    "Finding",
    "Severity",
    "available_profiles",
    "read_wav",
    "write_wav",
    "write_sweep_file",
    "load_reference",
    "save_measurement",
    "load_measurement",
    "load_session",
    "list_sessions",
    "RoomScopeError",
    "ConfigurationError",
    "InvalidAudioError",
    "SampleRateMismatchError",
    "AnalysisError",
    "InsufficientDataError",
    "AudioDeviceError",
    "AudioBackendUnavailableError",
    "SessionError",
)

_LAZY: dict[str, tuple[str, str]] = {
    "analyze": ("roomscope.core.pipeline", "analyze"),
    "analyze_impulse_response": ("roomscope.core.pipeline", "analyze_impulse_response"),
    "Reference": ("roomscope.core.pipeline", "Reference"),
    "compare": ("roomscope.core.compare", "compare"),
    "ComparisonResult": ("roomscope.models.comparison", "ComparisonResult"),
    "SweepSettings": ("roomscope.models.configuration", "SweepSettings"),
    "AnalysisSettings": ("roomscope.models.configuration", "AnalysisSettings"),
    "AnalysisResult": ("roomscope.models.result", "AnalysisResult"),
    "Validity": ("roomscope.models.result", "Validity"),
    "DecayResult": ("roomscope.models.result", "DecayResult"),
    "BandDecay": ("roomscope.models.result", "BandDecay"),
    "DecayMetric": ("roomscope.models.result", "DecayMetric"),
    "FrequencyResponseResult": ("roomscope.models.result", "FrequencyResponseResult"),
    "NoiseResult": ("roomscope.models.result", "NoiseResult"),
    "ReflectionsResult": ("roomscope.models.result", "ReflectionsResult"),
    "Reflection": ("roomscope.models.result", "Reflection"),
    "ResonanceResult": ("roomscope.models.result", "ResonanceResult"),
    "PlacementResult": ("roomscope.models.result", "PlacementResult"),
    "LoopbackResult": ("roomscope.models.result", "LoopbackResult"),
    "MeasurementSession": ("roomscope.models.session", "MeasurementSession"),
    "Project": ("roomscope.models.project", "Project"),
    "interpret": ("roomscope.interpretation.interpreter", "interpret"),
    "interpret_comparison": ("roomscope.interpretation.interpreter", "interpret_comparison"),
    "Finding": ("roomscope.interpretation.interpreter", "Finding"),
    "Severity": ("roomscope.interpretation.interpreter", "Severity"),
    "available_profiles": ("roomscope.interpretation.profiles", "available_profiles"),
    "read_wav": ("roomscope.io.wav", "read_wav"),
    "write_wav": ("roomscope.io.wav", "write_wav"),
    "write_sweep_file": ("roomscope.io.wav", "write_sweep_file"),
    "load_reference": ("roomscope.io.wav", "load_reference"),
    "save_measurement": ("roomscope.io.session_store", "save_measurement"),
    "load_measurement": ("roomscope.io.session_store", "load_measurement"),
    "load_session": ("roomscope.io.session_store", "load_session"),
    "list_sessions": ("roomscope.io.session_store", "list_sessions"),
}

__all__ = list(TIER1_EXPORTS)


def __getattr__(name: str) -> Any:
    target = _LAZY.get(name)
    if target is None:
        raise AttributeError(f"module 'roomscope' has no attribute {name!r}")
    module_name, attr = target
    from importlib import import_module

    value = getattr(import_module(module_name), attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(TIER1_EXPORTS))
