# Changelog

All notable changes to RoomScope are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/). How a version is cut is in
`docs/RELEASE_PLAN.md`.

## [Unreleased]

## [0.4.0] - 2026-09-24

First pre-release. Everything below was developed against synthetic rooms;
no hardware result is claimed, the desktop bundles are unsigned, and the
repository is still private. Review follow-ups are tracked as issues
#9–#16 (see `docs/RELEASE_PLAN.md` §6).

### Added
- Release plan (`docs/RELEASE_PLAN.md`, zh-CN digest): version ladder
  0.4.0 → 0.4.x → 0.5.0 → 1.0.0rc1 → 1.0.0 with the gates for each, and
  the version-driven release pipeline: a version change in `pyproject.toml`
  on `main` builds sdist/wheel, unsigned bundles for Linux, macOS and
  Windows, a CycloneDX SBOM and checksums, and opens a **draft** GitHub
  Release; publishing the draft is the maintainer's decision and is what
  creates the tag. PyPI upload runs only on a tag and only when the
  repository variable `ROOMSCOPE_PUBLISH_PYPI` is `true`. The workflow
  file itself is installed by the maintainer (RELEASE_PLAN.md §3).
- Verbatim LGPL-3.0, GPL-3.0 and PortAudio license texts under
  `packaging/licenses/`; `scripts/build_license_bundle.py` ships them in
  `THIRD_PARTY_LICENSES/_texts/` and fails when PySide6 is installed but
  the LGPL / GPL texts are missing (DEPENDENCIES.md §3–§4). The About
  notice points at those files.
- `scripts/check_bundle_contents.py --strip` deletes GPL-only Qt modules
  and ASIO DLLs from a frozen tree before the gate runs. The gate now
  recognises versioned Linux libraries (`libQt6QuickTimeline.so.6`),
  macOS framework binaries and the `Qt6`-prefixed file names
  (`Qt6VirtualKeyboard.dll`), which the previous name check missed;
  `--require-licenses` also requires the verbatim texts.
- 1.0-rc software that does not need hardware or a public flip: GUI
  Placement tab and tape-measure fields (S5); Python 3.14 in the CI
  matrix (S6); the M11 validation protocol with pre-chosen tolerances
  (`docs/VALIDATION.md`); `requirements/bundle.lock`; `CODEOWNERS`; docs
  link check; 85 % coverage gate on `core` and `models`; `docs/index.md`
  hub; fixtures README; keyboard shortcuts for every main action; plots
  use linestyle as well as colour; GitHub Actions pinned by SHA; themed
  documentation site (`scripts/build_docs_site.py`, S7); matplotlib / Qt
  chrome follows the system dark mode; Standalone shows the device rate
  next to the requested rate and calls `check_sample_rate` before a
  measurement; Compare lists matched reflections, resonances, loopback
  deltas and per-octave MAD; Help opens the license bundle or
  `docs/DEPENDENCIES.md`. JSON reads cap nesting depth as well as size;
  settings, recents and sweep sidecars use the same reader.
  `scripts/check_src_safety.py` bans network imports, pickle, eval and
  shell-outs under `src/`. Unsigned-bundle packaging adds Inno Setup, a
  Linux desktop/AppRun, a macOS dmg script, zip/tar archives and
  `scripts/smoke_bundle.py` (fake-backend measure, offscreen GUI).
  Linux x86_64 and Windows win_amd64 wheels of numpy/scipy/soundfile/
  sounddevice/matplotlib/Pillow were opened
  (`scripts/audit_wheel_contents.py`); the Windows sounddevice wheel
  ships ASIO DLLs that the bundle gate strips. `load_comparison` and
  `roomscope show comparison.json` re-derive findings (they are never
  stored); robustness tests cover comparison.json, more WAV/sidecar cases
  and a microphone used as loopback. CLI `--help`, text-report labels,
  DAW / Standalone / Results chrome and the remaining CLI messages go
  through gettext.
- v0.4 for everyone (ARCHITECTURE_V1.md milestone 0.4): gettext with a
  Simplified Chinese catalog for the `generic`, `vocal` and `voiceover`
  profile findings, the report labels, GUI chrome and CLI help (the other
  four profiles and the Standalone safety warning still fall back to
  English — #14); `--lang` / `settings.language` / `ROOMSCOPE_LANG`; user
  settings under `$ROOMSCOPE_HOME/settings.json`; self-contained sessions
  (sweep sidecar always copied, recording copied on `--copy-recording` /
  the GUI default); `roomscope session bundle` (`--no-audio`); project
  folders and `average_decay` (SHOULD; the ISO 3382-2 class thresholds are
  a secondary-source transcription, see #15); CSV exporter and
  `roomscope export`; user guide in English and Chinese; macOS
  `NSMicrophoneUsageDescription` and audio-input entitlement. `--json` is
  deprecated in favour of `--format json` (stderr warning only).
- v0.3 trust-the-chain (ARCHITECTURE_V1.md milestone 0.3): optional
  loopback compensation (`core/loopback.py`, `--loopback` /
  `--loopback-channel`); `AudioBackend` protocol with a fake backend and a
  PortAudio callback stream that honours progress and Stop; CLI
  `--backend`; GUI Demo mode, Stop, and a loopback channel; robustness
  tests and a JSON size cap; CI on Linux, macOS and Windows; hardware
  matrix started in `docs/HARDWARE_TESTS.md` (no cell is marked PASS).
- v0.2 reopen-and-compare (ARCHITECTURE_V1.md milestone 0.2): lazy Tier 1
  exports on `import roomscope`; lenient `from_dict` loaders; shipped JSON
  Schemas and `roomscope schema`; `compare()` of two `AnalysisResult`s with
  a validity on every delta; CLI `roomscope compare` and `analyze-ir`;
  `interpret_comparison`; GUI pick-two compare view with an explicit
  "input gain unchanged" checkbox. `jsonschema` is a dev dependency used
  only in tests.
- Session re-opening: `AnalysisResult.from_dict` rebuilds a saved result;
  `load_measurement` reloads `session.json` + `result.json` + the IR WAV;
  `list_sessions` finds session directories. CLI `roomscope show` prints a
  saved report (`--list` browses a folder). The GUI Home page has Open
  Session, Browse Folder and a recent-session list; File → Open Session
  does the same. Saves and opens are remembered under `$ROOMSCOPE_HOME`
  (`~/.roomscope` by default). `MeasurementSession.recording_profile`
  records which interpretation was used.
- v1.0 architecture design (`docs/ARCHITECTURE_V1.md`, Chinese digest in
  `docs/ARCHITECTURE_V1.zh-CN.md`): public API tiers, schema policy,
  session comparison, loopback reference channel, audio backend interface,
  internationalisation, packaging and release pipeline, quality and
  validation gates, milestones with exit criteria, and the decisions
  reserved for the maintainer.
- GitHub project files so other developers can clone, review and open pull
  requests: CI (pytest on Python 3.12/3.13, ruff, mypy, sdist/wheel), issue
  and pull-request templates, Dependabot, Contributor Covenant, and a
  security policy.
- Project foundation: Apache-2.0 license, architecture and methodology
  documents, dependency / third-party / provenance / license-decision audits.
- Python package `roomscope` (src layout, typed, ruff + mypy clean).
- DSP core: exponential sine sweep generation with analytic (Farina) and
  regularised spectral inverse filters; whole-recording deconvolution with
  automatic impulse-response location; Schroeder decay with Lundeby noise
  truncation and late-decay compensation; EDT / T20 / T30 / estimated RT60
  per ISO 3382-1 evaluation ranges with validity flags; time-reversed
  octave-band filtering with B*T check; frequency response with
  fractional-octave smoothing; background noise (dBFS, PSD, 50/60 Hz hum
  detection); early-reflection candidates; potential low-frequency
  resonance candidates.
- Placement geometry (`core/placement.py`): the vertical axis derived from the
  early reflections plus one or two tape measurements, in three tiers that
  degrade explicitly as inputs are withheld. Reports the loudspeaker height,
  the plane above both devices and the horizontal separation; never a
  coordinate, a room length or width, or a named wall, because one
  omnidirectional microphone at one position leaves the system underdetermined
  by two even with a measured loudspeaker distance. New CLI flags
  `--speaker-distance`, `--mic-height`, `--temperature`.
- Measurement session model and JSON/WAV storage.
- CLI: `roomscope sweep | analyze | devices | measure | gui`.
- Interpretation layer with a generic recording profile.
- Recording profiles (`interpretation/profiles.py`): seven profiles —
  generic, vocal, voiceover, acoustic_guitar, drums, room_mic, choir — with
  per-profile reflection/decay/noise thresholds and tailored advice on top of
  shared measurement-integrity checks. CLI `--profile` (`--profile vocal`),
  `Interpretation (<profile> profile):` in the report, and a profile selector
  in both GUI measurement modes.
- Minimal PySide6 GUI (Universal DAW Mode, Standalone Mode, results tabs).
- Synthetic test suite (unit, integration, offscreen GUI smoke tests).

### Changed
- The optional `gui` extra depends on `PySide6_Essentials` only, so a
  developer install does not pull GPL-only Qt Addons modules. `roomscope.ui.qt`
  defines `PySide6.__version__` so matplotlib's QtAgg backend still imports.
- The new release workflow attaches archives and checksums only (not the
  unpacked bundle directories), pins PyInstaller to `>=6.11,<7`, restricts
  `contents: write` to the draft-release job, and names archives by
  version and platform.

### Fixed
- The installed-wheel audit test failed on macOS CI: numpy's
  `macosx_14_0_arm64` wheel (what `macos-latest` installs) links Apple
  Accelerate and bundles no shared library at all, while the
  `macosx_11_0` wheel bundles OpenBLAS with libgfortran / libquadmath under
  `numpy/.dylibs/`. The test accepts either layout and rejects a mixed one;
  DEPENDENCIES.md §6 records both. (An earlier fix attributed the failure
  to `RECORD` omitting the `.dylibs/` folder; that was not the cause.)
- Comparison findings quote ISO 3382-1's "not enough to call the change
  significant" disclaimer. The 0.2 test now requires that wording instead
  of forbidding the word "significant".
- The wheel build includes each shipped `*.schema.json` file without
  adding `roomscope/schemas/__init__.py` twice.
- The results overview now names the recording profile that produced the
  findings. It previously always printed `generic`.
- Loopback deconvolution tests asserted a time-domain IR peak of 1.0 after
  inverse filters were changed to unit *in-band* gain. They now compare
  against `reference_pulse()`. Methodology docs matched the implementation.

[Unreleased]: https://github.com/jingyemingyue/RoomScope/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/jingyemingyue/RoomScope/releases/tag/v0.4.0
