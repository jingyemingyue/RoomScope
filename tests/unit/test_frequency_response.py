from __future__ import annotations

import numpy as np
import pytest

from roomscope.core.frequency_response import frequency_response


def test_delta_is_flat_zero_db(sample_rate: int) -> None:
    ir = np.zeros(sample_rate)
    ir[10] = 1.0
    fr = frequency_response(ir, sample_rate, smoothing_fraction=6)
    assert fr.frequencies_hz[0] > 0.0
    assert fr.frequencies_hz[-1] == pytest.approx(sample_rate / 2)
    assert np.allclose(fr.magnitude_db_raw, 0.0, atol=1e-9)
    assert fr.magnitude_db_smoothed is not None
    assert np.allclose(fr.magnitude_db_smoothed, 0.0, atol=1e-9)
    assert fr.smoothing_fraction == 6


def test_gain_is_reported_in_db(sample_rate: int) -> None:
    ir = np.zeros(sample_rate // 2)
    ir[0] = 0.5
    fr = frequency_response(ir, sample_rate, smoothing_fraction=0)
    assert fr.magnitude_db_smoothed is None
    assert np.allclose(fr.magnitude_db_raw, 20 * np.log10(0.5), atol=1e-9)


def test_comb_filter_notch_depth(sample_rate: int) -> None:
    delay = int(0.001 * sample_rate)  # 1 ms -> first notch at 500 Hz
    ir = np.zeros(sample_rate)
    ir[0] = 1.0
    ir[delay] = 0.5
    fr = frequency_response(ir, sample_rate, smoothing_fraction=0)
    i_notch = int(np.argmin(np.abs(fr.frequencies_hz - 500.0)))
    i_peak = int(np.argmin(np.abs(fr.frequencies_hz - 1000.0)))
    assert fr.magnitude_db_raw[i_notch] == pytest.approx(20 * np.log10(0.5), abs=0.05)
    assert fr.magnitude_db_raw[i_peak] == pytest.approx(20 * np.log10(1.5), abs=0.05)


def test_window_limits_analysed_length(sample_rate: int) -> None:
    ir = np.zeros(2 * sample_rate)
    ir[0] = 1.0
    fr = frequency_response(ir, sample_rate, window_s=0.25)
    assert fr.window_s == pytest.approx(0.25)
    assert fr.frequencies_hz[1] - fr.frequencies_hz[0] <= 1.0
