# 兼容性

以英文版 [COMPATIBILITY.md](COMPATIBILITY.md) 为准（含每一行的完整验证方式）。最后审查：2026-09-24。

## 操作系统与安装包

| 平台 | 交付物 | 验证方式 |
| --- | --- | --- |
| Windows 10/11 x64 | `RoomScope-setup.exe`、`roomscope-windows-x64.zip` | `windows-latest` 上的发布工作流：冻结包冒烟测试（命令行、模拟测量、离屏界面、无参数启动窗口启动器），用 Inno Setup 构建安装程序，按用户安装后在安装目录冒烟测试，再卸载；Windows / Python 3.12 上的 CI 测试 |
| macOS 14+，Apple 芯片 | `RoomScope-macos-arm64.dmg` | `macos-latest`（macOS 26）上的发布工作流：挂载 DMG、复制应用、`gui --smoke`、模拟 Finder 启动、验证临时签名、`lipo` 架构为 arm64、启动启用 hardened runtime 的副本；macOS / Python 3.12 上的 CI 测试。macOS 14 是打包的 NumPy / SciPy wheel 的最低版本（`macosx_14_0`，`LSMinimumSystemVersion` 14.0），尚未实际运行过 |
| macOS 14+，Intel | `RoomScope-macos-x86_64.dmg` | `macos-15-intel`（macOS 15）上的发布工作流：同样的 DMG 检查，架构为 x86_64 |
| Linux x86_64 | `roomscope-linux-x86_64.tar.gz` | `ubuntu-latest` 上的发布工作流及本地构建（`scripts/build_release.py`）；Ubuntu / Python 3.12–3.14 上的 CI 测试 |
| 其他（ARM Windows / Linux、更旧的 macOS） | 仅 wheel | 未验证 |

尚无安装包在真实音频硬件上被个人使用过（[HARDWARE_TESTS.md](HARDWARE_TESTS.md)）；上表均为 CI 与本地构建结果。

## Python 与依赖

最低声明版本：Python 3.12、NumPy 1.26、SciPy 1.12、soundfile 0.12、sounddevice 0.4.6、matplotlib **3.10**、PySide6_Essentials 6.6；已检查的最新版本：Python 3.14、NumPy 2.5.3、SciPy 1.18.1、soundfile 0.14.0、sounddevice 0.5.6、matplotlib 3.11.2、PySide6_Essentials 6.11.2。2026-09-24 在 Python 3.12 上安装全部最低版本、在 3.13 和 3.14 上安装最新版本并运行完整测试套件验证。matplotlib 3.8 / 3.9 的 wheel 仍包含 `_ttconv` 扩展（[DEPENDENCIES.md](DEPENDENCIES.md) §6），因此下限提高到 3.10。

## 录音文件（通用 DAW 模式）

同一段录音以以下封装测试（`tests/integration/test_daw_exports.py`）：WAV（16 / 24 / 32 位 PCM、32 位浮点）、WAVE_FORMAT_EXTENSIBLE、带 `bext`/`iXML`/`JUNK` 块的 Broadcast WAV（Pro Tools）、RF64、Wave64、AIFF、CAF（Logic Pro 录音）和 FLAC；单声道话筒的单声道与立体声导出。采样率 44.1–192 kHz。DAW 以错误速度播放扫描时会被诊断出来（[MEASUREMENT_METHODOLOGY.md](MEASUREMENT_METHODOLOGY.md) §2b）。

## DAW

Pro Tools、Logic Pro、GarageBand、Cubase / Nuendo、Fender Studio Pro（Studio One）、Ableton Live、REAPER、FL Studio、Bitwig Studio 和 Audacity 的分步说明见 [user-guide/daw-setup.zh-CN.md](user-guide/daw-setup.zh-CN.md)，每一步均按厂商当前手册核对（来源列于该页）。**尚未在真实硬件上用任何 DAW 运行过 RoomScope**。

## 音频主机 API（独立模式）

PortAudio 提供的所有主机 API 都会被列出和探测（`roomscope devices --probe`）；输入与输出保持在同一主机 API，播放前检查声道，使用两个独立设备时给出警告。各主机 API 的行为及出处见 [AUDIO_DEVICES.zh-CN.md](AUDIO_DEVICES.zh-CN.md)。以模拟设备表和合成后端验证；**尚未用真实声卡验证**。

## 跨平台行为

2026-09-24 审查并修复，测试模拟对应平台（`tests/unit/test_cross_platform.py`）：Windows 管道输出使用 UTF-8、可移植的 `project.json` 路径、大小写不敏感文件系统（已在 macOS 和 Windows CI 上确认）、Windows 多进程日志轮转、Windows 显示语言与 `zh-Hans` 区域标记、Windows 无法转换的日期、写入自身文件夹的会话打包。包内所有文件读写都显式使用 `encoding="utf-8"`；非 ASCII 路径可用。
