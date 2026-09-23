"""Optional electrical loopback (reference) channel.

One interface output drives the loudspeaker and is also returned electrically
into a second input. The deconvolved loopback must look like a pulse, not a
room: a channel that decays like a microphone recording is refused and the
analysis continues uncompensated.

Compensation is regularised spectral division (Kirkeby et al. 1998; the same
shape ``roomscope.core.sweep.design_spectral_inverse`` uses) inside the
excitation band::

    H_room = H_mic · conj(H_lb) / (|H_lb|² + ε(f))

``H_lb`` is a short FIR cut around the loopback peak so that compensation
removes the interface *response* and does not shift the acoustic time origin.
The loopback peak is still the electrical time zero: ``path_delay_ms`` is the
delay of the microphone's direct sound relative to it, and
``distance_upper_bound_m = c · path_delay`` is a bound (loudspeaker DSP
latency only adds delay).

Nothing here estimates clock drift: both channels share one converter clock.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy import fft as sfft

from roomscope.core.deconvolution import LocatedImpulseResponse, confidence_label
from roomscope.core.placement import speed_of_sound_m_s
from roomscope.core.sweep import (
    SPECTRAL_REG_TRANSITION_OCTAVES,
    _regularisation_shape_db,
)
from roomscope.models.audio import FloatArray
from roomscope.models.result import ExcitationBand, LoopbackResult

#: Window of the deconvolved loopback used as the interface FIR (ms).
LOOPBACK_FIR_PRE_MS = 5.0
LOOPBACK_FIR_POST_MS = 15.0
#: 99 % of the energy after the peak must land inside this many milliseconds.
MAX_ELECTRICAL_SETTLE_MS = 10.0
#: Late peak (5–80 ms) must sit at least this far below the direct-sound sample.
MIN_LATE_PEAK_DROP_DB = 25.0
LATE_PEAK_START_MS = 5.0
LATE_PEAK_END_MS = 80.0
#: Frequency-response reference string when compensation was applied.
LOOPBACK_FR_REFERENCE = "relative dB (0 dB = the interface loopback)"
#: Stated acceptance for a synthetic interface response after compensation
#: (median absolute error over the normalisation band).
COMPENSATION_TOLERANCE_DB = 1.0


@dataclass(frozen=True)
class LoopbackAssessment:
    """Outcome of :func:`assess_loopback` before compensation is applied."""

    accepted: bool
    reason: str | None
    located: LocatedImpulseResponse | None
    fir: FloatArray | None
    settle_ms: float | None
    drop_db: float | None
    notes: tuple[str, ...] = ()


def energy_settling_ms(h_full: FloatArray, peak_index: int, sample_rate: int) -> float | None:
    """Time after the peak that holds 99 % of the remaining energy (ms)."""
    tail = np.asarray(h_full[peak_index:], dtype=np.float64) ** 2
    total = float(np.sum(tail))
    if total <= 0.0:
        return None
    idx = int(np.searchsorted(np.cumsum(tail), 0.99 * total))
    return idx / sample_rate * 1000.0


def late_peak_drop_db(h_full: FloatArray, peak_index: int, sample_rate: int) -> float | None:
    """How far (dB) the strongest sample 5–80 ms after the peak sits below it."""
    start = peak_index + round(LATE_PEAK_START_MS * sample_rate / 1000.0)
    stop = peak_index + round(LATE_PEAK_END_MS * sample_rate / 1000.0)
    if stop > h_full.shape[0] or stop <= start:
        return None
    peak = float(np.max(np.abs(h_full[peak_index : peak_index + 1])))
    late = float(np.max(np.abs(h_full[start:stop])))
    if peak <= 0.0:
        return None
    return 20.0 * math.log10(peak / max(late, 1e-300))


def loopback_fir(h_full: FloatArray, peak_index: int, sample_rate: int) -> FloatArray:
    """Short interface FIR around the loopback peak, copied out of ``h_full``."""
    start = max(0, peak_index - round(LOOPBACK_FIR_PRE_MS * sample_rate / 1000.0))
    stop = min(
        h_full.shape[0],
        peak_index + round(LOOPBACK_FIR_POST_MS * sample_rate / 1000.0) + 1,
    )
    fir = np.asarray(h_full[start:stop], dtype=np.float64)
    if fir.shape[0] < 16:
        return np.asarray(h_full[max(0, peak_index - 8) : peak_index + 8], dtype=np.float64)
    return fir


def assess_loopback(
    located: LocatedImpulseResponse,
    h_full: FloatArray,
    sample_rate: int,
    *,
    clipped: bool,
) -> LoopbackAssessment:
    """Refuse a loopback that is not an electrical pulse.

    A silent, clipped, low-confidence or room-like channel is rejected so that
    compensation cannot corrupt the microphone path.
    """
    notes: list[str] = []
    if clipped:
        return LoopbackAssessment(
            accepted=False,
            reason="the loopback channel clips; compensation is not applied",
            located=located,
            fir=None,
            settle_ms=None,
            drop_db=None,
            notes=tuple(notes),
        )
    confidence = confidence_label(located.pre_peak_margin_db)
    if confidence != "high":
        return LoopbackAssessment(
            accepted=False,
            reason=(
                "the loopback peak does not stand far enough above the content before it "
                f"(confidence {confidence}); the channel may be a microphone, not an "
                "electrical return. Compensation is not applied"
            ),
            located=located,
            fir=None,
            settle_ms=None,
            drop_db=None,
            notes=tuple(notes),
        )
    settle = energy_settling_ms(h_full, located.peak_index, sample_rate)
    drop = late_peak_drop_db(h_full, located.peak_index, sample_rate)
    if settle is None or drop is None:
        return LoopbackAssessment(
            accepted=False,
            reason=(
                "the loopback recording is too short after the peak to check that the "
                "return is electrical; compensation is not applied"
            ),
            located=located,
            fir=None,
            settle_ms=settle,
            drop_db=drop,
            notes=tuple(notes),
        )
    if settle > MAX_ELECTRICAL_SETTLE_MS or drop < MIN_LATE_PEAK_DROP_DB:
        return LoopbackAssessment(
            accepted=False,
            reason=(
                f"the loopback still carries energy {settle:.1f} ms after the peak "
                f"(late peak {drop:.1f} dB down); that looks like a room, not a cable. "
                "Compensation is not applied"
            ),
            located=located,
            fir=None,
            settle_ms=settle,
            drop_db=drop,
            notes=tuple(notes),
        )
    fir = loopback_fir(h_full, located.peak_index, sample_rate)
    notes.append(
        f"loopback settled in {settle:.1f} ms (late peak {drop:.1f} dB down); "
        f"using a {fir.shape[0]}-sample interface FIR around the peak"
    )
    return LoopbackAssessment(
        accepted=True,
        reason=None,
        located=located,
        fir=fir,
        settle_ms=settle,
        drop_db=drop,
        notes=tuple(notes),
    )


def compensate(
    h_mic: FloatArray,
    fir: FloatArray,
    sample_rate: int,
    excitation_band: ExcitationBand,
) -> FloatArray:
    """Return ``h_mic`` divided by the interface FIR, regularised outside the band."""
    nfft = int(sfft.next_fast_len(max(h_mic.shape[0], 2 * fir.shape[0]), real=True))
    spec_mic = sfft.rfft(h_mic, nfft)
    spec_lb = sfft.rfft(fir, nfft)
    freqs = np.fft.rfftfreq(nfft, 1.0 / sample_rate)
    lo = float(excitation_band.low_hz)
    hi = float(excitation_band.high_hz)
    ratio = 2.0 ** float(SPECTRAL_REG_TRANSITION_OCTAVES)
    ref_lo = max(lo / ratio, 1.0)
    ref_hi = min(hi * ratio, sample_rate / 2.0 - 1.0)
    if ref_lo >= ref_hi:
        ref_lo, ref_hi = lo, hi
    shape_db = _regularisation_shape_db(freqs, (lo, hi), (ref_lo, ref_hi))
    power = np.abs(spec_lb) ** 2
    in_band = (freqs >= lo) & (freqs <= hi)
    scale = float(np.median(power[in_band])) if np.any(in_band) else float(np.median(power[1:]))
    scale = max(scale, 1e-30)
    eps = scale * 10.0 ** (shape_db / 10.0)
    spec_room = spec_mic * np.conj(spec_lb) / (power + eps)
    compensated = np.asarray(sfft.irfft(spec_room, nfft)[: h_mic.shape[0]], dtype=np.float64)
    return compensated


def path_metrics(
    *,
    mic_peak_index: int,
    loopback_peak_index: int,
    sample_rate: int,
    reference_length: int,
    temperature_c: float | None,
) -> tuple[int, float, float]:
    """``(latency_samples, path_delay_ms, distance_upper_bound_m)``.

    ``latency_samples`` is the loopback peak relative to ``len(reference) - 1``
    (the electrical I/O delay of the interface). ``path_delay_ms`` is the
    microphone peak relative to the loopback peak.
    """
    latency = int(loopback_peak_index - (reference_length - 1))
    path_delay_ms = (mic_peak_index - loopback_peak_index) / sample_rate * 1000.0
    temperature = 20.0 if temperature_c is None else float(temperature_c)
    bound = speed_of_sound_m_s(temperature) * max(path_delay_ms, 0.0) / 1000.0
    return latency, float(path_delay_ms), float(bound)


def make_loopback_result(
    *,
    channel: int | None,
    assessment: LoopbackAssessment,
    sample_rate: int,
    reference_length: int,
    mic_peak_index: int | None,
    temperature_c: float | None,
    compensation_applied: bool,
) -> LoopbackResult:
    """Build the stored :class:`LoopbackResult` from an assessment."""
    located = assessment.located
    latency: int | None = None
    delay_ms: float | None = None
    bound: float | None = None
    hz: FloatArray | None = None
    db: FloatArray | None = None
    notes = list(assessment.notes)
    if located is not None and mic_peak_index is not None:
        latency, delay_ms, bound = path_metrics(
            mic_peak_index=mic_peak_index,
            loopback_peak_index=located.peak_index,
            sample_rate=sample_rate,
            reference_length=reference_length,
            temperature_c=temperature_c,
        )
        if delay_ms < 0.0:
            notes.append(
                f"the microphone peak precedes the loopback peak by {-delay_ms:.2f} ms; "
                "the path-delay bound is not reported"
            )
            bound = None
    if assessment.fir is not None and assessment.fir.shape[0] >= 16:
        nfft = int(sfft.next_fast_len(max(4096, 2 * assessment.fir.shape[0]), real=True))
        spectrum = sfft.rfft(assessment.fir, nfft)
        freqs = np.fft.rfftfreq(nfft, 1.0 / sample_rate)
        mag = 20.0 * np.log10(np.maximum(np.abs(spectrum), 1e-300))
        hz = np.asarray(freqs[1:], dtype=np.float64)
        db = np.asarray(mag[1:], dtype=np.float64)
    return LoopbackResult(
        channel=channel,
        compensation_applied=compensation_applied,
        reason=assessment.reason,
        latency_samples=latency,
        path_delay_ms=delay_ms,
        distance_upper_bound_m=bound,
        interface_response_hz=hz,
        interface_response_db=db,
        notes=tuple(notes),
    )
