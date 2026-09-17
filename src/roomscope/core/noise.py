"""Background-noise analysis of a quiet segment of the recording.

All levels are digital levels in dBFS (AES17 convention: a full-scale sine
wave reads 0 dBFS RMS). Without an SPL calibration RoomScope never converts
them to dB SPL.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import welch

from roomscope.core.filters import (
    apply_bandpass_zero_phase,
    band_fits,
    bandpass_sos,
    fractional_octave_band,
)
from roomscope.models.audio import FloatArray
from roomscope.models.result import HumCandidate, NoiseResult

_EPS = 1e-300
_SQRT2 = float(np.sqrt(2.0))
MAINS_BASE_FREQUENCIES_HZ = (50.0, 60.0)
HUM_MAX_HARMONIC_HZ = 1000.0
HUM_MAX_HARMONICS = 12
HUM_DETECTION_PROMINENCE_DB = 10.0
HUM_MIN_HARMONICS_FOR_DETECTION = 2


def rms_dbfs(x: FloatArray) -> float:
    """RMS level in dBFS with the AES17 sine reference."""
    rms = float(np.sqrt(np.mean(np.asarray(x, dtype=np.float64) ** 2)))
    return float(20.0 * np.log10(max(rms * _SQRT2, _EPS)))


def peak_dbfs(x: FloatArray) -> float:
    return float(20.0 * np.log10(max(float(np.max(np.abs(x))), _EPS)))


@dataclass(frozen=True)
class QuietSegment:
    start: int
    end: int
    source: str
    note: str | None = None


def find_quiet_segment(
    *,
    recording_length: int,
    sample_rate: int,
    sweep_start_index: int,
    reference_length: int,
    min_segment_s: float,
    guard_s: float = 0.1,
    skip_head_s: float = 0.05,
    expected_decay_s: float = 3.0,
) -> QuietSegment | None:
    """Prefer the silence before the sweep; fall back to the file tail."""
    min_len = round(min_segment_s * sample_rate)
    head = round(skip_head_s * sample_rate)
    guard = round(guard_s * sample_rate)
    pre_end = sweep_start_index - guard
    if pre_end - head >= min_len:
        return QuietSegment(start=head, end=pre_end, source="pre-sweep")
    sweep_end = sweep_start_index + reference_length
    tail_start = sweep_end + round(expected_decay_s * sample_rate)
    if recording_length - tail_start >= min_len:
        return QuietSegment(
            start=tail_start,
            end=recording_length,
            source="tail",
            note=(
                "quiet segment taken from the end of the recording; it may contain late "
                "reverberation, so the noise floor may be overestimated"
            ),
        )
    return None


def _hum_candidate(
    freqs: FloatArray, psd_db: FloatArray, base_hz: float, nyquist: float
) -> HumCandidate:
    resolution = float(freqs[1] - freqs[0]) if freqs.shape[0] > 1 else float("inf")
    harmonics: list[tuple[float, float]] = []
    k = 1
    while k <= HUM_MAX_HARMONICS:
        f_k = k * base_hz
        if f_k > min(HUM_MAX_HARMONIC_HZ, nyquist * 0.9):
            break
        peak_half_width = max(2.0, 1.5 * resolution)
        lo = np.searchsorted(freqs, f_k - peak_half_width)
        hi = np.searchsorted(freqs, f_k + peak_half_width, side="right")
        neighbourhood = max(10.0, 0.15 * f_k)
        n_lo = np.searchsorted(freqs, f_k - neighbourhood)
        n_hi = np.searchsorted(freqs, f_k + neighbourhood, side="right")
        exclude_lo = np.searchsorted(freqs, f_k - peak_half_width - resolution)
        exclude_hi = np.searchsorted(freqs, f_k + peak_half_width + resolution, side="right")
        if hi <= lo or n_hi - n_lo < 6:
            k += 1
            continue
        peak_level = float(np.max(psd_db[lo:hi]))
        surround = np.concatenate([psd_db[n_lo:exclude_lo], psd_db[exclude_hi:n_hi]])
        if surround.shape[0] < 3:
            k += 1
            continue
        prominence = peak_level - float(np.median(surround))
        if prominence >= HUM_DETECTION_PROMINENCE_DB:
            harmonics.append((float(f_k), float(prominence)))
        k += 1
    strongest = max((p for _, p in harmonics), default=None)
    return HumCandidate(
        base_hz=base_hz,
        harmonics=tuple(harmonics),
        strongest_prominence_db=strongest,
        detected=len(harmonics) >= HUM_MIN_HARMONICS_FOR_DETECTION,
    )


def analyze_noise(
    recording: FloatArray,
    sample_rate: int,
    segment: QuietSegment | None,
    *,
    octave_bands_hz: tuple[float, ...],
) -> NoiseResult:
    if segment is None:
        return NoiseResult(
            segment_source=None,
            segment_start_s=None,
            segment_duration_s=None,
            rms_dbfs=None,
            peak_dbfs=None,
            band_levels_dbfs=(),
            psd_frequencies_hz=None,
            psd_db=None,
            hum=(),
            notes=(
                "No quiet segment found: add at least 1 s of silence before the sweep "
                "(the generated test signal already contains it) or record a longer tail.",
            ),
        )
    x = np.asarray(recording[segment.start : segment.end], dtype=np.float64)
    notes: list[str] = []
    if segment.note:
        notes.append(segment.note)

    band_levels: list[tuple[float, float]] = []
    for center in octave_bands_hz:
        band = fractional_octave_band(center, 1)
        if not band_fits(band, sample_rate):
            continue
        sos = bandpass_sos(band, sample_rate)
        if x.shape[0] <= 3 * sos.shape[0] * 2 + 1:
            continue
        band_levels.append((center, rms_dbfs(apply_bandpass_zero_phase(x, sos))))

    # 2 Hz resolution with several averaged segments (Welch) keeps random
    # spectral peaks small enough for the hum detector.
    nperseg = int(min(x.shape[0], sample_rate // 2))
    freqs, psd = welch(x, fs=sample_rate, window="hann", nperseg=nperseg, scaling="density")
    freqs = np.asarray(freqs, dtype=np.float64)
    psd_db = np.asarray(10.0 * np.log10(np.maximum(psd, _EPS)), dtype=np.float64)

    hum: list[HumCandidate] = []
    resolution = sample_rate / nperseg
    if resolution <= 5.0:
        nyquist = sample_rate / 2.0
        hum = [_hum_candidate(freqs, psd_db, base, nyquist) for base in MAINS_BASE_FREQUENCIES_HZ]
    else:
        notes.append(
            f"quiet segment is too short ({x.shape[0] / sample_rate:.2f} s) for mains-hum detection"
        )

    return NoiseResult(
        segment_source=segment.source,
        segment_start_s=segment.start / sample_rate,
        segment_duration_s=x.shape[0] / sample_rate,
        rms_dbfs=rms_dbfs(x),
        peak_dbfs=peak_dbfs(x),
        band_levels_dbfs=tuple(band_levels),
        psd_frequencies_hz=freqs,
        psd_db=psd_db,
        hum=tuple(hum),
        notes=tuple(notes),
    )
