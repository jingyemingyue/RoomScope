"""Recording profiles.

A profile converts measurements into advice for a kind of recording. The
interface is fixed in v0.1 so that vocal / voice-over / acoustic guitar /
drums / room-mic / choir profiles can be added without touching the DSP.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from roomscope.errors import ConfigurationError
from roomscope.interpretation.interpreter import Finding, Severity
from roomscope.models.result import AnalysisResult, Validity


@runtime_checkable
class RecordingProfile(Protocol):
    name: str
    description: str

    def interpret(self, result: AnalysisResult) -> list[Finding]: ...


class GenericProfile:
    """Profile-independent observations that apply to any close-miked recording."""

    name = "generic"
    description = "General observations, not tied to a specific instrument or voice."

    # Thresholds are deliberately coarse and documented in MEASUREMENT_METHODOLOGY.md.
    strong_reflection_db = -10.0
    strong_reflection_window_ms = 30.0
    long_decay_s = 0.6
    very_long_decay_s = 1.0
    quiet_noise_margin_db = 60.0

    def interpret(self, result: AnalysisResult) -> list[Finding]:
        findings: list[Finding] = []
        findings.extend(self._data_quality(result))
        findings.extend(self._reflections(result))
        findings.extend(self._decay(result))
        findings.extend(self._noise(result))
        findings.extend(self._resonances(result))
        return findings

    def _data_quality(self, result: AnalysisResult) -> list[Finding]:
        findings: list[Finding] = []
        ir = result.impulse_response
        if ir.direct_sound_confidence != "high":
            findings.append(
                Finding(
                    topic="measurement",
                    severity=Severity.WARNING,
                    message=(
                        "The direct sound could not be identified with confidence, so delays and "
                        "levels of reflections may be off. Check that the correct reference sweep "
                        "was used, lower the playback level if the loudspeaker distorts, and "
                        "measure again."
                    ),
                    evidence={"pre_peak_margin_db": ir.pre_peak_margin_db},
                )
            )
        for warning in result.warnings:
            if "clipping" in warning:
                findings.append(
                    Finding(
                        topic="measurement",
                        severity=Severity.WARNING,
                        message="The recording clips. Lower the playback or input gain and measure again.",
                        evidence={"warning": warning},
                    )
                )
        broadband = result.decay.broadband
        if broadband.t20.validity is Validity.INSUFFICIENT_RANGE:
            findings.append(
                Finding(
                    topic="measurement",
                    severity=Severity.NOTICE,
                    message=(
                        "The decay range is too small for a reliable reverberation time. A longer "
                        "sweep, a slightly higher playback level or a quieter room increases it."
                    ),
                    evidence={
                        "peak_to_noise_db": broadband.peak_to_noise_db,
                        "reason": broadband.t20.reason,
                    },
                )
            )
        return findings

    def _reflections(self, result: AnalysisResult) -> list[Finding]:
        strong = [
            r
            for r in result.reflections.reflections
            if r.relative_db >= self.strong_reflection_db
            and r.delay_ms <= self.strong_reflection_window_ms
        ]
        if not strong:
            return []
        first = max(strong, key=lambda r: r.relative_db)
        return [
            Finding(
                topic="early_reflections",
                severity=Severity.NOTICE,
                message=(
                    f"A relatively strong early reflection is present approximately "
                    f"{first.delay_ms:.0f} ms after the direct sound ({first.relative_db:.1f} dB). "
                    "For close vocal or instrument recording, try moving the microphone or the "
                    "performer farther from nearby hard surfaces, or treat that surface, and "
                    "measure again."
                ),
                evidence={
                    "delay_ms": first.delay_ms,
                    "relative_db": first.relative_db,
                    "count_within_window": len(strong),
                },
            )
        ]

    def _decay(self, result: AnalysisResult) -> list[Finding]:
        findings: list[Finding] = []
        broadband = result.decay.broadband
        rt = broadband.rt60_estimate_s
        if rt is None:
            return findings
        if rt >= self.very_long_decay_s:
            severity, text = Severity.WARNING, "long"
        elif rt >= self.long_decay_s:
            severity, text = Severity.NOTICE, "noticeable"
        else:
            severity, text = Severity.INFO, "short"
        findings.append(
            Finding(
                topic="reverberation",
                severity=severity,
                message=(
                    f"The broadband decay is {text} (estimated RT60 {rt:.2f} s from {broadband.rt60_basis}). "
                    + (
                        "Dry close-miked recordings will pick up audible room sound; consider "
                        "absorption or a closer microphone position."
                        if severity is not Severity.INFO
                        else "This is typical of a treated or small, well-damped room."
                    )
                ),
                evidence={"rt60_estimate_s": rt, "basis": broadband.rt60_basis},
            )
        )
        low_bands = [
            b for b in result.decay.bands if b.center_hz is not None and b.center_hz <= 250.0
        ]
        mid_bands = [
            b
            for b in result.decay.bands
            if b.center_hz is not None and 500.0 <= b.center_hz <= 2000.0
        ]
        low = [b.rt60_estimate_s for b in low_bands if b.rt60_estimate_s is not None]
        mid = [b.rt60_estimate_s for b in mid_bands if b.rt60_estimate_s is not None]
        if low and mid and max(low) > 1.5 * (sum(mid) / len(mid)):
            findings.append(
                Finding(
                    topic="reverberation",
                    severity=Severity.NOTICE,
                    message=(
                        "Low frequencies decay clearly more slowly than the mid range, which usually "
                        "makes bass-heavy sources sound boomy at this position. Bass trapping or a "
                        "different position helps."
                    ),
                    evidence={"low_max_rt60_s": max(low), "mid_mean_rt60_s": sum(mid) / len(mid)},
                )
            )
        return findings

    def _noise(self, result: AnalysisResult) -> list[Finding]:
        findings: list[Finding] = []
        noise = result.noise
        for hum in noise.hum:
            if hum.detected:
                findings.append(
                    Finding(
                        topic="noise",
                        severity=Severity.WARNING,
                        message=(
                            f"Mains hum components at multiples of {hum.base_hz:.0f} Hz were detected in "
                            "the quiet part of the recording. Check grounding, cables, dimmers and "
                            "power supplies before treating the room."
                        ),
                        evidence={
                            "base_hz": hum.base_hz,
                            "harmonics": [list(h) for h in hum.harmonics],
                        },
                    )
                )
        if noise.rms_dbfs is not None:
            peak_db = 20.0 * __import__("math").log10(
                max(abs(result.impulse_response.peak_value), 1e-12)
            )
            findings.append(
                Finding(
                    topic="noise",
                    severity=Severity.INFO,
                    message=(
                        f"Background noise in the quiet segment is {noise.rms_dbfs:.1f} dBFS RMS "
                        "(uncalibrated digital level, not dB SPL). Compare it with the level of the "
                        "sources you record at the same gain."
                    ),
                    evidence={
                        "rms_dbfs": noise.rms_dbfs,
                        "segment_source": noise.segment_source,
                        "ir_peak_db": peak_db,
                    },
                )
            )
        return findings

    def _resonances(self, result: AnalysisResult) -> list[Finding]:
        candidates = [c for c in result.resonances.candidates if c.decay_distinguishable]
        if not candidates:
            return []
        listed = ", ".join(f"{c.frequency_hz:.0f} Hz" for c in candidates[:4])
        return [
            Finding(
                topic="low_frequency",
                severity=Severity.NOTICE,
                message=(
                    f"Potential low-frequency resonances around {listed}: these frequencies stand out "
                    "in the response and ring longer than their surroundings. Measure one or two other "
                    "positions to see whether they follow the room or the position."
                ),
                evidence={"candidates": [c.to_dict() for c in candidates]},
            )
        ]


_PROFILES: dict[str, RecordingProfile] = {GenericProfile.name: GenericProfile()}


def available_profiles() -> list[str]:
    return sorted(_PROFILES)


def get_profile(name: str) -> RecordingProfile:
    try:
        return _PROFILES[name]
    except KeyError as exc:
        raise ConfigurationError(
            f"unknown recording profile '{name}'; available: {available_profiles()}"
        ) from exc
