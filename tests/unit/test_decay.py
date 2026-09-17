from __future__ import annotations

import numpy as np
import pytest

from roomscope.core.decay import (
    MIN_BT_PRODUCT,
    analyze_band,
    analyze_decay,
    estimate_truncation,
    fit_decay_metric,
    schroeder_curve,
)
from roomscope.core.filters import fractional_octave_band
from roomscope.models.configuration import AnalysisSettings
from roomscope.models.result import Validity
from tests.conftest import DECAY_CONSTANT, exponential_decay_ir


def test_exact_exponential_decay_gives_exact_rt60(sample_rate: int) -> None:
    rt60 = 0.5
    n = int(1.2 * sample_rate)
    t = np.arange(n) / sample_rate
    # Deterministic alternating-sign exponential: the EDC is exactly exponential.
    ir = np.exp(-DECAY_CONSTANT * t / (2 * rt60)) * np.where(np.arange(n) % 2 == 0, 1.0, -1.0)
    band = analyze_band(ir, sample_rate, None, noise_margin_db=10.0)
    for metric in (band.edt, band.t20, band.t30):
        assert metric.validity is Validity.VALID
        assert metric.seconds == pytest.approx(rt60, rel=0.01)
        assert metric.nonlinearity_permille is not None and metric.nonlinearity_permille < 1.0
    assert band.rt60_estimate_s == pytest.approx(rt60, rel=0.01)
    assert band.rt60_basis == "T30"
    assert abs(band.curvature_percent or 0.0) < 2.0


@pytest.mark.parametrize("rt60", [0.25, 0.6, 1.2])
def test_noisy_exponential_decay_within_five_percent(sample_rate: int, rt60: float) -> None:
    ir = exponential_decay_ir(sample_rate, rt60, length_s=2.0 * rt60)
    band = analyze_band(ir, sample_rate, None, noise_margin_db=10.0)
    assert band.t20.validity is Validity.VALID
    assert band.t30.validity is Validity.VALID
    assert band.t20.seconds == pytest.approx(rt60, rel=0.05)
    assert band.t30.seconds == pytest.approx(rt60, rel=0.05)


def test_noise_floor_limits_available_range(sample_rate: int) -> None:
    rt60 = 0.5
    ir = exponential_decay_ir(sample_rate, rt60, length_s=1.5)
    rng = np.random.default_rng(7)
    # Noise floor about 30 dB below the start level.
    ir = ir + rng.normal(0.0, 10 ** (-30 / 20), ir.shape[0])
    band = analyze_band(ir, sample_rate, None, noise_margin_db=10.0)
    assert 24.0 < band.peak_to_noise_db < 36.0
    assert band.edt.validity is Validity.VALID
    assert band.t20.validity is Validity.INSUFFICIENT_RANGE
    assert band.t30.validity is Validity.INSUFFICIENT_RANGE
    assert band.t20.seconds is None and band.t30.seconds is None
    assert "Insufficient decay range" in (band.t20.reason or "")
    assert band.rt60_estimate_s is None


def test_truncation_point_near_noise_crossing(sample_rate: int) -> None:
    rt60 = 0.5
    ir = exponential_decay_ir(sample_rate, rt60, length_s=1.5)
    rng = np.random.default_rng(3)
    ir = ir + rng.normal(0.0, 10 ** (-40 / 20), ir.shape[0])
    trunc = estimate_truncation(ir**2, sample_rate)
    # Decay reaches -40 dB at rt60 * 40 / 60
    expected = rt60 * 40.0 / 60.0
    assert trunc.truncation_index / sample_rate == pytest.approx(expected, rel=0.25)
    assert trunc.late_slope_db_per_s is not None and trunc.late_slope_db_per_s < 0.0
    assert trunc.noise_floor_db == pytest.approx(-40.0 + 10 * np.log10(1.0), abs=3.0)


def test_schroeder_curve_is_monotonic_and_starts_at_zero(sample_rate: int) -> None:
    ir = exponential_decay_ir(sample_rate, 0.4, length_s=0.8)
    curve = schroeder_curve(ir, sample_rate)
    assert curve.edc_db[0] == pytest.approx(0.0)
    assert np.all(np.diff(curve.edc_db) <= 1e-9)


def test_fit_reports_insufficient_when_curve_short(sample_rate: int) -> None:
    ir = exponential_decay_ir(sample_rate, 2.0, length_s=0.3)
    curve = schroeder_curve(ir, sample_rate, compensate=False)
    metric = fit_decay_metric("T30", curve, (-5.0, -35.0), noise_margin_db=10.0)
    assert metric.validity is not Validity.VALID
    assert metric.seconds is None


def test_octave_band_decay_and_bt_flag(sample_rate: int) -> None:
    rt60 = 0.6
    ir = exponential_decay_ir(sample_rate, rt60, length_s=1.2)
    result = analyze_decay(ir, sample_rate, AnalysisSettings())
    labels = [b.band_label for b in result.bands]
    assert labels == ["63 Hz", "125 Hz", "250 Hz", "500 Hz", "1 kHz", "2 kHz", "4 kHz", "8 kHz"]
    one_khz = next(b for b in result.bands if b.center_hz == 1000.0)
    assert one_khz.t30.validity is Validity.VALID
    assert one_khz.t30.seconds == pytest.approx(rt60, rel=0.1)
    assert one_khz.filter_bt_product is not None and one_khz.filter_bt_product > MIN_BT_PRODUCT
    assert one_khz.filter_warning is None


def test_short_decay_in_low_band_is_flagged_unreliable(sample_rate: int) -> None:
    band = fractional_octave_band(63.0, 1)
    # A 30 ms decay in the 63 Hz band gives B*T ~ 1.3 < 4.
    ir = exponential_decay_ir(sample_rate, 0.03, length_s=0.5)
    from roomscope.core.filters import apply_bandpass, bandpass_sos

    filtered = apply_bandpass(ir, bandpass_sos(band, sample_rate))
    result = analyze_band(filtered, sample_rate, band, noise_margin_db=10.0)
    assert result.filter_bt_product is not None and result.filter_bt_product < MIN_BT_PRODUCT
    assert result.filter_warning is not None
    assert result.t20.validity in (Validity.UNRELIABLE, Validity.INSUFFICIENT_RANGE)
    assert result.rt60_estimate_s is None


def test_bands_that_do_not_fit_are_skipped() -> None:
    sr = 44100
    ir = exponential_decay_ir(sr, 0.3, length_s=0.6)
    settings = AnalysisSettings(octave_bands_hz=(1000.0, 16000.0))
    result = analyze_decay(ir, sr, settings)
    assert [b.band_label for b in result.bands] == ["1 kHz"]
