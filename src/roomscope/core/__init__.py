"""Pure DSP core. No GUI, device or file-format code lives here.

All functions take and return NumPy arrays or small dataclasses so that they
can be tested with synthetic signals.
"""

from __future__ import annotations

from roomscope.core.compare import compare
from roomscope.core.pipeline import Reference, analyze, analyze_impulse_response
from roomscope.core.sweep import generate_ess, inverse_filter, measurement_signal

__all__ = [
    "Reference",
    "analyze",
    "analyze_impulse_response",
    "compare",
    "generate_ess",
    "inverse_filter",
    "measurement_signal",
]
