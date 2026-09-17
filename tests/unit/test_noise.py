from __future__ import annotations

import numpy as np
import pytest

from roomscope.core.noise import (
    QuietSegment,
    analyze_noise,
    find_quiet_segment,
    peak_dbfs,
    rms_dbfs,
)
from roomscope.models.configuration import DEFAULT_OCTAVE_BANDS_HZ


def test_full_scale_sine_is_zero_dbfs_rms(sample_rate: int) -> None:
    t = np.arange(sample_rate) / sample_rate
    sine = np.sin(2 * np.pi * 1000.0 * t)
    assert rms_dbfs(sine) == pytest.approx(0.0, abs=0.01)
    assert peak_dbfs(0.5 * sine) == pytest.approx(-6.02, abs=0.01)


def test_quiet_segment_prefers_pre_sweep(sample_rate: int) -> None:
    seg = find_quiet_segment(
        recording_length=10 * sample_rate,
        sample_rate=sample_rate,
        sweep_start_index=2 * sample_rate,
        reference_length=3 * sample_rate,
        min_segment_s=0.5,
    )
    assert seg is not None and seg.source == "pre-sweep"
    assert seg.start == int(0.05 * sample_rate)
    assert seg.end == 2 * sample_rate - int(0.1 * sample_rate)


def test_quiet_segment_falls_back_to_tail_or_none(sample_rate: int) -> None:
    tail = find_quiet_segment(
        recording_length=12 * sample_rate,
        sample_rate=sample_rate,
        sweep_start_index=int(0.1 * sample_rate),
        reference_length=3 * sample_rate,
        min_segment_s=0.5,
    )
    assert tail is not None and tail.source == "tail" and tail.note
    none = find_quiet_segment(
        recording_length=4 * sample_rate,
        sample_rate=sample_rate,
        sweep_start_index=int(0.1 * sample_rate),
        reference_length=3 * sample_rate,
        min_segment_s=0.5,
    )
    assert none is None


def _noise(sample_rate: int, seconds: float, seed: int = 0) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1e-4, int(seconds * sample_rate))


def test_white_noise_has_no_hum(sample_rate: int) -> None:
    x = _noise(sample_rate, 3.0)
    res = analyze_noise(
        x,
        sample_rate,
        QuietSegment(0, x.shape[0], "pre-sweep"),
        octave_bands_hz=DEFAULT_OCTAVE_BANDS_HZ,
    )
    assert res.rms_dbfs == pytest.approx(20 * np.log10(1e-4 * np.sqrt(2)), abs=0.2)
    assert not any(h.detected for h in res.hum)
    assert len(res.band_levels_dbfs) == len(DEFAULT_OCTAVE_BANDS_HZ)
    assert res.psd_db is not None and res.psd_frequencies_hz is not None


def test_mains_hum_detected_at_right_base_frequency(sample_rate: int) -> None:
    x = _noise(sample_rate, 3.0)
    t = np.arange(x.shape[0]) / sample_rate
    for k, amp in ((1, 5e-4), (2, 2.5e-4), (3, 1e-4), (5, 5e-5)):
        x = x + amp * np.sin(2 * np.pi * 60.0 * k * t)
    res = analyze_noise(
        x,
        sample_rate,
        QuietSegment(0, x.shape[0], "pre-sweep"),
        octave_bands_hz=DEFAULT_OCTAVE_BANDS_HZ,
    )
    by_base = {h.base_hz: h for h in res.hum}
    assert by_base[60.0].detected
    assert [f for f, _ in by_base[60.0].harmonics][:3] == [60.0, 120.0, 180.0]
    assert not by_base[50.0].detected


def test_no_segment_gives_notes_only(sample_rate: int) -> None:
    res = analyze_noise(
        np.zeros(sample_rate), sample_rate, None, octave_bands_hz=DEFAULT_OCTAVE_BANDS_HZ
    )
    assert res.rms_dbfs is None and res.segment_source is None
    assert res.notes


def test_short_segment_skips_hum(sample_rate: int) -> None:
    x = _noise(sample_rate, 0.1)
    res = analyze_noise(
        x, sample_rate, QuietSegment(0, x.shape[0], "tail"), octave_bands_hz=DEFAULT_OCTAVE_BANDS_HZ
    )
    assert res.hum == ()
    assert any("too short" in n for n in res.notes)
