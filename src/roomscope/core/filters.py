"""Band filters and fractional-octave smoothing.

Octave bands use the base-2 definition of IEC 61260-1 (``f_low = f_c * 2^(-1/2b)``,
``f_high = f_c * 2^(1/2b)`` for a 1/b-octave band). The band-pass filters are
Butterworth designs applied in the time-reversed direction for decay analysis
(Jacobsen & Rindel 1987) — they are *not* certified IEC 61260 class-1 filters
and RoomScope does not claim standard-compliant band levels.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import butter, sosfilt, sosfiltfilt

from roomscope.errors import ConfigurationError
from roomscope.models.audio import FloatArray


@dataclass(frozen=True)
class Band:
    center_hz: float
    low_hz: float
    high_hz: float

    @property
    def bandwidth_hz(self) -> float:
        return self.high_hz - self.low_hz

    @property
    def label(self) -> str:
        if self.center_hz >= 1000.0:
            return f"{self.center_hz / 1000.0:g} kHz"
        return f"{self.center_hz:g} Hz"


def fractional_octave_band(center_hz: float, fraction: int = 1) -> Band:
    if center_hz <= 0.0 or fraction <= 0:
        raise ConfigurationError("band centre and fraction must be positive")
    half = 2.0 ** (1.0 / (2.0 * fraction))
    return Band(center_hz=center_hz, low_hz=center_hz / half, high_hz=center_hz * half)


def band_fits(band: Band, sample_rate: int, max_relative_to_nyquist: float = 0.9) -> bool:
    return band.high_hz < max_relative_to_nyquist * sample_rate / 2.0 and band.low_hz > 0.0


def bandpass_sos(band: Band, sample_rate: int, order: int = 3) -> FloatArray:
    """Butterworth band-pass in second-order sections (``order`` poles per skirt)."""
    if not band_fits(band, sample_rate):
        raise ConfigurationError(
            f"band {band.label} does not fit below the Nyquist frequency at {sample_rate} Hz"
        )
    nyquist = sample_rate / 2.0
    sos = butter(
        order, [band.low_hz / nyquist, band.high_hz / nyquist], btype="bandpass", output="sos"
    )
    return np.asarray(sos, dtype=np.float64)


def apply_bandpass(x: FloatArray, sos: FloatArray, *, time_reversed: bool = True) -> FloatArray:
    """Apply the filter forward, or time-reversed (filter the reversed signal and
    reverse the result) so that the filter's own decay does not lengthen the
    measured decay."""
    if time_reversed:
        return np.asarray(sosfilt(sos, x[::-1])[::-1], dtype=np.float64)
    return np.asarray(sosfilt(sos, x), dtype=np.float64)


def apply_bandpass_zero_phase(x: FloatArray, sos: FloatArray) -> FloatArray:
    """Zero-phase filtering, used for level measurements (not for decays)."""
    return np.asarray(sosfiltfilt(sos, x), dtype=np.float64)


def filter_decay_time_20db(sos: FloatArray, sample_rate: int, max_s: float = 2.0) -> float | None:
    """Time for the filter's own impulse response envelope to fall 20 dB."""
    n = int(max_s * sample_rate)
    impulse = np.zeros(n, dtype=np.float64)
    impulse[0] = 1.0
    response = np.asarray(sosfilt(sos, impulse), dtype=np.float64)
    energy = response**2
    # Backward integration of the filter's own energy gives a smooth envelope.
    edc = np.cumsum(energy[::-1])[::-1]
    edc_db = 10.0 * np.log10(np.maximum(edc / edc[0], 1e-300))
    below = np.nonzero(edc_db <= -20.0)[0]
    if below.shape[0] == 0:
        return None
    return float(below[0]) / sample_rate


def fractional_octave_smooth(
    frequencies_hz: FloatArray,
    magnitude_db: FloatArray,
    fraction: int,
) -> FloatArray:
    """Power-average ``magnitude_db`` over a +/- 1/(2*fraction)-octave window.

    Works on any ascending frequency grid. At low frequencies where the window
    is narrower than one bin the value is returned unchanged.
    """
    if fraction <= 0:
        return np.asarray(magnitude_db, dtype=np.float64)
    if frequencies_hz.shape != magnitude_db.shape:
        raise ConfigurationError("frequency and magnitude arrays must have the same shape")
    half = 2.0 ** (1.0 / (2.0 * fraction))
    power = 10.0 ** (np.asarray(magnitude_db, dtype=np.float64) / 10.0)
    cumulative = np.concatenate([[0.0], np.cumsum(power)])
    lo = np.searchsorted(frequencies_hz, frequencies_hz / half, side="left")
    hi = np.searchsorted(frequencies_hz, frequencies_hz * half, side="right")
    hi = np.maximum(hi, lo + 1)
    mean_power = (cumulative[hi] - cumulative[lo]) / (hi - lo)
    return np.asarray(10.0 * np.log10(np.maximum(mean_power, 1e-300)), dtype=np.float64)
