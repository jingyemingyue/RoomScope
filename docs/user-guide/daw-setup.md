# Measuring through your DAW

Universal DAW Mode works with any DAW that can play one WAV file and record
another at the same time. RoomScope never talks to the DAW: it only needs the
recording, exported whole. This page lists what every DAW has to get right,
then the steps in the DAWs most studios use. The Chinese translation is
[daw-setup.zh-CN.md](daw-setup.zh-CN.md).

> The menu names below are those of recent versions of each DAW, taken from
> its documentation. They have not yet been checked on every DAW with real
> hardware ([HARDWARE_TESTS.md](../HARDWARE_TESTS.md)). If your version
> differs, please open a *Measurement problem* issue so the notes can be
> corrected.

## What every DAW must do

1. **Same sample rate.** Generate the test signal at the project's sample
   rate: `roomscope sweep --sample-rate 44100 --out sweep_44k.wav`, or pick
   the rate in the GUI's Step 1. A 48 kHz file played unconverted in a
   44.1 kHz project runs 8 % slow and cannot be deconvolved; RoomScope reports
   *"a file generated at 48000 Hz was played at 44100 Hz"* when that happens.
   Keep the `.roomscope-sweep.json` sidecar next to the WAV.
2. **No time-stretching.** Warp, Flex Time, Follow Tempo, elastic audio and
   stretch modes must be off for the test-signal clip. RoomScope reports
   *"the DAW time-stretched it"* when the sweep runs at the wrong speed.
3. **A clean playback path.** Bypass every plug-in on the test-signal track,
   on the buses it passes and on the master: limiters, clippers, "loudness"
   or tape plug-ins, and **room-correction** plug-ins (SoundID Reference,
   ARC and the like) unless you mean to measure the corrected system. No
   fades, clip gain or automation on the test signal. A fader or clip gain
   below 0 dB is fine.
4. **One loudspeaker.** Route the test-signal track to the one loudspeaker
   you are measuring (pan hard or use a mono output). Two loudspeakers
   playing the same sweep interfere and the result describes neither.
5. **Record the microphone on its own mono track**, input monitoring off
   (otherwise the microphone feeds back to the loudspeaker). Start recording
   before the test signal starts, or record the whole clip in one pass: the
   file begins with one second of silence for exactly this. Record one pass
   only: turn loop / cycle recording off.
6. **Export the recorded track or clip whole** at the project sample rate as
   WAV (Broadcast WAV, RF64 and Wave64 are fine), AIFF, CAF or FLAC, 24-bit or
   32-bit float, **without normalising** (normalising hides the noise floor
   level you compare between takes). Mono or stereo both work; with a stereo
   file pick the microphone channel in the GUI or with `--channel`. Do not
   trim: RoomScope finds the sweep, and the silence after it is the decay.
7. **Latency does not matter.** RoomScope finds the sweep wherever it is in
   the recording, so plug-in delay compensation and interface latency need no
   setting.
8. **Optional loopback.** Record the interface's electrical return (an output
   cabled back to a spare input) on a second track in the same pass. Export
   both tracks as one two-channel file (`--channel 0 --loopback-channel 1`)
   or as two files (`--loopback return.wav`).

Then analyse:

```bash
roomscope analyze --recording "Mic_01.wav" --sweep sweep_44k.wav --out session/
```

or choose the files in the GUI's Universal DAW Mode.

## Avid Pro Tools

* **Sample rate:** set when the session is created (Session Setup shows it).
  Generate the sweep at that rate.
* **Import:** File ▸ Import ▸ Audio. If the dialog offers *Apply SRC*, the
  rates differ: go back and generate the sweep at the session rate instead.
* **Time-stretching:** leave Elastic Audio off (the track's Elastic Audio
  selector shows *None*).
* **Record:** a new mono audio track with the microphone input, record-enabled,
  with TrackInput monitoring off. Clear the inserts on the sweep track and on
  the master fader.
* **Export:** select the recorded clip and use *Export Clips as Files* from the
  Clip List menu (WAV, the session rate, 24-bit). Pro Tools writes Broadcast
  WAV; RoomScope reads it as is.

## Apple Logic Pro and GarageBand

* **Sample rate:** File ▸ Project Settings ▸ Audio. Generate the sweep at that
  rate. GarageBand projects run at 44.1 kHz: generate the sweep with
  `--sample-rate 44100`.
* **Import:** File ▸ Import ▸ Audio File, or drag the WAV to a new audio track.
* **Time-stretching:** keep Flex off on the track, and set *Flex & Follow* to
  *Off* in the region inspector so Smart Tempo does not conform the sweep.
* **Record:** a mono audio track with the microphone input, input monitoring
  off. Turn Cycle off. Logic's recording file (CAF, WAV or AIFF) can be
  analysed directly.
* **Export:** select the recorded region, File ▸ Export ▸ Region as Audio File,
  WAV or AIFF, the project rate, *Normalize* off. In GarageBand mute the sweep
  track and use Share ▸ Export Song to Disk (uncompressed) with the master
  effects off.

## Steinberg Cubase and Nuendo

* **Sample rate:** Project ▸ Project Setup.
* **Import:** File ▸ Import ▸ Audio File. If *Convert to project sample rate*
  is offered, the rates differ: generate the sweep at the project rate.
* **Time-stretching:** keep *Musical Mode* off for the sweep event.
* **Record:** a mono audio track with the microphone input, monitoring off.
  Check that the Control Room has no insert or room-correction plug-in on the
  monitor path, or bypass it.
* **Export:** select the recorded event and use Audio ▸ Bounce Selection, or
  File ▸ Export ▸ Audio Mixdown with only the microphone channel selected
  (Channel Batch Export), WAV, the project rate, no normalisation.

## PreSonus / Fender Studio One

* **Sample rate:** Song ▸ Song Setup ▸ General.
* **Import:** drag the WAV from the Browser to a new audio track.
* **Time-stretching:** in the Inspector set *Follow Tempo* to *Don't Follow*
  (Timestretch off) for the sweep event.
* **Record:** a mono track with the microphone input, input monitoring off.
* **Export:** Song ▸ Export Stems with only the microphone track selected, or
  select the recorded event and Event ▸ Bounce Selection, then export that
  file. WAV, the song rate, no normalisation.

## Ableton Live

* **Sample rate:** Settings ▸ Audio ▸ Sample Rate (the whole Set runs at it).
* **Import:** drag the WAV to an audio track in the Arrangement View.
* **Time-stretching:** open the clip and switch **Warp off**. Live warps long
  samples automatically when *Auto-Warp Long Samples* is on (Settings ▸
  Record, Warp & Launch); warped playback is the most common reason a Live
  measurement fails.
* **Record:** a second audio track, *Audio From* the microphone input
  (mono), Monitor *Off*, armed; record in the Arrangement.
* **Export:** select the whole take in the Arrangement, File ▸ Export
  Audio/Video, *Rendered Track* = the microphone track, WAV or AIFF, the Set's
  sample rate, *Normalize* off.

## Cockos REAPER

* **Sample rate:** Project Settings ▸ Project sample rate (tick it so the
  device follows the project).
* **Import:** Insert ▸ Media file.
* **Time-stretching:** in the item properties (F2) keep the playback rate at
  1.0 and remove stretch markers.
* **Record:** arm a track with the microphone as mono input, record
  monitoring off.
* **Export:** File ▸ Render, *Source* = Selected media items (or Selected
  tracks as stems), *Bounds* = the item or the whole project, WAV, the project
  rate, normalisation off.

## Image-Line FL Studio

* **Sample rate:** Options ▸ Audio settings.
* **Import:** drag the WAV into the Playlist as an audio clip.
* **Time-stretching:** in the audio clip's settings leave stretching off
  (mode *Resample*, no time change).
* **Playback path:** the default template puts a limiter on the Master
  insert: bypass it for the measurement.
* **Record:** route the microphone input to a free Mixer insert, arm it and
  record audio into the Playlist.
* **Export:** File ▸ Export ▸ Wave file with *Split mixer tracks*, and use
  the file of the microphone's insert. WAV, the project rate.

## Bitwig Studio

* **Sample rate:** Settings ▸ Audio.
* **Import:** drag the WAV to an audio track in the Arranger.
* **Time-stretching:** set the clip's *Stretch* mode to *Off* in the
  Inspector.
* **Record:** an audio track with the microphone input, monitoring off.
* **Export:** File ▸ Export Audio with only the microphone track selected,
  WAV, the project rate.

## Audacity

* **Sample rate:** the *Project Rate* (Audio Setup ▸ Audio Settings).
* **Import:** File ▸ Import ▸ Audio.
* **Record:** turn *Overdub* on (Transport ▸ Transport Options) so the sweep
  plays while you record, and *Software Playthrough* off. Record on a new
  mono track.
* **Export:** select the recorded track and File ▸ Export ▸ Export Selected
  Audio, WAV, 24-bit or 32-bit float.

## When the report says something is wrong

| RoomScope says | What happened in the DAW | Fix |
| --- | --- | --- |
| *"a file generated at 48000 Hz was played at 44100 Hz"* | Project or export rate differs from the sweep's; no conversion | Generate the sweep at the project rate |
| *"the DAW time-stretched it"* | Warp / Flex / Follow Tempo / stretch on the sweep clip | Switch stretching off for the clip |
| *"the recording starts ... after the sweep began"* | Recording started late, or the export was trimmed | Record from before the sweep; export the whole clip |
| *"harmonic ... was folded back"* | A limiter, clipper or overloaded bus in the playback path | Bypass master and track plug-ins; lower the sweep track |
| *"flat-topped peaks ... probable clipping"* | Microphone preamp too hot | Lower the input gain |
| *"the recording contains N sweep passes"* | Loop / cycle recording, or the sweep placed twice | Record one pass |
| *"recording is silent"* | Wrong input, muted track, or the sweep track exported instead | Check the input and which track you exported |
| *"direct-sound detection confidence is low"* with none of the above | Wrong reference sweep, very noisy room, or a loudspeaker far into distortion | Use the sweep you played; lower the playback level |
