"""The analysis pipeline shared by the CLI, the GUI and the Python API.

recording + reference sweep
    -> channel selection and validation
    -> deconvolution (whole recording, no manual trimming)
    -> impulse response location
    -> decay analysis (broadband + octave bands)
    -> frequency response
    -> background noise (quiet segment of the recording)
    -> early reflections
    -> potential low-frequency resonances
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import numpy as np
from scipy.signal import resample_poly

from roomscope.core.decay import analyze_decay
from roomscope.core.deconvolution import confidence_label, deconvolve, locate_impulse_response
from roomscope.core.frequency_response import frequency_response
from roomscope.core.noise import analyze_noise, find_quiet_segment
from roomscope.core.reflections import detect_early_reflections
from roomscope.core.resonance import detect_potential_resonances
from roomscope.core.sweep import generate_ess, inverse_filter, inverse_filter_spectral
from roomscope.errors import ConfigurationError, InvalidAudioError, SampleRateMismatchError
from roomscope.models.audio import AudioSignal, FloatArray
from roomscope.models.configuration import AnalysisSettings, SweepSettings
from roomscope.models.result import AnalysisResult, ImpulseResponseResult

SILENCE_THRESHOLD_DBFS = -80.0
CLIPPING_THRESHOLD = 0.999
CLIPPING_MIN_SAMPLES = 8


@dataclass(frozen=True)
class Reference:
    """The excitation signal that was played.

    Either ``settings`` (preferred: the sweep is regenerated exactly, at any
    sample rate) or ``signal`` (an arbitrary mono reference at
    ``sample_rate``, inverted by regularised spectral division).
    """

    settings: SweepSettings | None = None
    signal: FloatArray | None = None
    sample_rate: int | None = None

    def __post_init__(self) -> None:
        if self.settings is None and self.signal is None:
            raise ConfigurationError("a reference needs sweep settings or a reference signal")
        if self.signal is not None and self.sample_rate is None:
            raise ConfigurationError("a reference signal needs its sample rate")

    @classmethod
    def from_settings(cls, settings: SweepSettings) -> Reference:
        return cls(settings=settings)

    @classmethod
    def from_signal(cls, signal: FloatArray, sample_rate: int) -> Reference:
        mono = signal if signal.ndim == 1 else np.ascontiguousarray(signal[:, 0])
        return cls(signal=np.asarray(mono, dtype=np.float64), sample_rate=sample_rate)


@dataclass(frozen=True)
class _PreparedReference:
    inverse: FloatArray
    reference_length: int
    sweep_settings: SweepSettings | None
    warnings: tuple[str, ...]


def _prepare_reference(reference: Reference, sample_rate: int) -> _PreparedReference:
    warnings: list[str] = []
    if reference.settings is not None:
        settings = reference.settings
        if settings.sample_rate != sample_rate:
            try:
                settings = settings.with_sample_rate(sample_rate)
            except ConfigurationError as exc:
                raise SampleRateMismatchError(
                    f"recording is at {sample_rate} Hz but the sweep cannot be regenerated at that rate: {exc}"
                ) from exc
            warnings.append(
                f"reference sweep regenerated at the recording sample rate ({sample_rate} Hz); "
                f"it was defined at {reference.settings.sample_rate} Hz"
            )
        return _PreparedReference(
            inverse=inverse_filter(settings),
            reference_length=settings.sweep_samples,
            sweep_settings=settings,
            warnings=tuple(warnings),
        )
    assert reference.signal is not None and reference.sample_rate is not None
    signal = reference.signal
    if reference.sample_rate != sample_rate:
        gcd = int(np.gcd(sample_rate, reference.sample_rate))
        signal = np.asarray(
            resample_poly(signal, sample_rate // gcd, reference.sample_rate // gcd),
            dtype=np.float64,
        )
        warnings.append(
            f"reference signal resampled from {reference.sample_rate} Hz to {sample_rate} Hz"
        )
    warnings.append(
        "reference given as an audio file without a RoomScope sweep definition; "
        "using regularised spectral division instead of the analytic inverse filter"
    )
    return _PreparedReference(
        inverse=inverse_filter_spectral(signal),
        reference_length=signal.shape[0],
        sweep_settings=None,
        warnings=tuple(warnings),
    )


def _validate_recording(mono: FloatArray, sample_rate: int) -> list[str]:
    warnings: list[str] = []
    peak = float(np.max(np.abs(mono)))
    if peak <= 0.0 or 20.0 * np.log10(peak) < SILENCE_THRESHOLD_DBFS:
        raise InvalidAudioError(
            f"recording is silent (peak below {SILENCE_THRESHOLD_DBFS:g} dBFS); check the input routing"
        )
    clipped = int(np.count_nonzero(np.abs(mono) >= CLIPPING_THRESHOLD))
    if clipped >= CLIPPING_MIN_SAMPLES:
        warnings.append(
            f"recording contains {clipped} samples at or above {CLIPPING_THRESHOLD:g} full scale: "
            "probable clipping; lower the playback level and measure again"
        )
    if mono.shape[0] < sample_rate:
        raise InvalidAudioError("recording is shorter than one second")
    return warnings


def analyze(
    recording: AudioSignal,
    reference: Reference,
    settings: AnalysisSettings | None = None,
) -> AnalysisResult:
    """Run the full v0.1 analysis chain and return an :class:`AnalysisResult`."""
    settings = settings or AnalysisSettings()
    sample_rate = recording.sample_rate
    warnings: list[str] = []

    mono, channel, channel_warning = recording.select_channel(settings.channel)
    if channel_warning:
        warnings.append(channel_warning)
    warnings.extend(_validate_recording(mono, sample_rate))

    prepared = _prepare_reference(reference, sample_rate)
    warnings.extend(prepared.warnings)

    h_full = deconvolve(mono, prepared.inverse)
    located = locate_impulse_response(
        h_full,
        recording_length=mono.shape[0],
        reference_length=prepared.reference_length,
        sample_rate=sample_rate,
        pre_delay_ms=settings.ir_pre_delay_ms,
        max_length_s=settings.ir_max_length_s,
    )
    ir = located.samples
    confidence = confidence_label(located.pre_peak_margin_db)
    ir_notes: list[str] = []
    if located.valid_length_samples / sample_rate < 1.0:
        ir_notes.append(
            f"only {located.valid_length_samples / sample_rate:.2f} s of decay were recorded after the "
            "sweep; long reverberation times cannot be evaluated"
        )
    if confidence != "high":
        ir_notes.append(
            f"content before the direct sound is only {located.pre_peak_margin_db:.1f} dB below it "
            "(distortion, noise or a wrong reference); direct-sound detection confidence is "
            f"{confidence}"
        )
    warnings.extend(ir_notes)

    impulse = ImpulseResponseResult(
        sample_rate=sample_rate,
        samples=ir,
        direct_sound_index=located.direct_index,
        pre_delay_samples=located.pre_delay_samples,
        peak_value=located.peak_value,
        valid_length_s=located.valid_length_samples / sample_rate,
        pre_peak_margin_db=located.pre_peak_margin_db,
        direct_sound_confidence=confidence,
        sweep_start_in_recording_s=located.sweep_start_index_in_recording / sample_rate,
        notes=tuple(ir_notes),
    )

    decay = analyze_decay(ir, sample_rate, settings)
    response = frequency_response(
        ir,
        sample_rate,
        window_s=settings.fr_window_s,
        smoothing_fraction=settings.fr_smoothing_fraction,
    )
    segment = find_quiet_segment(
        recording_length=mono.shape[0],
        sample_rate=sample_rate,
        sweep_start_index=located.sweep_start_index_in_recording,
        reference_length=prepared.reference_length,
        min_segment_s=settings.noise_min_segment_s,
    )
    noise = analyze_noise(mono, sample_rate, segment, octave_bands_hz=settings.octave_bands_hz)
    reflections = detect_early_reflections(
        ir,
        sample_rate,
        located.direct_index,
        min_delay_ms=settings.reflections_min_delay_ms,
        max_delay_ms=settings.reflections_max_delay_ms,
        threshold_db=settings.reflections_threshold_db,
        prominence_db=settings.reflections_prominence_db,
        direct_sound_confidence=confidence,
    )
    resonances = detect_potential_resonances(
        ir,
        sample_rate,
        response,
        max_hz=settings.resonance_max_hz,
        min_prominence_db=settings.resonance_min_prominence_db,
    )
    sweep_dict = prepared.sweep_settings.to_dict() if prepared.sweep_settings is not None else {}
    analysis_dict = settings.to_dict()
    analysis_dict["channel_analysed"] = channel
    return AnalysisResult(
        created_at=datetime.now(UTC).replace(microsecond=0).isoformat(),
        sample_rate=sample_rate,
        sweep_settings=sweep_dict,
        analysis_settings=analysis_dict,
        impulse_response=impulse,
        decay=decay,
        frequency_response=response,
        noise=noise,
        reflections=reflections,
        resonances=resonances,
        warnings=tuple(warnings),
    )


def synthetic_recording(
    settings: SweepSettings,
    room_ir: FloatArray,
    *,
    noise_rms: float = 0.0,
    gain: float = 1.0,
    seed: int | None = 0,
) -> AudioSignal:
    """Convolve the measurement signal with ``room_ir`` and add white noise.

    Used by the tests and the examples to prove the round trip without a real
    room. ``generate_ess`` is imported here so that the helper lives next to
    ``analyze``; it is not used by the analysis itself.
    """
    from scipy.signal import fftconvolve

    from roomscope.core.sweep import measurement_signal

    excitation = measurement_signal(settings)
    recorded = np.asarray(fftconvolve(excitation, room_ir, mode="full"), dtype=np.float64) * gain
    if noise_rms > 0.0:
        rng = np.random.default_rng(seed)
        recorded = recorded + rng.normal(0.0, noise_rms, recorded.shape[0])
    return AudioSignal(samples=recorded, sample_rate=settings.sample_rate, source="synthetic")


__all__ = ["Reference", "analyze", "generate_ess", "synthetic_recording"]
