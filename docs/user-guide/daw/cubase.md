# Cubase / Nuendo recipe

Status: **DRAFT — untested.** Written from Steinberg's Cubase Pro
operation manual; menu names are to be confirmed on the version recorded in
[../../DAW_COMPATIBILITY.md](../../DAW_COMPATIBILITY.md) during the matrix
run. Cubase Pro, Cubase Artist and Nuendo share the audio engine and these
menus; each gets its own matrix row and only a tested row counts. Follow
[README.md](README.md) for the common procedure. Chinese:
[cubase.zh-CN.md](cubase.zh-CN.md).

## 1. Audio device and sample rate

* *Studio › Studio Setup › Audio System*: the driver = the interface
  (on macOS Cubase lists the Core Audio device as the "ASIO driver").
* *Project › Project Setup…* (*Shift-S*): **Sample Rate** = the interface's
  rate. Cubase asks to switch the device when they differ; make them agree
  and generate the sweep at that rate.
* *Studio › Audio Connections* (*F4*): **Inputs** — a mono bus on input M;
  **Outputs** — *Stereo Out* on the interface's monitor pair. If you use
  the **Control Room**, its *Main* channel must point at the monitor pair
  and its **inserts must be empty or bypassed** for the measurement:
  Control Room inserts are not part of an export, but they *are* in the
  path to the loudspeakers, and room-correction plug-ins usually live
  there.

## 2. Import the sweep without stretching

Cubase stretches an audio clip to the project tempo only when **Musical
Mode** is on for that clip. It switches Musical Mode on automatically for
files that carry tempo information (ACID loops, MediaBay-tagged files); a
plain sweep WAV has none, but verify:

1. *File › Import › Audio File…*. In the *Import Options* dialog keep
   *Copy File to Project Folder*; do **not** convert the sample rate (if the
   dialog wants to, the project rate is wrong — fix it and import again).
2. Open the **Pool** (*Project › Pool*, *Cmd-P*) and check that the
   **Musical Mode** column is **unticked** for the sweep clip. Selecting the
   event also shows *Musical Mode* on the **Info Line**; it must be off.
3. The track's time base (musical / linear) does not stretch audio and may
   stay as it is. Do not apply any *Audio › Processes* to the clip.
4. Cycle off; no tempo track changes are needed.

## 3. Route and record

* Track 1 (the sweep): output **Stereo Out**. No inserts on the track.
* **Stereo Out**: no inserts and no EQ for the measurement — an export
  includes the output channel's inserts, so a limiter or dither plug-in
  (UV22HR) there would end up in the file.
* Track 2: *Project › Add Track › Audio*, mono, **Input: the mono bus on
  input M**. Record enable. Keep the **Monitor** button (the speaker icon)
  **off**: with it on, the microphone is played through the monitors during
  the take.
* Set the left locator before the event; **Record** (`*` on the numeric
  keypad, or the transport button); stop about three seconds after the sweep
  ends.

## 4. Get the recording out

**Option A (best): the recorded file.** *Pool*: right-click the take →
*Show in Finder*. Cubase records into *<Project>/Audio* as WAV (BWF chunks
included; RoomScope reads them). Nothing has touched this file.

**Option B: export the track.** *File › Export › Audio Mixdown…*:

| Option | Value |
| --- | --- |
| Channel Selection | **Multiple** → tick only the microphone track (or *Single* with the track's channel selected) |
| Export Range | *Locators* set around the take, or the whole project |
| File Format | **Wave** |
| Sample Rate | the project's rate |
| Bit Depth | **32 bit float** (24 bit also fine; there is no dither unless a dither plug-in is inserted) |
| Mono / Stereo | as the track (mono) |
| Real-Time Export | off |
| After Export | nothing (do not *Create Audio Track* / *Insert to Pool* unless you want to) |

## 5. Cubase-specific traps

| Symptom reported by `roomscope check` | Cubase setting to look at |
| --- | --- |
| time-stretched by x % | *Musical Mode* on for the clip (Pool column / Info Line); a warp or *Set Definition From Tempo* applied to the clip |
| played at the wrong speed by x % | project rate ≠ the sweep's rate; a conversion accepted in *Import Options* |
| harmonic k at x dB / response deviates x dB | inserts or EQ on *Stereo Out*; Control Room inserts (room correction, limiter) in the monitor path; the *Dim* or a level trim in the Control Room is harmless but a plug-in is not |
| clipped at x dBFS | a limiter on Stereo Out; input gain too high; the Control Room *Main* level too hot into the loop cable |
| n passes | Cycle on, or two takes in one lane |

## 6. Verification checklist for the matrix run

- [ ] Cubase (or Nuendo) edition, version and macOS version recorded
- [ ] Menu paths above confirmed on that version (note any renamed item)
- [ ] *Import Options* behaviour on a rate mismatch recorded (asks / converts silently)
- [ ] Musical Mode state after importing the sweep WAV recorded (expected: off)
- [ ] Control Room in use or not; if in use, inserts confirmed empty
- [ ] Chain check PASS with Option A **and** with Option B
- [ ] Loopback recording saved to `tests/fixtures/daw/cubase/` with a README
