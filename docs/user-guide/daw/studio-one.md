# Studio One Pro recipe

Status: **DRAFT — untested.** Written from the PreSonus Studio One
reference manual and knowledge base; menu names are to be confirmed on the
version recorded in [../../DAW_COMPATIBILITY.md](../../DAW_COMPATIBILITY.md)
during the matrix run. The product is called *Studio One Pro* since
version 7 (earlier *Studio One Professional*); the recipe should also hold
for Studio One Artist, which is untested. Follow [README.md](README.md) for
the common procedure. Chinese: [studio-one.zh-CN.md](studio-one.zh-CN.md).

## 1. Audio device and sample rate

* *Studio One › Settings › Audio Setup*: Audio Device = the interface; the
  device's sample rate is shown here.
* *Song › Song Setup › General*: **Sample Rate** = the interface's rate.
  Studio One warns when the song and the device disagree; make them agree
  and generate the sweep at that rate.

## 2. Import the sweep without stretching

Studio One can stretch imported audio to the song tempo when it knows (or
guesses) the file's tempo. Disable it for the measurement song:

1. When creating the song, untick **Stretch Audio Files to Song Tempo** in
   the *New Song* dialog; for an existing song, *Song › Song Setup ›
   General* → untick **Stretch audio files to Song tempo**.
2. Import: drag the WAV from the *Browser › Files* tab onto an empty audio
   track, or *Song › Import File…*. Do not accept a sample-rate conversion.
3. Select the event, open the **Inspector** (*F4* / the *i* button) and
   check the event parameters: **Tempo: Don't Follow** (the other values
   are *Follow* and *Timestretch*); **Speedup: 1.00** (Speedup is
   tempo-independent time-stretching and must stay at ×1); **Transpose 0**,
   **Tune 0**.
4. Loop (the cycle button) off.

## 3. Route and record

* Track 1 (the sweep): Output **Main**. No inserts on the track.
* **Main** channel: no inserts for the measurement. In *Song › Song Setup ›
  Audio I/O Setup › Outputs* the Main output must be the interface's
  monitor pair. If your version has a separate monitoring bus (Listen bus /
  Control Room-style routing), keep its inserts empty too: they are in the
  path to the loudspeakers.
* Track 2: *Track › Add Tracks…*, Audio, mono, **Input: Input M** (define
  the mono input in *Audio I/O Setup › Inputs* if it does not exist). Record
  arm the track. Keep the blue **Monitor** button **off**: with it on, the
  microphone is played through the monitors during the take.
* Playhead before the event; **Record**; stop about three seconds after the
  sweep ends.

## 4. Get the recording out

**Option A (best): the recorded file.** *Browser › Pool*: right-click the
take → *Show in Finder*. Studio One records WAV files into
*<Song folder>/Media*. Nothing has touched this file.

**Option B: export the track.** *Song › Export Stems…*:

| Option | Value |
| --- | --- |
| Sources | *Tracks* → tick only the microphone track |
| Format | **Wave** |
| Resolution | **32 Bit Float** — Studio One adds dither by default when exporting below 32-bit float, so float avoids it; if 24 Bit is chosen, make sure *Dither* is off |
| Sample Rate | the song's rate |
| Export Range | the whole song, or the loop range set around the take |
| Import to Track | off |

*Song › Export Mixdown* with the microphone track soloed also works with the
same format settings, but it renders through the Main bus; Export Stems (or
Option A) is cleaner.

## 5. Studio One-specific traps

| Symptom reported by `roomscope check` | Studio One setting to look at |
| --- | --- |
| time-stretched by x % | Inspector *Tempo* set to Follow or Timestretch; *Stretch audio files to Song tempo* on; *Speedup* ≠ 1.00 |
| played at the wrong speed by x % | song rate ≠ the sweep's rate; a conversion accepted on import; *Speedup* in *Tape* stretch mode (which changes pitch and speed together) |
| harmonic k at x dB / response deviates x dB | inserts on Main or on a monitoring / Listen bus; a plug-in on the sweep track |
| raised noise floor at high frequencies | dither on an export below 32-bit float |
| n passes | Loop on, or two takes recorded into the same event |

## 6. Verification checklist for the matrix run

- [ ] Studio One Pro version and macOS version recorded
- [ ] Menu paths above confirmed on that version (note any renamed item)
- [ ] Default state of *Stretch audio files to Song tempo* in a new song recorded
- [ ] Whether import converts the sample rate silently or asks — recorded
- [ ] Whether *Export Stems* below 32-bit float dithers by default — confirmed or corrected here
- [ ] Chain check PASS with Option A **and** with Option B
- [ ] Loopback recording saved to `tests/fixtures/daw/studio-one/` with a README
