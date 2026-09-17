# Status

Snapshot: 2026-09-17, v0.1.0.dev1 (foundation). Everything below was
verified by actually running it on macOS (Apple silicon, Python 3.12.14).
Nothing is marked PASS that was not run.

## Implemented

| Area | What exists |
| --- | --- |
| Excitation | ESS generation (Farina), fades, level, silences; WAV + JSON sidecar; 44.1–192 kHz |
| Inverse filters | Analytic (time-reversed, −6 dB/oct) and regularised spectral division |
| Deconvolution | Whole-recording linear convolution; automatic IR location; pre-peak margin / confidence; sweep-start estimate |
| Reverberation | Schroeder integration, Lundeby truncation + compensation, EDT/T20/T30 with ISO 3382-1 ranges, validity flags, non-linearity, curvature, B·T check; broadband + octave bands 63 Hz–8 kHz (time-reversed Butterworth) |
| Frequency response | FFT with optional gating; raw kept; configurable fractional-octave smoothing |
| Background noise | Quiet-segment selection (pre-sweep / tail), RMS + peak dBFS (AES17), octave-band levels, Welch PSD, 50/60 Hz hum candidates |
| Early reflections | ETC peak candidates (delay ms, level dB re direct) with local-trend prominence |
| Low-frequency resonances | Candidate peaks (< 300 Hz) with narrow-band decay vs. filter ringing comparison |
| Models & storage | Validated settings; result model with JSON export; MeasurementSession; session directory (session.json, result.json, impulse_response.wav) |
| Interpretation | Finding model; RecordingProfile interface; generic profile |
| CLI | `roomscope sweep / analyze / devices / measure / gui`, text report and JSON output |
| Standalone Mode | Device enumeration and play+record through PortAudio with safety defaults |
| GUI | PySide6 window: Home, Universal DAW Mode (4 steps), Standalone Mode, Results (Overview, IR, FR, Decay, Noise, Reflections), session saving |

## Tested (all PASS on 2026-09-17)

```
pytest      96 passed  (tests/unit 79, tests/integration 15, tests/ui 2 offscreen)
ruff check  All checks passed  (src, tests, examples, scripts)
ruff format 61 files already formatted
mypy        Success: no issues found in 39 source files (strict)
```

What the tests prove with synthetic signals (no real-room recording is used
as evidence):

* Sweep instantaneous frequency follows `f1·exp(t/L)` (2 % tolerance);
  levels, fades, silences and lengths are exact; all six sample rates work;
  invalid settings are rejected.
* Sweep ⊛ inverse filter is a unit pulse (analytic and spectral): peak 1.0,
  everything outside ±2 ms below −35 dB.
* Loopback recording → IR peak 1.000 at the expected index; delay and gain
  are recovered; too-short, silent and tail-less recordings raise clear
  errors; clipping is warned.
* Exact exponential decay → EDT/T20/T30 within 1 %; noisy exponential decays
  (RT60 0.25/0.6/1.2 s) within 5 %; octave-band T30 within 10 %; a 30 dB
  decay range yields `insufficient_decay_range` for T20/T30 (no number);
  B·T < 4 is flagged unreliable; Lundeby cross-point lands near the noise
  crossing.
* Frequency response of a delta is 0 dB flat; comb-filter notch/peak depths
  are exact; smoothing preserves constants and reduces spikes.
* Full-scale sine = 0 dBFS RMS (AES17); 60 Hz hum with harmonics is detected
  and 50 Hz is not; white noise triggers no hum.
* Discrete reflections at 18/35 ms with −9/−15 dB are found within 0.1 ms
  and 0.5 dB, also in a band-limited IR with a diffuse tail.
* A ringing 62 Hz mode is reported as a distinguishable resonance candidate;
  a flat response yields none.
* End-to-end: RT60 0.45 s, reflection 18 ms/−9 dB and noise −77 dBFS are
  recovered from a synthetic room; recordings at 44.1 and 96 kHz against a
  48 kHz sweep definition; stereo channel auto-selection and explicit
  selection; WAV-only reference (spectral inverse) and resampled reference;
  loudspeaker distortion (2nd/3rd order) leaves the linear IR clean; CLI
  round trip incl. JSON; session save/load; GUI DAW-mode flow offscreen.
* macOS basic run: `roomscope sweep`, `roomscope analyze`,
  `roomscope devices` (12 Core Audio devices listed), the example script,
  and the GUI (offscreen) ran successfully. **Not run:** a real Standalone
  measurement through loudspeakers/microphone (needs a person in the room to
  set levels) and the on-screen GUI on a display.

## Known limitations

* Single source, single position: at most ISO 3382-2 "survey" accuracy; no
  spatial averaging.
* Direct sound = strongest deconvolved sample; a reflection stronger than the
  direct sound would be mis-identified (confidence margin does not catch it).
* Band filters are Butterworth, not certified IEC 61260 class 1; short
  decays in the 63/125 Hz bands are limited by B·T and are flagged.
* Lundeby parameters (20 ms initial blocks, 5 intervals/10 dB, 7.5 dB
  margins) are RoomScope's choices within the published ranges; other tools
  will differ slightly.
* Reflection and resonance outputs are candidates; in dense diffuse tails
  some reflection candidates are statistical; room modes are not identified.
* Noise levels are dBFS only; no SPL calibration; mains-hum thresholds are
  engineering choices.
* No clock-drift correction between separate playback and recording
  devices (Universal DAW Mode relies on the DAW/interface clocking).
* `result.json` with curves is several MB for long IRs (`--no-curves` to
  shrink); the raw IR WAV is the authoritative record.
* The GUI is functional but plain; no session re-opening in the GUI yet.

## Not implemented (by design for v0.1 or deferred)

VST3/AU/AAX plug-ins, room score, auto-EQ/correction, cloud/accounts, 3D
room modelling, absorption material calculators, dB SPL, room-mode
identification, multi-position averaging, phase display, additional
recording profiles (vocal, voice-over, guitar, drums, room mic, choir — the
interface exists), session browser, packaged binaries.

## Dependencies

Runtime: numpy 2.5.3, scipy 1.18.1, soundfile 0.14.0, sounddevice 0.5.6,
matplotlib 3.11.2; optional GUI: PySide6 6.11.2 (Qt 6.11.2). Dev: pytest,
pytest-cov, ruff, mypy. Full table with licenses: DEPENDENCIES.md.

## License status

RoomScope: Apache-2.0 (LICENSE verbatim from apache.org, NOTICE present;
rationale in LICENSE_DECISION.md). All runtime dependencies are permissive
or LGPL used dynamically; no copyleft obligation reaches RoomScope's source.
Obligations that apply to a future *binary* distribution (Qt LGPL texts and
notices, libsndfile LGPL, FreeType credit, PortAudio/Qhull/Agg notices,
Windows ASIO DLL removal) are listed in DEPENDENCIES.md §3–4 and must be
re-checked before any binary release.

## Third-party provenance

No third-party source files vendored (CODE_PROVENANCE.md). Twenty-one
external repositories were audited (THIRD_PARTY_REVIEW.md); all were used as
conceptual references only. GPL projects (DRC, Aliki) and proprietary REW
were not copied.

## Known licensing risks

* Frozen desktop builds must add Qt/PySide6 license texts (the wheels ship
  none) and keep Qt as replaceable shared libraries.
* Windows sounddevice wheels contain ASIO DLLs built with the proprietary
  Steinberg SDK — strip them.
* matplotlib's bundled `ttconv` license and the Linux/Windows wheel contents
  of several packages are still UNKNOWN / NEEDS REVIEW.
* Two in-force patents adjacent to the field (US 9,959,883; US 10,816,391)
  are noted in MEASUREMENT_METHODOLOGY.md §10 so the design does not drift
  into them. Not a legal opinion.

## Next recommended milestone (v0.1.1 / v0.2)

1. A real-room validation campaign: measure one treated and one untreated
   room with RoomScope and a second tool (e.g. REW, used only as a
   comparison instrument), and document agreement of T20/T30 per band.
2. Standalone Mode hardware test on macOS, Windows and Linux (device
   selection, channel mapping, sample-rate negotiation).
3. Loopback/reference-channel support (second input for the interface
   output) to remove interface response and clock ambiguity.
4. Recording profiles beyond "generic" (vocal, voice-over, acoustic guitar).
5. Session re-opening in the GUI and a small session browser.
6. Packaging (briefcase/PyInstaller one-dir) with the license bundle from
   DEPENDENCIES.md §3–4.
