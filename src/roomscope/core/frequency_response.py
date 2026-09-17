"""Frequency response from the impulse response.

The raw magnitude is the FFT of the (optionally time-windowed) impulse
response and is always kept. Smoothing is a configurable fractional-octave
power average computed *from* the raw curve and stored separately.
"""

from __future__ import annotations

import numpy as np

from roomscope.core.filters import fractional_octave_smooth
from roomscope.models.audio import FloatArray
from roomscope.models.result import FrequencyResponseResult

_EPS = 1e-300


def _taper_end(segment: FloatArray, sample_rate: int, taper_ms: float) -> FloatArray:
    """Half-cosine fade over the last ``taper_ms`` so that a hard window edge
    does not add ripple. Returns a copy."""
    out = np.array(segment, dtype=np.float64)
    n_taper = min(out.shape[0], round(taper_ms * sample_rate / 1000.0))
    if n_taper > 1:
        k = np.arange(n_taper, dtype=np.float64)
        out[-n_taper:] *= np.cos(0.5 * np.pi * (k + 1) / n_taper) ** 2
    return out


def frequency_response(
    ir: FloatArray,
    sample_rate: int,
    *,
    window_s: float | None = None,
    smoothing_fraction: int = 6,
    min_resolution_hz: float = 1.0,
    end_taper_ms: float = 5.0,
) -> FrequencyResponseResult:
    """Magnitude response (dB, relative) of ``ir``.

    ``window_s`` limits the analysed part of the IR (a form of gating); when
    ``None`` the whole IR is used. The FFT length is chosen so that the
    frequency resolution is at least ``min_resolution_hz``.
    """
    if window_s is not None:
        n = max(2, min(ir.shape[0], round(window_s * sample_rate)))
        segment = _taper_end(ir[:n], sample_rate, end_taper_ms)
        effective_window = n / sample_rate
    else:
        segment = np.asarray(ir, dtype=np.float64)
        effective_window = segment.shape[0] / sample_rate
    n_min = int(np.ceil(sample_rate / min_resolution_hz))
    nfft = 1 << max(segment.shape[0], n_min).bit_length()
    spectrum = np.fft.rfft(segment, nfft)
    freqs = np.fft.rfftfreq(nfft, 1.0 / sample_rate)
    magnitude_db = 20.0 * np.log10(np.maximum(np.abs(spectrum), _EPS))
    # Drop the DC bin: it is meaningless on a logarithmic frequency axis.
    freqs = np.asarray(freqs[1:], dtype=np.float64)
    magnitude_db = np.asarray(magnitude_db[1:], dtype=np.float64)
    smoothed: FloatArray | None = None
    if smoothing_fraction > 0:
        smoothed = fractional_octave_smooth(freqs, magnitude_db, smoothing_fraction)
    return FrequencyResponseResult(
        frequencies_hz=freqs,
        magnitude_db_raw=magnitude_db,
        magnitude_db_smoothed=smoothed,
        smoothing_fraction=smoothing_fraction,
        window_s=float(effective_window),
    )
