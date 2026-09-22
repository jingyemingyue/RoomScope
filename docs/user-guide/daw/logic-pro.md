# Logic Pro recipe

Status: **DRAFT — untested.** Written from Apple's Logic Pro User Guide;
menu names are to be confirmed on the version recorded in
[../../DAW_COMPATIBILITY.md](../../DAW_COMPATIBILITY.md) during the matrix
run. Follow [README.md](README.md) for the common procedure; this page only
adds Logic's own settings. Chinese: [logic-pro.zh-CN.md](logic-pro.zh-CN.md).

## 1. Audio device and sample rate

* *Logic Pro › Settings › Audio › Devices*: Output Device and Input Device
  = the interface.
* *File › Project Settings › Audio › Sample Rate*: the interface's rate.
  Logic sets the interface to the project rate; generate the sweep at the
  same rate so that the import needs no conversion.

## 2. Import the sweep without stretching

Logic's Smart Tempo can flex imported audio to the project tempo. Switch it
off for this project *before* importing:

1. *File › Project Settings › Smart Tempo*: **Default for Project Tempo
   mode: Keep Project Tempo**; **Set imported audio files to: Off**.
2. *File › Import › Audio File…* (or drag the WAV onto an empty audio
   track). Do not accept a sample-rate conversion — if Logic offers one, the
   project rate is wrong; fix it and import again.
3. Select the region; in the **Region inspector** (top left, *Region:*
   panel; press *I* if hidden) check **Flex & Follow: Off**. The four values
   are *Off*, *On*, *On + Align Bars*, *On + Align Bars and Beats*; only
   *Off* leaves the audio untouched.
4. Make sure **Varispeed** is off (the control bar's Varispeed button, if it
   is shown, must not be lit). Varispeed changes the playback speed of the
   whole project and would be reported by RoomScope as "played at the wrong
   speed".
5. Cycle (loop) off.

## 3. Route and record

* Track 1 (the sweep): Output **Stereo Out** (or the output pair that feeds
  the monitors). No plug-ins on the track.
* **Stereo Out** channel strip and the **Master** fader: no plug-ins at all
  for the measurement (no limiter, no room-correction or monitoring
  plug-in).
* Track 2: *Track › New Audio Track*, mono, **Input: Input M** (the loopback
  input for the chain check, the microphone input for the room). Click
  **R** (record enable). Keep **I** (input monitoring) **off**: with it on,
  the microphone would be played through the monitors during the take.
* Put the playhead before the sweep region and press **R** (Record). Stop
  about three seconds after the sweep ends.

## 4. Get the recording out

**Option A (best): the recorded file.** *Browsers › Project* (the Project
Audio browser, *F*): select the take, then *Show in Finder* from the
Audio File menu (or drag the file to the Finder). Logic records into
*<Project>/Media/Audio Files* in WAVE, AIFF or CAF depending on
*File › Project Settings › Recording › Recording File Type*; RoomScope reads
all three. This file has been through nothing.

**Option B: export the region.** Select the recorded region, then
*File › Export › Region as Audio File…*:

| Option | Value |
| --- | --- |
| Save Format | **WAVE** (AIFF also fine) |
| Bit Depth | **32 Bit (float)** (24 Bit also fine) |
| Normalize | **Off** (not *Overload Protection Only*, not *On*) |
| Bypass Effect Plug-ins | on (there should be none anyway) |
| Include Audio Tail | off |
| Include Volume/Pan Automation | off |

Do not use *File › Bounce* for the measurement: its defaults include
normalisation and it renders the whole mix.

## 5. Logic-specific traps (check these when a chain check fails)

| Symptom reported by `roomscope check` | Logic setting to look at |
| --- | --- |
| time-stretched by x % | Region inspector *Flex & Follow* not Off; Project Settings › Smart Tempo *Set imported audio files to* not Off; the track's Flex button on |
| played at the wrong speed by x % | Varispeed on; project rate ≠ the rate the sweep was generated at; a sample-rate conversion accepted on import |
| harmonic k at x dB / response deviates x dB | a plug-in on Stereo Out or the Master; *Settings › Audio › General › Software Monitoring* combined with *I* on the microphone track |
| clipped at x dBFS | export with *Normalize: On* is not clipping but *Overload Protection Only* hides one; lower the sweep level or the input gain |
| n passes | Cycle on, or two takes in one region |

## 6. Verification checklist for the matrix run

- [ ] Logic Pro version and macOS version recorded
- [ ] Menu paths above confirmed on that version (note any renamed item)
- [ ] Default value of *Set imported audio files to* on a fresh project recorded
- [ ] Recording File Type default recorded (WAVE / AIFF / CAF)
- [ ] Chain check PASS with Option A **and** with Option B
- [ ] Loopback recording saved to `tests/fixtures/daw/logic-pro/` with a README
