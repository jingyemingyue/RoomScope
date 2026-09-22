"""Plain-text report of an analysis result (shared by CLI and GUI overview)."""

from __future__ import annotations

from roomscope.interpretation import Finding
from roomscope.models.comparison import ComparisonResult
from roomscope.models.result import (
    AnalysisResult,
    DecayMetric,
    PlacementLength,
    PlacementResult,
    Validity,
)


def _metric(metric: DecayMetric) -> str:
    if metric.validity is Validity.VALID and metric.seconds is not None:
        return f"{metric.seconds:5.2f} s"
    if metric.validity is Validity.UNRELIABLE and metric.seconds is not None:
        return f"({metric.seconds:4.2f})?"
    if metric.validity is Validity.INSUFFICIENT_RANGE:
        return "insuff."
    return "  n/a  "


def _length(label: str, length: PlacementLength) -> str:
    """One placement figure, with its qualifier on the same line as the number."""
    if length.metres is None:
        hint = f" (add {length.missing_input})" if length.missing_input else ""
        return f"  {label:<26} not determined{hint}"
    value = f"{length.metres:.2f} m"
    if length.input_uncertainty_m is not None:
        value += f" +/-{length.input_uncertainty_m:.2f} from the stated inputs only"
    if length.validity is not Validity.VALID:
        value += f"  [{length.validity}]"
    return f"  {label:<26} {value}"


def _placement_section(placement: PlacementResult) -> list[str]:
    lines = [f"Placement (tier {placement.tier}; no coordinates are derived -- see the JSON):"]
    lines.append(
        f"  speed of sound            {placement.speed_of_sound_m_s:.1f} m/s at "
        f"{placement.temperature_c:.0f} C" + (" (assumed)" if placement.temperature_assumed else "")
    )
    lines.append(_length("loudspeaker height", placement.source_height_m))
    lines.append(_length("plane above the devices", placement.ceiling_height_m))
    lines.append(_length("horizontal separation", placement.horizontal_separation_m))
    for name, length in (
        ("loudspeaker height", placement.source_height_m),
        ("plane above the devices", placement.ceiling_height_m),
        ("horizontal separation", placement.horizontal_separation_m),
    ):
        if length.reason:
            lines.append(f"    {name}: {length.reason}")
    named = [c for c in placement.candidates if c.surface]
    if named:
        lines.append("  attributed arrivals:")
        for candidate in named:
            lines.append(
                f"    {candidate.delay_ms:6.1f} ms  {candidate.surface}"
                f"  excess path {candidate.excess_path_m:.2f} m"
            )
    for note in placement.notes:
        lines.append(f"  note: {note}")
    lines.append("")
    return lines


def format_report(
    result: AnalysisResult, findings: list[Finding] | None = None, profile_name: str = "generic"
) -> str:
    lines: list[str] = []
    ir = result.impulse_response
    lines.append("RoomScope analysis")
    lines.append("=" * 72)
    lines.append(f"Sample rate: {result.sample_rate} Hz    created: {result.created_at}")
    margin = f"{ir.pre_peak_margin_db:.1f} dB" if ir.pre_peak_margin_db is not None else "n/a"
    lines.append(
        f"Impulse response: {ir.samples.shape[0] / result.sample_rate:.2f} s analysed, "
        f"{ir.valid_length_s:.2f} s of decay recorded, direct-sound confidence {ir.direct_sound_confidence} "
        f"(pre-peak margin {margin})"
    )
    lines.append(f"Sweep found at {ir.sweep_start_in_recording_s:.2f} s in the recording.")
    if ir.loopback is not None:
        lb = ir.loopback
        if lb.compensation_applied:
            delay = (
                f"{lb.path_delay_ms:.2f} ms" if lb.path_delay_ms is not None else "n/a"
            )
            bound = (
                f"{lb.distance_upper_bound_m:.2f} m"
                if lb.distance_upper_bound_m is not None
                else "n/a"
            )
            lines.append(
                f"Loopback: compensated; electrical path delay {delay}; "
                f"distance upper bound {bound}."
            )
        else:
            lines.append(
                "Loopback: offered but not applied"
                + (f" ({lb.reason})" if lb.reason else ".")
            )
    lines.append("")
    lines.append("Reverberation (extrapolated to 60 dB; 'insuff.' = insufficient decay range)")
    lines.append(
        f"{'band':>10}  {'EDT':>8}  {'T20':>8}  {'T30':>8}  {'RT60 est.':>10}  {'range dB':>8}  note"
    )
    rows = [result.decay.broadband, *result.decay.bands]
    for band in rows:
        rt60 = (
            f"{band.rt60_estimate_s:.2f} s({band.rt60_basis})"
            if band.rt60_estimate_s is not None
            else "-"
        )
        note = band.filter_warning.split(":")[0] if band.filter_warning else ""
        lines.append(
            f"{band.band_label:>10}  {_metric(band.edt):>8}  {_metric(band.t20):>8}  {_metric(band.t30):>8}  "
            f"{rt60:>10}  {band.peak_to_noise_db:8.1f}  {note}"
        )
    lines.append("")
    noise = result.noise
    if noise.rms_dbfs is not None:
        lines.append(
            f"Background noise ({noise.segment_source}, {noise.segment_duration_s:.2f} s): "
            f"{noise.rms_dbfs:.1f} dBFS RMS, peak {noise.peak_dbfs:.1f} dBFS  [{noise.calibration}]"
        )
        hums = [h for h in noise.hum if h.detected]
        if hums:
            for hum in hums:
                harmonics = ", ".join(f"{f:.0f} Hz (+{p:.0f} dB)" for f, p in hum.harmonics)
                lines.append(
                    f"  Potential mains hum at multiples of {hum.base_hz:.0f} Hz: {harmonics}"
                )
        else:
            lines.append("  No mains hum detected (50/60 Hz harmonics).")
    else:
        lines.append("Background noise: no quiet segment available.")
    for note in noise.notes:
        lines.append(f"  note: {note}")
    lines.append("")
    refl = result.reflections
    lines.append(
        f"Early reflections ({refl.window_ms[0]:.0f}-{refl.window_ms[1]:.0f} ms, above {refl.threshold_db:.0f} dB):"
    )
    if refl.reflections:
        for r in refl.reflections[:10]:
            lines.append(f"  {r.delay_ms:6.1f} ms   {r.relative_db:6.1f} dB")
    else:
        lines.append("  none above threshold")
    lines.append("")
    placement = result.placement
    if placement is not None:
        lines.extend(_placement_section(placement))
    res = result.resonances
    lines.append(f"Potential low-frequency resonances (< {res.max_frequency_hz:.0f} Hz):")
    if res.candidates:
        for c in res.candidates:
            decay = (
                f"{c.narrowband_decay_20db_s * 1000:.0f} ms"
                if c.narrowband_decay_20db_s is not None
                else "n/a"
            )
            ring = (
                f"{c.filter_ringing_20db_s * 1000:.0f} ms"
                if c.filter_ringing_20db_s is not None
                else "n/a"
            )
            flag = (
                "decay distinguishable from filter"
                if c.decay_distinguishable
                else "not distinguishable from filter ringing"
            )
            lines.append(
                f"  {c.frequency_hz:6.1f} Hz  +{c.level_above_baseline_db:4.1f} dB  20 dB decay {decay} (filter {ring})  {flag}"
            )
    else:
        lines.append("  none")
    if result.warnings:
        lines.append("")
        lines.append("Warnings:")
        for warning in result.warnings:
            lines.append(f"  - {warning}")
    if findings:
        lines.append("")
        lines.append(f"Interpretation ({profile_name} profile):")
        for finding in findings:
            lines.append(f"  [{finding.severity}] {finding.topic}: {finding.message}")
    return "\n".join(lines)


def format_comparison_report(
    comparison: ComparisonResult,
    findings: list[Finding] | None = None,
    profile_name: str = "generic",
) -> str:
    """Plain-text comparison. Wording may change; this is not a Tier 1 interface."""
    lines = ["RoomScope comparison", "=" * 72]
    if comparison.common_band is not None:
        low, high = comparison.common_band
        lines.append(f"Common excitation band: {low:g}–{high:g} Hz")
    lines.append(f"Comparable: {'yes' if comparison.comparable else 'no'}")
    for note in comparison.notes:
        lines.append(f"  note: {note}")
    lines.append("")
    lines.append("Decay deltas (VALID only when both sides are VALID):")
    lines.append(f"{'metric':<32} {'base':>8} {'cand':>8} {'delta':>10} {'%':>8}  validity")
    for item in comparison.decay:
        base = f"{item.baseline:.3f}" if item.baseline is not None else "—"
        cand = f"{item.candidate:.3f}" if item.candidate is not None else "—"
        if item.validity is Validity.VALID and item.delta is not None:
            delta = f"{item.delta:+.3f}"
            pct = f"{item.delta_percent:+.1f}" if item.delta_percent is not None else "—"
        else:
            delta = "—"
            pct = "—"
        lines.append(f"{item.name:<32} {base:>8} {cand:>8} {delta:>10} {pct:>8}  {item.validity}")
        if item.reason and item.validity is not Validity.VALID:
            lines.append(f"    {item.reason}")
    if comparison.frequency_response is not None:
        lines.append("")
        lines.append("Frequency-response mean |Δ| per octave (dB):")
        for label, mad in comparison.frequency_response.band_mad_db:
            lines.append(f"  {label:<10} {mad:5.2f} dB")
    if comparison.reflections:
        lines.append("")
        lines.append("Early reflections:")
        for match in comparison.reflections:
            if match.status == "matched":
                lines.append(
                    f"  matched  {match.baseline_delay_ms:.1f}→{match.candidate_delay_ms:.1f} ms  "
                    f"{match.baseline_relative_db:.1f}→{match.candidate_relative_db:.1f} dB"
                )
            elif match.status == "appeared":
                lines.append(
                    f"  appeared {match.candidate_delay_ms:.1f} ms  {match.candidate_relative_db:.1f} dB"
                )
            else:
                lines.append(
                    f"  disappeared {match.baseline_delay_ms:.1f} ms  {match.baseline_relative_db:.1f} dB"
                )
    if comparison.noise:
        lines.append("")
        lines.append("Noise:")
        for item in comparison.noise:
            extra = f"  [{item.reason}]" if item.reason else ""
            lines.append(f"  {item.name}: {item.validity}{extra}")
    if comparison.placement:
        lines.append("")
        lines.append("Placement:")
        for item in comparison.placement:
            extra = f"  [{item.reason}]" if item.reason else ""
            lines.append(f"  {item.name}: {item.validity}{extra}")
    if findings:
        lines.append("")
        lines.append(f"Interpretation ({profile_name} profile):")
        for finding in findings:
            lines.append(f"  [{finding.severity}] {finding.topic}: {finding.message}")
    return "\n".join(lines)
