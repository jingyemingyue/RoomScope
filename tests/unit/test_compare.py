"""Validity-aware comparison of two analysis results."""

from __future__ import annotations

from dataclasses import replace

from roomscope.core.compare import compare
from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.interpretation import interpret_comparison
from roomscope.models.comparison import CompareSettings
from roomscope.models.configuration import SweepSettings
from roomscope.models.result import Validity
from tests.conftest import make_rir


def _result(
    sweep: SweepSettings, *, rt60_s: float, reflections: list[tuple[float, float]], seed: int = 0
):
    ir = make_rir(
        sweep.sample_rate, rt60_s=rt60_s, reflections=reflections, diffuse_level=0.02, seed=seed
    )
    return analyze(
        synthetic_recording(sweep, ir, noise_rms=1e-5, seed=seed), Reference.from_settings(sweep)
    )


def test_compare_two_synthetic_positions(short_sweep: SweepSettings) -> None:
    baseline = _result(short_sweep, rt60_s=0.35, reflections=[(0.018, 0.35)])
    candidate = _result(short_sweep, rt60_s=0.55, reflections=[(0.0185, 0.20)], seed=4)
    comparison = compare(baseline, candidate)
    assert comparison.comparable
    assert comparison.common_band is not None
    assert all(item.validity is not None for item in comparison.decay)
    rt = next(item for item in comparison.decay if item.name == "broadband.rt60_estimate")
    assert rt.validity is Validity.VALID
    assert rt.delta_s is not None and rt.delta_s > 0.0
    assert rt.delta_percent is not None
    matched = [m for m in comparison.reflections if m.status == "matched"]
    assert matched
    assert matched[0].level_delta_db is not None
    noise = next(item for item in comparison.noise if item.name == "noise.rms_dbfs")
    assert noise.validity is Validity.UNRELIABLE
    assert noise.reason == "gain not declared equal"
    same = compare(baseline, candidate, settings=CompareSettings(same_input_gain=True))
    noise_ok = next(item for item in same.noise if item.name == "noise.rms_dbfs")
    assert noise_ok.validity is Validity.VALID
    findings = interpret_comparison(comparison)
    assert findings
    assert all(f.message for f in findings)
    joined = " ".join(f.message.lower() for f in findings)
    assert "not enough to call the change significant" in joined
    assert "the change is significant" not in joined


def test_compare_not_comparable_when_band_too_narrow(short_sweep: SweepSettings) -> None:
    baseline = _result(short_sweep, rt60_s=0.35, reflections=[(0.018, 0.35)])
    narrow = replace(
        baseline,
        impulse_response=replace(
            baseline.impulse_response,
            excitation_band=replace(baseline.impulse_response.excitation_band, high_hz=30.0)
            if baseline.impulse_response.excitation_band is not None
            else None,
        ),
    )
    comparison = compare(narrow, baseline)
    assert comparison.comparable is False
    assert comparison.decay == ()
    findings = interpret_comparison(comparison)
    assert findings[0].message_id == "comparison.not_comparable"


def test_decay_delta_not_comparable_unless_both_valid(short_sweep: SweepSettings) -> None:
    baseline = _result(short_sweep, rt60_s=0.35, reflections=[(0.018, 0.35)])
    broken = replace(
        baseline,
        decay=replace(
            baseline.decay,
            broadband=replace(
                baseline.decay.broadband,
                t30=replace(
                    baseline.decay.broadband.t30,
                    validity=Validity.INSUFFICIENT_RANGE,
                    seconds=None,
                    reason="synthetic",
                ),
            ),
        ),
    )
    other = _result(short_sweep, rt60_s=0.4, reflections=[(0.018, 0.3)], seed=2)
    comparison = compare(broken, other)
    t30 = next(item for item in comparison.decay if item.name == "broadband.t30")
    assert t30.validity is Validity.NOT_COMPARABLE
    assert t30.delta_s is None
    assert "synthetic" in (t30.reason or "")


def test_placement_refused_unless_both_tier_two(short_sweep: SweepSettings) -> None:
    baseline = _result(short_sweep, rt60_s=0.35, reflections=[(0.018, 0.35)])
    comparison = compare(baseline, baseline)
    place = next(item for item in comparison.placement if item.name == "placement.source_height_m")
    assert place.validity is Validity.NOT_COMPARABLE
