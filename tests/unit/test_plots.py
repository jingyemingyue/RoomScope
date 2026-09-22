from __future__ import annotations

from matplotlib.figure import Figure

from roomscope.core.pipeline import Reference, analyze, synthetic_recording
from roomscope.ui.plots import plot_decay, plot_frequency_response
from tests.conftest import make_rir


def test_decay_and_fr_plots_use_linestyle_not_only_colour(short_sweep) -> None:
    ir = make_rir(short_sweep.sample_rate, rt60_s=0.35, reflections=[(0.018, 0.35)])
    recording = synthetic_recording(short_sweep, ir, noise_rms=1e-5)
    result = analyze(recording, Reference.from_settings(short_sweep))
    decay = Figure()
    plot_decay(decay, result)
    styles = {line.get_linestyle() for line in decay.axes[0].lines}
    assert len(styles) > 1
    fr = Figure()
    plot_frequency_response(fr, result)
    fr_styles = {line.get_linestyle() for line in fr.axes[0].lines}
    assert ":" in fr_styles
    assert "-" in fr_styles
