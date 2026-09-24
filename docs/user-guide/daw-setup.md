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

* **Sample rate:** set when the session is created; Session Setup shows it
  [P1, p. 1814]. Generate the sweep at that rate.
* **Import:** File ▸ Import ▸ Audio [P1, p. 641]. If the Import Audio dialog's
  comments field warns that the file's rate differs from the session's
  [P1, p. 643], generate the sweep at the session rate instead of enabling
  *Apply SRC*.
* **Time-stretching:** leave Elastic Audio off: the track's Elastic Audio
  selector reads *None – Disable Elastic Audio* [P1, p. 1317].
* **Record:** a new mono audio track with the microphone input,
  record-enabled. With TrackInput off the track is in Auto Input mode, which
  still plays the input while recording [P1, pp. 768–769]: pull the
  microphone track's fader down, which does not affect the recording.
  Clear the inserts on the sweep track and on the master fader.
* **Export:** select the recorded clip and use *Export Clips as Files* from
  the Clip List menu [P1, p. 649]: WAV, mono, the session rate and bit depth
  (converting 32-bit float to 24-bit adds dither). Pro Tools writes Broadcast
  WAV; RoomScope reads it as is.

## Apple Logic Pro and GarageBand

* **Sample rate:** File ▸ Project Settings ▸ Audio ▸ Sample Rate [G1]. The
  Assets tab of Project Settings has *Convert audio file sample rate when
  importing* [G1]; generating the sweep at the project rate makes it moot.
  GarageBand for Mac has no sample-rate setting in its guide; generate the
  sweep at 44.1 kHz (`--sample-rate 44100`), the rate GarageBand's iPhone/iPad
  guide names for imports [G9].
* **Import:** Logic: File ▸ Import ▸ Audio File, or drag the WAV to a track
  [G2]. GarageBand: drag the WAV onto a track [G8].
* **Time-stretching:** Logic 12.3: in the Region inspector untick *Flex* and
  set *Smart Tempo* to *Off* [G3] (Logic 10.4–12.2: *Flex & Follow* = *Off*
  [G4]); in File ▸ Project Settings ▸ Smart Tempo set *Set Imported Files To*
  to *Flex Off* and untick *Trim start of new regions* [G5]. GarageBand: in the
  audio editor untick *Follow Tempo and Pitch* and leave *Enable Flex* off
  [G10].
* **Record:** a mono audio track with the microphone input. Logic's software
  monitoring is on by default and plays the input of a recording track [G6]:
  turn it off (Settings ▸ Audio ▸ General) or pull the track's fader down. Turn
  Cycle off. Logic's recording file (CAF, WAVE/BWF or AIFF) can be analysed
  directly [G7].
* **Export:** Logic: select the recorded region, File ▸ Export ▸ *1 Region as
  Audio File*, WAV or AIFF, *Normalize* Off, *Bypass Effect Plug-ins* on
  [G11]. GarageBand: mute the sweep track, turn *Export projects at full
  volume* off (Settings ▸ Advanced; it normalises the export) [G12] and use
  Share ▸ Export Song to Disk as WAVE or AIFF [G13]. That export trims silence
  at the start and end of the project [G13]; the microphone's room noise before
  the sweep is not digital silence, but check that the exported file starts
  before the sweep.

## Steinberg Cubase and Nuendo

* **Sample rate:** Project ▸ Project Setup [C1].
* **Import:** File ▸ Import ▸ Audio File [C2]. The import options dialog
  (shown when Preferences ▸ Editing ▸ Audio ▸ *On Import Audio Files* is set to
  *Open Options Dialog*) offers *Convert to Project Settings* when the file's
  rate or bit depth differs [C2]; generate the sweep at the project rate so no
  rate conversion is needed.
* **Time-stretching:** keep *Musical Mode* off for the sweep clip (Sample Editor
  or Pool; ACID-tagged files switch it on automatically) [C3].
* **Record:** a mono audio track with the microphone input. Every Auto
  Monitoring mode except *Manual* (Preferences ▸ VST) switches monitoring on
  while a track is record-enabled [C4]: set it to *Manual*. Check that the
  Control Room has no insert or room-correction plug-in on the monitor path,
  or bypass it [C5].
* **Export:** File ▸ Export ▸ Selected Events with *Processing* = *Dry* [C6];
  or set the locators to the take and use File ▸ Export ▸ Audio Mixdown with
  *Channel Selection* = *Single*, the microphone channel [C7]. (Audio ▸ Bounce
  Selection also works; it writes the new file into the project's Audio
  folder and applies event fades and volume [C8].)

## Fender Studio Pro (formerly PreSonus Studio One)

Studio One became Fender Studio Pro with version 8 (January 2026), and
"Song" became "Session" [S1, S2]; the older menu names are in brackets.

* **Sample rate:** Session ▸ Session Setup (Song ▸ Song Setup before v8)
  [S2, S6].
* **Import:** drag the WAV from the Browser to an audio track [S3].
* **Time-stretching:** in the **Track** Inspector set the track's *Tempo* mode
  to *Don't Follow* [S4]; in the Event Inspector keep *Speedup* at 1,
  *Transpose* and *Tune* at 0 and *Normalize* off. A gear-wheel icon on an
  event means it is being resampled or stretched [S4].
* **Record:** a mono track with the microphone input. Monitoring switches on
  automatically when Record is enabled [S5]: switch the Monitor button off
  after arming.
* **Export:** right-click the recorded event ▸ *Export Selection* [S7], or
  Session ▸ Export Stems (Song ▸ Export Stems before v8) with only the
  microphone track selected (a stem includes the track's inserts) [S7]. WAV,
  the session rate, no normalisation.

## Ableton Live

* **Sample rate:** Settings (Options ▸ Settings on Windows, Live ▸ Settings on
  macOS) ▸ Audio ▸ *In/Out Sample Rate* [L1]. Live converts a file at another
  rate in real time, which its Audio Fact Sheet calls non-neutral [L2]: one
  more reason to generate the sweep at the Set's rate.
* **Import:** drag the WAV to an audio track in the Arrangement View.
* **Time-stretching:** open the clip and switch **Warp off** in the Clip
  View [L3]. *Auto-Warp Long Samples* (Settings ▸ Record, Warp & Launch) is on
  by default [L4], so a long test file is warped unless you switch it off.
* **Record:** a second audio track, *Audio From* the microphone input
  (mono), Monitor *Off*, armed; record in the Arrangement [L5].
* **Export:** select the whole take in the Arrangement, File ▸ Export
  Audio/Video, *Rendered Track* = the microphone track, *Include Return and
  Main Effects* off, WAV or AIFF, the Set's sample rate, *Normalize* off [L6].
  *Create Fades on Clip Edges* adds fades of at most 4 ms [L2]; the test file
  starts and ends with silence, so they do not touch the sweep.

## Cockos REAPER

* **Sample rate:** File ▸ Project Settings ▸ tick *Project sample rate*
  [R1, p. 32], and enable *Allow projects to override device sample rate* in
  Preferences ▸ Audio ▸ Device so that the interface follows the project [R2].
  REAPER converts items at another rate in real time [R1, p. 32].
* **Import:** Insert ▸ Media file [R1, p. 90].
* **Time-stretching:** in the Item Properties (F2) keep *Playback rate* at 1.0,
  leave *Preserve pitch* off and remove stretch markers [R1, p. 134].
* **Record:** arm a track with the microphone as mono input, record
  monitoring off.
* **Export:** File ▸ Render, *Source* = *Selected media items* (or
  *Stems (selected tracks)*), WAV, the project rate; normalisation stays off
  unless set under *Postprocess…* [R1, pp. 411–415]. Default item fades
  (Preferences ▸ Project ▸ Item Fade Defaults) fall on the silence at both ends
  of the test file.

## Image-Line FL Studio

* **Sample rate:** Options ▸ Audio settings (F10) ▸ *Sample Rate*; exports use
  this rate [F1].
* **Import:** drag the WAV into the Playlist as an audio clip.
* **Time-stretching:** in the clip's channel settings keep the mode
  *Resample* and the *Time* knob at *(none)*, the defaults [F2]. The default
  declicking adds a 10 ms fade-out [F2], which falls on the test file's
  closing silence.
* **Playback path:** since FL Studio 20.7 the default template is "Basic 808
  with limiter" [F3]; bypass the limiter on the Master insert for the
  measurement.
* **Record:** route the microphone input to a free Mixer insert. Live inputs
  are routed to the Master and back to the outputs by default [F4], so set the
  insert's *Monitor external input* to *Off* (it can feed back otherwise) and
  switch *Loop record* off, which is on by default and stacks takes [F4].
  Arm the insert and record audio into the Playlist.
* **Export:** File ▸ Export ▸ Wave file with *Split mixer tracks*, and use
  the file of the microphone's insert (muted tracks are skipped) [F5]. WAV,
  the project rate.

## Bitwig Studio

* **Sample rate:** Dashboard ▸ Settings ▸ Audio [B1].
* **Import:** drag the WAV to an audio track in the Arranger. Dashboard ▸
  Settings ▸ Audio Import can be set to *Original speed [Raw]* [B2].
* **Time-stretching:** in the Inspector set the clip's *Stretch* ▸ *Mode* to
  *Raw*, which ignores stretch data and plays the file at its original speed
  [B2]. (There is no *Off* mode.)
* **Record:** an audio track with the microphone input, monitoring off.
* **Export:** File ▸ Export Audio with only the microphone track selected,
  WAV, sample rate *Current* (no conversion) [B3].

## Audacity

* **Sample rate:** *Project Sample Rate* in the *Quality* section of Audio
  Setup ▸ Audio Settings [A1].
* **Import:** File ▸ Import ▸ Audio [A2].
* **Record:** in Transport ▸ Transport Options turn *Hear other tracks during
  recording* on and *Enable audible input monitoring* off (*Overdub* and
  *Software Playthrough* in older versions) [A3]. Set Audio Setup ▸ Recording
  Channels to 1 (Mono), put the cursor at the start and use **Record New
  Track** (Shift+R): plain Record starts at the end of the selected track,
  after the sweep [A4].
* **Export:** select the recorded track and use File ▸ Export Audio… with
  *Export Range* = *Current Selection*, WAV, *Signed 24-bit PCM* or *32-bit
  float* [A5]. (*Export Selected Audio* was removed in Audacity 3.4 [A6].)

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

## Sources

Menu names and defaults above were checked against these pages (2026-09):

* [P1] Avid, Pro Tools Reference Guide 2026.4 — https://resources.avid.com/SupportFiles/PT/Pro_Tools_Reference_Guide_2026.4.pdf
* [G1] Apple, Logic Pro User Guide, Set the project sample rate — https://support.apple.com/guide/logicpro/set-the-project-sample-rate-lgcpce0958b8/mac
* [G2] Apple, Logic Pro User Guide, Add and delete audio files — https://support.apple.com/guide/logicpro/add-and-delete-audio-files-lgcp1bb0ad7d/mac
* [G3] Apple, Logic Pro User Guide, Choose the Smart Tempo setting — https://support.apple.com/guide/logicpro/choose-the-smart-tempo-setting-lgcpb7abb9cc/mac
* [G4] Apple, Logic Pro 12.2 User Guide, Flex & Follow — https://support.apple.com/guide/logicpro/lgcpb7abb9cc/12.2/mac/15.6
* [G5] Apple, Logic Pro User Guide, Smart Tempo project settings — https://support.apple.com/guide/logicpro/smart-tempo-project-settings-lgcp6ad7156e/mac
* [G6] Apple, Logic Pro User Guide, General settings (software monitoring) — https://support.apple.com/guide/logicpro/general-settings-lgcp0ed343a9/mac
* [G7] Apple, Logic Pro User Guide, Recording settings — https://support.apple.com/guide/logicpro/recording-settings-lgcp411dd5c8/mac
* [G8] Apple, GarageBand for Mac User Guide, Import audio and MIDI files — https://support.apple.com/guide/garageband/import-audio-and-midi-files-gbndd01649ed/mac
* [G9] Apple, GarageBand for iPhone User Guide (imports converted to 44.1 kHz) — https://support.apple.com/guide/garageband-iphone/
* [G10] Apple, GarageBand for Mac User Guide, Intro to the Audio Editor — https://support.apple.com/guide/garageband/intro-to-the-audio-editor-gbndca7725e3/mac
* [G11] Apple, Logic Pro User Guide, Export regions as audio files — https://support.apple.com/guide/logicpro/export-regions-as-audio-files-lgcp8e5ce2d3/mac
* [G12] Apple, GarageBand for Mac User Guide, Change Advanced settings — https://support.apple.com/guide/garageband/change-advanced-settings-gbnded6e79bc/mac
* [G13] Apple, GarageBand for Mac User Guide, Export songs to disk — https://support.apple.com/guide/garageband/export-songs-to-disk-or-icloud-gbnd7cbf5ed9/mac
* [C1]–[C8] Steinberg, Cubase Pro / Nuendo 15 help (steinberg.help): Project Setup; Import Options dialog (`importing_audio_and_midi_open_options_dialog_r`); Musical Mode; Auto Monitoring (Preferences ▸ VST); Control Room; Export Selected Events (`parts_and_events_export_selected_events_r`); Export Audio Mixdown options (`export_audio_mixdown_options_r`); Bounce Selection (`parts_and_events_from_events_new_files_creating_t`) — https://steinberg.help/r/cubase-pro/15.0/en/
* [S1] synthanatomy.com, report on the Fender Studio Pro 8 release (January 2026; third-party)
* [S2]–[S7] Fender Studio Pro 8.1 manual: Events; The Browser ▸ Files tab; Timestretching and Track/Event Inspectors; Audio Tracks; Session Setup; Exporting Audio and MIDI Files — https://fenderstudiopromanual.fender.com/en/Content/ (Studio One 5 Reference Manual for pre-v8 names)

* [L1] Ableton, Live 12 manual, First Steps — https://www.ableton.com/en/live-manual/12/first-steps/
* [L2] Ableton, Live 12 manual, Audio Fact Sheet — https://www.ableton.com/en/live-manual/12/audio-fact-sheet/
* [L3] Ableton, Live 12 manual, Clip View — https://www.ableton.com/en/live-manual/12/clip-view/
* [L4] Ableton, manual, Audio Clips, Tempo and Warping — https://www.ableton.com/en/manual/audio-clips-tempo-and-warping/
* [L5] Ableton, Live 12 manual, Routing and I/O — https://www.ableton.com/en/live-manual/12/routing-and-i-o/
* [L6] Ableton, Live 12 manual, Managing Files and Sets — https://www.ableton.com/en/live-manual/12/managing-files-and-sets/
* [R1] Cockos, REAPER User Guide 7.80 — https://www.reaper.fm/userguide/ReaperUserGuide780.pdf
* [R2] RØDE, RØDECaster Pro II multitrack guidelines for REAPER (PC) — https://edge.rode.com/pdf/page/2004/modules/5489/RCPII_Multitrack_Guidelines_Reaper_PC.pdf
* [F1] Image-Line, FL Studio manual, Audio Settings — https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/envsettings_audio.htm
* [F2] Image-Line, FL Studio manual, Sampler channel settings — https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/chansettings_sampler.htm
* [F3] Image-Line, FL Studio 20.7 release notes — https://www.image-line.com/fl-studio-news/fl-studio-207-released
* [F4] Image-Line, FL Studio manual, Recording audio — https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/recording_audio.htm
* [F5] Image-Line, FL Studio manual, Export — https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/fformats_save_export.htm
* [B1] Bitwig Studio user guide, The Dashboard — https://www.bitwig.com/userguide/latest/the_dashboard/
* [B2] Bitwig Studio user guide, Inspecting audio clips — https://www.bitwig.com/userguide/latest/inspecting_audio_clips/
* [B3] Bitwig Studio user guide, Exporting audio — https://www.bitwig.com/userguide/latest/exporting_audio/
* [A1] Audacity manual, Audio Settings Preferences — https://manual.audacityteam.org/man/audio_settings_preferences.html
* [A2] Audacity manual, File Menu — https://manual.audacityteam.org/man/file_menu.html
* [A3] Audacity manual, Transport Options — https://manual.audacityteam.org/man/transport_menu_transport_options.html
* [A4] Audacity manual, Recording — https://manual.audacityteam.org/man/transport_menu_recording.html
* [A5] Audacity manual, Export dialog — https://manual.audacityteam.org/man/file_export_dialog.html
* [A6] Audacity forum, "What happened to Export Selected Audio?" — https://forum.audacityteam.org/t/what-happened-to-export-selected-audio/88742
