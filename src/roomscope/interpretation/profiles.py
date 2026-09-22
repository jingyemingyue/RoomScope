"""Recording profiles.

A profile converts measurements into advice for a kind of recording. The
interface is fixed in v0.1 so that vocal / voice-over / acoustic guitar /
drums / room-mic / choir profiles can be added without touching the DSP.

The DSP layer never writes advice; a profile only reads an
:class:`AnalysisResult` and returns :class:`Finding` objects with the
measured values in ``evidence``. Thresholds are coarse engineering choices,
documented in MEASUREMENT_METHODOLOGY.md §8, and are stated in each finding's
evidence.
"""

from __future__ import annotations

import math
from typing import Protocol, runtime_checkable

from roomscope.errors import ConfigurationError
from roomscope.interpretation.interpreter import Finding, Severity
from roomscope.models.result import AnalysisResult, Reflection, ResonanceCandidate, Validity


@runtime_checkable
class RecordingProfile(Protocol):
    name: str
    description: str

    def interpret(self, result: AnalysisResult) -> list[Finding]: ...


class ProfileBase:
    """Shared interpretation machinery.

    Measurement-integrity checks (direct-sound confidence, clipping,
    insufficient decay range) are identical for every profile and live here.
    The four profile sections — reflections, decay, noise, resonances — use
    class-level thresholds plus per-profile message methods, so each profile
    keeps its own wording while sharing the surrounding logic.
    """

    name: str
    description: str

    #: Strongest reflection level (dB re direct sound) that counts as strong.
    strong_reflection_db = -10.0
    #: Reflections at or below this delay (ms) are the ones that colour a close-miked source.
    strong_reflection_window_ms = 30.0
    #: RT60 above which the decay is called "noticeable" for this kind of recording.
    long_decay_s = 0.6
    #: RT60 above which the decay is called "long" (a warning).
    very_long_decay_s = 1.0
    #: Dynamic range below the direct sound at which noise starts to matter.
    quiet_noise_margin_db = 60.0
    #: Low bands decaying more than this many times slower than mid bands is an imbalance.
    slow_low_ratio = 1.5
    #: Bands at or below this centre frequency count as "low".
    low_band_max_hz = 250.0
    #: Bands between these centre frequencies count as "mid".
    mid_band_min_hz = 500.0
    mid_band_max_hz = 2000.0

    def interpret(self, result: AnalysisResult) -> list[Finding]:
        findings: list[Finding] = []
        findings.extend(self._data_quality(result))
        findings.extend(self._reflections(result))
        findings.extend(self._decay(result))
        findings.extend(self._noise(result))
        findings.extend(self._resonances(result))
        return findings

    # ------------------------------------------------------------- helpers

    def _strong_reflections(self, result: AnalysisResult) -> list[Reflection]:
        return [
            r
            for r in result.reflections.reflections
            if r.relative_db >= self.strong_reflection_db
            and r.delay_ms <= self.strong_reflection_window_ms
        ]

    def _distinguishable_resonances(self, result: AnalysisResult) -> list[ResonanceCandidate]:
        return [c for c in result.resonances.candidates if c.decay_distinguishable]

    def _low_mid_imbalance(self, result: AnalysisResult) -> tuple[float, float] | None:
        """(low max RT60, mid mean RT60) when low bands clearly outlast mid bands."""
        low_bands = [
            b
            for b in result.decay.bands
            if b.center_hz is not None and b.center_hz <= self.low_band_max_hz
        ]
        mid_bands = [
            b
            for b in result.decay.bands
            if b.center_hz is not None
            and self.mid_band_min_hz <= b.center_hz <= self.mid_band_max_hz
        ]
        low = [b.rt60_estimate_s for b in low_bands if b.rt60_estimate_s is not None]
        mid = [b.rt60_estimate_s for b in mid_bands if b.rt60_estimate_s is not None]
        if not low or not mid:
            return None
        mid_mean = sum(mid) / len(mid)
        if max(low) > self.slow_low_ratio * mid_mean:
            return max(low), mid_mean
        return None

    # ------------------------------------------------ measurement integrity

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

    # ------------------------------------------------------------ sections

    def _reflections(self, result: AnalysisResult) -> list[Finding]:
        strong = self._strong_reflections(result)
        if not strong:
            return []
        first = max(strong, key=lambda r: r.relative_db)
        return [
            Finding(
                topic="early_reflections",
                severity=Severity.NOTICE,
                message=self.reflection_message(first),
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
        if rt is not None:
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
                    message=self.decay_message(rt, severity, text, broadband.rt60_basis),
                    evidence={"rt60_estimate_s": rt, "basis": broadband.rt60_basis},
                )
            )
        imbalance = self._low_mid_imbalance(result)
        if imbalance is not None:
            low_max, mid_mean = imbalance
            findings.append(
                Finding(
                    topic="reverberation",
                    severity=Severity.NOTICE,
                    message=self.low_imbalance_message(low_max, mid_mean),
                    evidence={"low_max_rt60_s": low_max, "mid_mean_rt60_s": mid_mean},
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
                        message=self.hum_message(hum.base_hz),
                        evidence={
                            "base_hz": hum.base_hz,
                            "harmonics": [list(h) for h in hum.harmonics],
                        },
                    )
                )
        if noise.rms_dbfs is not None:
            peak_db = 20.0 * math.log10(max(abs(result.impulse_response.peak_value), 1e-12))
            findings.append(
                Finding(
                    topic="noise",
                    severity=Severity.INFO,
                    message=self.noise_floor_message(noise.rms_dbfs, noise.segment_source),
                    evidence={
                        "rms_dbfs": noise.rms_dbfs,
                        "segment_source": noise.segment_source,
                        "ir_peak_db": peak_db,
                    },
                )
            )
            if peak_db - noise.rms_dbfs < self.quiet_noise_margin_db:
                findings.append(
                    Finding(
                        topic="noise",
                        severity=Severity.NOTICE,
                        message=(
                            f"The direct sound is only {peak_db - noise.rms_dbfs:.0f} dB above the "
                            "noise floor in the quiet segment. Sources quieter than this will be "
                            "recorded with audible noise; lower the noise at the source or increase "
                            "the playback level within the headroom of the chain."
                        ),
                        evidence={"direct_to_noise_db": peak_db - noise.rms_dbfs},
                    )
                )
        return findings

    def _resonances(self, result: AnalysisResult) -> list[Finding]:
        candidates = self._distinguishable_resonances(result)
        if not candidates:
            return []
        return [
            Finding(
                topic="low_frequency",
                severity=Severity.NOTICE,
                message=self.resonance_message(candidates),
                evidence={"candidates": [c.to_dict() for c in candidates]},
            )
        ]

    # ------------------------------------------------------------ messages

    def reflection_message(self, r: Reflection) -> str:
        return (
            f"A relatively strong early reflection is present approximately "
            f"{r.delay_ms:.0f} ms after the direct sound ({r.relative_db:.1f} dB). "
            "For close vocal or instrument recording, try moving the microphone or the "
            "performer farther from nearby hard surfaces, or treat that surface, and "
            "measure again."
        )

    def decay_message(self, rt: float, severity: Severity, text: str, basis: str | None) -> str:
        if severity is Severity.INFO:
            return (
                f"The broadband decay is short (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "This is typical of a treated or small, well-damped room."
            )
        return (
            f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
            + (f" from {basis}" if basis else "")
            + "). "
            "Dry close-miked recordings will pick up audible room sound; consider "
            "absorption or a closer microphone position."
        )

    def low_imbalance_message(self, low_max: float, mid_mean: float) -> str:
        return (
            f"Low frequencies decay clearly more slowly than the mid range "
            f"({low_max:.2f} s vs {mid_mean:.2f} s), which usually makes bass-heavy sources "
            "sound boomy at this position. Bass trapping or a different position helps."
        )

    def hum_message(self, base_hz: float) -> str:
        return (
            f"Mains hum components at multiples of {base_hz:.0f} Hz were detected in "
            "the quiet part of the recording. Check grounding, cables, dimmers and "
            "power supplies before treating the room."
        )

    def noise_floor_message(self, rms_dbfs: float, segment_source: str | None) -> str:
        segment = segment_source or "quiet"
        return (
            f"Background noise in the {segment} segment is {rms_dbfs:.1f} dBFS RMS "
            "(uncalibrated digital level, not dB SPL). Compare it with the level of the "
            "sources you record at the same gain."
        )

    def resonance_message(self, candidates: list[ResonanceCandidate]) -> str:
        listed = ", ".join(f"{c.frequency_hz:.0f} Hz" for c in candidates[:4])
        return (
            f"Potential low-frequency resonances around {listed}: these frequencies stand out "
            "in the response and ring longer than their surroundings. Measure one or two other "
            "positions to see whether they follow the room or the position."
        )


class GenericProfile(ProfileBase):
    """Profile-independent observations that apply to any close-miked recording."""

    name = "generic"
    description = "General observations, not tied to a specific instrument or voice."


class VocalProfile(ProfileBase):
    """Close-miked lead or backing vocals."""

    name = "vocal"
    description = "Close-miked lead or backing vocals."

    strong_reflection_db = -12.0
    strong_reflection_window_ms = 25.0
    long_decay_s = 0.5
    very_long_decay_s = 0.8

    def reflection_message(self, r: Reflection) -> str:
        return (
            f"A strong early reflection is present approximately {r.delay_ms:.0f} ms after the "
            f"direct sound ({r.relative_db:.1f} dB). Close-miked vocals are coloured by "
            "reflections this early; move the microphone closer to the singer and farther from "
            "the nearest hard surface, or treat that surface, then measure again."
        )

    def decay_message(self, rt: float, severity: Severity, text: str, basis: str | None) -> str:
        if severity is Severity.INFO:
            return (
                f"The broadband decay is short (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "A dry room like this suits close vocal recording."
            )
        return (
            f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
            + (f" from {basis}" if basis else "")
            + "). "
            "A vocal that is this live picks up room colour between phrases; add absorption "
            "or move to a drier position."
        )

    def low_imbalance_message(self, low_max: float, mid_mean: float) -> str:
        return (
            f"Low frequencies decay more slowly than the mid range "
            f"({low_max:.2f} s vs {mid_mean:.2f} s), which makes vocals sound boxy at this "
            "position. Bass trapping or a different position helps."
        )

    def noise_floor_message(self, rms_dbfs: float, segment_source: str | None) -> str:
        segment = segment_source or "quiet"
        return (
            f"Background noise in the {segment} segment is {rms_dbfs:.1f} dBFS RMS "
            "(uncalibrated digital level, not dB SPL). Vocal tracks are often compressed, "
            "which brings this noise up; compare it with your chain's noise at the same gain."
        )


class VoiceOverProfile(ProfileBase):
    """Voice-over, narration and audiobook."""

    name = "voiceover"
    description = "Voice-over, narration and audiobook."

    strong_reflection_db = -14.0
    strong_reflection_window_ms = 20.0
    long_decay_s = 0.4
    very_long_decay_s = 0.7

    def reflection_message(self, r: Reflection) -> str:
        return (
            f"An early reflection is present approximately {r.delay_ms:.0f} ms after the direct "
            f"sound ({r.relative_db:.1f} dB). Voice-over is usually close-miked and heavily "
            "processed, so even a reflection this weak colours the voice; move the microphone "
            "closer to the talent and farther from the nearest hard surface, or treat the surface."
        )

    def decay_message(self, rt: float, severity: Severity, text: str, basis: str | None) -> str:
        if severity is Severity.INFO:
            return (
                f"The broadband decay is short (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "This suits voice-over: the narration stays dry and close."
            )
        return (
            f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
            + (f" from {basis}" if basis else "")
            + "). "
            "Voice-over needs a dry room; room tone of this length will sit under the "
            "narration. Add absorption or move to a drier position."
        )

    def low_imbalance_message(self, low_max: float, mid_mean: float) -> str:
        return (
            f"Low frequencies decay more slowly than the mid range "
            f"({low_max:.2f} s vs {mid_mean:.2f} s), which makes voice-over sound muddy. "
            "Bass trapping or a different position helps."
        )

    def noise_floor_message(self, rms_dbfs: float, segment_source: str | None) -> str:
        segment = segment_source or "quiet"
        return (
            f"Background noise in the {segment} segment is {rms_dbfs:.1f} dBFS RMS "
            "(uncalibrated digital level, not dB SPL). Voice-over is usually quiet and "
            "close-miked, so this floor will be audible under the narration."
        )

    def resonance_message(self, candidates: list[ResonanceCandidate]) -> str:
        listed = ", ".join(f"{c.frequency_hz:.0f} Hz" for c in candidates[:4])
        return (
            f"Potential low-frequency resonances around {listed}: these frequencies stand out "
            "in the response and ring longer than their surroundings, which colours voice and "
            "dialogue. Move the microphone or treat the affected corner, then measure again."
        )


class AcousticGuitarProfile(ProfileBase):
    """Acoustic guitar, single microphone or close pair."""

    name = "acoustic_guitar"
    description = "Acoustic guitar, single microphone or close pair."

    strong_reflection_db = -10.0
    strong_reflection_window_ms = 30.0
    long_decay_s = 0.7
    very_long_decay_s = 1.1

    def reflection_message(self, r: Reflection) -> str:
        return (
            f"A strong early reflection is present approximately {r.delay_ms:.0f} ms after the "
            f"direct sound ({r.relative_db:.1f} dB). Acoustic guitar is vulnerable to comb "
            "filtering from early reflections; move the microphone or the instrument farther "
            "from the nearest hard surface, or treat it, then measure again."
        )

    def decay_message(self, rt: float, severity: Severity, text: str, basis: str | None) -> str:
        if severity is Severity.INFO:
            return (
                f"The broadband decay is short (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "Acoustic guitar keeps its transients and body in a room like this."
            )
        return (
            f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
            + (f" from {basis}" if basis else "")
            + "). "
            "For acoustic guitar, a decay this long clouds transients and adds boom; "
            "a position with absorption behind the performer helps."
        )

    def low_imbalance_message(self, low_max: float, mid_mean: float) -> str:
        return (
            f"Low frequencies decay more slowly than the mid range "
            f"({low_max:.2f} s vs {mid_mean:.2f} s), which makes the guitar sound boomy at "
            "this position. Bass trapping or a different position helps."
        )


class DrumsProfile(ProfileBase):
    """Drums, close mics (kick, snare, toms) with or without overheads."""

    name = "drums"
    description = "Drums, close mics (kick, snare, toms) with or without overheads."

    # Drums are loud and close-miked: only a hard slap is worth reporting.
    strong_reflection_db = -6.0
    strong_reflection_window_ms = 20.0
    long_decay_s = 0.8
    very_long_decay_s = 1.2

    def reflection_message(self, r: Reflection) -> str:
        return (
            f"A very strong early reflection is present approximately {r.delay_ms:.0f} ms after "
            f"the direct sound ({r.relative_db:.1f} dB). Drums mask most reflections, but a slap "
            "this strong will smear transients; move the kit or the overheads, or hang "
            "absorption at the reflection point."
        )

    def decay_message(self, rt: float, severity: Severity, text: str, basis: str | None) -> str:
        if severity is Severity.INFO:
            return (
                f"The broadband decay is short (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "The kit will stay tight in a room like this."
            )
        return (
            f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
            + (f" from {basis}" if basis else "")
            + "). "
            "A room this live rings under the kit; for a tighter drum sound add absorption "
            "or move the kit."
        )

    def low_imbalance_message(self, low_max: float, mid_mean: float) -> str:
        return (
            f"Low frequencies decay more slowly than the mid range "
            f"({low_max:.2f} s vs {mid_mean:.2f} s), so the kick and low toms will boom at "
            "this position. Bass trapping or a different kit position helps."
        )

    def _noise(self, _result: AnalysisResult) -> list[Finding]:
        # Drums overwhelm any plausible background noise; a noise finding would be noise.
        return []


class RoomMicProfile(ProfileBase):
    """Room microphone or ambient pickup: the room is the instrument."""

    name = "room_mic"
    description = "Room microphone or ambient pickup: the room is the instrument."

    # The room is what is being recorded; only a hard slap is a defect.
    strong_reflection_db = -5.0
    strong_reflection_window_ms = 40.0
    long_decay_s = 0.9
    very_long_decay_s = 1.4

    def reflection_message(self, r: Reflection) -> str:
        return (
            f"A very strong early reflection is present approximately {r.delay_ms:.0f} ms after "
            f"the direct sound ({r.relative_db:.1f} dB). For a room microphone this is a hard "
            "slap that will sit under everything; reposition the microphone or add absorption "
            "at the reflection point."
        )

    def decay_message(self, rt: float, severity: Severity, text: str, basis: str | None) -> str:
        if severity is Severity.INFO:
            return (
                f"The broadband decay is short (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "A room microphone in a room this dry records mostly direct sound; if you want "
                "ambience, the microphone needs to be farther from the source."
            )
        if severity is Severity.WARNING:
            return (
                f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "For a room microphone this is a long room tone that may swamp the source; "
                "check whether the ambience stays usable, and consider absorption or a closer "
                "microphone position."
            )
        return (
            f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
            + (f" from {basis}" if basis else "")
            + "). "
            "For a room microphone this is usable ambience; keep the microphone position and "
            "listen for how it sits under the source."
        )

    def low_imbalance_message(self, low_max: float, mid_mean: float) -> str:
        return (
            f"Low frequencies decay more slowly than the mid range "
            f"({low_max:.2f} s vs {mid_mean:.2f} s), so the room sound will be bass-heavy at "
            "this position. Bass trapping or a different microphone position helps."
        )

    def noise_floor_message(self, rms_dbfs: float, segment_source: str | None) -> str:
        segment = segment_source or "quiet"
        return (
            f"Background noise in the {segment} segment is {rms_dbfs:.1f} dBFS RMS "
            "(uncalibrated digital level, not dB SPL). A room microphone captures everything, "
            "so this floor is part of what you record; it is audible whenever the source pauses."
        )

    def resonance_message(self, candidates: list[ResonanceCandidate]) -> str:
        listed = ", ".join(f"{c.frequency_hz:.0f} Hz" for c in candidates[:4])
        return (
            f"Potential low-frequency resonances around {listed}: these frequencies ring longer "
            "than their surroundings, so the room sound will be uneven there. Measure one or "
            "two other positions to see whether they follow the room."
        )


class ChoirProfile(ProfileBase):
    """Choir or small ensemble, one or more microphones."""

    name = "choir"
    description = "Choir or small ensemble, one or more microphones."

    strong_reflection_db = -12.0
    strong_reflection_window_ms = 30.0
    long_decay_s = 0.8
    very_long_decay_s = 1.3

    def reflection_message(self, r: Reflection) -> str:
        return (
            f"An early reflection is present approximately {r.delay_ms:.0f} ms after the direct "
            f"sound ({r.relative_db:.1f} dB). For an ensemble, early reflections smear diction; "
            "move the microphones away from the nearest hard surface or treat it, and measure "
            "again."
        )

    def decay_message(self, rt: float, severity: Severity, text: str, basis: str | None) -> str:
        if severity is Severity.INFO:
            return (
                f"The broadband decay is short (estimated RT60 {rt:.2f} s"
                + (f" from {basis}" if basis else "")
                + "). "
                "An ensemble keeps its diction in a room like this."
            )
        return (
            f"The broadband decay is {text} (estimated RT60 {rt:.2f} s"
            + (f" from {basis}" if basis else "")
            + "). "
            "For a choir, decay this long gives ambience but blurs diction; absorption behind "
            "the ensemble or a different microphone position helps."
        )

    def low_imbalance_message(self, low_max: float, mid_mean: float) -> str:
        return (
            f"Low frequencies decay more slowly than the mid range "
            f"({low_max:.2f} s vs {mid_mean:.2f} s), which makes the ensemble bottom-heavy "
            "and muddies diction. Bass trapping or a different position helps."
        )


_PROFILES: dict[str, RecordingProfile] = {
    "generic": GenericProfile(),
    "vocal": VocalProfile(),
    "voiceover": VoiceOverProfile(),
    "acoustic_guitar": AcousticGuitarProfile(),
    "drums": DrumsProfile(),
    "room_mic": RoomMicProfile(),
    "choir": ChoirProfile(),
}


def available_profiles() -> list[str]:
    return sorted(_PROFILES)


def get_profile(name: str) -> RecordingProfile:
    try:
        return _PROFILES[name]
    except KeyError as exc:
        raise ConfigurationError(
            f"unknown recording profile '{name}'; available: {available_profiles()}"
        ) from exc
