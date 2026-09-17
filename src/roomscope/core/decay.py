"""Reverberation analysis: Schroeder integration, noise truncation, EDT/T20/T30.

Method (see docs/MEASUREMENT_METHODOLOGY.md for references)
--------------------------------------------------------------
1. The band-limited impulse response ``h`` is squared and the energy decay
   curve is obtained by backward integration (Schroeder 1965):
   ``EDC(t) = integral_t^inf h^2(tau) dtau``.
2. Before integrating, the noise floor is estimated and the integration is
   truncated at the point where the decay meets the noise, following the
   iterative procedure of Lundeby et al. (1995). The energy of the decay after
   the truncation point is estimated from the fitted late slope and added back
   (late-decay compensation).
3. EDT, T20 and T30 are least-squares line fits over the ranges
   0..-10 dB, -5..-25 dB and -5..-35 dB of the EDC, extrapolated to 60 dB
   (ISO 3382-1). A metric is only reported when the lower limit of its range
   lies at least ``noise_margin_db`` (10 dB) above the noise floor; otherwise
   it is marked "insufficient decay range".
4. Band filtering uses time-reversed Butterworth filters. The product of
   filter bandwidth and reverberation time (B*T) is reported; results with
   B*T < 4 are flagged as unreliable because the filter's own decay is then
   comparable to the room decay (Jacobsen & Rindel 1987).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from roomscope.core.filters import (
    Band,
    apply_bandpass,
    band_fits,
    bandpass_sos,
    fractional_octave_band,
)
from roomscope.models.audio import FloatArray
from roomscope.models.configuration import AnalysisSettings
from roomscope.models.result import BandDecay, DecayMetric, DecayResult, Validity

_EPS = 1e-300
_EDT_RANGE = (0.0, -10.0)
_T20_RANGE = (-5.0, -25.0)
_T30_RANGE = (-5.0, -35.0)
#: Minimum bandwidth-time product for time-reversed filtering (Jacobsen & Rindel 1987).
MIN_BT_PRODUCT = 4.0
DECAY_METHOD = (
    "Schroeder backward integration with Lundeby noise truncation and late-decay "
    "compensation; EDT/T20/T30 by least-squares fit per ISO 3382-1; "
    "time-reversed Butterworth octave-band filtering"
)


def _to_db(power: FloatArray) -> FloatArray:
    return np.asarray(10.0 * np.log10(np.maximum(power, _EPS)), dtype=np.float64)


def _local_average(power: FloatArray, block: int) -> tuple[FloatArray, FloatArray]:
    """Average ``power`` in consecutive blocks; return (block_centre_index, mean)."""
    block = max(1, block)
    n_blocks = power.shape[0] // block
    if n_blocks == 0:
        return np.array([power.shape[0] / 2.0]), np.array([float(np.mean(power))])
    trimmed = power[: n_blocks * block].reshape(n_blocks, block)
    means = trimmed.mean(axis=1)
    centres = (np.arange(n_blocks) + 0.5) * block
    return centres, means


def _linear_fit(x: FloatArray, y: FloatArray) -> tuple[float, float, float]:
    """Least-squares line ``y = slope * x + intercept``; returns (slope, intercept, r2)."""
    if x.shape[0] < 2:
        return float("nan"), float("nan"), float("nan")
    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    ss_res = float(np.sum((y - predicted) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0
    return float(slope), float(intercept), float(r2)


@dataclass(frozen=True)
class TruncationEstimate:
    """Result of the Lundeby noise-floor / crosspoint iteration."""

    start_index: int
    truncation_index: int
    noise_floor_db: float
    peak_db: float
    late_slope_db_per_s: float | None
    converged: bool
    iterations: int


def estimate_truncation(
    power: FloatArray,
    sample_rate: int,
    *,
    max_iterations: int = 6,
    intervals_per_10db: float = 5.0,
) -> TruncationEstimate:
    """Lundeby et al. (1995) iterative estimate of the noise floor and the
    point where the decay meets it.

    ``power`` is the squared impulse response starting at (or shortly before)
    the direct sound. Levels are in dB relative to 1 (same scale for peak and
    noise so that their difference is the usable dynamic range).
    """
    n = power.shape[0]
    if n < 16:
        return TruncationEstimate(
            0,
            n,
            float(_to_db(np.array([np.mean(power)]))[0]),
            float(_to_db(np.array([np.max(power)]))[0]),
            None,
            False,
            0,
        )

    # 1. First local averages (about 20 ms blocks).
    block = max(1, round(0.02 * sample_rate))
    centres, means = _local_average(power, block)
    level_db = _to_db(means)
    start_block = int(np.argmax(level_db))
    peak_db = float(level_db[start_block])
    start_index = int(min(n - 1, max(0, centres[start_block] - block / 2.0)))

    # 2. Noise from the last 10 %.
    tail = power[int(0.9 * n) :]
    noise_db = float(_to_db(np.array([np.mean(tail)]))[0])

    # 3. Preliminary slope from the peak down to noise + 10 dB.
    usable = np.nonzero(level_db[start_block:] > noise_db + 10.0)[0]
    if usable.shape[0] < 2:
        return TruncationEstimate(start_index, n, noise_db, peak_db, None, False, 0)
    stop_block = start_block + int(usable[-1]) + 1
    t = centres[start_block:stop_block] / sample_rate
    slope, intercept, _ = _linear_fit(t, level_db[start_block:stop_block])
    if not np.isfinite(slope) or slope >= 0.0:
        return TruncationEstimate(start_index, n, noise_db, peak_db, None, False, 0)
    cross_t = (noise_db - intercept) / slope

    converged = False
    iterations = 0
    late_slope = slope
    while iterations < max_iterations:
        iterations += 1
        # 5./6. New block length: `intervals_per_10db` intervals per 10 dB of decay.
        seconds_per_10db = 10.0 / abs(late_slope)
        block = round(seconds_per_10db / intervals_per_10db * sample_rate)
        block = int(np.clip(block, max(1, int(0.001 * sample_rate)), int(0.05 * sample_rate)))
        centres, means = _local_average(power, block)
        level_db = _to_db(means)
        times = centres / sample_rate

        # 7. Noise from a segment starting 5-10 dB (here 7.5 dB) of decay after
        #    the crosspoint, at least the last 10 % of the response.
        noise_start_t = cross_t + 7.5 / abs(late_slope)
        noise_start = int(noise_start_t * sample_rate)
        noise_start = min(noise_start, int(0.9 * n))
        noise_start = max(noise_start, 0)
        noise_db = float(_to_db(np.array([np.mean(power[noise_start:])]))[0])

        # 8. Late slope over 10-20 dB starting 5-10 dB above the noise.
        lower = noise_db + 7.5
        upper = lower + 15.0
        mask = (level_db <= upper) & (level_db >= lower) & (times >= start_index / sample_rate)
        if int(np.count_nonzero(mask)) < 3:
            break
        new_slope, new_intercept, _ = _linear_fit(times[mask], level_db[mask])
        if not np.isfinite(new_slope) or new_slope >= 0.0:
            break
        new_cross_t = (noise_db - new_intercept) / new_slope
        late_slope = new_slope
        if abs(new_cross_t - cross_t) < 0.001:
            cross_t = new_cross_t
            converged = True
            break
        cross_t = new_cross_t

    truncation = int(np.clip(round(cross_t * sample_rate), start_index + 1, n))
    return TruncationEstimate(
        start_index, truncation, noise_db, peak_db, late_slope, converged, iterations
    )


@dataclass(frozen=True)
class SchroederCurve:
    time_s: FloatArray
    edc_db: FloatArray
    truncation: TruncationEstimate
    compensation_energy: float


def schroeder_curve(
    band_ir: FloatArray,
    sample_rate: int,
    *,
    compensate: bool = True,
) -> SchroederCurve:
    """Energy decay curve (dB, 0 dB at the decay start) with noise truncation."""
    power = np.asarray(band_ir, dtype=np.float64) ** 2
    trunc = estimate_truncation(power, sample_rate)
    segment = power[trunc.start_index : trunc.truncation_index]
    if segment.shape[0] == 0:
        segment = power[trunc.start_index : trunc.start_index + 1]
    compensation = 0.0
    if (
        compensate
        and trunc.late_slope_db_per_s is not None
        and trunc.truncation_index < power.shape[0]
    ):
        # Energy of the extrapolated exponential decay after the truncation:
        # p(t) = p_c * 10^(slope * (t - t_c) / 10)  ->  integral = p_c * (-10 / (slope * ln 10)).
        slope = trunc.late_slope_db_per_s
        p_c = 10.0 ** (trunc.noise_floor_db / 10.0)
        compensation = p_c * (-10.0 / (slope * np.log(10.0))) * sample_rate
    edc = np.cumsum(segment[::-1])[::-1] + compensation
    edc_db = _to_db(edc / max(float(edc[0]), _EPS))
    time_s = np.arange(segment.shape[0], dtype=np.float64) / sample_rate
    return SchroederCurve(
        time_s=time_s, edc_db=edc_db, truncation=trunc, compensation_energy=compensation
    )


def fit_decay_metric(
    name: str,
    curve: SchroederCurve,
    evaluation_range_db: tuple[float, float],
    *,
    noise_margin_db: float,
) -> DecayMetric:
    """Fit one metric; report INSUFFICIENT_RANGE instead of a number when the
    evaluation range is not at least ``noise_margin_db`` above the noise."""
    upper, lower = evaluation_range_db
    available = curve.truncation.peak_db - curve.truncation.noise_floor_db
    needed = abs(lower) + noise_margin_db
    if available < needed:
        return DecayMetric(
            name=name,
            seconds=None,
            validity=Validity.INSUFFICIENT_RANGE,
            evaluation_range_db=evaluation_range_db,
            reason=(
                f"Insufficient decay range: {available:.1f} dB available, "
                f"{needed:.0f} dB needed ({abs(lower):.0f} dB range + {noise_margin_db:.0f} dB above noise)"
            ),
        )
    edc = curve.edc_db
    below_upper = np.nonzero(edc <= upper)[0]
    below_lower = np.nonzero(edc <= lower)[0]
    if below_upper.shape[0] == 0 or below_lower.shape[0] == 0:
        return DecayMetric(
            name=name,
            seconds=None,
            validity=Validity.INSUFFICIENT_RANGE,
            evaluation_range_db=evaluation_range_db,
            reason="Insufficient decay range: the decay curve does not reach the evaluation range",
        )
    i0 = int(below_upper[0])
    i1 = int(below_lower[0])
    if i1 - i0 < 3:
        return DecayMetric(
            name=name,
            seconds=None,
            validity=Validity.UNRELIABLE,
            evaluation_range_db=evaluation_range_db,
            reason="Evaluation range covers fewer than 3 samples",
        )
    slope, _, r2 = _linear_fit(curve.time_s[i0 : i1 + 1], edc[i0 : i1 + 1])
    if not np.isfinite(slope) or slope >= 0.0:
        return DecayMetric(
            name=name,
            seconds=None,
            validity=Validity.UNRELIABLE,
            evaluation_range_db=evaluation_range_db,
            reason="Decay slope is not negative",
        )
    seconds = -60.0 / slope
    nonlinearity = 1000.0 * (1.0 - r2)
    return DecayMetric(
        name=name,
        seconds=float(seconds),
        validity=Validity.VALID,
        evaluation_range_db=evaluation_range_db,
        nonlinearity_permille=float(nonlinearity),
    )


def _decimate_curve(
    curve: SchroederCurve, sample_rate: int, step_s: float = 0.001
) -> tuple[FloatArray, FloatArray]:
    step = max(1, round(step_s * sample_rate))
    return curve.time_s[::step], curve.edc_db[::step]


def _mark_unreliable(metric: DecayMetric, reason: str) -> DecayMetric:
    if metric.validity is not Validity.VALID:
        return metric
    return DecayMetric(
        name=metric.name,
        seconds=metric.seconds,
        validity=Validity.UNRELIABLE,
        evaluation_range_db=metric.evaluation_range_db,
        nonlinearity_permille=metric.nonlinearity_permille,
        reason=reason,
    )


def analyze_band(
    band_ir: FloatArray,
    sample_rate: int,
    band: Band | None,
    *,
    noise_margin_db: float,
) -> BandDecay:
    curve = schroeder_curve(band_ir, sample_rate)
    edt = fit_decay_metric("EDT", curve, _EDT_RANGE, noise_margin_db=noise_margin_db)
    t20 = fit_decay_metric("T20", curve, _T20_RANGE, noise_margin_db=noise_margin_db)
    t30 = fit_decay_metric("T30", curve, _T30_RANGE, noise_margin_db=noise_margin_db)

    bt_product: float | None = None
    filter_warning: str | None = None
    if band is not None:
        reference_t = next((m.seconds for m in (t30, t20, edt) if m.seconds is not None), None)
        if reference_t is not None:
            bt_product = band.bandwidth_hz * reference_t
            if bt_product < MIN_BT_PRODUCT:
                filter_warning = (
                    f"B*T = {bt_product:.1f} < {MIN_BT_PRODUCT:g}: the band filter's own decay is "
                    "comparable to the measured decay; values in this band are unreliable"
                )
                edt = _mark_unreliable(edt, filter_warning)
                t20 = _mark_unreliable(t20, filter_warning)
                t30 = _mark_unreliable(t30, filter_warning)

    rt60: float | None = None
    basis: str | None = None
    for metric in (t30, t20):
        if metric.validity is Validity.VALID and metric.seconds is not None:
            rt60 = metric.seconds
            basis = metric.name
            break
    curvature: float | None = None
    if t20.seconds is not None and t30.seconds is not None and t20.seconds > 0.0:
        curvature = 100.0 * (t30.seconds / t20.seconds - 1.0)

    edc_time, edc_db = _decimate_curve(curve, sample_rate)
    return BandDecay(
        band_label=band.label if band is not None else "broadband",
        center_hz=band.center_hz if band is not None else None,
        low_hz=band.low_hz if band is not None else None,
        high_hz=band.high_hz if band is not None else None,
        noise_floor_db=float(curve.truncation.noise_floor_db - curve.truncation.peak_db),
        peak_to_noise_db=float(curve.truncation.peak_db - curve.truncation.noise_floor_db),
        truncation_time_s=float(curve.truncation.truncation_index / sample_rate),
        edt=edt,
        t20=t20,
        t30=t30,
        rt60_estimate_s=rt60,
        rt60_basis=basis,
        curvature_percent=curvature,
        filter_bt_product=bt_product,
        filter_warning=filter_warning,
        edc_time_s=edc_time,
        edc_db=edc_db,
    )


def analyze_decay(ir: FloatArray, sample_rate: int, settings: AnalysisSettings) -> DecayResult:
    """Broadband and octave-band decay analysis of an impulse response."""
    broadband = analyze_band(ir, sample_rate, None, noise_margin_db=settings.decay_noise_margin_db)
    bands: list[BandDecay] = []
    for center in settings.octave_bands_hz:
        band = fractional_octave_band(center, 1)
        if not band_fits(band, sample_rate):
            continue
        sos = bandpass_sos(band, sample_rate)
        filtered = apply_bandpass(ir, sos, time_reversed=True)
        bands.append(
            analyze_band(
                filtered, sample_rate, band, noise_margin_db=settings.decay_noise_margin_db
            )
        )
    return DecayResult(method=DECAY_METHOD, broadband=broadband, bands=tuple(bands))
