from __future__ import annotations

import numpy as np
import pytest

from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.errors import ConfigurationError
from roomscope.interpretation import Severity, available_profiles, interpret
from roomscope.models.configuration import SweepSettings
from tests.conftest import make_rir


def test_generic_profile_reports_reflection_and_hum(short_sweep: SweepSettings) -> None:
    sr = short_sweep.sample_rate
    ir = make_rir(sr, rt60_s=0.35, reflections=[(0.018, 10 ** (-8 / 20))], diffuse_level=0.01)
    rec = synthetic_recording(short_sweep, ir, noise_rms=2e-5)
    t = np.arange(rec.n_samples) / sr
    hum = sum(a * np.sin(2 * np.pi * 50.0 * k * t) for k, a in ((1, 4e-4), (2, 2e-4), (3, 1e-4)))
    rec = type(rec)(samples=rec.samples + hum, sample_rate=sr)
    result = analyze(rec, Reference.from_settings(short_sweep))
    findings = interpret(result)
    topics = {f.topic for f in findings}
    assert "early_reflections" in topics
    reflection = next(f for f in findings if f.topic == "early_reflections")
    assert reflection.evidence["delay_ms"] == pytest.approx(18.0, abs=0.5)
    assert any(f.topic == "noise" and f.severity is Severity.WARNING for f in findings)
    assert all(f.to_dict()["message"] for f in findings)


def test_unknown_profile_rejected(short_sweep: SweepSettings) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.3)
    rec = synthetic_recording(short_sweep, ir)
    result = analyze(rec, Reference.from_settings(short_sweep))
    assert available_profiles() == ["generic"]
    with pytest.raises(ConfigurationError):
        interpret(result, "vocal")
