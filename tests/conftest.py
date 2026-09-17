"""Shared fixtures: synthetic rooms and short sweeps so the suite runs fast."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pytest

from roomscope.models.audio import FloatArray
from roomscope.models.configuration import SweepSettings

DECAY_CONSTANT = 3.0 * np.log(10.0) * 2.0  # 60 dB in natural-log units: ln(10^6) = 13.8155


def make_rir(
    sample_rate: int,
    *,
    rt60_s: float = 0.5,
    length_s: float | None = None,
    direct: float = 1.0,
    reflections: Sequence[tuple[float, float]] = (),
    diffuse_level: float = 0.02,
    seed: int = 0,
    start_delay_s: float = 0.0,
) -> FloatArray:
    """Synthetic room impulse response.

    ``direct`` impulse at ``start_delay_s``, discrete ``reflections`` as
    ``(delay_s, linear_gain)`` relative to the direct sound, and a Gaussian
    diffuse tail whose energy decays 60 dB in ``rt60_s``.
    """
    length = length_s if length_s is not None else max(1.0, 1.6 * rt60_s)
    n = int(length * sample_rate)
    t = np.arange(n) / sample_rate
    rng = np.random.default_rng(seed)
    d0 = round(start_delay_s * sample_rate)
    tail = np.zeros(n)
    if diffuse_level > 0.0:
        envelope = np.exp(-DECAY_CONSTANT * np.maximum(t - t[d0], 0.0) / (2.0 * rt60_s))
        envelope[:d0] = 0.0
        tail = rng.normal(0.0, 1.0, n) * envelope * diffuse_level
    ir = tail
    ir[d0] += direct
    for delay_s, gain in reflections:
        idx = d0 + round(delay_s * sample_rate)
        if idx < n:
            ir[idx] += direct * gain
    return np.asarray(ir, dtype=np.float64)


def exponential_decay_ir(
    sample_rate: int, rt60_s: float, length_s: float, seed: int = 1
) -> FloatArray:
    """Gaussian noise with an exactly exponential energy envelope (no direct sound)."""
    n = int(length_s * sample_rate)
    t = np.arange(n) / sample_rate
    rng = np.random.default_rng(seed)
    return np.asarray(
        rng.normal(0.0, 1.0, n) * np.exp(-DECAY_CONSTANT * t / (2.0 * rt60_s)), dtype=np.float64
    )


@pytest.fixture(scope="session")
def sample_rate() -> int:
    return 48000


@pytest.fixture(scope="session")
def short_sweep(sample_rate: int) -> SweepSettings:
    """A 2 s sweep keeps the whole suite fast while staying realistic."""
    return SweepSettings(
        sample_rate=sample_rate,
        duration_s=2.0,
        pre_silence_s=1.0,
        post_silence_s=1.5,
        level_dbfs=-12.0,
    )
