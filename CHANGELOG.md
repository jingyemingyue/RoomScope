# Changelog

All notable changes to RoomScope are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
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
