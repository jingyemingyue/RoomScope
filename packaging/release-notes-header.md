**RoomScope {version}** is a pre-release of an open-source, DAW-independent
recording-room analyzer: exponential sine sweep, impulse response, EDT / T20 /
T30, frequency response, noise, early reflections and low-frequency
resonances, with a validity flag on every number.

> **Pre-release.** Everything was tested against synthetic rooms only; no
> result has been validated on real measurement hardware yet. The desktop
> bundles are **unsigned**.

### Download

| System | File | Start |
| --- | --- | --- |
| Windows 10/11 x64 | `RoomScope-setup.exe` (installer, no admin rights) or `roomscope-windows-x64.zip` | Start menu → RoomScope / `roomscope-gui.exe` |
| macOS 13+, Apple silicon | `RoomScope.dmg` | Drag to Applications, right-click → Open the first time |
| Linux x86_64 | `roomscope-linux-x86_64.tar.gz` | `roomscope/roomscope-gui` |
| Python 3.12+ (any OS) | `roomscope-{version}-py3-none-any.whl` | `pip install "./roomscope-{version}-py3-none-any.whl[gui]"` |

Checksums are in `SHA256SUMS-*`; a CycloneDX SBOM and the pinned bundle lock
are attached. Gatekeeper / SmartScreen steps, the Linux system libraries and
the first measurement are in the
[user guide](https://github.com/jingyemingyue/RoomScope/blob/v{version}/docs/user-guide/en.md)
([简体中文](https://github.com/jingyemingyue/RoomScope/blob/v{version}/docs/user-guide/zh-CN.md)).
Start with the monitor level low: RoomScope never changes system volume.

---

