# RoomScope user guide

RoomScope measures a recording room so you can hear what the room is doing to
close-miked sources. It does not score the room and it does not correct it.

This page is the English guide. The Chinese translation is
[zh-CN.md](zh-CN.md).

## Install

**From Python (pipx).** `pipx install "roomscope[gui]"` gives you the `roomscope`
command without a virtual environment you have to manage. `pip install -e ".[gui]"`
is the developer install from a clone.

**Unsigned desktop bundle.** The `release.yml` workflow builds one-directory
bundles for macOS, Windows and Linux. Until the maintainer holds signing
identities they are **unsigned**:

* **macOS:** right-click the app → Open, or System Settings → Privacy & Security
  after Gatekeeper blocks it. Grant microphone access when asked
  (`NSMicrophoneUsageDescription` is in the bundle Info.plist).
* **Windows:** SmartScreen may warn; choose “More info” → “Run anyway”.
* **Linux:** extract the directory and run `roomscope`. An AppImage may follow.

The About dialog and `THIRD_PARTY_LICENSES/` list Qt, libsndfile and the other
bundled licenses.

## Universal DAW Mode

1. `roomscope sweep --out sweep.wav` (or the GUI “Universal DAW Mode” generate
   button). Keep the `.roomscope-sweep.json` sidecar next to the WAV.
2. Import the WAV on a new DAW track. Route it to the monitors.
3. Arm a second track with the measurement microphone. Do not trim the bounce.
4. Optional loopback: bounce a two-channel export (microphone + electrical
   return) and pass `--channel 0 --loopback-channel 1`.
5. `roomscope analyze --recording take.wav --sweep sweep.wav --out session/`
   or drop the files in the GUI.

Per-DAW notes from users belong in issues labelled `good first issue`.

## Standalone Mode and the loopback cable

`roomscope devices` lists interfaces. `roomscope measure --out session/` plays
the sweep and records. `--input-channels 1,2 --loopback-channel 2` records an
electrical return on input 2.

Start at a low monitor level. Levels above −12 dBFS need `--acknowledge-level`
every time; that confirmation is never saved.

**Demo** (GUI or `roomscope --backend fake measure`) runs the same flow on a
synthetic room. Nothing is sent to a loudspeaker.

## Reading a result

Each metric has a validity flag. `insufficient_decay_range` means the number is
withheld, not that it is zero. There is no single score.

Core diagnostics (`warnings`, `notes`, `reason`) stay in English in
`result.json` so bug reports compare across languages. The UI shows them
verbatim under a heading that says so.

## Comparing two positions

`roomscope compare baseline/ candidate/ --same-input-gain` (or the GUI Compare
page). A decay delta is only VALID when both sides are VALID. The noise delta
needs an explicit “input gain unchanged” declaration. A change is never called
significant; ISO 3382-1’s just-noticeable difference for T is quoted as context.

## Projects and averaging

A project folder holds `project.json` and ordinary session folders.
`roomscope project init --out room/ --name Booth` then
`roomscope project add room/ session/ --position desk`.
`roomscope project average room/` averages VALID T values only, never decay
curves, and names the ISO 3382-2 class the position counts reach.

## Export and language

`roomscope export session/ --format csv --out curves/` writes every curve.
`--lang zh_CN` (or Settings → Language, or `ROOMSCOPE_LANG`) translates
findings, the report labels, the GUI and the CLI. Units stay untranslated;
digits stay ASCII.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Direct-sound confidence not high | Wrong sweep sidecar; loudspeaker distortion; trim the recording? Do not trim. |
| Clipping warning | Lower playback or input gain. |
| Insufficient decay range | Longer sweep, slightly louder playback, or a quieter room. |
| Device rate mismatch | The GUI shows the device rate next to the requested one; pick a supported rate. |
| Loopback refused | The return must look like an electrical pulse, not a room. |

## Bug-report bundle

`roomscope session bundle session/ --out report.zip` zips the folder.
`--no-audio` leaves the WAVs out if you do not want to share a recording of
the room. Attach the zip to a measurement issue. Settings and the rotating
log live under `$ROOMSCOPE_HOME` (`~/.roomscope` by default).
