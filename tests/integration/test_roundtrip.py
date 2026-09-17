"""End-to-end round trips: generate sweep -> synthetic room -> analyse."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import fftconvolve

from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.core.sweep import measurement_signal
from roomscope.models.audio import AudioSignal
from roomscope.models.configuration import AnalysisSettings, SweepSettings
from roomscope.models.result import Validity
from tests.conftest import make_rir


def test_round_trip_recovers_rt60_reflection_and_noise(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    rt60 = 0.45
    ir = make_rir(sr, rt60_s=rt60, reflections=[(0.018, 10 ** (-9 / 20))], diffuse_level=0.01)
    rec = synthetic_recording(short_sweep, ir, noise_rms=3e-5)
    result = analyze(rec, Reference.from_settings(short_sweep))

    assert result.impulse_response.peak_value == pytest.approx(1.0, abs=0.02)
    assert result.impulse_response.direct_sound_confidence == "high"
    broadband = result.decay.broadband
    assert broadband.t30.validity is Validity.VALID
    assert broadband.rt60_estimate_s == pytest.approx(rt60, rel=0.1)
    mid = [b for b in result.decay.bands if b.center_hz in (500.0, 1000.0, 2000.0)]
    for band in mid:
        assert band.rt60_estimate_s == pytest.approx(rt60, rel=0.15)
    strong = [r for r in result.reflections.reflections if r.relative_db > -12.0]
    assert len(strong) == 1
    assert strong[0].delay_ms == pytest.approx(18.0, abs=0.2)
    assert result.noise.segment_source == "pre-sweep"
    assert result.noise.rms_dbfs == pytest.approx(20 * np.log10(3e-5 * np.sqrt(2)), abs=0.5)
    assert not any(h.detected for h in result.noise.hum)


@pytest.mark.parametrize("recording_rate", [44100, 96000])
def test_recording_at_other_sample_rate_regenerates_reference(
    short_sweep: SweepSettings, recording_rate: int
) -> None:
    played = short_sweep.with_sample_rate(recording_rate)  # what the DAW effectively played
    ir = make_rir(recording_rate, rt60_s=0.4, diffuse_level=0.01)
    rec = synthetic_recording(played, ir, noise_rms=3e-5)
    result = analyze(rec, Reference.from_settings(short_sweep))
    assert result.sample_rate == recording_rate
    assert any("regenerated" in w for w in result.warnings)
    assert result.decay.broadband.rt60_estimate_s == pytest.approx(0.4, rel=0.1)


def test_stereo_recording_channel_selection(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    ir = make_rir(sr, rt60_s=0.3, diffuse_level=0.01)
    mono = synthetic_recording(short_sweep, ir, noise_rms=1e-5).samples
    stereo = AudioSignal(np.stack([mono * 0.01, mono], axis=1), sr)
    auto = analyze(stereo, Reference.from_settings(short_sweep))
    assert auto.analysis_settings["channel_analysed"] == 1
    assert any("channels" in w for w in auto.warnings)
    explicit = analyze(stereo, Reference.from_settings(short_sweep), AnalysisSettings(channel=0))
    assert explicit.analysis_settings["channel_analysed"] == 0
    assert explicit.impulse_response.peak_value == pytest.approx(0.01, rel=0.05)


def test_reference_from_signal_without_sweep_definition(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    ir = make_rir(sr, rt60_s=0.4, diffuse_level=0.01)
    rec = synthetic_recording(short_sweep, ir, noise_rms=3e-5)
    reference = Reference.from_signal(measurement_signal(short_sweep), sr)
    result = analyze(rec, reference)
    assert any("spectral division" in w for w in result.warnings)
    assert result.impulse_response.peak_value == pytest.approx(1.0, abs=0.05)
    assert result.decay.broadband.rt60_estimate_s == pytest.approx(0.4, rel=0.1)


def test_reference_signal_at_other_rate_is_resampled(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    ir = make_rir(sr, rt60_s=0.4, diffuse_level=0.01)
    rec = synthetic_recording(short_sweep, ir, noise_rms=3e-5)
    other = short_sweep.with_sample_rate(96000)
    reference = Reference.from_signal(measurement_signal(other), 96000)
    result = analyze(rec, reference)
    assert any("resampled" in w for w in result.warnings)
    assert result.decay.broadband.rt60_estimate_s == pytest.approx(0.4, rel=0.15)


def test_noisy_measurement_reports_insufficient_range(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    ir = make_rir(sr, rt60_s=0.5, diffuse_level=0.01)
    rec = synthetic_recording(short_sweep, ir, noise_rms=0.02)
    result = analyze(rec, Reference.from_settings(short_sweep))
    broadband = result.decay.broadband
    assert broadband.t30.validity is Validity.INSUFFICIENT_RANGE
    assert broadband.t30.seconds is None
    assert "Insufficient decay range" in (broadband.t30.reason or "")


def test_loudspeaker_distortion_is_separated_from_linear_response(
    short_sweep: SweepSettings,
) -> None:
    sr = short_sweep.sample_rate
    ir = make_rir(sr, rt60_s=0.4, diffuse_level=0.01)
    excitation = measurement_signal(short_sweep)
    # Memoryless 2nd/3rd order distortion of the loudspeaker before the room.
    distorted = excitation + 0.1 * excitation**2 + 0.05 * excitation**3
    rec = AudioSignal(fftconvolve(distorted, ir)[: excitation.shape[0] + ir.shape[0]], sr)
    result = analyze(rec, Reference.from_settings(short_sweep))
    assert result.impulse_response.pre_peak_margin_db > 15.0
    assert result.impulse_response.peak_value == pytest.approx(1.0, rel=0.1)
    assert result.decay.broadband.rt60_estimate_s == pytest.approx(0.4, rel=0.1)
