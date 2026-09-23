# Hardware test matrix

ARCHITECTURE_V1.md §7.3: executed at least once per platform before 1.0
(M10) and recorded here with the date, the RoomScope version and the
interface. Community results are accepted through the measurement issue
template with a bundle attached.

Nothing below is marked PASS that was not run on real hardware. This file
is the started matrix for milestone 0.3; the cells are empty on purpose.

| Check | macOS | Windows | Linux |
| --- | --- | --- | --- |
| Device enumeration | | | |
| Sample-rate negotiation 44.1 kHz | | | |
| Sample-rate negotiation 48 kHz | | | |
| Sample-rate negotiation 96 kHz | | | |
| Channel mapping beyond 1–2 | | | |
| Loopback capture | | | |
| Stop during playback (output silent within one callback) | | | |
| Full Standalone measurement | | | |
| Same signal through one DAW (Universal DAW Mode) | | | |

Record a row as `PASS YYYY-MM-DD, RoomScope x.y.z, <interface name>` or
`FAIL` with an issue link. Do not fill a cell from the fake backend.
