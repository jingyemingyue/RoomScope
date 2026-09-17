# Measurement methodology

Every quantity RoomScope reports is listed here with its algorithm source,
unit, computation conditions, validity rule and known limitations. All DSP is
an independent implementation from the cited publications and standards
(see CODE_PROVENANCE.md). Bibliographic details were verified against the
publishers' records on 2026-09-17; items that could only be confirmed through
secondary sources are marked.

## 1. Excitation: exponential sine sweep (ESS)

**Source.** Farina (2000) [1], Farina (2007) [2], Müller & Massarani (2001) [3];
ISO 18233:2006 [11] endorses swept-sine excitation for room acoustics.

**Formula** (`core/sweep.py`). With `L = T / ln(f2/f1)`:

```
x(t) = sin( 2*pi*f1*L * (exp(t/L) - 1) ),    0 <= t < T
f(t) = f1 * exp(t/L)
```

Defaults: 48 kHz, 20 Hz–20 kHz, 10 s, peak −12 dBFS, sin²/cos² fades of
50 ms / 10 ms, 1 s of silence before and 3 s after. Supported sample rates:
44.1, 48, 88.2, 96, 176.4, 192 kHz. The user chooses duration, start/end
frequency, fades, level and silences.

**Why these defaults.** Müller & Massarani recommend short half-cosine fades
to avoid switching noise while keeping ripple < 0.1 dB, and starting below /
ending above the band of interest [3]. Farina (2007) shows most pre-ringing
comes from the fade-out and band limiting [2]; a very short fade-out is a
compromise between his "no fade-out, sweep to Nyquist" advice and DAW
compatibility (a file that ends at Nyquist is resampled unpredictably by
some DAWs). The silence after the sweep captures the decay; the silence
before it is the quiet segment for the noise analysis.

**Level safety.** The default is conservative and RoomScope never changes
system volume. Standalone Mode defaults to −20 dBFS and needs an explicit
acknowledgement above −12 dBFS.

## 2. Inverse filter and deconvolution

**Analytic inverse** (`core/sweep.py::inverse_filter`, Farina [1] §5):
the time-reversed sweep with an amplitude envelope `exp(-t/L)` (−6 dB per
octave), which compensates the −3 dB/octave energy spectrum of the log sweep
[3]. The filter is normalised so that the reference sweep convolved with it
peaks at exactly 1.0; a loopback therefore yields an impulse response with
peak 1.0 and everything is reported *relative* to that.

**Spectral inverse** (`inverse_filter_spectral`): when the reference is an
arbitrary WAV without a RoomScope sweep definition, a regularised spectral
division `H_inv = conj(X) / (|X|² + β)` with β = −60 dB relative to the
maximum of `|X|²` is used (Kirkeby-type regularisation as discussed by Farina
[2]). Same normalisation.

**Deconvolution** (`core/deconvolution.py`): full linear convolution of the
whole recording with the inverse filter (FFT). Because the convolution is
zero-padded (linear, not circular), harmonic distortion products of the
loudspeaker land *before* the linear response at `Δt_k = L·ln(k)` for the
k-th harmonic [1][3] and are never wrapped into the IR.

**Impulse-response location.** The direct sound is taken as the strongest
sample of the deconvolved signal. The IR keeps `ir_pre_delay_ms` (5 ms)
before it and up to `ir_max_length_s` (6 s) after it, limited by how much
recording exists after the sweep (`valid_length_s`). The *pre-peak margin*
(dB between the peak and the strongest content in the 0.5 s window ending
2 ms before it) is reported and mapped to a confidence: high ≥ 20 dB,
medium ≥ 10 dB, low otherwise. A low margin means distortion pre-responses,
noise or a wrong reference; findings and reflection notes say so.

**Sample rates.** If the recording's rate differs from the sweep definition,
the reference is regenerated at the recording's rate (this is what the DAW
effectively played) and a warning is recorded. A WAV-only reference is
resampled with `scipy.signal.resample_poly`.

**Limitations.** A strong reflection louder than the direct sound (rare, but
possible with the microphone close to a wall and far from the source) would
be taken as t = 0; the confidence margin does not catch that case. Clock
mismatch between separate playback and recording devices smears high
frequencies [2]; Standalone Mode uses one full-duplex device, Universal DAW
Mode inherits whatever clocking the DAW/interface provides.

## 3. Reverberation: EDT, T20, T30, estimated RT60

**Source.** Schroeder (1965) [4] for backward integration; Lundeby et al.
(1995) [5] for noise truncation and compensation (step list as reproduced by
Karjalainen et al. 2002 [15]); ISO 3382-1:2009 [9] / ISO 3382-2:2008 [10] for
evaluation ranges and the noise margin; Jacobsen & Rindel (1987) [6] for
time-reversed filtering.

**Procedure** (`core/decay.py`):

1. Band filtering: Butterworth band-pass (3 poles per skirt, second-order
   sections) for octave bands 63 Hz–8 kHz (base-2 edges `fc·2^(±1/2)`,
   IEC 61260-1 [12]), applied *time-reversed* so that the filter's own decay
   precedes the room decay. The filters are not certified IEC 61260 class 1.
2. Lundeby truncation (iterative, max 6 passes): 20 ms local averages, noise
   from the last 10 %, regression from the peak to noise + 10 dB, cross-point,
   new interval (5 intervals per 10 dB, clamped 1–50 ms), noise re-estimated
   from 7.5 dB of decay after the cross-point (at least the last 10 %), late
   slope over 15 dB starting 7.5 dB above noise, repeat until the cross-point
   moves < 1 ms. These parameter values are RoomScope's choices within the
   ranges published by Lundeby (10–50 ms; 3–10 intervals/10 dB; 5–10 dB;
   10–20 dB).
3. Schroeder curve: `EDC(t) = Σ_{τ≥t} h²(τ)` from the decay start (peak of the
   smoothed energy) to the truncation point, plus the late-decay
   compensation `C = p(t_c)·(−10 / (slope·ln 10))` (energy of the extrapolated
   exponential tail). Normalised to 0 dB at the start.
4. Least-squares line fits over the ISO 3382-1 ranges and extrapolation to
   60 dB: EDT 0…−10 dB (×6), T20 −5…−25 dB (×3), T30 −5…−35 dB (×2). The
   ISO "degree of non-linearity" `ξ = 1000·(1 − r²)` (‰) is reported.
5. **Validity.** A metric is reported only when the available decay range
   (peak level of the smoothed energy minus the estimated noise floor, in dB)
   is at least `|lower limit| + 10 dB`: 20 dB for EDT, 35 dB for T20, 45 dB
   for T30 (ISO 3382: the evaluation range must lie ≥ 10 dB above the noise
   [9][10], restated by Hak et al. 2012 [17]). Otherwise the metric is
   `insufficient_decay_range` with the numbers in `reason`.
6. **B·T check.** With time-reversed filtering the bandwidth × reverberation
   time product should exceed about 4 (about 16 with forward filtering) [6];
   below 4 the band's metrics are marked `unreliable` and a warning explains
   why. The numbers 16 / 4 are confirmed only through works citing [6].
7. **Estimated RT60** is T30 when valid, else T20, else none; the basis is
   always reported. Curvature `C = 100·(T30/T20 − 1)` % is given when both
   exist.

**Units.** Seconds; the Schroeder curve in dB relative to its start.

**Limitations.** One source and one microphone position correspond to the
ISO 3382-2 *survey* level at best; no spatial averaging is performed. Very
short decays in low bands are limited by the filters (B·T rule). The
truncation parameters differ from those in other packages (ODEON, ITA
Toolbox), so small systematic differences to other tools are expected [19].

## 4. Frequency response

**Source.** Standard FFT of the impulse response; fractional-octave
smoothing as power averaging in a `±1/(2n)`-octave window (a common
engineering definition; no standard governs it).

**Procedure** (`core/frequency_response.py`). Optional gating window
`fr_window_s` (default: the whole valid IR, 5 ms half-cosine end taper when
gated); FFT length chosen for ≥ 1 Hz resolution; magnitude in dB relative to
the loopback reference (0 dB = flat). The raw curve is always stored; the
smoothed curve (default 1/6 octave, configurable, 0 = off) is stored
separately and labelled.

**Limitations.** Relative dB only; the absolute gain of loudspeaker, mic and
preamp is included. No phase display in v0.1.

## 5. Background noise

**Source.** AES17-2020 [18] for the dBFS definition (0 dBFS = RMS of a
full-scale sine); Welch (1967) for the PSD estimate.

**Procedure** (`core/noise.py`). Quiet segment = recording from 50 ms after
the start to 100 ms before the detected sweep start (≥ 0.5 s), else the file
tail 3 s after the sweep end (flagged as possibly containing reverberation),
else none. Reported: RMS in dBFS (sine reference), peak dBFS, octave-band RMS
levels (zero-phase filtered), Welch PSD (Hann, 2 Hz resolution), and mains
hum candidates: for 50 Hz and 60 Hz, harmonics up to 1 kHz whose PSD peak
(±2 Hz) exceeds the median of the ±15 % neighbourhood by ≥ 10 dB; "detected"
means ≥ 2 such harmonics.

**Units.** dBFS and dB re FS²/Hz. **Never dB SPL** without calibration, which
v0.1 does not support.

**Limitations.** The pre-sweep segment is only as quiet as the DAW routing
allows (e.g. monitor bleed); the hum thresholds are engineering choices.

## 6. Early reflections

**Source.** Energy-time-curve inspection after Heyser (1971) [16]; onset
detection considerations from Defrance et al. (2008) and Usher (2010).

**Procedure** (`core/reflections.py`). Hilbert envelope with a 0.1 ms
peak-hold, expressed in dB relative to the direct sound; a 6 ms moving
average of the dB envelope models the local diffuse level; peaks between
0.8 ms and 80 ms after the direct sound, above −20 dB re direct and at least
6 dB above the local trend, are reported as candidates `(delay_ms,
relative_db)`.

**Limitations.** Candidates, not identified surfaces. In a dense early
diffuse tail some candidates are statistical. Delays are relative to the
detected direct sound (see confidence above).

## 7. Potential low-frequency resonances

**Source.** Decay-time-versus-frequency reasoning after Karjalainen et al.
(2002) [15] and Mäkivirta et al. (2003); no standard exists. The related
Genelec patent US 7,742,607 expired in 2022 (see §10).

**Procedure** (`core/resonance.py`). Below 300 Hz, peaks of the 1/24-octave
smoothed response that stand ≥ 6 dB above the 1-octave smoothed baseline are
candidates. For each, a 1/3-octave band-pass (2 poles per skirt,
time-reversed) is applied and the time for the band envelope to fall 20 dB
is compared with the same measure for the filter alone; the decay is called
distinguishable only when it is ≥ 2× the filter ringing.

**Limitations.** "Potential resonance" only. Identifying a room mode needs
room dimensions and several positions; RoomScope does not claim it.

## 8. Interpretation layer

Findings are produced from the result by a recording profile
(`interpretation/profiles.py`), never by the DSP. The generic profile flags:
low direct-sound confidence, clipping, insufficient decay range, early
reflections ≥ −10 dB within 30 ms, RT60 ≥ 0.6 s (notice) or ≥ 1.0 s
(warning), low bands decaying > 1.5× slower than mid bands, mains hum, and
distinguishable resonance candidates. Thresholds are coarse engineering
choices and are stated in each finding's evidence.

## 9. Things RoomScope deliberately does not do

No room score, no auto-EQ or correction, no dB SPL without calibration, no
room-mode identification, no plug-in hosting, no spatial averaging.

## 10. Patents

A Google Patents search (2026-09-17, not a legal opinion) found no in-force
patent claiming ESS generation with inverse-filter deconvolution, Schroeder
integration, ISO 3382 evaluation, ETC-based reflection detection or
decay-versus-frequency resonance detection as such; these methods are
published 1965–2003 prior art. Two in-force patents to stay clear of by
design: US 9,959,883 B2 (automatic two-sweep pass-band scheme) and
US 10,816,391 B2 (clock-drift correction between unsynchronised emitter and
receiver devices). Room-*correction* filter design is densely patented
(Dirac, Sonarworks, Audyssey/Sound United, DTS, Harman); RoomScope measures
and reports only.

## References

1. A. Farina, "Simultaneous Measurement of Impulse Response and Distortion with a Swept-Sine Technique," AES 108th Convention, Paris, 2000, preprint 5093. (confirmed, primary text)
2. A. Farina, "Advancements in Impulse Response Measurements by Sine Sweeps," AES 122nd Convention, Vienna, 2007, paper 7121. (confirmed, primary text)
3. S. Müller, P. Massarani, "Transfer-Function Measurement with Sweeps," J. Audio Eng. Soc. 49(6), 443–471, 2001. (confirmed)
4. M. R. Schroeder, "New Method of Measuring Reverberation Time," J. Acoust. Soc. Am. 37(3), 409–412, 1965. doi:10.1121/1.1909343 (confirmed)
5. A. Lundeby, T. E. Vigran, H. Bietz, M. Vorländer, "Uncertainties of Measurements in Room Acoustics," Acustica 81(4), 344–355, 1995. (confirmed via secondary sources; algorithm as summarised in [15])
6. F. Jacobsen, J. H. Rindel, "Time reversed decay measurements," J. Sound Vib. 117(1), 187–190, 1987. doi:10.1016/0022-460X(87)90444-5; F. Jacobsen, "A note on acoustic decay measurements," J. Sound Vib. 115(1), 163–170, 1987. (bibliography confirmed; B·T limits confirmed only through citing works)
7. G.-B. Stan, J.-J. Embrechts, D. Archambeau, "Comparison of Different Impulse Response Measurement Techniques," J. Audio Eng. Soc. 50(4), 249–262, 2002. (confirmed)
8. A. Novak, P. Lotton, L. Simon, "Synchronized Swept-Sine: Theory, Application, and Implementation," J. Audio Eng. Soc. 63(10), 786–798, 2015. doi:10.17743/jaes.2015.0071 (confirmed)
9. ISO 3382-1:2009, Acoustics — Measurement of room acoustic parameters — Part 1: Performance spaces. (confirmed; clause numbers not read from the standard text)
10. ISO 3382-2:2008 + Cor 1:2009, Part 2: Reverberation time in ordinary rooms. (confirmed)
11. ISO 18233:2006, Acoustics — Application of new measurement methods in building and room acoustics. (confirmed)
12. IEC 61260-1:2014 / ANSI/ASA S1.11-2014/Part 1, Electroacoustics — Octave-band and fractional-octave-band filters — Part 1: Specifications. (confirmed)
15. M. Karjalainen, P. Antsalo, A. Mäkivirta, T. Peltonen, V. Välimäki, "Estimation of Modal Decay Parameters from Noisy Response Measurements," J. Audio Eng. Soc. 50(11), 867–878, 2002. (confirmed)
16. R. C. Heyser, "Determination of Loudspeaker Signal Arrival Times, Parts I–III," J. Audio Eng. Soc. 19(9–11), 1971. (confirmed)
17. C. C. J. M. Hak, R. H. C. Wenmaekers, L. C. J. van Luxemburg, "Measuring Room Impulse Responses: Impact of the Decay Range on Derived Room Acoustic Parameters," Acta Acustica united with Acustica 98(6), 907–915, 2012. doi:10.3813/AAA.918574 (confirmed)
18. AES17-2020, AES standard method for digital audio engineering — Measurement of digital audio equipment. (confirmed via AES publications; defines 0 dB FS as the RMS of a full-scale sine)
19. D. Cabrera, J. Xun, M. Guski, "Calculating Reverberation Time from Impulse Responses: A Comparison of Software Implementations," Acoustics Australia 44(2), 369–378, 2016. doi:10.1007/s40857-016-0055-6 (confirmed)

Additional supporting references (A. Mäkivirta et al. 2003; G. Defrance et
al. 2008; J. Usher 2010; M. Guski & M. Vorländer 2014; C. L. Christensen et
al. 2013) are listed with their confirmation status in
`docs/research/literature.md`.
