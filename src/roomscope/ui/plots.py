"""Matplotlib plots of an :class:`AnalysisResult`.

Every axis is labelled with its unit; nothing is normalised in a way that
hides the measurement scale. Functions draw into a :class:`~matplotlib.figure.Figure`
so they work in the Qt canvas and in scripts alike.
"""

from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from roomscope.core.reflections import reflection_envelope_db
from roomscope.models.result import AnalysisResult, Validity
from roomscope.ui.theme import PLOT_SERIES, plot_colors, style_figure

_EPS = 1e-300

# Linestyles so a plot is readable when colour is not (ARCHITECTURE_V1 §5.8).
_LINESTYLES = ("-", "--", "-.", ":", (0, (3, 1, 1, 1)))


def plot_impulse_response(fig: Figure, result: AnalysisResult) -> None:
    fig.clear()
    ir = result.impulse_response
    sr = ir.sample_rate
    t_ms = (np.arange(ir.samples.shape[0]) - ir.direct_sound_index) * 1000.0 / sr
    ax1 = fig.add_subplot(2, 1, 1)
    n_zoom = min(ir.samples.shape[0], int(0.1 * sr) + ir.direct_sound_index)
    ax1.plot(t_ms[:n_zoom], ir.samples[:n_zoom], linewidth=0.8)
    ax1.set_xlabel("Time after direct sound (ms)")
    ax1.set_ylabel("Amplitude (relative)")
    ax1.set_title("Impulse response, first 100 ms")
    ax1.grid(True, alpha=0.3)
    ax2 = fig.add_subplot(2, 1, 2)
    env = reflection_envelope_db(ir.samples, sr, hold_ms=0.5)
    env = env - float(np.max(env))
    ax2.plot(t_ms / 1000.0, env, linewidth=0.8)
    ax2.set_xlabel("Time after direct sound (s)")
    ax2.set_ylabel("Envelope (dB re direct)")
    ax2.set_ylim(-100.0, 5.0)
    ax2.set_title("Energy-time curve")
    ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    style_figure(fig)


def plot_frequency_response(fig: Figure, result: AnalysisResult) -> None:
    fig.clear()
    fr = result.frequency_response
    ax = fig.add_subplot(1, 1, 1)
    ax.semilogx(
        fr.frequencies_hz,
        fr.magnitude_db_raw,
        linewidth=0.5,
        alpha=0.35,
        linestyle=":",
        color=plot_colors()["muted"],
        label="raw",
    )
    if fr.magnitude_db_smoothed is not None:
        ax.semilogx(
            fr.frequencies_hz,
            fr.magnitude_db_smoothed,
            linewidth=1.6,
            linestyle="-",
            color=PLOT_SERIES[0],
            label=f"1/{fr.smoothing_fraction}-octave smoothed",
        )
    loopback = result.impulse_response.loopback
    if (
        loopback is not None
        and loopback.interface_response_hz is not None
        and loopback.interface_response_db is not None
    ):
        ax.semilogx(
            loopback.interface_response_hz,
            loopback.interface_response_db,
            linewidth=1.0,
            alpha=0.8,
            linestyle="--",
            label="interface (loopback)",
        )
    ax.set_xlim(20.0, result.sample_rate / 2.0)
    finite = fr.magnitude_db_raw[np.isfinite(fr.magnitude_db_raw)]
    if finite.shape[0]:
        top = float(np.percentile(finite, 99.5))
        ax.set_ylim(top - 60.0, top + 10.0)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Magnitude (dB, relative)")
    ax.set_title(f"Frequency response ({fr.window_s:.2f} s window)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower left")
    fig.tight_layout()
    style_figure(fig)


def plot_decay(fig: Figure, result: AnalysisResult) -> None:
    fig.clear()
    ax = fig.add_subplot(1, 1, 1)
    bb = result.decay.broadband
    ax.plot(bb.edc_time_s, bb.edc_db, linewidth=2.4, linestyle="-", label="broadband")
    for index, band in enumerate(result.decay.bands):
        rt = band.rt60_estimate_s
        label = band.band_label + (
            f"  RT60~{rt:.2f} s" if rt is not None else "  (insufficient range)"
        )
        ax.plot(
            band.edc_time_s,
            band.edc_db,
            linewidth=0.9,
            alpha=0.8,
            linestyle=_LINESTYLES[(index + 1) % len(_LINESTYLES)],
            label=label,
        )
    ax.set_ylim(-70.0, 5.0)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Schroeder decay (dB)")
    ax.set_title("Energy decay curves (Lundeby-truncated)")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize="small")
    fig.tight_layout()
    style_figure(fig)


def plot_noise(fig: Figure, result: AnalysisResult) -> None:
    fig.clear()
    noise = result.noise
    ax = fig.add_subplot(1, 1, 1)
    if noise.psd_frequencies_hz is None or noise.psd_db is None:
        ax.text(
            0.5, 0.5, "No quiet segment available", ha="center", va="center", transform=ax.transAxes
        )
        ax.set_axis_off()
        fig.tight_layout()
        style_figure(fig)
        return
    f = noise.psd_frequencies_hz
    mask = f > 0
    ax.semilogx(f[mask], noise.psd_db[mask], linewidth=0.7)
    for hum in noise.hum:
        if hum.detected:
            for freq, prominence in hum.harmonics:
                idx = int(np.argmin(np.abs(f - freq)))
                ax.plot(freq, noise.psd_db[idx], "v", markerfacecolor="none")
                ax.annotate(
                    f"{freq:.0f} Hz +{prominence:.0f} dB",
                    (freq, noise.psd_db[idx]),
                    fontsize="x-small",
                )
    ax.set_xlim(10.0, result.sample_rate / 2.0)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("PSD (dB re FS^2/Hz)")
    title = f"Background noise: {noise.rms_dbfs:.1f} dBFS RMS ({noise.segment_source})"
    ax.set_title(title + "  [uncalibrated]")
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    style_figure(fig)


def plot_reflections(fig: Figure, result: AnalysisResult) -> None:
    fig.clear()
    ir = result.impulse_response
    sr = ir.sample_rate
    refl = result.reflections
    ax = fig.add_subplot(1, 1, 1)
    env = reflection_envelope_db(ir.samples, sr, hold_ms=0.1)
    half = max(1, round(0.5e-3 * sr))
    lo = max(0, ir.direct_sound_index - half)
    hi = min(env.shape[0], ir.direct_sound_index + half + 1)
    env = env - float(np.max(env[lo:hi]))
    start = max(0, ir.direct_sound_index - round(2e-3 * sr))
    stop = min(env.shape[0], ir.direct_sound_index + round(refl.window_ms[1] * sr / 1000.0) + 1)
    t_ms = (np.arange(start, stop) - ir.direct_sound_index) * 1000.0 / sr
    ax.plot(t_ms, env[start:stop], linewidth=0.8, label="envelope")
    if refl.reflections:
        ax.plot(
            [r.delay_ms for r in refl.reflections],
            [r.relative_db for r in refl.reflections],
            "o",
            markerfacecolor="none",
            label="candidate reflections",
        )
    ax.axhline(refl.threshold_db, color="gray", linestyle="--", linewidth=0.8, label="threshold")
    ax.set_ylim(-60.0, 5.0)
    ax.set_xlabel("Time after direct sound (ms)")
    ax.set_ylabel("Level re direct sound (dB)")
    ax.set_title(f"Early reflections (direct-sound confidence: {refl.direct_sound_confidence})")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right")
    fig.tight_layout()
    style_figure(fig)


def decay_table_rows(result: AnalysisResult) -> list[tuple[str, str, str, str, str]]:
    """Rows (band, EDT, T20, T30, RT60 estimate) for a table widget."""

    def fmt(metric_seconds: float | None, validity: Validity) -> str:
        if validity is Validity.VALID and metric_seconds is not None:
            return f"{metric_seconds:.2f} s"
        if validity is Validity.UNRELIABLE and metric_seconds is not None:
            return f"({metric_seconds:.2f} s)"
        if validity is Validity.INSUFFICIENT_RANGE:
            return "insufficient range"
        return "n/a"

    rows: list[tuple[str, str, str, str, str]] = []
    for band in (result.decay.broadband, *result.decay.bands):
        rt = (
            f"{band.rt60_estimate_s:.2f} s ({band.rt60_basis})"
            if band.rt60_estimate_s is not None
            else "-"
        )
        rows.append(
            (
                band.band_label,
                fmt(band.edt.seconds, band.edt.validity),
                fmt(band.t20.seconds, band.t20.validity),
                fmt(band.t30.seconds, band.t30.validity),
                rt,
            )
        )
    return rows
