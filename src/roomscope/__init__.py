"""RoomScope: an open-source, DAW-independent recording environment analyzer.

The package is organised core-first:

* :mod:`roomscope.core` -- pure DSP functions (sweep, deconvolution, decay, ...).
* :mod:`roomscope.models` -- data models (settings, results, measurement session).
* :mod:`roomscope.io` -- WAV and session storage.
* :mod:`roomscope.audio` -- optional audio device access for Standalone Mode.
* :mod:`roomscope.interpretation` -- recording-engineer oriented explanations.
* :mod:`roomscope.cli` / :mod:`roomscope.ui` -- thin front ends over the core.
"""

from __future__ import annotations

__all__ = ["__version__"]

__version__ = "0.1.0.dev1"
