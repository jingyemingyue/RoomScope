# RoomScope 用户指南

RoomScope 用来测量录音房间，让你听到房间对近距离拾音声源做了什么。它不给房间打分，也不做校正。

英文原文见 [en.md](en.md)。

## 安装

从项目的 [Releases 页面](https://github.com/jingyemingyue/RoomScope/releases)
下载。每个 Release 都附有 `SHA256SUMS-*` 文件，可与下载文件的校验值比对
（macOS / Linux：`shasum -a 256 <文件>`；PowerShell：`Get-FileHash <文件>`）。

| 系统 | 文件 | 启动方式 |
| --- | --- | --- |
| Windows 10/11 x64 | `RoomScope-setup.exe`（安装程序）或 `roomscope-windows-x64.zip` | 开始菜单 → RoomScope，或运行 zip 里的 `roomscope-gui.exe` |
| macOS 14+，Apple 芯片 | `RoomScope-macos-arm64.dmg` | 把 RoomScope 拖进“应用程序”后打开 |
| macOS 14+，Intel | `RoomScope-macos-x86_64.dmg` | 把 RoomScope 拖进“应用程序”后打开 |
| Linux x86_64 | `roomscope-linux-x86_64.tar.gz` | `tar xzf roomscope-linux-x86_64.tar.gz && roomscope/roomscope-gui` |

Windows 和 Linux 包含两个程序：桌面程序 `roomscope-gui` 和命令行工具 `roomscope`
（在终端运行 `roomscope --help`）。macOS 上，应用的可执行文件带参数运行时就是命令行工具：
`/Applications/RoomScope.app/Contents/MacOS/RoomScope --help`。

在维护者持有签名证书之前，这些包都**没有用于分发的签名**（macOS 应用只有临时签名，未经公证；Windows 文件没有 Authenticode 签名），首次打开时系统会提示：

* **macOS：** 先打开一次应用；macOS 提示无法验证时选“完成”，然后在“系统设置 → 隐私与安全性”中点“仍要打开”（该按钮在第一次尝试后出现）并确认。从 macOS 15 Sequoia 起，右键 → 打开不再能绕过这一检查；在 macOS 14 上仍然可用（[Apple](https://developer.apple.com/news/?id=saqachfa)）。系统询问麦克风权限时请允许。打包的 NumPy 和 SciPy 需要 macOS 14 或更新版本；DMG 只在 macOS 15（Intel）和 26（Apple 芯片）的 CI 运行器上构建和启动过。
* **Windows：** SmartScreen 可能拦截，选“更多信息”→“仍要运行”。安装程序只为当前用户安装，不需要管理员权限；可在“设置 → 应用”中卸载。
* **Linux：** 需要系统自带的 PortAudio、OpenGL/EGL 和 XCB 库（Debian / Ubuntu：`sudo apt install libportaudio2 libegl1 libxkbcommon-x11-0 libxcb-cursor0`）。`packaging/linux/roomscope.desktop` 是可参考的桌面启动项。

**用 Python 安装。** RoomScope 还没有发布到 PyPI。使用 Python 3.12 或更新版本，把 Release 附带的 wheel 装进虚拟环境：

```bash
python3 -m venv roomscope-env
roomscope-env/bin/pip install "./roomscope-<version>-py3-none-any.whl[gui]"
roomscope-env/bin/roomscope gui
```

只需要命令行和 Python API 时去掉 `[gui]`。从源码开发请用 `pip install -e ".[gui]"`。

关于对话框和 `THIRD_PARTY_LICENSES/` 列出了 Qt、libsndfile 等许可证。

## 通用 DAW 模式

1. `roomscope sweep --sample-rate <工程采样率> --out sweep.wav`（或界面里的生成按钮，选择工程采样率）。把 `.roomscope-sweep.json` 和 WAV 放在一起。
2. 把 WAV 导入 DAW 新轨道，关闭时间伸缩（Warp、Flex、Follow Tempo），回放链路上不要有插件。路由到一只扬声器。
3. 用测量话筒武装第二条轨道，关闭输入监听，在扫描播放时录音。完整导出录音轨，不要裁切或标准化。
4. 可选 loopback：导出双声道（话筒 + 电回送），使用 `--channel 0 --loopback-channel 1`。
5. `roomscope analyze --recording take.wav --sweep sweep.wav --out session/`，或在界面里打开这些文件。

**Pro Tools、Logic Pro / GarageBand、Cubase / Nuendo、Studio One、Ableton Live、REAPER、FL Studio、Bitwig Studio 和 Audacity 的分步说明，以及报告中各条提示对应的 DAW 原因：[daw-setup.zh-CN.md](daw-setup.zh-CN.md)。**

## 独立模式与 loopback 线

`roomscope devices` 列出设备。`roomscope measure --out session/` 播放扫描并录音。`--input-channels 1,2 --loopback-channel 2` 在输入 2 记录电回送。

先把监听开低。超过 −12 dBFS 每次都要 `--acknowledge-level`；该确认永不保存。

**演示**（界面或 `roomscope --backend fake measure`）在合成房间上走同一流程，不会对扬声器发声。

### 各平台注意事项

`roomscope devices` 会在方括号里显示每个设备的主机 API。

* **Windows。** 同一台声卡会按每种主机 API 各列一次。优先选 `[Windows WASAPI]`（或 `[Windows WDM-KS]`）；避免 `[MME]` 和 `[Windows DirectSound]`，它们要经过 Windows 混音器。共享模式下 WASAPI 只能以设备的共享模式格式运行（[Microsoft：Device formats](https://learn.microsoft.com/en-us/windows/win32/coreaudio/device-formats)）：请在“声音”控制面板（控制面板 ▸ 硬件和声音 ▸ 声音 ▸ 设备 ▸ 属性 ▸ 高级 ▸ *默认格式*）中把它设为测量采样率，并在“设置 ▸ 声音 ▸ 设备”中把*音频增强*设为关闭（[Microsoft 支持](https://support.microsoft.com/en-us/windows/fix-sound-or-audio-problems-in-windows-73025246-b61c-40fb-671a-2535c7cd56c8)）。在“设置 ▸ 隐私和安全性 ▸ 麦克风”中允许桌面应用使用麦克风。安装包不含 ASIO 支持（ASIO DLL 用 Steinberg 的专有 SDK 构建，已被移除，见 DEPENDENCIES.md §3）；只能通过 ASIO 工作的声卡请用通用 DAW 模式测量。
* **macOS。** Core Audio。在“系统设置 ▸ 隐私与安全性 ▸ 麦克风”中允许 RoomScope；没有该权限时录音是静音，RoomScope 会报告 *“recording is silent”*。在“音频 MIDI 设置”中设定声卡采样率；输入和输出是不同设备时，可在那里把它们合成一个聚合设备。
* **Linux。** 通过系统 PortAudio（`libportaudio2`）使用 ALSA。`hw:` 设备使用声卡自身的采样率；`pipewire`、`pulse` 或 `default` 经过声音服务器，可能被重采样：RoomScope 在测量前会把设备采样率显示在请求的采样率旁边。你的用户可能需要加入 `audio` 组。

## 读结果

每个指标都有有效性标记。`insufficient_decay_range` 表示数字被收回，不是零。没有总分。

核心诊断（`warnings` / `notes` / `reason`）在 `result.json` 里始终是英文，方便跨语言对比缺陷。界面在标明这一点的标题下原样显示。

结果页有七个标签：

| 标签 | 内容 |
| --- | --- |
| 概览 | 宽带与倍频程 EDT / T20 / T30 / RT60 及有效性；文本报告；核心诊断（始终英文）。 |
| 脉冲响应 | 反卷积后的 IR。峰值是直达声，不会归一化到 1.0。 |
| 频率响应 | 原始（点线）与平滑（实线）幅度。虚线是电 loopback（仅在补偿成功时）。0 dB 是接口，不是“房间是平的”。 |
| 衰减 | Schroeder / 能量衰减曲线。宽带为实线；倍频程用不同虚线，不只靠颜色区分。 |
| 噪声 | 安静段频谱和 50/60 Hz 交流声候选。 |
| 早期反射 | ETC 峰值（延时 ms，相对直达声的 dB）。 |
| 摆位 | 多余路径；只有卷尺量过扬声器距离时才给出扬声器高度、设备上方平面和水平间距。不给墙面命名。 |

低频共振候选写在概览文本报告里（以及 `roomscope export` 的 `resonances.csv`），没有单独标签。

## 摆位

结果页有“摆位”标签。没有卷尺量的扬声器距离时，RoomScope 只报告每条到达的多余路径。有了距离（以及要求垂直轴时的话筒高度）后，会报告扬声器高度、两个设备上方的平面和水平间距。它从不给墙面命名，也不给出房间长宽。

在通用 DAW 模式或独立模式的分析之前填入卷尺数字，或在命令行使用 `--speaker-distance` / `--mic-height` / `--temperature`。

## 对比两个位置

`roomscope compare baseline/ candidate/ --same-input-gain`（或界面的对比页）。只有两侧都是 VALID 时，衰减差值才是 VALID。噪声差值需要明确声明“输入增益未变”。变化从不被称为显著；ISO 3382-1 对 T 的刚可察觉差只作为背景引用。

对比页列出配对的早期反射（延时 ±0.5 ms）和低频共振（1/6 倍频程内，并比较 decay-distinguishable 标志）。`roomscope compare … --out comparison.json` 只写入数字；`roomscope show comparison.json` 会再打印报告并**重新生成**解读（解读从不写入该文件）。

## 项目与平均

项目文件夹包含 `project.json` 和普通会话文件夹。
`roomscope project init --out room/ --name Booth`，再
`roomscope project add room/ session/ --position desk`。
`roomscope project average room/` 只平均有效的 T 值，从不平均衰减曲线，并标出位置数量达到的 ISO 3382-2 等级。

## 导出与语言

`roomscope export session/ --format csv --out curves/` 导出每条曲线。
`--lang zh_CN`（或设置 → 语言，或 `ROOMSCOPE_LANG`）会翻译解读、文本报告标签、界面和命令行帮助（`roomscope --help` 及每个子命令）。单位不翻译；数字保持 ASCII。`roomscope.core` 的诊断字符串保持英文。

## 排错

| 现象 | 检查 |
| --- | --- |
| 直达声置信度不高 | 扫频侧车文件不对；扬声器失真；不要裁切录音。 |
| 参考扫频不对 | WAV 旁的 `.roomscope-sweep.json` 必须是 RoomScope 为**这次**扫描写出的文件（同一时长、频带和淡入淡出）。用另一次会话的侧车，或把录音本身当参考，都会找错 IR。 |
| 一次导出里有多遍扫描 | 只播放一遍。同一 WAV 里两遍扫描会像两条 IR；RoomScope 保留最强峰，其余被当成“房间”。一次只导出一条 take。 |
| 削波警告 | 降低回放或输入增益。 |
| 衰减范围不足 | 加长扫描、略提高回放，或换更安静的房间。 |
| 设备采样率不符 | 界面会在请求采样率旁边显示设备实际采样率。 |
| loopback 被拒绝 | 回送必须像电脉冲，不能是房间响应。若第二声道是另一支话筒，补偿会被拒绝，分析在未补偿路径上继续。 |

## 报告问题

**帮助 ▸ 用于问题报告的环境报告** 显示维护者首先需要的信息：RoomScope 版本和构建提交、操作系统、库版本、设置和音频设备（*探测采样率* 会加上每个设备接受的采样率，不会播放任何声音）。用 *复制* 把它粘贴到 issue 中；*打开 Issue 页面* 会打开模板选择页。在终端中同样的报告是 `roomscope doctor`（`--probe`、`--json`）。RoomScope 不会自动发送任何内容；发布前请检查文本，因为设备名称可能包含个人姓名。

`roomscope session bundle session/ --out report.zip` 打包会话。
`--no-audio` 可去掉 WAV，避免分享房间录音。把 zip 附在测量类 issue 上。设置和滚动日志在 `$ROOMSCOPE_HOME`（默认 `~/.roomscope`），报告中的 *打开数据文件夹* 按钮会打开它。

用真实声卡或通过 DAW 运行过 RoomScope？请使用 *Audio interface test report* 和 *DAW compatibility report* 模板记录结果；这些真实运行是 [HARDWARE_TESTS.md](../HARDWARE_TESTS.md) 的唯一来源。
