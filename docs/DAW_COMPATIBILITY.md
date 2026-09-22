# DAW compatibility matrix (macOS)

Status: **skeleton, 2026-09-22.** No row is green yet. A DAW is
"supported" only when its row below carries a green chain-check verdict
with the DAW version, the macOS version, the date and a fixture. Everything
else is *untested*, whatever the design says about WAV in / WAV out. The
procedure behind every row is [user-guide/daw/README.md](user-guide/daw/README.md)
(Chinese: [user-guide/daw/README.zh-CN.md](user-guide/daw/README.zh-CN.md));
the chain check itself is specified in
[ARCHITECTURE_V1.md §5.4](ARCHITECTURE_V1.md#54-the-chain-check-corechain_checkpy-roomscope-check).

## Tiers

* **Tier A — first (milestone 0.2 exit criterion):** Logic Pro, Studio One
  Pro, Cubase (the Cubase recipe also covers Nuendo, which gets its own
  row). Draft recipes exist for all three.
* **Tier B — before 1.0-rc:** Pro Tools, Ableton Live, REAPER, FL Studio,
  Bitwig Studio, Digital Performer. No recipe yet.

## How a row turns green

1. Follow the DAW's recipe on a real installation with a real interface.
2. Run the chain check in DAW form (`roomscope check --recording … --sweep …
   --daw "<name> <version>"`) on the recording obtained **both** ways the
   recipe describes (the recorded file, and the export).
3. Both verdicts PASS → record the row, correct the recipe where the menus
   differed, drop the DRAFT mark, and commit the loopback recording (a few
   seconds) under `tests/fixtures/daw/<name>/` with a README stating the
   DAW version, the interface and a CC0 declaration.
4. A FAIL that the recipe cannot prevent is an issue against RoomScope (a
   detector or reader gap) or a documented limitation of that DAW; the row
   stays red with the reason.

Rows are re-run on every RoomScope release candidate and whenever a DAW's
major version changes. Community rows (other versions, other DAWs) are
welcome through the measurement issue template with the session bundle
attached; they are recorded with "community" in the *Run by* column.

## Matrix

Verdict values: **PASS**, **PASS w/ warnings**, **FAIL**, **untested**.

| Tier | DAW | Recipe | DAW version | macOS | Interface | Rate | File obtained by | Verdict | Fixture | Date | Run by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | Logic Pro | [draft](user-guide/daw/logic-pro.md) | — | — | — | — | — | untested | — | — | — |
| A | Studio One Pro | [draft](user-guide/daw/studio-one.md) | — | — | — | — | — | untested | — | — | — |
| A | Cubase Pro | [draft](user-guide/daw/cubase.md) | — | — | — | — | — | untested | — | — | — |
| A | Nuendo | [draft (Cubase)](user-guide/daw/cubase.md) | — | — | — | — | — | untested | — | — | — |
| B | Pro Tools | none | — | — | — | — | — | untested | — | — | — |
| B | Ableton Live | none | — | — | — | — | — | untested | — | — | — |
| B | REAPER | none | — | — | — | — | — | untested | — | — | — |
| B | FL Studio | none | — | — | — | — | — | untested | — | — | — |
| B | Bitwig Studio | none | — | — | — | — | — | untested | — | — | — |
| B | Digital Performer | none | — | — | — | — | — | untested | — | — | — |

## Known DAW-side behaviours to watch (from the recipes)

| DAW | Where the sweep can be altered | Where the export can be altered |
| --- | --- | --- |
| Logic Pro | Smart Tempo *Set imported audio files to*; region *Flex & Follow*; Varispeed | *Export Region* Normalize (Off / Overload Protection Only / On); Bounce normalises by default |
| Studio One Pro | *Stretch audio files to Song tempo*; event *Tempo* (Follow / Timestretch); *Speedup* | dither on exports below 32-bit float |
| Cubase / Nuendo | *Musical Mode* (auto for tempo-tagged files only); *Import Options* rate conversion; Control Room inserts in the monitor path | Stereo Out inserts are included in *Audio Mixdown* |

The integrity step of the analysis (speed, stretch, skew, passes) catches
every one of these regardless of DAW; the recipes exist so that users do not
hit them in the first place.
