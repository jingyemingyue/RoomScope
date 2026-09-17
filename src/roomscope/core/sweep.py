"""Exponential sine sweep (ESS) generation and inverse filters.

Method
------
The sweep follows Farina (2000): with ``L = T / ln(f2/f1)`` the signal is

    x(t) = sin( 2*pi*f1*L * (exp(t/L) - 1) ),     0 <= t < T

whose instantaneous frequency ``f(t) = f1 * exp(t/L)`` rises exponentially
from ``f1`` to ``f2``. The analytic inverse filter is the time-reversed sweep
multiplied by an amplitude envelope that falls 6 dB per octave,
``exp(-t/L)``, so that the convolution of sweep and inverse filter is
(approximately) a band-limited Dirac pulse. Harmonic distortion products of
the loudspeaker appear *before* the linear impulse response at
``dt_k = L * ln(k)`` for the k-th harmonic, which is why they can be
separated by simple windowing.

Everything here is an independent implementation from the published
equations (see docs/MEASUREMENT_METHODOLOGY.md); no third-party code was used.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import fftconvolve

from roomscope.errors import ConfigurationError
from roomscope.models.audio import FloatArray
from roomscope.models.configuration import SweepSettings


def _raised_cosine_fades(n: int, fade_in: int, fade_out: int) -> FloatArray:
    """Window that is 1 except for sin^2 ramps of ``fade_in``/``fade_out`` samples."""
    window = np.ones(n, dtype=np.float64)
    if fade_in > 0:
        k = np.arange(fade_in, dtype=np.float64)
        window[:fade_in] = np.sin(0.5 * np.pi * k / fade_in) ** 2
    if fade_out > 0:
        k = np.arange(fade_out, dtype=np.float64)
        window[n - fade_out :] = np.cos(0.5 * np.pi * (k + 1) / fade_out) ** 2
    return window


def sweep_time_axis(settings: SweepSettings) -> FloatArray:
    return np.arange(settings.sweep_samples, dtype=np.float64) / settings.sample_rate


def instantaneous_frequency(settings: SweepSettings, t: FloatArray) -> FloatArray:
    """``f(t) = f1 * exp(t / L)`` in Hz."""
    return settings.start_hz * np.exp(t / settings.sweep_rate)


def generate_ess(settings: SweepSettings, *, apply_level: bool = True) -> FloatArray:
    """Return the sweep only (no leading/trailing silence), peak-scaled to ``level_dbfs``."""
    t = sweep_time_axis(settings)
    rate = settings.sweep_rate
    phase = 2.0 * np.pi * settings.start_hz * rate * (np.exp(t / rate) - 1.0)
    x = np.sin(phase)
    fade_in = round(settings.fade_in_s * settings.sample_rate)
    fade_out = round(settings.fade_out_s * settings.sample_rate)
    x *= _raised_cosine_fades(x.shape[0], fade_in, fade_out)
    if apply_level:
        x *= settings.amplitude
    return x


def measurement_signal(settings: SweepSettings) -> FloatArray:
    """Pre-silence + sweep + post-silence, the file that is played through the DAW."""
    pre = round(settings.pre_silence_s * settings.sample_rate)
    post = round(settings.post_silence_s * settings.sample_rate)
    return np.concatenate(
        [np.zeros(pre), generate_ess(settings), np.zeros(post)],
    ).astype(np.float64)


def inverse_filter(settings: SweepSettings) -> FloatArray:
    """Analytic inverse filter (Farina 2000), normalised for the reference sweep.

    The filter is scaled so that convolving the *level-scaled* reference sweep
    with it yields a pulse with peak value 1.0. A perfect loopback therefore
    gives an impulse response with peak 1.0 (0 dB), and any gain in the
    measurement chain shows up as a proportional change.
    """
    reference = generate_ess(settings)
    unit = generate_ess(settings, apply_level=False)
    t = sweep_time_axis(settings)
    envelope = np.exp(-t / settings.sweep_rate)
    inv = unit[::-1] * envelope
    pulse = fftconvolve(reference, inv, mode="full")
    peak = float(np.max(np.abs(pulse)))
    if not np.isfinite(peak) or peak <= 0.0:
        raise ConfigurationError("inverse filter normalisation failed (degenerate sweep)")
    return inv / peak


def inverse_filter_spectral(
    reference: FloatArray,
    *,
    regularisation_db: float = -60.0,
) -> FloatArray:
    """Regularised spectral-division inverse for an arbitrary reference signal.

    ``H_inv = conj(X) / (|X|^2 + beta)`` with ``beta`` relative to the maximum
    of ``|X|^2``. Used when the reference is an audio file without a RoomScope
    sweep definition (so ``f1``/``f2``/``T`` are unknown). Normalised like
    :func:`inverse_filter`.
    """
    if reference.ndim != 1 or reference.shape[0] < 16:
        raise ConfigurationError("reference signal must be a mono array with at least 16 samples")
    n = reference.shape[0]
    nfft = 1 << (2 * n - 1).bit_length()
    spectrum = np.fft.rfft(reference, nfft)
    power = np.abs(spectrum) ** 2
    beta = float(np.max(power)) * 10.0 ** (regularisation_db / 10.0)
    if beta <= 0.0:
        raise ConfigurationError("reference signal is silent")
    inv_spectrum = np.conj(spectrum) / (power + beta)
    inv = np.fft.irfft(inv_spectrum, nfft)
    # The inverse of a causal signal of length n is anti-causal; rotate so that
    # it occupies [0, n) like the analytic inverse filter (time-reversed sweep).
    inv = np.roll(inv, n - 1)[:n]
    pulse = fftconvolve(reference, inv, mode="full")
    peak = float(np.max(np.abs(pulse)))
    if not np.isfinite(peak) or peak <= 0.0:
        raise ConfigurationError("spectral inverse normalisation failed")
    return np.asarray(inv / peak, dtype=np.float64)


def reference_pulse(settings: SweepSettings) -> FloatArray:
    """Convolution of the reference sweep with its inverse filter (ideal loopback)."""
    return np.asarray(
        fftconvolve(generate_ess(settings), inverse_filter(settings), mode="full"),
        dtype=np.float64,
    )


def harmonic_pre_response_offsets_s(settings: SweepSettings, max_order: int = 5) -> list[float]:
    """Time (s) by which the k-th harmonic response precedes the linear IR."""
    return [settings.sweep_rate * float(np.log(k)) for k in range(2, max_order + 1)]
