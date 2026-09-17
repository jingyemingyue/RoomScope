from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import fftconvolve, hilbert

from roomscope.core.sweep import (
    generate_ess,
    harmonic_pre_response_offsets_s,
    instantaneous_frequency,
    inverse_filter,
    inverse_filter_spectral,
    measurement_signal,
    reference_pulse,
    sweep_time_axis,
)
from roomscope.errors import ConfigurationError
from roomscope.models.configuration import SUPPORTED_SAMPLE_RATES, SweepSettings


def test_sweep_length_and_level(short_sweep: SweepSettings) -> None:
    x = generate_ess(short_sweep)
    assert x.shape[0] == short_sweep.sweep_samples == int(2.0 * short_sweep.sample_rate)
    assert np.max(np.abs(x)) == pytest.approx(short_sweep.amplitude, rel=1e-3)
    assert short_sweep.amplitude == pytest.approx(10 ** (-12 / 20))


def test_sweep_fades_start_and_end_at_zero(short_sweep: SweepSettings) -> None:
    x = generate_ess(short_sweep)
    assert x[0] == 0.0
    assert abs(x[-1]) < 1e-3 * short_sweep.amplitude


def test_instantaneous_frequency_follows_exponential_law(short_sweep: SweepSettings) -> None:
    x = generate_ess(short_sweep, apply_level=False)
    sr = short_sweep.sample_rate
    phase = np.unwrap(np.angle(hilbert(x)))
    measured = np.diff(phase) * sr / (2 * np.pi)
    t = sweep_time_axis(short_sweep)[:-1]
    expected = instantaneous_frequency(short_sweep, t)
    # Compare in the middle of the sweep (away from fades and Hilbert edge effects)
    lo, hi = int(0.2 * len(t)), int(0.8 * len(t))
    assert np.allclose(measured[lo:hi], expected[lo:hi], rtol=0.02)
    assert expected[0] == pytest.approx(short_sweep.start_hz)
    assert instantaneous_frequency(short_sweep, np.array([short_sweep.duration_s]))[
        0
    ] == pytest.approx(short_sweep.end_hz, rel=1e-6)


def test_measurement_signal_has_silences(short_sweep: SweepSettings) -> None:
    sig = measurement_signal(short_sweep)
    sr = short_sweep.sample_rate
    assert sig.shape[0] == short_sweep.total_samples
    assert np.all(sig[: int(1.0 * sr)] == 0.0)
    assert np.all(sig[-int(1.5 * sr) :] == 0.0)


def test_inverse_filter_produces_unit_pulse(short_sweep: SweepSettings) -> None:
    pulse = reference_pulse(short_sweep)
    k = int(np.argmax(np.abs(pulse)))
    assert pulse[k] == pytest.approx(1.0, abs=1e-9)
    # The linear response sits at the end of the sweep (index M - 1 of the full convolution).
    assert k == short_sweep.sweep_samples - 1
    rel = np.abs(pulse) / np.abs(pulse[k])
    w = int(2e-3 * short_sweep.sample_rate)
    outside = np.concatenate([rel[: k - w], rel[k + w + 1 :]])
    assert 20 * np.log10(outside.max()) < -35.0


def test_spectral_inverse_matches_analytic_behaviour(short_sweep: SweepSettings) -> None:
    ref = generate_ess(short_sweep)
    inv = inverse_filter_spectral(ref)
    assert inv.shape[0] == ref.shape[0]
    pulse = fftconvolve(ref, inv)
    k = int(np.argmax(np.abs(pulse)))
    assert pulse[k] == pytest.approx(1.0, abs=1e-6)
    assert k == short_sweep.sweep_samples - 1
    rel = np.abs(pulse) / np.abs(pulse[k])
    w = int(2e-3 * short_sweep.sample_rate)
    outside = np.concatenate([rel[: k - w], rel[k + w + 1 :]])
    assert 20 * np.log10(outside.max()) < -35.0


def test_inverse_filter_is_time_reversed_with_6db_per_octave_envelope(
    short_sweep: SweepSettings,
) -> None:
    inv = inverse_filter(short_sweep)
    unit = generate_ess(short_sweep, apply_level=False)[::-1]
    # envelope ratio between t and t + L*ln2 (one octave) must be 1/2
    rate = short_sweep.sweep_rate
    sr = short_sweep.sample_rate
    i0 = int(0.1 * sr)
    i1 = i0 + round(rate * np.log(2) * sr)
    env = np.abs(hilbert(inv / np.max(np.abs(unit))))
    ratio = np.median(env[i1 - 50 : i1 + 50]) / np.median(env[i0 - 50 : i0 + 50])
    assert ratio == pytest.approx(0.5, rel=0.1)


def test_harmonic_pre_response_offsets(short_sweep: SweepSettings) -> None:
    offsets = harmonic_pre_response_offsets_s(short_sweep, max_order=3)
    rate = short_sweep.sweep_rate
    assert offsets == pytest.approx([rate * np.log(2), rate * np.log(3)])


@pytest.mark.parametrize("sr", SUPPORTED_SAMPLE_RATES)
def test_all_supported_sample_rates_generate(sr: int) -> None:
    settings = SweepSettings(sample_rate=sr, duration_s=1.0)
    x = generate_ess(settings)
    assert x.shape[0] == sr
    assert np.all(np.isfinite(x))


def test_unsupported_sample_rate_rejected() -> None:
    with pytest.raises(ConfigurationError):
        SweepSettings(sample_rate=32000)


def test_end_frequency_above_nyquist_rejected() -> None:
    with pytest.raises(ConfigurationError):
        SweepSettings(sample_rate=44100, end_hz=23000.0)


def test_level_above_full_scale_rejected() -> None:
    with pytest.raises(ConfigurationError):
        SweepSettings(level_dbfs=1.0)


def test_spectral_inverse_rejects_silence() -> None:
    with pytest.raises(ConfigurationError):
        inverse_filter_spectral(np.zeros(1000))
