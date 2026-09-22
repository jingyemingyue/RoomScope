# Status

Snapshot: 2026-09-17, v0.1.0.dev1 (foundation). Everything below was
verified by actually running it on macOS (Apple silicon, Python 3.12.14).
Nothing is marked PASS that was not run.

Snapshot 2: 2026-09-22 — recording profiles (vocal, voice-over, acoustic
guitar, drums, room mic, choir) added on top of the foundation; same
verification policy.

Snapshot 3: 2026-09-22 — developer-facing GitHub foundation (CI, issue/PR
templates, code of conduct, security policy). Re-verified on Linux x86_64
(Ubuntu, Python 3.12.3). The `gui` extra now installs PySide6_Essentials
only.

Snapshot 5: 2026-09-22 — v0.2 reopen and compare: Tier 1 lazy exports,
lenient loaders, shipped JSON Schemas, `compare()` / CLI / GUI, and
comparison findings. Hardware validation is still not claimed.

Snapshot 6: 2026-09-22 — 0.2 follow-up after CI on `0ad2a4e`: the
comparison test now requires the ISO 3382-1 "not significant" disclaimer
instead of forbidding the word "significant", and the wheel `force-include`
lists each schema JSON file so `roomscope/schemas/__init__.py` is not
added twice. Re-verified on Linux x86_64 (Ubuntu, Python 3.12.3).

Snapshot 7: 2026-09-22 — v0.3 trust the chain: loopback compensation,
`AudioBackend` + fake backend, progress and Stop, robustness tests, CI
OS matrix, hardware matrix started. Hardware cells are not marked PASS.
Re-verified on Linux x86_64 (Ubuntu, Python 3.12.3).

Snapshot 8: 2026-09-22 — v0.4 for everyone: gettext + zh-CN, self-contained
sessions and bundles, user settings, projects/averaging (SHOULD), CSV
export, user guide, unsigned-bundle pipeline (`release.yml`, license
bundle, GPL-module gate). Hardware cells are not marked PASS.

Snapshot 10: 2026-09-22 — 1.0-rc software on top of 0.4: Placement tab
(S5), Python 3.14 in CI (S6), M11 validation protocol with pre-chosen
tolerances, bundle.lock, SBOM/checksums and a trusted-publishing job
that still needs the maintainer `pypi` environment. Hardware cells are
not marked PASS. The repository is not public.

Snapshot 9: 2026-09-22 — 0.4 follow-up after the first local suite: `--json`
prints JSON again (deprecation on stderr, not `warnings.warn`); license
discovery follows files under `.dist-info/licenses/`; macOS
`NSMicrophoneUsageDescription` and the audio-input entitlement are in
`packaging/macos/`. Re-verified on Linux x86_64 (Ubuntu, Python 3.12.3).

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
| Placement geometry | Excess path per candidate; with a tape-measured loudspeaker distance the exact product of perpendicular distances and its two-sided bracket; with a microphone height the vertical axis (loudspeaker height, plane above the devices, horizontal separation). No coordinates, no room length or width, no wall named |
| Low-frequency resonances | Candidate peaks (< 300 Hz) with narrow-band decay vs. filter ringing comparison |
| Models & storage | Validated settings; result model with JSON export and `from_dict` load; MeasurementSession; self-contained session directory (session.json, result.json, IR WAV, optional recording.wav, always-copied sweep sidecar); `load_measurement` / `list_sessions` / `bundle_session`; recent list and `settings.json` under `$ROOMSCOPE_HOME`; shipped JSON Schemas; `comparison.json`; `project.json` |
| Interpretation | Finding model (`message_id` / `params` / `locale`); messages through gettext `_()`; RecordingProfile registry + entry points; seven profiles; `interpret_comparison` |
| CLI | `roomscope sweep / analyze / analyze-ir / show / compare / schema / devices / measure / gui / session bundle / export / project`; global `--lang`, `--format`, `--backend`, `--copy-recording` |
| Public API | Lazy Tier 1 exports from `import roomscope` (ARCHITECTURE_V1.md §5.1) |
| Loopback | Optional electrical return: pulse validation, regularised compensation, path-delay bound; refused room-like or clipped channels leave the analysis uncompensated |
| Audio backends | `AudioBackend` protocol; PortAudio callback stream (progress, Stop); fake backend for CI and Demo |
| Averaging | `average_decay`: VALID T values only; ISO 3382-2 class labelled from Table 1 (secondary-source transcription) |
| Export | CSV exporter for decay, FR, noise PSD, reflections, resonances; `roomscope.exporters` entry points |
| i18n | stdlib gettext; `zh_CN` catalog; `--lang` / settings / `ROOMSCOPE_LANG` |
| GUI | PySide6 window: Home, Universal DAW Mode, Standalone Mode, Results (including Placement), session save/open, Compare, Demo, Stop, Settings, project-folder browser, tape-measure fields |
| Standalone Mode | Device enumeration and play+record through the selected backend with safety defaults |
| Bundles | `scripts/build_license_bundle.py`, `scripts/check_bundle_contents.py`, `packaging/roomscope.spec`, unsigned `release.yml` on `v*` tags |

## Tested (all PASS on 2026-09-17 on macOS; profile work re-verified 2026-09-22;
Linux x86_64 re-verified 2026-09-22 after the loopback-peak test fix)

```
pytest      304 passed  (tests/unit 246, tests/integration 42, tests/ui 8 offscreen, tests/robustness 8)
ruff check  All checks passed  (src, tests, examples, scripts)
ruff format files already formatted
mypy        Success: no issues found in 68 source files (strict)
```

The 2026-09-17 macOS log recorded 256 tests. Later DSP work replaced a
peak-normalised inverse with unit in-band gain and consolidated some
assertions; the two loopback tests that still expected a time-domain peak
of 1.0 were updated on 2026-09-22 and pass on Linux. Session-reopen tests
(result `from_dict`, `load_measurement`, recent list, `roomscope show`,
GUI re-open) plus the 0.2 compare / schema / Tier 1 lock tests brought
the suite to 259. 0.3 added loopback, the backend protocol and robustness
tests (283). 0.4 adds i18n, settings, bundles, averaging, CSV, license
gates and the macOS microphone plist (301). 1.0-rc adds the Placement
tab, the validation-protocol test and the bundle-lock test (304). GUI
tests also check that
matplotlib's QtAgg backend loads against PySide6_Essentials (no Addons).

What the tests prove with synthetic signals (no real-room recording is used
as evidence):

* Sweep instantaneous frequency follows `f1·exp(t/L)` (2 % tolerance);
  levels, fades, silences and lengths are exact; all six sample rates work;
  invalid settings are rejected.
* Sweep ⊛ inverse filter is a band-limited pulse with **unit in-band
  magnitude** (0 dB median over the normalisation band, analytic and
  spectral). The time-domain peak is about `2·bandwidth/fs` (~0.82 at
  48 kHz), not 1.0; everything outside ±2 ms is below −35 dB re that peak.
* Loopback recording → IR peak matches `reference_pulse()` at the expected
  index; delay and gain are recovered; too-short, silent and tail-less
  recordings raise clear errors; clipping is warned.
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
* Recording profiles: all seven profiles produce findings with measured
  evidence on a rich synthetic room; voiceover flags a weaker reflection than
  generic; vocal flags a decay that room_mic accepts; drums skips noise
  findings; each profile names its recording kind; CLI `--profile` selects
  the profile and rejects unknown names (added 2026-09-22).
* End-to-end: RT60 0.45 s, reflection 18 ms/−9 dB and noise −77 dBFS are
  recovered from a synthetic room; recordings at 44.1 and 96 kHz against a
  48 kHz sweep definition; stereo channel auto-selection and explicit
  selection; WAV-only reference (spectral inverse) and resampled reference;
  loudspeaker distortion (2nd/3rd order) leaves the linear IR clean; CLI
  round trip incl. JSON; session save/load/re-open (`load_measurement`,
  `roomscope show`, GUI File → Open and Home recent/browse); two synthetic
  positions compare with a validity on every decay delta and a noise delta
  that stays UNRELIABLE until `same_input_gain` is declared; `roomscope
  schema` matches the shipped files; the Tier 1 export list matches
  ARCHITECTURE_V1.md §5.1; a synthetic interface FIR is removed to within
  1.0 dB median in-band error; a room-like loopback is refused; Stop on
  the fake backend zeroes the next callback block; `roomscope --backend
  fake measure` completes a Standalone session; GUI DAW-mode, Demo and
  pick-two compare offscreen.
* macOS basic run: `roomscope sweep`, `roomscope analyze`,
  `roomscope devices` (12 Core Audio devices listed), the example script,
  and the GUI (offscreen) ran successfully. **Not run:** a real Standalone
  measurement through loudspeakers/microphone (needs a person in the room to
  set levels) and the on-screen GUI on a display.

**Not run:** no placement result has ever been checked against a real room
with a tape measure. Every placement figure in the test suite comes from
arrivals synthesised by the image-source construction, so the tests prove the
algebra and the refusals, not the acoustics of any real surface.

## Known limitations

* A single session is still at most ISO 3382-2 "survey" accuracy.
  `average_decay` means VALID T values across a project's positions and
  names the Table 1 class; those thresholds are a secondary-source
  transcription, not a purchased-standard verification. Decay curves are
  never averaged.
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
* The GUI is functional but plain. Session re-opening, a folder/recent
  list, a two-session comparison, Settings, Demo/Stop, a `project.json`
  folder view and a Placement tab (S5) are in. There is no large session
  database.

## Not implemented (by design for v0.1 or deferred)

VST3/AU/AAX plug-ins, room score, auto-EQ/correction, cloud/accounts, 3D
room modelling, absorption material calculators, dB SPL, room-mode
identification, phase display, a generated documentation site, signed
desktop installers. Unsigned bundle scaffolding exists (`release.yml`);
a person installing a frozen bundle on macOS/Windows is not claimed.

## Dependencies

Runtime: numpy 2.5.3, scipy 1.18.1, soundfile 0.14.0, sounddevice 0.5.6,
matplotlib 3.11.2; optional GUI extra `gui`: PySide6_Essentials 6.11.2
(Qt 6.11.2, LGPL; Addons not installed). Dev: pytest, pytest-cov, ruff,
mypy. Full table with licenses: DEPENDENCIES.md.

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

## Next recommended milestone (v1.0-rc)

0.4 exit criteria of [ARCHITECTURE_V1.md](ARCHITECTURE_V1.md) §10 that
can be proven without a signed installer are implemented on this
revision: gettext + zh-CN, self-contained sessions and bug-report
bundles, user settings, projects/averaging, CSV export, the user guide,
and the unsigned-bundle pipeline (license bundle with no unresolved
required package, GPL/ASIO gate, `release.yml` on `v*` tags). A person
installing a frozen bundle on macOS/Windows is **not** claimed here —
those artifacts are produced by the release workflow when the maintainer
pushes a tag. [HARDWARE_TESTS.md](HARDWARE_TESTS.md) is still empty.

The remaining MUST items are still 1.0-rc: API/schema freeze, the
validation campaign *executed* (M11 protocol is written), the hardware
matrix executed at least once per platform (M10), signed bundles or an
explicit maintainer decision (M9 remainder), SECURITY / CONTRIBUTING /
STATUS updated for the freeze, repository public (M13, maintainer),
pre-release on PyPI (the workflow job exists; publishing is maintainer).

Maintainer-only actions that this work does not do: public visibility flip,
a numbered GitHub Release, a license change, or rewriting published
history.
