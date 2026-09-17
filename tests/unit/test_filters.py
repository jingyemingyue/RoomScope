from __future__ import annotations

import numpy as np
import pytest

from roomscope.core.filters import (
    apply_bandpass,
    apply_bandpass_zero_phase,
    band_fits,
    bandpass_sos,
    filter_decay_time_20db,
    fractional_octave_band,
    fractional_octave_smooth,
)
from roomscope.errors import ConfigurationError


def test_octave_band_edges() -> None:
    band = fractional_octave_band(1000.0, 1)
    assert band.low_hz == pytest.approx(707.107, rel=1e-4)
    assert band.high_hz == pytest.approx(1414.214, rel=1e-4)
    assert band.bandwidth_hz == pytest.approx(707.107, rel=1e-4)
    assert band.label == "1 kHz"
    third = fractional_octave_band(1000.0, 3)
    assert third.low_hz == pytest.approx(890.899, rel=1e-4)
    assert third.high_hz == pytest.approx(1122.462, rel=1e-4)
    assert fractional_octave_band(63.0).label == "63 Hz"


def test_band_fits_below_nyquist() -> None:
    assert band_fits(fractional_octave_band(8000.0), 44100)
    assert not band_fits(fractional_octave_band(16000.0), 44100)
    with pytest.raises(ConfigurationError):
        bandpass_sos(fractional_octave_band(16000.0), 44100)


def test_bandpass_passes_centre_and_rejects_far_frequencies(sample_rate: int) -> None:
    band = fractional_octave_band(1000.0)
    sos = bandpass_sos(band, sample_rate)
    t = np.arange(sample_rate) / sample_rate
    inband = np.sin(2 * np.pi * 1000.0 * t)
    out = apply_bandpass_zero_phase(inband, sos)
    assert np.sqrt(np.mean(out[sample_rate // 4 :] ** 2)) == pytest.approx(np.sqrt(0.5), rel=0.02)
    far = np.sin(2 * np.pi * 4000.0 * t)
    out_far = apply_bandpass_zero_phase(far, sos)
    attenuation_db = 20 * np.log10(
        np.sqrt(np.mean(out_far[sample_rate // 4 :] ** 2)) / np.sqrt(0.5)
    )
    assert attenuation_db < -30.0


def test_time_reversed_filtering_keeps_energy_and_order(sample_rate: int) -> None:
    sos = bandpass_sos(fractional_octave_band(500.0), sample_rate)
    impulse = np.zeros(sample_rate)
    mid = sample_rate // 2
    impulse[mid] = 1.0
    forward = apply_bandpass(impulse, sos, time_reversed=False)
    reverse = apply_bandpass(impulse, sos, time_reversed=True)
    assert np.sum(forward**2) == pytest.approx(np.sum(reverse**2), rel=1e-6)
    # Forward filtering rings after the impulse, reverse filtering rings before it.
    assert np.sum(forward[:mid] ** 2) < 1e-12
    assert np.sum(reverse[mid + 1 :] ** 2) < 1e-12


def test_filter_decay_time_is_positive_and_shorter_for_wide_bands(sample_rate: int) -> None:
    narrow = filter_decay_time_20db(
        bandpass_sos(fractional_octave_band(63.0), sample_rate), sample_rate
    )
    wide = filter_decay_time_20db(
        bandpass_sos(fractional_octave_band(4000.0), sample_rate), sample_rate
    )
    assert narrow is not None and wide is not None
    assert 0.0 < wide < narrow


def test_fractional_octave_smooth_preserves_constant_and_reduces_spike() -> None:
    freqs = np.linspace(1.0, 20000.0, 20000)
    flat = np.full_like(freqs, 3.0)
    assert np.allclose(fractional_octave_smooth(freqs, flat, 3), 3.0)
    spiked = flat.copy()
    spiked[10000] = 23.0
    smoothed = fractional_octave_smooth(freqs, spiked, 3)
    assert smoothed[10000] < 23.0
    assert smoothed[10000] > 3.0
    assert np.array_equal(fractional_octave_smooth(freqs, spiked, 0), spiked)


def test_fractional_octave_smooth_shape_mismatch() -> None:
    with pytest.raises(ConfigurationError):
        fractional_octave_smooth(np.arange(10.0), np.arange(9.0), 3)
