"""Electrical-loopback validation and regularised compensation."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import fftconvolve

from roomscope.core.deconvolution import deconvolve, locate_impulse_response
from roomscope.core.loopback import (
    COMPENSATION_TOLERANCE_DB,
    LOOPBACK_FR_REFERENCE,
    MAX_ELECTRICAL_SETTLE_MS,
    MIN_LATE_PEAK_DROP_DB,
    assess_loopback,
    energy_settling_ms,
    late_peak_drop_db,
)
from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.core.sweep import inverse_filter, measurement_signal, normalisation_band_hz
from roomscope.errors import ConfigurationError, SampleRateMismatchError
from roomscope.models.audio import AudioSignal
from roomscope.models.configuration import AnalysisSettings, SweepSettings
from roomscope.models.result import Validity
from tests.conftest import fr_median_db, make_rir


def _pad_to(samples: np.ndarray, n: int) -> np.ndarray:
    if samples.shape[0] >= n:
        return np.asarray(samples[:n], dtype=np.float64)
    return np.pad(np.asarray(samples, dtype=np.float64), (0, n - samples.shape[0]))


def _locate(h: np.ndarray, rec_len: int, sweep: SweepSettings):
    return locate_impulse_response(
        h,
        recording_length=rec_len,
        reference_length=sweep.sweep_samples,
        sample_rate=sweep.sample_rate,
        pre_delay_ms=5.0,
        max_length_s=1.0,
        sweep_rate_s=sweep.sweep_rate,
    )


def test_electrical_loopback_is_accepted(short_sweep: SweepSettings) -> None:
    rec = measurement_signal(short_sweep)
    h = deconvolve(rec, inverse_filter(short_sweep))
    located = _locate(h, rec.shape[0], short_sweep)
    settle = energy_settling_ms(h, located.peak_index, short_sweep.sample_rate)
    drop = late_peak_drop_db(h, located.peak_index, short_sweep.sample_rate)
    assert settle is not None and settle <= MAX_ELECTRICAL_SETTLE_MS
    assert drop is not None and drop >= MIN_LATE_PEAK_DROP_DB
    assessment = assess_loopback(located, h, short_sweep.sample_rate, clipped=False)
    assert assessment.accepted
    assert assessment.fir is not None


def test_room_like_loopback_is_refused(short_sweep: SweepSettings) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.4, reflections=[(0.018, 0.35)])
    rec = synthetic_recording(short_sweep, ir, noise_rms=1e-5)
    h = deconvolve(rec.samples, inverse_filter(short_sweep))
    located = _locate(h, rec.n_samples, short_sweep)
    assessment = assess_loopback(located, h, short_sweep.sample_rate, clipped=False)
    assert assessment.accepted is False
    assert assessment.reason is not None
    assert "room" in assessment.reason or "cable" in assessment.reason


def test_clipped_loopback_is_refused(short_sweep: SweepSettings) -> None:
    rec = measurement_signal(short_sweep)
    h = deconvolve(rec, inverse_filter(short_sweep))
    located = _locate(h, rec.shape[0], short_sweep)
    assessment = assess_loopback(located, h, short_sweep.sample_rate, clipped=True)
    assert assessment.accepted is False
    assert assessment.reason is not None
    assert "clip" in assessment.reason


def test_analyze_without_loopback_leaves_slot_empty(short_sweep: SweepSettings) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.3, reflections=[(0.018, 0.3)])
    result = analyze(
        synthetic_recording(short_sweep, ir, noise_rms=1e-5),
        Reference.from_settings(short_sweep),
    )
    assert result.impulse_response.loopback is None


def test_stereo_loopback_channel_must_differ_from_mic(short_sweep: SweepSettings) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.3)
    mic = synthetic_recording(short_sweep, ir, noise_rms=1e-5).samples
    stereo = np.stack([mic, mic], axis=1)
    rec = AudioSignal(stereo, short_sweep.sample_rate)
    with pytest.raises(ConfigurationError, match="differ"):
        analyze(
            rec,
            Reference.from_settings(short_sweep),
            AnalysisSettings(channel=0, loopback_channel=0),
        )


def test_separate_loopback_sample_rate_must_match(short_sweep: SweepSettings) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.3)
    rec = synthetic_recording(short_sweep, ir, noise_rms=1e-5)
    other = AudioSignal(rec.samples, 44100)
    with pytest.raises(SampleRateMismatchError):
        analyze(rec, Reference.from_settings(short_sweep), loopback=other)


def test_compensate_flattens_a_known_interface_fir(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    interface = np.array([1.0, 0.35, 0.12, 0.04], dtype=np.float64)
    room = make_rir(sr, rt60_s=0.35, reflections=[(0.018, 0.3)], diffuse_level=0.01)
    colored = np.asarray(fftconvolve(interface, room), dtype=np.float64)
    mic = synthetic_recording(short_sweep, colored, noise_rms=1e-6)
    lb_ir = np.zeros(int(0.05 * sr), dtype=np.float64)
    lb_ir[: interface.shape[0]] = interface
    lb_raw = synthetic_recording(short_sweep, lb_ir, noise_rms=1e-7)
    loopback = AudioSignal(_pad_to(lb_raw.samples, mic.n_samples), sr)
    dry = analyze(
        synthetic_recording(short_sweep, room, noise_rms=1e-6), Reference.from_settings(short_sweep)
    )
    wet = analyze(mic, Reference.from_settings(short_sweep))
    fixed = analyze(mic, Reference.from_settings(short_sweep), loopback=loopback)
    assert fixed.impulse_response.loopback is not None
    assert fixed.impulse_response.loopback.compensation_applied is True
    assert fixed.frequency_response.reference == LOOPBACK_FR_REFERENCE
    band = dry.impulse_response.excitation_band
    assert band is not None
    lo, hi = normalisation_band_hz(band.low_hz, band.high_hz)

    def median_err(a, b) -> float:
        freqs = a.frequency_response.frequencies_hz
        select = (freqs >= lo) & (freqs <= hi)
        # interpolate b onto a's grid
        from numpy import interp

        b_on_a = interp(
            freqs[select],
            b.frequency_response.frequencies_hz,
            b.frequency_response.magnitude_db_raw,
        )
        return float(np.median(np.abs(a.frequency_response.magnitude_db_raw[select] - b_on_a)))

    assert median_err(fixed, dry) < COMPENSATION_TOLERANCE_DB
    assert median_err(wet, dry) > COMPENSATION_TOLERANCE_DB
    assert abs(fr_median_db(fixed) - fr_median_db(dry)) < COMPENSATION_TOLERANCE_DB


def test_room_used_as_loopback_does_not_corrupt_mic(short_sweep: SweepSettings) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.4, reflections=[(0.018, 0.35)])
    rec = synthetic_recording(short_sweep, ir, noise_rms=1e-5)
    result = analyze(rec, Reference.from_settings(short_sweep), loopback=rec)
    assert result.impulse_response.loopback is not None
    assert result.impulse_response.loopback.compensation_applied is False
    assert result.impulse_response.loopback.reason is not None


def test_path_delay_and_tape_bound(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    delay_s = 0.006
    room = make_rir(sr, rt60_s=0.3, reflections=[(0.018, 0.3)], start_delay_s=delay_s)
    mic = synthetic_recording(short_sweep, room, noise_rms=1e-6)
    loopback = AudioSignal(_pad_to(measurement_signal(short_sweep), mic.n_samples), sr)
    result = analyze(
        mic,
        Reference.from_settings(short_sweep),
        AnalysisSettings(placement_distance_m=5.0, placement_mic_height_m=1.2),
        loopback=loopback,
    )
    lb = result.impulse_response.loopback
    assert lb is not None and lb.compensation_applied
    assert lb.path_delay_ms is not None
    assert lb.path_delay_ms == pytest.approx(delay_s * 1000.0, abs=0.4)
    assert lb.distance_upper_bound_m is not None
    assert lb.distance_upper_bound_m < 5.0
    assert result.placement is not None
    assert any("exceeds the loopback path-delay bound" in n for n in result.placement.notes)
    if result.placement.source_height_m.validity is Validity.VALID:
        raise AssertionError("tape longer than the bound must not stay VALID")
