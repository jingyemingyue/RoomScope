# Measuring through a DAW: the common procedure

Status: **draft procedure, 2026-09-22.** Every DAW-specific recipe in this
folder follows these steps and only adds the DAW's own menus and traps. A
recipe is marked DRAFT until its row in
[../../DAW_COMPATIBILITY.md](../../DAW_COMPATIBILITY.md) is green; a draft is
written from the vendor's documentation and is confirmed line by line during
the matrix run. Chinese version: [README.zh-CN.md](README.zh-CN.md).

RoomScope never talks to the DAW. It writes a sweep WAV, the DAW plays it and
records the result, RoomScope reads the exported (or recorded) file. So DAW
compatibility is about three things: the sweep must reach the interface
**unchanged** (no rate conversion, no stretching, no plug-ins), the recording
must come back **complete and untouched** (no normalisation, dither or
trimming), and RoomScope must be able to **read what the DAW wrote**.

## 0. Before anything

* **One interface, one clock.** Monitors on the interface's main outputs;
  the measurement microphone on input N. A USB microphone with its own clock
  is a separate case (see the hardware guide); do not start with it.
* **Match the sample rate everywhere.** Set the interface's rate (in the
  DAW's audio settings or the interface's control app), create the project
  at that rate, and generate the sweep at *exactly* that rate:
  `roomscope sweep --sample-rate 48000 --out sweep_48k.wav` (the GUI shows
  the interface's current rate). Then nothing in the DAW has to convert.
* **Keep the sidecar next to the WAV.** `sweep_48k.roomscope-sweep.json`
  is what lets RoomScope regenerate the exact reference; do not rename or
  separate the two files.
* **Monitor level low** before the first playback. The sweep peaks at
  −12 dBFS by default; raise the monitor level between runs only if the
  recording is too quiet (RoomScope tells you).

## A. Chain check first (once per DAW + interface)

An electrical loop: the DAW plays the sweep out of the interface and the
interface records it straight back in, through a cable or the interface's
own loopback feature. No loudspeaker, no microphone. The expected result is
known exactly, so every defect RoomScope finds belongs to the DAW, the export
or the interface.

1. Cable the interface: output N → input M (a TRS or XLR cable), or enable
   the interface's loopback input in its control app and use that as the
   input.
2. New project at the interface's rate. Import the sweep WAV onto track 1
   without conversion. Apply the DAW's **no-stretch settings** from its
   recipe (this is the step most likely to be wrong).
3. Track 2: a mono audio track, input = the loopback input, record armed,
   **input monitoring off**.
4. Track 1 → main output. **Nothing** on the main bus and nothing in the
   monitor path (no limiter, EQ, room correction, loudness compensation).
5. Put the playhead before the sweep region, start recording, stop about
   three seconds after the sweep ends. One pass only.
6. Get the recording out (see "Export rules"): the recorded file from the
   project's audio folder is best; otherwise export track 2.
7. Run the check:

   ```bash
   roomscope check --recording loop.wav --sweep sweep_48k.wav --daw "Logic Pro 11.2"
   ```

   Expected: `PASS`. On `FAIL`, every failing criterion names the likely
   cause (stretched, resampled, a plug-in, clipping, two passes, …) — fix it
   and repeat until it passes. Do not measure a room with a failing chain.

## B. The room measurement

Same project, same tracks. Unplug the loop cable, put the microphone on
input M, monitors on, the microphone where you record. Record one pass,
get the file out, then:

```bash
roomscope analyze --recording take1.wav --sweep sweep_48k.wav --out session1/ --profile vocal
```

(or *Import Recording* → *Analyze* in the GUI). RoomScope re-runs the
integrity checks on this recording as well.

## Export rules (every DAW)

| Rule | Why |
| --- | --- |
| Prefer the **recorded file itself** from the project's audio folder (Logic: Project Audio browser; Studio One: Pool; Cubase: Pool → "Show in Finder") | It has been through nothing at all |
| If exporting: **WAV, 32-bit float** (24-bit is fine if dither is off) | Float cannot clip and needs no dither |
| **Normalise off**, dither off, no "overload protection" | Level changes are harmless but dither and normalisation are not what you measured |
| Export the **whole take**, untrimmed | RoomScope finds the sweep itself; the silence before it is the noise measurement |
| Mono or stereo both fine; **no plug-ins** on the exported track or on the master | A limiter or EQ is not the room |
| AIFF / CAF / BWF / FLAC are read as well; MP3 / AAC are refused | Lossy codecs destroy the sweep |

## Traps that apply to every DAW

* **Tempo-following clips** (warp / flex / elastic / musical mode / stretch):
  the sweep is time-stretched. RoomScope reports "time-stretched by x %".
* **Sample-rate conversion** on import or export: RoomScope handles a clean
  conversion, but a file played at the wrong speed is refused ("played at
  the wrong speed by x %").
* **Varispeed / speed-up controls**: same symptom as conversion.
* **Plug-ins on the master or in the monitor path**: harmonic distortion or
  a non-flat response in the chain check.
* **Input monitoring on the microphone track**: the microphone is fed to the
  monitors while it records — a feedback loop and a coloured measurement.
* **Loop / cycle playback, count-in with a click, two takes in one file**:
  several sweep passes; RoomScope analyses the strongest and says so.
* **Bluetooth or system-audio outputs** instead of the interface: the chain
  check fails on bandwidth and distortion.

## What to record for the compatibility matrix

DAW name and exact version, macOS version, interface model, sample rate,
how the file was obtained (recorded file or export, with the settings), the
chain-check verdict, the date, and who ran it. Attach the loopback recording
(a few seconds) as the fixture for `tests/fixtures/daw/<name>/`.
