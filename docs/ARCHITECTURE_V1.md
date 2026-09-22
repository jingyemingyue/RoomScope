# RoomScope v1.0 architecture (design): macOS, compatibility first

Status: **proposal, revised 2026-09-22** after the maintainer narrowed the
scope. v1.0 targets **macOS only**, must be a **practical small tool** (the
GUI stays plain), and must **first be compatible with every mainstream DAW
and with the audio hardware people actually own**. Windows and Linux move to
post-1.0; the core stays platform-neutral, so they remain a packaging job,
not a redesign.

[ARCHITECTURE.md](ARCHITECTURE.md) describes what exists (the v0.1
foundation). This document describes what v1.0 adds, what it freezes and what
it still refuses. Nothing below is implemented unless marked *(landed)* or
*(in PR #2)*. A Chinese digest is in
[ARCHITECTURE_V1.zh-CN.md](ARCHITECTURE_V1.zh-CN.md); the English text is
authoritative. Decisions only the project owner can take are marked
**maintainer decision** and collected in §15. The scope table in §3 is the
contract.

## 0. Summary

"Compatible with every DAW and every interface" cannot be assumed from the
WAV-in / WAV-out design; it has to be **proven per DAW and per device class,
and re-proven by the tool itself every time someone measures**. v1.0 is built
around that:

1. **The chain check.** `roomscope check` (and a *Check my setup* button)
   analyses an *electrical loopback* recording -- the sweep played by the DAW
   or by RoomScope and recorded through a cable back into the interface, no
   microphone -- and gives a PASS / FAIL verdict with the DAW-side or
   hardware-side cause of each failure (§5.4). It is how the DAW and
   hardware compatibility matrices are filled in (§5.5, §6.5) and how a user
   proves their own setup before measuring a room.
2. **Sweep integrity verification in the pipeline.** Every analysis estimates
   whether the recorded sweep was played at the wrong speed (a sample-rate
   mismatch), time-stretched (a DAW's warp / flex / elastic / musical mode),
   skewed by clock drift between two devices, played more than once, clipped
   or distorted, and refuses to report metrics instead of reporting wrong
   ones (§5.3). Detection only, never correction (§3.3).
3. **Every export format a DAW produces.** WAV in all its variants, BWF,
   RF64, AIFF / AIFC, CAF, FLAC, split-mono pairs, any channel count; lossy
   formats refused with a reason (§5.2).
4. **Core Audio done right.** The interface's current sample rate is the
   default and nothing changes a device's configuration without an explicit
   choice; separate input and output devices (USB measurement microphones)
   work and are drift-checked; aggregate devices are documented; a level
   check and a live input meter come before the first sweep; Stop silences
   the output at once (§6).
5. **Reopen, compare, keep.** Saved sessions reopen *(PR #2)*, two sessions
   compare with validity-aware deltas, session folders are self-contained
   and can be zipped for support (§7).
6. **A signed macOS app and a PyPI wheel**, built by a release workflow that
   also produces the license bundle the LGPL / FreeType / PortAudio
   obligations require (§8).
7. **Evidence before the number 1.0**: the DAW matrix, the hardware matrix,
   robustness tests for foreign files, and a real-room validation against a
   reference instrument are release gates (§9).

Everything the project brief forbade stays forbidden: no room score, no
auto-EQ, no plug-ins, no cloud, no accounts, no telemetry, no dB SPL without
a calibration, no room coordinates (§3.3).

## 1. Who v1.0 is for

| Audience | What v1.0 gives them | What they must never need |
| --- | --- | --- |
| Recording engineers, students, home recordists on a Mac | A signed `.app`; the four-step DAW workflow with a tested recipe for their DAW; Standalone Mode that works with their interface or USB microphone; a *Check my setup* verdict before the first real measurement; a comparison of two positions; a session folder they can send when asking for help; a guide in English and Chinese | Python, a terminal, an account, an internet connection, a calibrated microphone, a second computer |
| Integrators and researchers | `pip install roomscope`; a small public API with a stability promise; `result.json` / `session.json` / `comparison.json` with a documented versioning policy | Reverse engineering the JSON; importing private modules |
| Contributors | A package layout where DAW recipes, profiles and device reports can be added without touching the DSP; a CI that runs on macOS; matrices that say exactly what has been proven | A DSP background to add a recipe, a profile or a device report |

## 2. Principles

Unchanged from v0.1 and the brief: DAW-independent (WAV in, WAV out),
core-first (`roomscope.core` is pure NumPy/SciPy), scientific correctness
(published methods, validity flags), honest numbers (dBFS unless calibrated,
no score), legal clarity (no vendored code, audited dependencies), safety
(conservative levels, nothing touches system audio settings).

Added for v1.0:

* **Compatibility is proven, not assumed.** A DAW or a device class is
  "supported" only when its row in the matrix is green, with the version and
  date, and the tool re-checks the chain on every measurement.
* **Detect and refuse; never silently repair.** A recording that was
  resampled, stretched, skewed, clipped or distorted produces a verdict and
  advice, not corrected numbers.
* **Compatibility is a feature of the files too.** Every file written by any
  1.x version is readable by every later 1.x version; readers are lenient,
  writers are strict (§7.3).
* **A session is self-contained.** A session folder carries what is needed
  to re-analyse it and to report a bug (§7.4).
* **Offline by construction.** No network code in the package; CI fails if
  `socket`, `urllib`, `http`, `requests` or `ssl` are imported under `src/`.
* **Cancel is a safety control.** Anything that drives a loudspeaker can be
  stopped at once, and stopping silences the output before anything else.
* **Plain is fine.** The GUI is an engineering tool: every control has a
  label, every number a unit, every plot an axis. No visual design work is
  scheduled for 1.0.

## 3. Scope of v1.0

### 3.1 MUST (release blockers), in priority order

| # | Item | Why it blocks | Section |
| --- | --- | --- | --- |
| M1 | **DAW compatibility**: audio-format breadth; sweep integrity verification (speed, stretch, skew, passes, level, distortion); the chain check in DAW form; per-DAW recipes; the nine DAWs of the brief green in the compatibility matrix on macOS | The maintainer's first requirement; every wrong number RoomScope could print to a DAW user comes from one of these failure modes | §5 |
| M2 | **Hardware compatibility on macOS**: audio backend interface with Core Audio rules; device-rate default and no silent reconfiguration; separate input / output devices with drift detection; aggregate devices; USB measurement microphones; channel maps beyond 1–2; level check and live input meter; Stop; the chain check in Standalone form; the device classes of §6.1 green in the hardware matrix | The second requirement; Standalone Mode has never run on real hardware | §6 |
| M3 | Session re-opening and the session browser *(in PR #2)* | A tool that cannot show yesterday's measurement cannot compare positions | §7.1 |
| M4 | Comparison of two sessions (core, CLI, a plain GUI table) | The third product question of the brief: "did moving help?" | §7.2 |
| M5 | Format stability policy and a small public API | Integrators and the tool's own reopen / compare need to read what was written | §7.3 |
| M6 | Self-contained sessions and support bundles | Support by e-mail, not screen-share | §7.4 |
| M7 | macOS `.app` (arm64 and x86_64), notarized or an explicit maintainer decision; PyPI wheel; release workflow; license bundle; GPL-module gate | Nobody outside the project installs from git | §8 |
| M8 | User guide in English and Chinese with the per-DAW recipes and the hardware setups (aggregate device, USB microphone) | A signed binary without recipes produces wrong measurements | §8.4 |
| M9 | Quality gates: macOS in CI, robustness tests for foreign files, the two matrices executed, a real-room validation against a reference instrument | The methodology has only synthetic evidence today | §9 |
| M10 | Public-repository checklist executed *(maintainer decision)* | The release is open only if the repository is | §11 |

### 3.2 SHOULD (planned; a slip does not block 1.0)

| # | Item | Section |
| --- | --- | --- |
| S1 | Two-channel loopback compensation (microphone + loopback in one recording): removes the interface response and bounds the loudspeaker distance | §7.5 |
| S2 | Demo mode on the fake backend (the backend itself is MUST for CI) | §6.2 |
| S3 | `roomscope analyze-ir`: analyse an impulse response from another tool | §7.7 |
| S4 | JSON Schema files shipped with the package (the policy in §7.3 is MUST; the files are not) | §7.3 |
| S5 | Simplified Chinese for interpretation findings and the GUI through gettext (the guide in Chinese is MUST) | §7.6 |
| S6 | CSV export of curves | §7.7 |
| S7 | Placement tab in the GUI | §7.6 |

### 3.3 Not in 1.0 (by design, or deferred with a stated reason)

* **Windows and Linux.** Post-1.0 packaging work. Nothing in `core`,
  `models`, `io`, `cli` or `interpretation` is macOS-specific; only
  `audio/coreaudio_rules.py`, the bundle recipe and the hardware matrix are.
* **Correction of speed, stretch or drift.** RoomScope estimates them to
  refuse a measurement (§5.3). Correcting a sampling-frequency offset between
  separate, unsynchronised devices and then computing acoustic parameters is
  the subject of an in-force patent (US 10,816,391 B2,
  MEASUREMENT_METHODOLOGY.md §10); a correction feature would need a claim
  review first and is not planned.
* **Automatic two-sweep pass-band schemes** (US 9,959,883 B2). One sweep.
* **Plug-ins (VST3 / AU / AAX).** Not needed for DAW independence and
  legally different (VST3 SDK dual-licensed GPLv3 / proprietary; AAX needs
  an Avid agreement). A later shell must talk to the Apache-2.0 core across
  a process boundary that does not exist yet.
* **dB SPL.** The calibration slot in the models is reserved; no workflow in
  1.0. USB measurement microphones ship calibration files that would make
  this cheap later, which is why the slot exists.
* **Multi-position averaging and multi-position placement, projects,
  exporter and profile plug-in entry points, internationalisation of the
  core's diagnostics.** Useful, not needed for a practical 1.0.
* **Room score, auto-EQ, room-mode identification, 3D models, absorption
  calculators, cloud, accounts, telemetry, update checks.** Unchanged.

## 4. Target package layout

Additions are marked `+`, changed modules `~`; everything unmarked stays as in
v0.1. `roomscope.core` keeps its single entry point `pipeline.analyze` and
gains two pure modules (`integrity`, `compare`); the chain check is a
function over an `AnalysisResult`, so it is pure as well.

```
src/roomscope/
  __init__.py            ~ version + lazy re-exports of the public API (§7.3)
  __main__.py            + `python -m roomscope` (used by the .app launcher)
  errors.py                exception hierarchy (unchanged)
  logging_config.py      ~ also a rotating log file under ROOMSCOPE_HOME for bug reports
  models/
    audio.py             ~ AudioSignal + file metadata (format, subtype, channels)
    configuration.py     ~ AnalysisSettings + loopback_channel (S1), calibration slot
    result.py            ~ + SweepIntegrity, ChainCheck, LoopbackResult (S1); roomscope_version;
                           from_dict (in PR #2)
    result_load.py         (in PR #2)
    comparison.py        + ComparisonResult, MetricDelta, ReflectionMatch
    session.py           ~ + recording_profile (PR #2), roomscope_version, daw (name, version),
                           device names; lenient from_dict
  core/
    sweep.py, deconvolution.py, impulse.py, filters.py, decay.py,
    frequency_response.py, noise.py, linearity.py, reflections.py,
    placement.py, resonance.py                            (unchanged)
    integrity.py         + sweep trajectory fit (speed / stretch), pulse compactness (skew)
    chain_check.py       + PASS / FAIL verdict over an AnalysisResult of a loopback recording
    compare.py           + validity-aware comparison of two results
    loopback.py          + reference-channel validation and compensation (S1)
    pipeline.py          ~ analyze(): integrity step; analyze_impulse_response() (S3)
  io/
    wav.py               ~ read_audio(): WAV/BWF/RF64/AIFF/AIFC/CAF/FLAC, split-mono pairs,
                           lossy refused; write unchanged
    session_store.py     ~ copy_recording, bundle(), chain_check.json; list_sessions (PR #2)
    recent.py              (in PR #2)
  audio/
    backend.py           + AudioBackend protocol, DeviceInfo (+ current rate, transport hints)
    portaudio.py         ~ today's devices.py + playrec.py as a callback stream: progress,
                           cancel, multi-channel input, input-only metering stream
    coreaudio_rules.py   + macOS policy: device-rate default, reconfiguration opt-in,
                           aggregate / separate-device advice, permission hints
    fake.py              + synthetic-room backend for CI (and the demo mode, S2)
  interpretation/
    interpreter.py       ~ Finding unchanged; interpret_comparison(); chain-check advice texts
    profiles.py          ~ RecordingProfile + interpret_comparison
  cli/
    main.py              ~ + check, compare, session bundle, --format, --copy-recording
    report.py            ~ integrity and chain-check sections; comparison report
  ui/
    app.py, main_window.py, pages.py, results.py, plots.py, workers.py, state.py, qt.py
    browser.py             (in PR #2)
    check_page.py        + "Check my setup" (DAW form and Standalone form)
    compare_view.py      + two sessions side by side (a table and one difference plot)
docs/
  DAW_COMPATIBILITY.md   + the matrix (nine DAWs x macOS): version, date, recipe, verdict
  HARDWARE_TESTS.md      + the matrix (device classes): interface, date, verdict
  user-guide/            + EN + zh-CN: install, per-DAW recipes, hardware setups, reading results
```

Dependency direction (arrows point at what may be imported):

```
ui / cli ──▶ interpretation ──▶ models ◀── core
   │              │                          ▲
   ├──▶ io ───────┴──────────────────────────┘
   └──▶ audio (backend protocol; portaudio / coreaudio_rules only when a backend is requested)
```

`core` never imports `io`, `audio`, `ui` or `cli`; every string it produces
stays English and is stored verbatim in `result.json`. `models` imports only
`errors`. Nothing outside `audio/coreaudio_rules.py` and the bundle recipe
knows it is on macOS.

## 5. DAW compatibility (M1)

### 5.1 What goes wrong between "import the WAV" and "export the recording"

RoomScope never talks to a DAW, so DAW compatibility is the set of things a
DAW can do to the sweep or to the recording on the way through. Each row is a
failure mode, its symptom in the recording, how RoomScope detects it, and the
advice it gives. The detection column is what §5.3 and §5.4 implement; the
advice column is what the per-DAW recipes (§5.5) prevent.

| Failure mode (where it hides) | Symptom in the recording | Detection | Advice |
| --- | --- | --- | --- |
| Sample-rate conversion on import or export at another rate (most DAWs ask; some convert silently) | Frequencies and duration both scaled by the rate ratio (e.g. 8.8 % for 44.1 ↔ 48 kHz) | Sweep trajectory fit: speed factor ≠ 1 | The sidecar regenerates the reference at the *recording's* rate, so a clean conversion is fine; a wrong-speed playback is refused with the ratio and the two rates |
| Tempo-following clips: warp / flex / elastic audio / musical mode / stretch mode, often on by default for long clips | Duration scaled, frequencies unchanged; the deconvolved pulse becomes a chirp | Trajectory fit: stretch factor ≠ 1; pulse compactness | Turn the clip's warp / stretch mode off, re-export |
| Clock drift between two devices (USB microphone + interface, or two interfaces) | Pulse smeared at high frequencies (Farina 2007 §3.4) | Pulse compactness below the ideal; small speed factor | Use one interface, or an aggregate device with drift correction (§6.1); measure again |
| Loop / repeated playback, count-in, a second take in the same file | Several sweep passes | `sweep_passes` *(landed)* | Record one pass; RoomScope analyses the strongest and says so |
| Plug-ins in the playback or monitoring path: limiter on the master bus, saturation, room-correction software, monitor controllers with loudness compensation | Harmonic distortion; frequency-response deviations; aliased products from digital clipping | Harmonic and aliased distortion indicators *(landed)*; the chain check's flatness criterion (§5.4) | Bypass every plug-in on the sweep track, the master bus and the monitor path for the measurement |
| Clipping in the DAW, the export, or the converter | Flat-topped peaks, possibly below full scale after a gain change | `ClippingCheck` *(landed)* | Lower the level, re-export without normalisation |
| Export with a different file format, bit depth, channel layout or as split-mono files | Unreadable or half-read file | `read_audio` breadth (§5.2) | Any format in §5.2 works; lossy formats are refused with the reason |
| Stereo export with the microphone on one side, or a stem with silent channels | Only one useful channel | Channel auto-selection *(landed)*, explicit `--channel` | Explicit selection in the GUI |
| Dither or noise shaping on export | Raised noise floor at high frequencies | Noise analysis notes it | Export 24-bit or 32-bit float without dither |
| Recording started after the sweep began (input monitoring, punch-in) | Missing low frequencies | Recording-start check *(landed)* | Start the recording first; the file begins with silence for this purpose |
| Recording delay compensation, latency offsets | Constant time shift | Harmless: whole-recording deconvolution is shift-invariant *(landed)* | None |
| Playback through Bluetooth or a lossy codec path | Band-limited response, codec nonlinearity | Chain check FAIL on flatness and distortion | Use a wired interface |
| Automatic gain, "voice isolation" or noise reduction on a built-in microphone | Time-varying gain, gated tail | Decay non-linearity and curvature flags; chain check | Use an interface or a USB measurement microphone |

### 5.2 Audio-format breadth

`io.wav.read_wav` becomes `read_audio` (the old name stays as an alias for
one minor release). Through libsndfile (already the reader) it accepts WAV
in every variant a DAW writes (PCM 16 / 24 / 32, float 32 / 64,
`WAVE_FORMAT_EXTENSIBLE`, BWF with `bext`, RF64 for exports over 4 GB),
AIFF / AIFC, CAF, FLAC, and any channel count. Split-mono pairs
(`take.L.wav` + `take.R.wav`, one DAW's default) are accepted as a list and
combined; RoomScope then treats them as one two-channel recording. Files in
lossy formats (MP3, AAC, Opus, Ogg Vorbis) are refused with the sentence
"lossy formats destroy the sweep; export PCM or float". Odd sample rates that
the sweep cannot be regenerated at (§ `SUPPORTED_SAMPLE_RATES`) are refused
naming the rate and the six supported ones. The `AudioSignal` gains file
metadata (container, subtype, channel count, duration) that the session
records, so a bug report says what the DAW exported.

A robustness test set (§9.2) holds one small file per format and per
variant, plus truncated, empty, silent and NaN cases.

### 5.3 Sweep integrity verification (`core/integrity.py`)

Runs inside `analyze` on every recording whose sweep definition is known
(a reference WAV without a sidecar gets the pass, clipping and distortion
checks only, and says so). Pure NumPy/SciPy, clean-room from the ESS
definition; detection only.

*Trajectory fit.* Over the located sweep, minus its faded ends, the
instantaneous frequency is tracked as the STFT ridge (peak bin per frame with
parabolic interpolation, frames long enough to resolve the lowest excited
frequency). The ESS has `f(t) = f1 · exp(t / L)`; a playback-speed factor
`r` (a rate mismatch) scales both frequency and time, a stretch factor `s`
(a tempo-following clip) scales time only:
`f(t) = r · f1 · exp(r · t / (s · L))`. A least-squares fit of `ln f` against
`t` gives `a = ln(r · f1)` and `b = r / (s · L)`, hence `r = exp(a) / f1` and
`s = r / (b · L)`. Octave errors of the ridge are rejected with a
median-based fit before the least squares. Both factors, their fit residual
and the frame count go into `SweepIntegrity`.

*Pulse compactness.* The fraction of the deconvolved direct sound's energy
inside ±0.5 ms of its peak, compared with the same fraction for
`reference_pulse(settings)` (the ideal band-limited pulse the tests already
use). Drift between two clocks and small stretches spread the pulse before
the trajectory fit can see them.

*Verdict inside the pipeline.* `|r − 1|` or `|s − 1|` above the tolerance
(starting point 0.1 %, to be tuned on the matrices and then documented in
MEASUREMENT_METHODOLOGY.md §2a), or a compactness below the tolerance, marks
every decay, response, reflection, resonance and placement metric UNRELIABLE
with one sentence naming the cause class and the fix, exactly as clipping and
aliased distortion do today (`_decay_unreliable_reasons`). The result carries
`impulse_response.integrity` with the numbers, so the report can say
"time-stretched by 3.2 %" rather than "unreliable".

*What it is not.* No resampling, no time-warping, no drift correction: the
estimated factors are used to refuse and to explain. That keeps RoomScope
outside US 10,816,391 B2 by construction (§3.3).

### 5.4 The chain check (`core/chain_check.py`, `roomscope check`)

An **electrical loopback** -- the sweep played by the DAW (DAW form) or by
RoomScope (Standalone form, §6) and recorded through a cable or the
interface's own loopback back into an input, no loudspeaker, no microphone
-- goes through the ordinary `analyze` and then through
`check_chain(result, settings) -> ChainCheck`. Criteria, each with its
tolerance in `CheckSettings` (starting points; final values fixed on the
matrices and documented):

| # | Criterion | Starting tolerance | Failure names |
| --- | --- | --- | --- |
| 1 | The reference sweep was found, once | one pass | "n passes: record a single pass" |
| 2 | Speed factor | ±0.05 % | "played at the wrong speed by x %: the file was resampled or the project rate differs" |
| 3 | Stretch factor | ±0.05 % | "time-stretched by x %: warp / flex / elastic / musical mode is on for the clip" |
| 4 | Pulse compactness | ≥ 0.9 × ideal | "the pulse is smeared: two clocks (USB microphone + interface?) -- use one interface or an aggregate device" |
| 5 | Clipping | none | "clipped at x dBFS: lower the level, export without normalisation" |
| 6 | Harmonics k = 2…5 re direct | ≤ −50 dB | "harmonic k at x dB: a limiter, saturator or clipping plug-in is in the playback path" |
| 7 | Aliased distortion | not significant | "digital clipping before the converter" |
| 8 | Frequency-response flatness inside the excitation band after 1/6-octave smoothing, outer 1/3 octave at each end excluded | within ±1.0 dB of the median | "response deviates x dB at f Hz: an EQ, a room-correction plug-in or a monitor controller is in the path" |
| 9 | Peak level | −40 … −1 dBFS | "too quiet / too hot" |
| 10 | Direct-sound confidence | high | "the sweep is not clean: check routing" |
| 11 | Loop noise floor | ≤ −70 dBFS (warning only) | "noisy loop: input gain high or an analogue path with noise" |

Verdict: PASS, PASS with warnings, or FAIL with the failing criteria and
their advice, printed as a checklist and stored as `chain_check.json` with
the DAW name and version (DAW form) or the device names (Standalone form).
The GUI's *Check my setup* page runs the same function and shows the same
checklist; nothing is judged in the UI.

Why an electrical loop: it removes the room and the loudspeaker, so every
remaining defect belongs to the DAW, the export or the interface, and the
expected result is known exactly (a flat 0 dB response and one pulse). It is
also cheap: one cable, no microphone, a minute.

### 5.5 Per-DAW recipes and the compatibility matrix

`docs/DAW_COMPATIBILITY.md` has one row per DAW of the brief -- Cubase /
Nuendo, Pro Tools, Logic Pro, Studio One, Ableton Live, REAPER, FL Studio,
Bitwig Studio, Digital Performer -- with: DAW version, macOS version, date,
the export format used, the chain-check verdict, and a link to the recipe.
A recipe (in `docs/user-guide/daw/<name>.md`, English and Chinese) is
written only *while* the row is being tested and says, for that DAW: how to
import without conversion or with the DAW's converter; where its
tempo-following mode lives and how to switch it off for the clip; how to
route the track to the interface output and record the input; how to export
one track as PCM 24-bit or float without normalisation or dither; which
plug-ins and monitor tools to bypass. A row without a green verdict is
listed as **untested**, never as supported.

Every matrix run keeps its loopback recording (a few seconds, small) as a
fixture under `tests/fixtures/daw/<name>/` with the DAW version in a README,
so that the integrity and chain-check code has a real file per DAW as a
regression test. Community rows (other versions, other DAWs) are accepted
through the measurement issue template with the session bundle attached.

**Exit criterion for M1:** nine green rows on the current macOS, each with
a recipe, a fixture and a date.

## 6. Hardware compatibility on macOS (M2)

### 6.1 Device classes

| Class | Examples people own | What RoomScope must handle | Guide section |
| --- | --- | --- | --- |
| Built-in output and microphone | every Mac | Works for a first try; the built-in microphone on recent Macs is processed by the system (see §5.1, last row) so the guide says what it is good for (a level check, not a measurement) | "Before you buy anything" |
| Class-compliant USB interfaces | 2-in / 2-out desktop interfaces | The common case: one device, one clock, channels 1–2; the device's current rate | "One interface" |
| Multi-channel USB / Thunderbolt interfaces | 8+ inputs, ADAT, dedicated drivers | Channel maps beyond 1–2, device names that differ between the driver's devices, rates up to 192 kHz | "Choosing channels" |
| USB measurement microphones | the calibrated USB microphone many home users have | Input device ≠ output device: two clocks; drift detection (§5.3); the aggregate-device setup with drift correction; the microphone's calibration file is not read in 1.0 (§3.3) | "USB microphone + interface" |
| Aggregate devices (Audio MIDI Setup) | any combination | Appear as one Core Audio device; RoomScope treats them like an interface and the guide explains the drift-correction checkbox | "Aggregate device" |
| Bluetooth and other codec paths | headphones, speakers | Not supported for measurement; the chain check fails them with a reason; the device list shows a hint when the name or transport suggests Bluetooth | "What not to use" |

**Exit criterion for M2:** `docs/HARDWARE_TESTS.md` has a green chain-check
row (Standalone form) and one complete Standalone measurement for at least
one device of each class except Bluetooth, at 44.1 and 48 kHz, plus one at
96 kHz, with the interface model, macOS version and date.

### 6.2 Audio backend protocol and Core Audio rules

```python
class AudioBackend(Protocol):
    name: str
    def list_devices(self) -> list[DeviceInfo]: ...          # + current_sample_rate, hints
    def check_sample_rate(self, device: int, sample_rate: int, *, kind: str) -> None: ...
    def play_and_record(
        self, playback: FloatArray, sample_rate: int, *,
        input_device: int | None, output_device: int | None,
        input_channels: Sequence[int],          # 1-based; [mic] or [mic, loopback]
        output_channel: int, level_dbfs: float, extra_record_s: float = 0.0,
        progress: Callable[[float], None] | None = None,
        cancel: threading.Event | None = None,
    ) -> AudioSignal: ...                       # shape (n, len(input_channels))
    def monitor_input(
        self, input_device: int | None, input_channels: Sequence[int], sample_rate: int,
        on_level: Callable[[Sequence[float]], None], stop: threading.Event,
    ) -> None: ...                              # input-only stream for the live meter
```

* **`portaudio`** keeps sounddevice / PortAudio but replaces the blocking
  `sd.playrec` with a callback `Stream`, so that `cancel` zeroes the output
  in the next callback and closes the stream, `progress` reports the played
  fraction, and several input channels can be captured at once. Levels, the
  −12 dBFS acknowledgement and the safety message are unchanged.
* **`fake`** synthesises a room (the `make_rir` family from
  `tests/conftest.py` moves to `audio/fake.py`) and honours `cancel` and
  `progress`. It backs the Standalone tests in CI on every runner and the
  demo mode (S2).
* **Core Audio rules (`audio/coreaudio_rules.py`, the only macOS-aware
  module):**
  1. The **default sample rate for a measurement is the output device's
     current nominal rate**, and the sweep is regenerated at it (the sweep
     is parametric, so this costs nothing). When the input device's rate
     differs, the GUI and CLI say so before anything plays.
  2. **No device is reconfigured silently.** PortAudio's Core Audio host
     API can switch a device's nominal rate to match a stream; RoomScope
     asks for another rate only when the user picked one explicitly and
     shows "the interface will be switched to 96 kHz for this measurement"
     first. The PortAudio stream flags that control this (`paMacCore…`)
     are verified during implementation and the finding recorded in
     HARDWARE_TESTS.md.
  3. **Separate input and output devices are allowed** (the USB-microphone
     case) with a note that two clocks are involved; the chain check and
     the integrity step decide whether the result is usable; the guide
     recommends the aggregate device with drift correction.
  4. **Channel maps** are 1-based and shown with the device's channel count;
     a channel outside the device's range is refused before the stream
     opens.
  5. **Hints, not decisions:** device names containing "Aggregate",
     "AirPods" or a Bluetooth transport get a hint next to them; nothing is
     hidden or disabled.

### 6.3 Level check and live input meter

Before the first sweep the Standalone page shows a **live input meter**
(peak and RMS in dBFS, updated a few times a second through
`monitor_input`) so the microphone gain can be set without playing anything,
and a **level check** button that plays 0.5 s of the sweep's own band-limited
noise at the chosen level (−20 dBFS by default) and reports the recorded
peak: below −40 dBFS "raise the gain or the level", above −3 dBFS "lower
it", otherwise "ready". Both are UI conveniences over the backend; nothing
is stored and nothing is judged as a room metric. A **Stop** button is
present during the check and the measurement (§2).

### 6.4 Microphone permission and where the app may write

macOS asks for microphone access per application. The `.app` carries
`NSMicrophoneUsageDescription` (§8.1); a user running `roomscope` from a
terminal is asked on behalf of the terminal application, and the guide says
so, because a silently empty recording is the symptom. RoomScope writes only
into the folders the user chose and into `ROOMSCOPE_HOME` (default
`~/.roomscope`, introduced by PR #2), which holds the recent list, the log
file and, later, settings.

### 6.5 Hardware matrix

`docs/HARDWARE_TESTS.md`: one row per tested device -- class (§6.1), model,
driver or class-compliant, macOS version, RoomScope version, rates tested,
channels tested, chain-check verdict (Standalone form), whether Stop
silenced within one callback period, and whether a full Standalone
measurement completed. Filled by hand, dated, with the person who ran it.
Community rows arrive through the issue template with the bundle attached.

## 7. The rest of the product

### 7.1 Reopen and browse (M3, in PR #2)

PR #2 lands `AnalysisResult.from_dict`, `load_measurement`,
`list_sessions`, a recent list under `ROOMSCOPE_HOME`, `roomscope show`, and
*Open Session* / *Browse Folder* in the GUI. This design builds on it and
changes nothing in it; the session gains a few fields (§7.3) and the
browser gains a "compare with…" action (§7.2).

### 7.2 Compare two sessions (M4)

`compare(baseline, candidate, *, settings=None) -> ComparisonResult` in
`core/compare.py`: pure, validity-aware, symmetric in what it refuses.

| Section | Rule | Output |
| --- | --- | --- |
| Comparability | Common excitation band = the intersection; refused when narrower than one octave. Both results must have passed the integrity step (§5.3); sample rates may differ | `comparable`, `common_band`, `notes` |
| Decay (broadband and per band) | A delta only when *both* metrics are VALID, else `NOT_COMPARABLE` with both reasons; delta in seconds and in percent. The report quotes the just-noticeable difference for T that ISO 3382-1 gives (about 5 %; clause to be verified against the standard text, like the other clause references) and never calls a change "significant" on its own | `MetricDelta` |
| Frequency response | Both smoothed curves on a shared logarithmic grid inside the common band, the coarser smoothing of the two; difference curve and the mean absolute difference per octave band | `difference_db`, `band_mad_db` |
| Early reflections | Matched by delay within ±0.5 ms; level delta for matches; unmatched listed as appeared / disappeared; needs high direct-sound confidence on both sides | `ReflectionMatch` list |
| Noise | VALID only if both have a verified quiet segment *and* the user declares the input gain unchanged (`CompareSettings.same_input_gain`); otherwise UNRELIABLE with "gain not declared equal" | `MetricDelta` per band |
| Resonances | Matched within 1/6 octave | `ResonanceMatch` list |
| Placement | Tier-2 heights when both present | `MetricDelta` |

Interpretation: `RecordingProfile.interpret_comparison` with a shared
implementation in `ProfileBase` that reuses each profile's own thresholds.
CLI `roomscope compare <baseline> <candidate>`; GUI: a plain two-column
table with the delta and its validity, one difference plot, and the
"input gain unchanged" checkbox. Stored as `comparison.json`.

### 7.3 Format stability and the public API (M5, S4)

* **Versioning.** Each JSON file carries an integer `schema_version`, bumped
  only for a change a 1.0 reader could misinterpret (a renamed key, a
  changed unit or time origin). Adding an optional key is not a bump; all
  v1.0 files stay schema 1 unless the release-candidate audit finds a v0.1
  key whose meaning changed.
* **Readers lenient, writers strict.** `MeasurementSession.from_dict` today
  refuses unknown fields; in v1.0 every `from_dict` ignores unknown keys
  (logged at INFO), refuses only a *higher* `schema_version` naming the
  RoomScope version that can read it, and applies migrations for lower
  ones. Writers are checked in the test suite by round-trip tests; JSON
  Schema files (S4) add machine-readable validation when they exist
  (`jsonschema`, MIT, tests only).
* **New keys.** `result.json`: `roomscope_version`,
  `impulse_response.integrity`, `impulse_response.loopback` (S1);
  `session.json`: `recording_profile` *(PR #2)*, `roomscope_version`,
  `platform`, `daw` (name, version, free text), `input_device`,
  `output_device`, `audio_file` metadata; new files `chain_check.json`,
  `comparison.json`. Findings are not stored: loading a session re-runs
  `interpret` with the stored profile and the running version, and the
  report names both.
* **Public API.** `roomscope/__init__.py` re-exports, lazily so that
  `import roomscope` stays cheap: `__version__`, `analyze`, `Reference`,
  `compare`, `check_chain`, `SweepSettings`, `AnalysisSettings`,
  `AnalysisResult` and its sub-results, `Validity`, `SweepIntegrity`,
  `ChainCheck`, `ComparisonResult`, `MeasurementSession`, `interpret`,
  `interpret_comparison`, `Finding`, `Severity`, `available_profiles`,
  `read_audio`, `write_wav`, `write_sweep_file`, `load_reference`,
  `save_measurement`, `load_measurement`, `load_session`, `list_sessions`,
  and the `RoomScopeError` hierarchy. These names and the JSON files follow
  semantic versioning for the 1.x line; a deprecation is announced with a
  `DeprecationWarning` one minor release before the change. Everything in
  `roomscope.core.*` beyond these is documented (MEASUREMENT_METHODOLOGY.md)
  and may gain keyword parameters; `ui` and `cli` internals are private.
  The text report is not an interface. A test keeps the export list and
  this paragraph in step; another proves `__version__` equals the
  `pyproject.toml` version.

### 7.4 Self-contained sessions and support bundles (M6)

```
<session>/
  session.json  result.json  impulse_response.wav           (as today)
  sweep.roomscope-sweep.json      always copied (tiny; makes the session re-analysable)
  recording.wav                   copied with --copy-recording; GUI default on
  chain_check.json                when the session was a chain check
```

`roomscope session bundle <session> [--no-audio]` zips the folder for a bug
report; `--no-audio` leaves the WAVs out for people who do not want to share
a recording of their room. The measurement issue template asks for the
bundle and says what it contains. Paths stay relative inside the folder, so
a folder moved as a whole keeps working.

### 7.5 Two-channel loopback compensation (S1)

With the microphone and an electrical loopback recorded together (a
two-channel export, or `input_channels=[mic, loopback]` in Standalone Mode),
`core/loopback.py` first validates the loopback with the chain-check
criteria of §5.4 (it must be an electrical pulse; a channel that decays like
a room is refused with a note and the analysis continues uncompensated),
then divides the interface response out inside the excitation band with the
regularised inverse the project already uses for reference WAVs
(`design_spectral_inverse`), and takes the loopback peak as the electrical
time zero: `path_delay_ms` and `distance_upper_bound_m = c · path_delay`
are reported as a **bound** (loudspeaker DSP latency only adds delay), and a
tape-measured `placement_distance_m` above the bound marks the placement
unreliable. No drift estimation between devices (same converter clock);
the loudspeaker's own response is not removed and the result says so.
Result model: `ImpulseResponseResult.loopback: LoopbackResult`.

### 7.6 GUI: plain, and what changes

Kept: PySide6 Essentials (LGPL) with matplotlib plots; QtCharts and every
GPL-only Qt module stay banned (§8.2 adds an automated check). No visual
design work. Changes, all functional:

* **Home:** New Measurement (two modes), *Check my setup*, Open Session,
  Browse Folder, recent sessions *(PR #2)*, Demo (S2).
* **Check my setup page:** DAW form (pick the loopback recording and the
  sweep, choose the DAW from the matrix list or type it) and Standalone
  form (pick devices, run); the checklist of §5.4 with the advice text.
* **Standalone page:** device list with current rate and channel counts;
  the rate defaults to the output device's; live input meter, level check,
  progress bar and Stop (§6.3); the "two clocks" note when input and output
  devices differ; an "also record loopback on channel n" option (S1).
* **DAW page:** the recipe link for the chosen DAW; the DAW name and version
  fields feed `session.json`; a file picker that accepts every format of
  §5.2 and split-mono pairs.
* **Results:** the six tabs of today; an *Integrity* line at the top of the
  overview (speed, stretch, compactness, passes, verdict); Placement tab
  (S7); the interface response on the response tab when a loopback was
  used (S1). Core diagnostics appear verbatim in English.
* **Compare:** §7.2.
* Keyboard navigation for every action, high-DPI scaling and the system
  dark mode come from Qt; plots never encode information in colour alone.
* Language: English UI in 1.0; Simplified Chinese for findings and the GUI
  through gettext is S5 (the *guide* in Chinese is M8).

### 7.7 CLI

| Command | Purpose | Status |
| --- | --- | --- |
| `sweep`, `analyze`, `devices`, `measure`, `gui` | as today | landed |
| `show <session>` / `show --list <folder>` | print / list stored sessions | in PR #2 |
| `check --recording <file> --sweep <file> [--daw "<name> <version>"]` | chain check, DAW form | M1 |
| `check --standalone --input-device n --output-device m [--input-channel k --output-channel j] [--sample-rate r]` | chain check, Standalone form | M2 |
| `compare <baseline> <candidate> [--out] [--same-input-gain]` | comparison | M4 |
| `session bundle <session> [--no-audio]` | zip for bug reports | M6 |
| `analyze-ir --ir <file> [--band lo hi]` | impulse response from another tool | S3 |
| `export <session> --format csv [--out]` | curves and tables | S6 |
| global `--format text\|json`, `--copy-recording`, `--backend <name>` | | M5, M6, M2 |

`analyze` and `measure` accept every format of §5.2 and split-mono pairs
(`--recording a.L.wav a.R.wav`). Exit codes: 0 success; 1 a
`RoomScopeError`; 2 usage error or a safety refusal; 3 a chain-check FAIL
(so scripts can gate on it); 130 interrupted. `--format json` writes exactly
the `result.json` payload plus `findings` to stdout, diagnostics to stderr;
`--json` stays as an alias for one minor release.

## 8. Distribution (M7)

### 8.1 The macOS app

* **Tool:** PyInstaller in one-directory mode producing `RoomScope.app`,
  shipped in a `.dmg` (`hdiutil`, no extra tool). One-directory keeps Qt,
  libsndfile and libquadmath as separate, replaceable shared libraries,
  which is what the LGPL obligations in DEPENDENCIES.md §3 require.
* **Architectures:** arm64 and x86_64 as two bundles (NumPy and SciPy do
  not ship universal2 wheels); the x86_64 bundle runs under Rosetta as a
  fallback. Minimum macOS: the oldest version the current PySide6 wheels
  support, stated in the README at release time.
* **`Info.plist`:** `CFBundleIdentifier`, `LSMinimumSystemVersion`,
  `NSMicrophoneUsageDescription` (without it the microphone is denied
  silently), high-resolution capable.
* **Signing:** hardened runtime, the `com.apple.security.device.audio-input`
  entitlement, Developer ID signing and notarization with `notarytool`. The
  identity is the maintainer's (**maintainer decision**, §15). Until it
  exists, bundles are published as *unsigned* with the Gatekeeper steps in
  the guide, and 1.0 is not called 1.0 without notarization or an explicit
  decision to ship unsigned.
* **Launch:** the app runs `roomscope gui`; the same bundle exposes
  `RoomScope.app/Contents/MacOS/roomscope` for the CLI, documented for
  people who want the commands without Python.

### 8.2 Bundle gates (CI, blocking)

The built bundle must contain no GPL-only Qt module (an allow-list of
`QtCore`, `QtGui`, `QtWidgets` and their plugins; anything else fails the
job), and a `THIRD_PARTY_LICENSES/` directory produced by
`scripts/build_license_bundle.py`, which extends today's
`scripts/dependency_licenses.py`: license texts of every bundled wheel, the
LGPL-3.0 and GPL-3.0 texts with the Qt and PySide6 source pointers, the Qt
third-party attributions for the Essentials modules, the FreeType credit,
the PortAudio license (not in the wheel), the Qhull and Agg notices. The
About dialog links to that directory. The UNKNOWN / NEEDS REVIEW items of
DEPENDENCIES.md §6 that concern macOS wheels (matplotlib's `ttconv`) are
resolved before the first bundle ships; the script fails the job on any
package whose license file it cannot find. Bundles are built from a lock
file (`requirements/bundle.lock`) so a tag can be rebuilt; the library keeps
its version ranges. Every bundle is launched on the runner
(`roomscope --version`, the synthetic example, the GUI offscreen) before it
is attached to a release.

### 8.3 PyPI and the release workflow

* Project name `roomscope` (free on PyPI on 2026-09-22; registering it and
  enabling trusted publishing is a **maintainer decision**). Pure-Python
  wheel and sdist as today's `package` job builds them; `pipx install
  "roomscope[gui]"` documented for people who have Python; a
  `[project.gui-scripts]` entry for a console-less launcher.
* `release.yml` on a `v*` tag pushed by the maintainer: lint, tests on
  Ubuntu and macOS (§9.1) → sdist and wheel → PyPI through trusted
  publishing to a GitHub environment that needs the maintainer's approval
  (release candidates go to PyPI as pre-releases) → the two macOS bundles
  → gates and smoke tests → `SHA256SUMS`, a CycloneDX SBOM (`cyclonedx-bom`,
  Apache-2.0, to be recorded in DEPENDENCIES.md), `THIRD_PARTY_LICENSES.zip`
  → a **draft** GitHub Release with the CHANGELOG section as its body; the
  maintainer publishes it.
* `pyproject.toml` is the single version source; `roomscope.__version__`
  reads package metadata; a test proves they agree.

### 8.4 User guide (M8)

`docs/user-guide/` in Markdown, English and Simplified Chinese: install
(app, pipx), the DAW workflow with the per-DAW recipes (§5.5), the hardware
setups of §6.1 (one interface; USB microphone + interface with the aggregate
device; what not to use), *Check my setup* before the first room, reading
each result tab (what a validity flag means, why there is no score),
comparing two positions, troubleshooting by symptom (each row of §5.1 has an
entry), and how to send a bundle. GitHub renders it; a generated site is
post-1.0.

## 9. Quality gates (M9)

### 9.1 CI

* `lint` (Ubuntu): ruff, ruff format, mypy strict, the no-network import
  gate (§2), the public-API list test, the version test, a link check on
  `docs/`.
* `test`: Ubuntu on Python 3.12 and 3.13 as today (cheap, catches most
  regressions), and **macOS on arm64 and x86_64 runners on Python 3.12** for
  every push and pull request, including the GUI smoke tests offscreen and
  the Standalone flow on the fake backend. macOS is the release platform,
  so it is not optional in CI.
* `robustness`: the file set of §9.2.
* `package`: as today, plus an install of the wheel into a clean
  environment.
* `bundle` (macOS, on `main` and tags): §8.2.

### 9.2 Test tiers

| Tier | Where | Evidence |
| --- | --- | --- |
| Unit, synthetic | `tests/unit` | Formulas, refusals, the trajectory fit recovering known speed and stretch factors, compactness of ideal and skewed pulses, chain-check criteria on synthetic loops |
| Integration, synthetic | `tests/integration` | Round trips; a resampled, a stretched and a drifted synthetic recording each refused with the right cause; comparison of two synthetic positions; loopback compensation of a synthetic interface response (S1) |
| GUI offscreen | `tests/ui` | Flows build and run: check page, compare view, Stop on the fake backend |
| Robustness | `tests/robustness` | One small file per format and variant of §5.2; truncated, empty, silent, NaN, lossy, odd-rate files; malformed JSON, sidecar, session files; oversized JSON — all raise `RoomScopeError`, nothing else |
| Fixtures, real | `tests/fixtures/daw/`, `tests/fixtures/hardware/` (already whitelisted in `.gitignore`) | The loopback recordings from the two matrices, a few seconds each, contributed under CC0 with a declaration in the README of the folder; regression evidence, never the only evidence for a change |
| Matrices, manual | `docs/DAW_COMPATIBILITY.md`, `docs/HARDWARE_TESTS.md` | §5.5, §6.5 |

Coverage is reported everywhere and enforced only for `core` and `models`
(threshold chosen when the gate is introduced, then only raised).

### 9.3 Validation campaign

Before 1.0 the methodology gets real-room evidence, published as
`docs/VALIDATION.md` with the raw files (CC0; release assets with checksums
when too large for the repository):

* at least one room, preferably one treated and one untreated, two
  positions each, one interface, one loudspeaker, one measurement
  microphone, on a green DAW and a green device from the matrices;
* the **same recorded file** analysed by RoomScope and by a reference
  instrument (Room EQ Wizard as a comparison instrument only, never copied;
  or an open toolbox with a clear license), which isolates the analysis
  from the acquisition;
* per-band T20 and T30, EDT, the strongest early reflection's delay, and
  the frequency response compared, with the acceptance tolerance written
  down *before* the measurements; every disagreement explained or turned
  into an issue; a campaign that fails its tolerance blocks 1.0 and is
  published anyway;
* the placement geometry checked against a tape measure
  (`source_height_m`, `ceiling_height_m`), which STATUS.md says has never
  happened.

## 10. Security and privacy

* **Attack surface:** files the user opens (audio through libsndfile, JSON
  through the standard library) and audio devices. The robustness tier
  covers the parsers; JSON loads are capped in size and depth; no `pickle`,
  no `numpy.load` with `allow_pickle`, no `eval`, no shell-outs.
* **Supply chain:** Dependabot (present) for pip and Actions; Actions
  pinned by SHA; the bundle lock file; an SBOM per release; PyPI trusted
  publishing; checksums and, once the identity exists, a notarized app.
* **Privacy:** everything stays on the machine; sessions may contain room
  names, notes and recordings of a private space, so bundles support
  `--no-audio` and the issue template says what a bundle contains before
  asking for one. No telemetry, no update check.
* **SECURITY.md** at 1.0: supported versions = the latest 1.x minor;
  private vulnerability reporting enabled (**maintainer decision**); the
  Standalone safety rules unchanged.

## 11. Community and governance

* **Opening the repository (M10, maintainer decision):** description and
  topics; branch protection on `main` (CI required, no force-push);
  `CODEOWNERS` naming the maintainer for `src/roomscope/core`,
  `docs/MEASUREMENT_METHODOLOGY.md` and the license documents; private
  vulnerability reporting; labels (`good first issue`, `help wanted`, `daw`,
  `hardware`, `dsp`, `gui`, `packaging`, `measurement`, `validation`);
  Discussions for measurement questions; the roadmap (§12) pinned.
  Recommended timing: at the first release candidate, so the candidate
  gets outside testing on DAWs and devices the maintainer does not own.
* **On-ramps without a DSP background:** a DAW recipe plus a matrix row
  with a fixture; a hardware row; a recording profile (a class and a
  synthetic test); a translation of the guide. All labelled
  `good first issue`.
* **DSP changes** keep today's rules: a published source, a synthetic test
  with a known expectation, a methodology entry.
* **Decisions** that change a public name, a file format, a dependency or a
  method are recorded as one-page ADRs in `docs/adr/` (context, decision,
  alternatives, consequences); the decisions of §13 become ADR-0001 onwards
  when this proposal is accepted.
* **Contribution terms:** Apache-2.0 §5; a DCO sign-off is a **maintainer
  decision**.

## 12. Milestones and exit criteria

| Version | Theme | Content | Exit criteria |
| --- | --- | --- | --- |
| 0.2 | Any DAW | `read_audio` breadth; `core/integrity.py` in the pipeline; `core/chain_check.py` and `roomscope check` (DAW form); the DAW page fields; recipes and `DAW_COMPATIBILITY.md`; fixtures per DAW; robustness tier | Nine green DAW rows on the current macOS with recipes, fixtures and dates; a resampled, a stretched and a drifted synthetic recording refused with the right cause |
| 0.3 | Any interface | `AudioBackend`, `portaudio` as a callback stream, `fake`, `coreaudio_rules`; device-rate default and reconfiguration opt-in; separate devices with drift detection; live meter, level check, progress, Stop; `check --standalone`; `HARDWARE_TESTS.md`; macOS runners in CI | Green rows for every class of §6.1 except Bluetooth at 44.1 and 48 kHz, one at 96 kHz; Stop silences within one callback period on real hardware; the Standalone flow runs in CI on the fake backend on macOS and Ubuntu |
| 0.4 | Reopen, compare, keep | PR #2 merged; `compare` core, CLI, GUI table, comparison findings; lenient readers, new session keys, public-API exports and tests; self-contained sessions and `session bundle`; loopback compensation (S1) and demo mode (S2) if time allows | Any v0.1 session reopens; two sessions compare with every delta carrying a validity; a bundle from the GUI reproduces the analysis on another Mac |
| 1.0-rc | Freeze and prove | Format and API freeze; validation campaign published; `.app` notarized or an explicit decision; guide in English and Chinese with all recipes; SECURITY / CONTRIBUTING / STATUS updated; repository public; PyPI pre-release; the two matrices re-run on the candidate | No open MUST item; every gate of §8–§9 green on the tag |
| 1.0 | Release | Fixes from the candidate only | Same gates; the release notes name the matrices, the validation results and the known limitations |
| post-1.0 | | Windows and Linux bundles and matrices; Simplified Chinese UI (S5) if not done; dB SPL from microphone calibration files; `analyze-ir`, CSV export, projects, averaging, profile / exporter entry points; a process boundary for plug-in shells (license review first); a documentation site | |

No dates: the exit criteria are the schedule.

## 13. Decisions and alternatives

| Decision | Chosen | Alternatives considered | Why |
| --- | --- | --- | --- |
| Platform for 1.0 | macOS only; the core stays platform-neutral | All three at once | The maintainer's scope; Windows and Linux are packaging and matrix work later, not a redesign |
| How compatibility is proven | An electrical-loopback chain check with a verdict, plus per-DAW and per-device matrices with fixtures | Trusting the WAV-in / WAV-out design; asking users to report | The expected result of a loop is known exactly, so every defect is attributable; the same check protects every later measurement |
| Rate / stretch / drift | Detect, explain, refuse | Estimate and correct | Correction is patented territory between separate devices and would hide chain problems from the user; a refusal with a named cause fixes the setup |
| Sample rate in Standalone Mode | The output device's current rate; switching is opt-in with a notice | Always 48 kHz | Nothing is reconfigured silently; the sweep is parametric so any supported rate costs nothing |
| Separate input / output devices | Allowed, drift-checked, aggregate device recommended | Refused | The USB measurement microphone is the most common home setup |
| GUI | Keep the plain PySide6 tool; functional additions only | A local web UI; a redesign | "A small tool"; the core boundary is unchanged, so a different front end stays possible later |
| Bundling | PyInstaller one-directory `.app` in a `.dmg` | Briefcase; py2app; Nuitka | Mature hooks for PySide6, SciPy and matplotlib; a predictable layout for the LGPL; revisit Briefcase if notarization automation proves painful |
| Audio-format breadth | libsndfile through soundfile, plus split-mono pairs; lossy refused | ffmpeg | Already a dependency, covers every DAW export format; lossy files are not measurements |
| Schemas | Versioning policy and round-trip tests are MUST; JSON Schema files are SHOULD | pydantic / msgspec; generated schemas | No new runtime dependency; the dataclasses stay the source of truth |
| Findings | Derived on load, never stored | Stored in `result.json` | Advice must come from thresholds the reader can look up in the running version |
| Comparison time origin | The direct sound of each result; the electrical zero when both have a loopback (S1) | Cross-correlation | The direct sound is already the origin of every decay figure |
| Internationalisation | Chinese guide now; gettext for findings and the GUI as SHOULD; core diagnostics stay English | Full UI translation as MUST | The guide is where a beginner needs their language; core strings are part of the stored record and of bug reports |
| Minimum Python | 3.12 (unchanged) | 3.11 | The code uses 3.12 syntax; the app carries its own interpreter |

## 14. Risks

| Risk | Effect | Mitigation |
| --- | --- | --- |
| DAW versions change behaviour (a new default warp mode, a new export dialog) | A green row goes stale | Rows carry versions and dates; the chain check catches the regression at the user's desk; community rows through the template |
| No notarization identity | Gatekeeper warnings; adoption drops | Maintainer decision early (§15); unsigned builds documented; the pipx path is unaffected |
| USB-microphone drift too large for a usable measurement without an aggregate device | The most common home setup fails | The guide's aggregate-device recipe with drift correction; the check names the cause; the fixture from that setup keeps the detector honest |
| PortAudio's Core Audio behaviour on rate switching differs from the assumption in §6.2 | A device gets reconfigured silently | Verified in 0.3 with the stream flags; recorded in HARDWARE_TESTS.md; the rate default avoids the case for most users |
| Tolerances of §5.3 and §5.4 too tight (false FAILs) or too loose | Users refused for nothing, or defects passed | Starting points only; fixed on the fixtures of both matrices, then documented with the evidence |
| Validation campaign needs rooms, gear and time | 1.0 slips | It is a MUST and the reason 1.0 means something; the protocol is written first so someone else can run it |
| Scope creep back towards the earlier three-platform draft | 1.0 never ships | §3 is the contract; SHOULD items slip without discussion |
| Patents adjacent to the field | Drift into a claimed method | Detection only; the two in-force patents named in §3.3 |
| GPL Qt modules entering the bundle | Obligations RoomScope cannot meet | The blocking bundle gate (§8.2) |
| PyPI name taken before registration | Renaming everything | Register `roomscope` before the first pre-release |
| PR #2 and this design diverging | Two session models | PR #2 is the baseline; this document only adds to it |

## 15. Maintainer decisions and open questions

1. **Notarization identity and budget:** Apple Developer Program for
   Developer ID signing, or ship 1.0 unsigned with documentation?
2. **PyPI project name and ownership:** register `roomscope`; enable trusted
   publishing.
3. **Public flip timing:** at 1.0-rc (recommended) or at 1.0?
4. **DAW licences for the matrix:** which of the nine DAWs the maintainer
   can run; trial versions are acceptable for a row if the version is
   recorded; rows nobody can run stay *untested* until a contributor
   supplies one.
5. **Hardware for the matrix:** which devices of §6.1 are available; which
   USB measurement microphone.
6. **Validation campaign:** reference instrument, rooms, who runs it; may
   Room EQ Wizard be used as a comparison instrument (its EULA allows use,
   not redistribution or reverse engineering)?
7. **DCO sign-off:** require it or rely on Apache-2.0 §5 alone?
8. **Recording copy default:** copy the raw recording into every session by
   default (self-contained, larger folders) or only on request?

## 16. Changes to existing code implied by this design

Listed so that reviewers can see the blast radius:

* `io/wav.py`: `read_audio` (alias `read_wav`), split-mono pairs, lossy
  refusal, file metadata on `AudioSignal`.
* `core/integrity.py`, `core/chain_check.py`, `core/compare.py` new;
  `core/loopback.py` (S1); `pipeline.analyze` gains the integrity step and
  the loopback step; `_decay_unreliable_reasons` gains the integrity
  reasons.
* `models/result.py`: `SweepIntegrity`, `ChainCheck`, `LoopbackResult`,
  `roomscope_version`; `models/comparison.py` new; `MeasurementSession`:
  lenient `from_dict`, `daw`, device names, file metadata, `platform`,
  `roomscope_version`; `AnalysisSettings`: `loopback_channel`,
  `calibration`.
* `audio/devices.py` + `audio/playrec.py` → `audio/portaudio.py` behind
  `AudioBackend`: callback stream, `input_channels`, `progress`, `cancel`,
  `monitor_input`; `audio/coreaudio_rules.py`, `audio/fake.py` new; the
  synthetic-room helpers move out of `tests/conftest.py`.
* `interpretation`: `interpret_comparison`; chain-check advice texts.
* `cli/main.py`: `check`, `compare`, `session bundle`, `--format`,
  `--copy-recording`, `--backend`, `--daw`, multi-file `--recording`;
  exit code 3; `--json` deprecated. `cli/report.py`: integrity,
  chain-check and comparison sections.
* `ui`: check page, compare view, meter / level check / Stop on the
  Standalone page, DAW fields and recipe link on the DAW page, integrity
  line on the overview.
* `roomscope/__init__.py`: lazy public exports; `__version__` from
  metadata; `__main__.py`.
* CI: macOS runners, robustness job, no-network gate, bundle job;
  `release.yml`; `scripts/build_license_bundle.py`.
* Docs: `DAW_COMPATIBILITY.md`, `HARDWARE_TESTS.md`, `VALIDATION.md`,
  `user-guide/` (EN + zh-CN), `adr/`; MEASUREMENT_METHODOLOGY.md §2a
  (integrity), §2b (chain check), §11 (comparison); DEPENDENCIES.md rows for
  `jsonschema`, `cyclonedx-bom`, PyInstaller (build-time tools, with their
  licenses); STATUS.md per milestone.
