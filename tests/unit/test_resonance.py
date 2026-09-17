from __future__ import annotations

import numpy as np
import pytest

from roomscope.core.frequency_response import frequency_response
from roomscope.core.resonance import detect_potential_resonances
from tests.conftest import DECAY_CONSTANT, make_rir


def test_ringing_low_frequency_mode_is_a_candidate(sample_rate: int) -> None:
    ir = make_rir(sample_rate, rt60_s=0.3, length_s=2.0, diffuse_level=0.01)
    t = np.arange(ir.shape[0]) / sample_rate
    # A 62 Hz mode ringing with RT60 = 1.5 s
    ir = ir + 0.15 * np.sin(2 * np.pi * 62.0 * t) * np.exp(-DECAY_CONSTANT * t / (2 * 1.5))
    fr = frequency_response(ir, sample_rate, smoothing_fraction=0)
    res = detect_potential_resonances(ir, sample_rate, fr, max_hz=300.0, min_prominence_db=6.0)
    assert res.candidates
    best = max(res.candidates, key=lambda c: c.level_above_baseline_db)
    assert best.frequency_hz == pytest.approx(62.0, abs=3.0)
    assert best.narrowband_decay_20db_s is not None
    assert best.filter_ringing_20db_s is not None
    assert best.decay_distinguishable is True
    assert any("Candidates only" in n for n in res.notes)


def test_flat_response_has_no_candidates(sample_rate: int) -> None:
    ir = np.zeros(sample_rate)
    ir[0] = 1.0
    fr = frequency_response(ir, sample_rate, smoothing_fraction=0)
    res = detect_potential_resonances(ir, sample_rate, fr, max_hz=300.0, min_prominence_db=6.0)
    assert res.candidates == ()
