# RoomScope

**An open-source, DAW-independent recording environment analyzer.**

RoomScope answers practical questions a recording engineer asks about a room
and a microphone position:

* Is this room usable for recording?
* What acoustic problems does this position have (strong early reflections,
  long decay, low-frequency build-up, mains hum, high noise floor)?
* Did moving the microphone or the performer improve things?

It measures the room with an exponential sine sweep (ESS), derives the room
impulse response by deconvolution, and reports reverberation (EDT / T20 /
T30 / estimated RT60), frequency response, background noise, early
reflections and potential low-frequency resonances. Every number carries its
unit, its algorithm source and a validity flag; when the data is not good
enough, RoomScope says *"Insufficient decay range"* instead of inventing a
figure. There is deliberately no "room score".

> Status: **v0.1 foundation, pre-alpha.** The DSP core, CLI and a minimal
> GUI exist and are covered by synthetic tests. See [docs/STATUS.md](docs/STATUS.md)
> for what is implemented, tested and known to be missing.

## Two workflows, one analysis core

### Universal DAW Mode

Works with any DAW that can import, play, record and export WAV files
(Cubase / Nuendo, Pro Tools, Logic Pro, Studio One, Ableton Live, REAPER,
FL Studio, Bitwig, Digital Performer, ...). RoomScope never talks to the DAW.

1. **Generate Test Signal** – RoomScope writes a sweep WAV (plus a small JSON
   sidecar with the exact sweep definition).
2. **Record Through Your DAW** – import the WAV on a track, play it through
   your interface and monitors, record the measurement microphone on another
   track.
3. **Import Recording** – export the recorded track as WAV (same sample rate
   as the project; any length, no trimming needed).
4. **Analyze** – RoomScope finds the sweep automatically, deconvolves it and
   produces the report.

### Standalone Mode

RoomScope plays the sweep and records the microphone itself through the
audio interface you select (PortAudio via `sounddevice`). Start with the
monitor level low: the default sweep level is conservative and RoomScope
never touches system volume or audio settings.

Both modes call exactly the same analysis pipeline
(`roomscope.core.pipeline.analyze`).

## Install (development)

Requires Python 3.12 or newer.

```bash
git clone https://github.com/jingyemingyue/RoomScope.git
cd RoomScope
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,gui]"
```

`gui` pulls in PySide6 (LGPL-3.0, large). Without it the CLI and the Python
API work fully.

## Quick start (CLI)

```bash
# 1. Generate the test signal (48 kHz, 20 Hz–20 kHz, 10 s sweep, -12 dBFS)
roomscope sweep --out sweep_48k.wav

# 2. Play it through your DAW, record the mic, export recording.wav

# 3. Analyze
roomscope analyze --recording recording.wav --sweep sweep_48k.wav --out results/

# Standalone: list devices, then measure
roomscope devices
roomscope measure --out session1/ --input-device 2 --output-device 3 --sample-rate 48000

# GUI (needs the gui extra)
roomscope gui
```

`results/` receives `result.json` (all metrics and curves),
`impulse_response.wav` (raw IR, float32) and `session.json` (measurement
metadata). Raw recordings are never modified.

## Python API

```python
from roomscope.core import Reference, analyze
from roomscope.io.wav import read_wav, load_reference

recording = read_wav("recording.wav")
reference = load_reference("sweep_48k.wav")   # uses the JSON sidecar if present
result = analyze(recording, reference)
print(result.decay.broadband.rt60_estimate_s, result.decay.broadband.rt60_basis)
for r in result.reflections.reflections:
    print(f"{r.delay_ms:.1f} ms  {r.relative_db:.1f} dB")
```

## Design principles

* **DAW-independent** – no DAW SDKs, ever. WAV in, WAV out.
* **Core-first** – DSP functions are pure NumPy/SciPy functions with no GUI,
  device or file-format dependencies, so a CLI, a desktop app, a plug-in or
  a Python API can share them.
* **Scientific correctness over features** – algorithms come from published
  papers and standards (Farina 2000, Schroeder 1965, Lundeby 1995,
  ISO 3382-1/-2, ...); see [docs/MEASUREMENT_METHODOLOGY.md](docs/MEASUREMENT_METHODOLOGY.md).
* **Honest numbers** – dBFS unless calibrated, validity flags on every metric,
  no pseudo-scientific room score.
* **Clean-room implementation and license hygiene** – no third-party source is
  vendored ([docs/CODE_PROVENANCE.md](docs/CODE_PROVENANCE.md)); every dependency and
  every reference repository is audited
  ([docs/DEPENDENCIES.md](docs/DEPENDENCIES.md),
  [docs/THIRD_PARTY_REVIEW.md](docs/THIRD_PARTY_REVIEW.md)).

## Documentation

| Document | Content |
| --- | --- |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Package layout, data flow, extension points |
| [docs/MEASUREMENT_METHODOLOGY.md](docs/MEASUREMENT_METHODOLOGY.md) | Algorithms, units, validity rules, references |
| [docs/DEPENDENCIES.md](docs/DEPENDENCIES.md) | Every runtime/dev dependency with license and purpose |
| [docs/THIRD_PARTY_REVIEW.md](docs/THIRD_PARTY_REVIEW.md) | Audit of external repositories that were studied |
| [docs/CODE_PROVENANCE.md](docs/CODE_PROVENANCE.md) | Provenance of any adapted or copied code (currently none) |
| [docs/LICENSE_DECISION.md](docs/LICENSE_DECISION.md) | Why RoomScope is Apache-2.0 |
| [docs/STATUS.md](docs/STATUS.md) | Implemented / tested / known limitations / next milestone |
| [docs/PROJECT_BRIEF.zh-CN.md](docs/PROJECT_BRIEF.zh-CN.md) | Original project brief (Chinese) |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Tests, lint and type checks:

```bash
pytest
ruff check . && ruff format --check .
mypy
```

## License

Apache License 2.0 – see [LICENSE](LICENSE) and [NOTICE](NOTICE).
