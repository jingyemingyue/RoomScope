# Changelog

All notable changes to RoomScope are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Session re-opening: `AnalysisResult.from_dict` rebuilds a saved result;
  `load_measurement` reloads `session.json` + `result.json` + the IR WAV;
  `list_sessions` finds session directories. CLI `roomscope show` prints a
  saved report (`--list` browses a folder). The GUI Home page has Open
  Session, Browse Folder and a recent-session list; File → Open Session
  does the same. Saves and opens are remembered under `$ROOMSCOPE_HOME`
  (`~/.roomscope` by default). `MeasurementSession.recording_profile`
  records which interpretation was used.
- v1.0 architecture design (`docs/ARCHITECTURE_V1.md`, Chinese digest in
  `docs/ARCHITECTURE_V1.zh-CN.md`): the release open to everyone -- public
  API tiers, schema policy, session comparison, loopback reference channel,
  audio backend interface, internationalisation, packaging and release
  pipeline, quality and validation gates, milestones with exit criteria, and
  the decisions reserved for the maintainer. A proposal; nothing in it is
  implemented by this entry.
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
- The optional `gui` extra now depends on `PySide6_Essentials` only, so a
  developer install does not pull GPL-only Qt Addons modules. `roomscope.ui.qt`
  defines `PySide6.__version__` so matplotlib's QtAgg backend still imports.

### Fixed
- The results overview now names the recording profile that produced the
  findings. It previously always printed `generic`.
- Loopback deconvolution tests asserted a time-domain IR peak of 1.0 after
  inverse filters were changed to unit *in-band* gain. They now compare
  against `reference_pulse()`. Methodology docs matched the implementation.
