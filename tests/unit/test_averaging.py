from __future__ import annotations

from roomscope.core.averaging import average_decay, iso_3382_2_class
from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.models.configuration import SweepSettings
from roomscope.models.result import Validity
from tests.conftest import make_rir


def test_iso_class_thresholds() -> None:
    assert iso_3382_2_class(1, 1) == "below_survey"
    assert iso_3382_2_class(1, 2) == "survey"
    assert iso_3382_2_class(2, 3) == "engineering"
    assert iso_3382_2_class(2, 6) == "precision"


def test_average_decay_means_valid_t_only(short_sweep: SweepSettings) -> None:
    a = analyze(
        synthetic_recording(
            short_sweep,
            make_rir(short_sweep.sample_rate, rt60_s=0.4, diffuse_level=0.02),
            noise_rms=1e-5,
        ),
        Reference.from_settings(short_sweep),
    )
    b = analyze(
        synthetic_recording(
            short_sweep,
            make_rir(short_sweep.sample_rate, rt60_s=0.6, diffuse_level=0.02),
            noise_rms=1e-5,
        ),
        Reference.from_settings(short_sweep),
    )
    averaged = average_decay([a, b], session_labels=["a", "b"])
    assert averaged.n_sessions == 2
    assert averaged.iso_3382_2_class == "survey"
    broadband = next(band for band in averaged.bands if band.band_label == a.decay.broadband.band_label)
    assert broadband.t20.validity is Validity.VALID
    assert broadband.t20.count == 2
    assert broadband.t20.seconds is not None
    left = a.decay.broadband.t20.seconds
    right = b.decay.broadband.t20.seconds
    assert left is not None and right is not None
    assert broadband.t20.seconds == (left + right) / 2
    assert broadband.t20.spread_s == abs(left - right)
    payload = averaged.to_dict()
    assert "edc_db" not in str(payload)
    assert payload["confirmation_status"].startswith("ISO 3382-2")
