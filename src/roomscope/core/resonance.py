"""Potential low-frequency resonance detection.

v0.1 deliberately reports *candidates* only:

* a candidate is a peak of the finely smoothed (1/24-octave) magnitude
  response that stands ``min_prominence_db`` above the 1-octave smoothed
  baseline, below ``max_hz``;
* for each candidate the decay of a 1/3-octave band around it is measured as
  the time for the band envelope to fall 20 dB, and compared with the same
  measure for the analysis filter alone. Only when the measured decay is
  clearly longer than the filter ringing is the decay called distinguishable.

Identifying an actual room mode requires knowledge of the room geometry and
several measurement positions and is out of scope.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks, sosfilt

from roomscope.core.filters import (
    apply_bandpass,
    band_fits,
    bandpass_sos,
    fractional_octave_band,
    fractional_octave_smooth,
)
from roomscope.core.impulse import envelope_db
from roomscope.models.audio import FloatArray
from roomscope.models.result import (
    FrequencyResponseResult,
    ResonanceCandidate,
    ResonanceResult,
)

MAX_CANDIDATES = 8
MIN_FREQUENCY_HZ = 20.0
DISTINGUISHABLE_RATIO = 2.0
_FINE_FRACTION = 24
_BASELINE_FRACTION = 1


def _decay_20db_s(signal: FloatArray, sample_rate: int, smoothing_s: float) -> float | None:
    env = envelope_db(signal, sample_rate, smoothing_s * 1000.0)
    peak = int(np.argmax(env))
    below = np.nonzero(env[peak:] <= env[peak] - 20.0)[0]
    if below.shape[0] == 0:
        return None
    return float(below[0]) / sample_rate


def detect_potential_resonances(
    ir: FloatArray,
    sample_rate: int,
    response: FrequencyResponseResult,
    *,
    max_hz: float,
    min_prominence_db: float,
) -> ResonanceResult:
    freqs = response.frequencies_hz
    raw = response.magnitude_db_raw
    mask = (freqs >= MIN_FREQUENCY_HZ) & (freqs <= max_hz)
    notes = [
        "Candidates only: a peak in the low-frequency response with a long narrow-band decay "
        "may be a room resonance, but room-mode identification is not attempted in v0.1.",
    ]
    if int(np.count_nonzero(mask)) < 8:
        notes.append("frequency resolution is too coarse for the resonance search")
        return ResonanceResult(max_frequency_hz=max_hz, candidates=(), notes=tuple(notes))

    f = freqs[mask]
    fine = fractional_octave_smooth(f, raw[mask], _FINE_FRACTION)
    baseline = fractional_octave_smooth(f, raw[mask], _BASELINE_FRACTION)
    excess = fine - baseline
    peaks, props = find_peaks(excess, height=min_prominence_db, prominence=min_prominence_db / 2.0)
    if peaks.shape[0] == 0:
        return ResonanceResult(max_frequency_hz=max_hz, candidates=(), notes=tuple(notes))
    order = np.argsort(props["peak_heights"])[::-1][:MAX_CANDIDATES]

    candidates: list[ResonanceCandidate] = []
    for idx in sorted(peaks[order]):
        f0 = float(f[idx])
        band = fractional_octave_band(f0, 3)
        decay: float | None = None
        ringing: float | None = None
        if band_fits(band, sample_rate):
            sos = bandpass_sos(band, sample_rate, order=2)
            smoothing_s = 2.0 / f0
            filtered = apply_bandpass(ir, sos, time_reversed=True)
            decay = _decay_20db_s(filtered, sample_rate, smoothing_s)
            impulse = np.zeros(max(int(2.0 * sample_rate), 16), dtype=np.float64)
            impulse[0] = 1.0
            ringing = _decay_20db_s(
                np.asarray(sosfilt(sos, impulse), dtype=np.float64), sample_rate, smoothing_s
            )
        distinguishable = (
            decay is not None
            and ringing is not None
            and ringing > 0.0
            and decay / ringing >= DISTINGUISHABLE_RATIO
        )
        candidates.append(
            ResonanceCandidate(
                frequency_hz=f0,
                level_above_baseline_db=float(excess[idx]),
                narrowband_decay_20db_s=decay,
                filter_ringing_20db_s=ringing,
                decay_distinguishable=distinguishable,
            )
        )
    return ResonanceResult(
        max_frequency_hz=max_hz, candidates=tuple(candidates), notes=tuple(notes)
    )
