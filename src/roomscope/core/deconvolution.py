"""Deconvolution of the recorded sweep and location of the impulse response.

Because linear convolution is shift invariant, the recording is convolved with
the inverse filter as a whole; the linear impulse response then appears at
``sweep_start + len(reference) - 1 + acoustic_delay`` in the output. Nothing is
cut before deconvolution, so no manual trimming is required from the user.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import fftconvolve

from roomscope.errors import AnalysisError, InvalidAudioError
from roomscope.models.audio import FloatArray


def deconvolve(recording: FloatArray, inverse: FloatArray) -> FloatArray:
    """Full linear convolution of the recording with the inverse filter."""
    if recording.ndim != 1 or inverse.ndim != 1:
        raise InvalidAudioError("deconvolve expects mono arrays")
    if recording.shape[0] < inverse.shape[0]:
        raise InvalidAudioError(
            "recording is shorter than the reference sweep; the file does not contain the full sweep"
        )
    return np.asarray(fftconvolve(recording, inverse, mode="full"), dtype=np.float64)


@dataclass(frozen=True)
class LocatedImpulseResponse:
    samples: FloatArray
    direct_index: int
    pre_delay_samples: int
    peak_value: float
    valid_length_samples: int
    sweep_start_index_in_recording: int
    pre_peak_margin_db: float
    truncated_by_max_length: bool


def locate_impulse_response(
    h_full: FloatArray,
    *,
    recording_length: int,
    reference_length: int,
    sample_rate: int,
    pre_delay_ms: float,
    max_length_s: float,
    margin_near_ms: float = 2.0,
    margin_far_s: float = 0.5,
) -> LocatedImpulseResponse:
    """Find the direct sound in the deconvolved signal and cut the IR around it.

    The direct sound is assumed to be the strongest sample of ``|h_full|``.
    The "pre-peak margin" compares the peak with the strongest content in the
    window ``[peak - margin_far, peak - margin_near]``; harmonic-distortion
    pre-responses or noise in that window lower the margin and therefore the
    confidence in the direct-sound detection.
    """
    if h_full.ndim != 1 or h_full.shape[0] == 0:
        raise AnalysisError("deconvolved signal is empty")
    magnitude = np.abs(h_full)
    peak = int(np.argmax(magnitude))
    peak_value = float(h_full[peak])
    if not np.isfinite(peak_value) or peak_value == 0.0:
        raise AnalysisError("deconvolved signal has no usable peak (silent recording?)")

    valid_length = recording_length - 1 - peak
    if valid_length <= 0:
        raise AnalysisError(
            "the direct sound was found at the very end of the recording; "
            "the recording does not contain the room decay after the sweep"
        )
    max_len = round(max_length_s * sample_rate)
    truncated = valid_length > max_len
    length_after_peak = min(valid_length, max_len)

    pre_delay = round(pre_delay_ms * sample_rate / 1000.0)
    start = max(0, peak - pre_delay)
    end = min(h_full.shape[0], peak + length_after_peak + 1)
    samples = np.array(h_full[start:end], dtype=np.float64)

    near = round(margin_near_ms * sample_rate / 1000.0)
    far = round(margin_far_s * sample_rate)
    lo = max(0, peak - far)
    hi = max(lo, peak - near)
    if hi > lo:
        before = float(np.max(magnitude[lo:hi]))
        margin_db = 20.0 * np.log10(abs(peak_value) / max(before, 1e-300))
    else:
        margin_db = float("inf")

    sweep_start = peak - (reference_length - 1)
    return LocatedImpulseResponse(
        samples=samples,
        direct_index=peak - start,
        pre_delay_samples=peak - start,
        peak_value=peak_value,
        valid_length_samples=valid_length,
        sweep_start_index_in_recording=max(0, sweep_start),
        pre_peak_margin_db=float(margin_db),
        truncated_by_max_length=truncated,
    )


def confidence_label(margin_db: float) -> str:
    if margin_db >= 20.0:
        return "high"
    if margin_db >= 10.0:
        return "medium"
    return "low"
