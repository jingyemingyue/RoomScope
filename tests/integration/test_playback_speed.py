"""A DAW that plays the sweep at the wrong speed (sample-rate mismatch without
conversion, or time-stretching) is diagnosed instead of reported as an
unidentifiable direct sound."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import fftconvolve, resample_poly

from roomscope.core.pipeline import Reference, analyze
from roomscope.core.playback_speed import diagnose_playback_speed, measure_sweep_speed
from roomscope.core.sweep import measurement_signal
from roomscope.errors import InvalidAudioError
from roomscope.interpretation import interpret
from roomscope.models.audio import AudioSignal
from roomscope.models.configuration import SweepSettings
from roomscope.models.result import KIND_SAMPLE_RATE, KIND_TIME_STRETCH, Validity
from roomscope.models.result_load import analysis_result_from_dict
from tests.conftest import make_rir

SWEEP = SweepSettings(
    sample_rate=48000, duration_s=3.0, pre_silence_s=1.0, post_silence_s=2.0, level_dbfs=-12.0
)


def _played(signal: np.ndarray, sample_rate: int, *, rt60_s: float = 0.4) -> np.ndarray:
    """``signal`` sounding in a room, recorded at ``sample_rate``."""
    ir = make_rir(sample_rate, rt60_s=rt60_s, diffuse_level=0.02, length_s=1.0, seed=3)
    wet = fftconvolve(signal, ir)[: signal.shape[0] + sample_rate] * 0.3
    return wet + np.random.default_rng(3).normal(0.0, 3e-4, wet.shape[0])


@pytest.fixture(scope="module")
def sweep_signal() -> np.ndarray:
    return measurement_signal(SWEEP)


def test_sweep_played_as_generated_measures_unit_speed(sweep_signal: np.ndarray) -> None:
    recording = _played(sweep_signal, 48000, rt60_s=1.2)
    speed = measure_sweep_speed(recording, 48000, SWEEP)
    assert speed == pytest.approx(1.0, abs=0.005)
    assert diagnose_playback_speed(recording, 48000, SWEEP) is None


@pytest.mark.parametrize(
    ("played_at", "expected_ratio"),
    [(44100, 44100 / 48000), (96000, 2.0), (88200, 88200 / 48000)],
)
def test_file_played_without_conversion_names_the_rate(
    sweep_signal: np.ndarray, played_at: int, expected_ratio: float
) -> None:
    # The 48 kHz samples played unchanged at another rate.
    speed = diagnose_playback_speed(_played(sweep_signal, played_at), played_at, SWEEP)
    assert speed is not None
    assert speed.kind == KIND_SAMPLE_RATE
    assert speed.played_rate_hz == played_at
    assert speed.generated_rate_hz == 48000
    assert speed.speed_ratio == pytest.approx(expected_ratio, rel=0.01)


def test_project_rate_differs_from_export_rate(sweep_signal: np.ndarray) -> None:
    """A 44.1 kHz project played the 48 kHz file unconverted and the take was
    exported at 48 kHz: the recording's rate matches the sweep's, its speed
    does not."""
    slowed = np.asarray(resample_poly(sweep_signal, 160, 147), dtype=np.float64)
    speed = diagnose_playback_speed(_played(slowed, 48000), 48000, SWEEP)
    assert speed is not None and speed.kind == KIND_SAMPLE_RATE
    assert speed.played_rate_hz == 44100


@pytest.mark.parametrize("stretch", [0.97, 1.03])
def test_time_stretch_is_not_a_sample_rate(sweep_signal: np.ndarray, stretch: float) -> None:
    stretched = np.asarray(resample_poly(sweep_signal, round(stretch * 100), 100), dtype=np.float64)
    speed = diagnose_playback_speed(_played(stretched, 48000), 48000, SWEEP)
    assert speed is not None
    assert speed.kind == KIND_TIME_STRETCH
    assert speed.played_rate_hz is None
    assert speed.speed_ratio == pytest.approx(1.0 / stretch, rel=0.005)


def test_noise_without_a_sweep_gives_no_diagnosis() -> None:
    noise = np.random.default_rng(0).normal(0.0, 0.1, 48000 * 6)
    assert measure_sweep_speed(noise, 48000, SWEEP) is None
    assert diagnose_playback_speed(noise, 48000, SWEEP) is None


def test_pipeline_reports_sample_rate_mismatch(sweep_signal: np.ndarray) -> None:
    recording = AudioSignal(_played(sweep_signal, 44100), 44100)
    result = analyze(recording, Reference.from_settings(SWEEP))
    ir = result.impulse_response
    assert ir.direct_sound_confidence != "high"
    assert ir.playback_speed is not None
    assert ir.playback_speed.played_rate_hz == 44100
    assert any("without sample-rate conversion" in note for note in ir.notes)
    assert result.decay.broadband.t30.validity is not Validity.VALID
    assert "speed it was generated at" in (result.decay.broadband.t30.reason or "")

    findings = interpret(result)
    ids = [f.message_id for f in findings]
    assert "measurement.playback_sample_rate" in ids
    # The specific cause replaces the generic "direct sound not identified".
    assert "measurement.direct_sound" not in ids
    message = next(f for f in findings if f.message_id == "measurement.playback_sample_rate")
    assert "48000 Hz" in message.message and "44100 Hz" in message.message

    restored = analysis_result_from_dict(result.to_dict())
    assert restored.impulse_response.playback_speed == ir.playback_speed


def test_pipeline_reports_time_stretch(sweep_signal: np.ndarray) -> None:
    stretched = np.asarray(resample_poly(sweep_signal, 103, 100), dtype=np.float64)
    result = analyze(AudioSignal(_played(stretched, 48000), 48000), Reference.from_settings(SWEEP))
    speed = result.impulse_response.playback_speed
    assert speed is not None and speed.kind == KIND_TIME_STRETCH
    ids = [f.message_id for f in interpret(result)]
    assert "measurement.playback_time_stretch" in ids


def test_good_measurement_is_not_checked(sweep_signal: np.ndarray) -> None:
    result = analyze(
        AudioSignal(_played(sweep_signal, 48000), 48000), Reference.from_settings(SWEEP)
    )
    assert result.impulse_response.direct_sound_confidence == "high"
    assert result.impulse_response.playback_speed is None
    assert result.to_dict()["impulse_response"]["playback_speed"] is None


def test_too_short_recording_explains_a_faster_playback(sweep_signal: np.ndarray) -> None:
    """A 48 kHz sweep played at 96 kHz lasts half as long: the recording is
    shorter than the reference, and the error says why."""
    recording = AudioSignal(_played(sweep_signal, 96000)[: 96000 * 3], 96000)
    with pytest.raises(InvalidAudioError, match="played at 96000 Hz"):
        analyze(recording, Reference.from_settings(SWEEP))


def test_finding_is_translated(sweep_signal: np.ndarray) -> None:
    from roomscope.i18n import activate

    result = analyze(
        AudioSignal(_played(sweep_signal, 44100), 44100), Reference.from_settings(SWEEP)
    )
    activate("zh_CN")
    try:
        finding = next(
            f for f in interpret(result) if f.message_id == "measurement.playback_sample_rate"
        )
    finally:
        activate("en")
    assert "采样率" in finding.message
    assert finding.params["played_rate_hz"] == 44100
