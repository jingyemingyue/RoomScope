# 用 DAW 测量

通用 DAW 模式适用于任何能在播放一个 WAV 的同时录制另一个的 DAW。RoomScope 从不与 DAW 通信，它只需要完整导出的录音。本页先列出每个 DAW 都必须做对的事，再给出常用 DAW 的具体步骤。英文原文见 [daw-setup.md](daw-setup.md)。

> 下面的菜单名称取自各 DAW 近期版本的官方文档，尚未在每个 DAW 上用真实硬件逐一验证（[HARDWARE_TESTS.md](../HARDWARE_TESTS.md)）。如果你的版本不同，请提交 *Measurement problem* issue，以便修正。

## 每个 DAW 都必须做到

1. **采样率一致。** 按工程采样率生成测试信号：`roomscope sweep --sample-rate 44100 --out sweep_44k.wav`，或在界面步骤 1 中选择采样率。48 kHz 的文件在 44.1 kHz 工程里未经转换直接播放会慢 8 %，无法解卷积；这时 RoomScope 会报告 *“a file generated at 48000 Hz was played at 44100 Hz”*。把 `.roomscope-sweep.json` 与 WAV 放在一起。
2. **不做时间伸缩。** 测试信号片段必须关闭 Warp、Flex Time、Follow Tempo、Elastic Audio 及各种伸缩模式。扫描速度不对时，RoomScope 会报告 *“the DAW time-stretched it”*。
3. **干净的回放链路。** 旁通测试信号轨道、它经过的总线以及主输出上的所有插件：限幅器、削波器、“响度”或磁带插件，以及**房间校正**插件（SoundID Reference、ARC 等）——除非你就是要测校正后的系统。测试信号上不要有淡入淡出、片段增益或自动化。推子或片段增益低于 0 dB 没有关系。
4. **只用一只扬声器。** 把测试信号轨道路由到要测的那一只扬声器（声像打到底或用单声道输出）。两只扬声器播放同一扫描会相互干涉，结果哪一只都不代表。
5. **在单独的单声道轨道上录话筒**，关闭输入监听（否则话筒会经扬声器回授）。在测试信号开始前开始录音，或一次录完整个片段：文件开头的一秒静音就是为此准备的。只录一遍：关闭循环录音。
6. **完整导出录音轨或片段**，采用工程采样率，格式为 WAV（Broadcast WAV、RF64、Wave64 均可）、AIFF、CAF 或 FLAC，24 位或 32 位浮点，**不要标准化**（标准化会掩盖你在不同录音间比较的底噪电平）。单声道或立体声都可以；立体声文件请在界面中或用 `--channel` 选择话筒声道。不要裁切：RoomScope 会自己找到扫描，扫描之后的静音就是衰减。
7. **延迟无关紧要。** RoomScope 会在录音中任何位置找到扫描，插件延迟补偿和声卡延迟都无需设置。
8. **可选 loopback。** 在同一遍录音中用第二条轨道录下声卡的电回送（一路输出用线接回一个空闲输入）。把两条轨道导出为一个双声道文件（`--channel 0 --loopback-channel 1`），或两个文件（`--loopback return.wav`）。

然后分析：

```bash
roomscope analyze --recording "Mic_01.wav" --sweep sweep_44k.wav --out session/
```

或在界面的通用 DAW 模式中选择这些文件。

## Avid Pro Tools

* **采样率：** 创建工程时设定，Session Setup 中可见 [P1，第 1814 页]。按该采样率生成扫描。
* **导入：** File ▸ Import ▸ Audio [P1，第 641 页]。若 Import Audio 对话框的备注栏提示文件采样率与工程不同 [P1，第 643 页]，请按工程采样率重新生成扫描，而不是勾选 *Apply SRC*。
* **时间伸缩：** 保持 Elastic Audio 关闭：轨道的 Elastic Audio 选择器显示 *None – Disable Elastic Audio* [P1，第 1317 页]。
* **录音：** 新建单声道音频轨，输入为话筒，开启录音待命。关闭 TrackInput 时轨道处于 Auto Input 模式，录音期间仍会监听输入 [P1，第 768–769 页]：请把话筒轨推子拉到底（推子不影响录音）。清空扫描轨道和主推子上的插入效果。
* **导出：** 选中录好的片段，在 Clip List 菜单中使用 *Export Clips as Files* [P1，第 649 页]：WAV、单声道、工程采样率与位深（32 位浮点转 24 位会加抖动）。Pro Tools 写出的是 Broadcast WAV，RoomScope 可直接读取。

## Apple Logic Pro 与 GarageBand

* **采样率：** File ▸ Project Settings ▸ Audio ▸ Sample Rate [G1]。Project Settings 的 Assets 页有 *Convert audio file sample rate when importing* [G1]；按工程采样率生成扫描就不需要它。GarageBand for Mac 的指南中没有采样率设置；请按 44.1 kHz 生成扫描（`--sample-rate 44100`），这是 GarageBand iPhone/iPad 指南所写的导入采样率 [G9]。
* **导入：** Logic：File ▸ Import ▸ Audio File，或把 WAV 拖到轨道上 [G2]。GarageBand：把 WAV 拖到轨道上 [G8]。
* **时间伸缩：** Logic 12.3：在片段检查器中取消勾选 *Flex*，并把 *Smart Tempo* 设为 *Off* [G3]（Logic 10.4–12.2：*Flex & Follow* = *Off* [G4]）；在 File ▸ Project Settings ▸ Smart Tempo 中把 *Set Imported Files To* 设为 *Flex Off*，并取消勾选 *Trim start of new regions* [G5]。GarageBand：在音频编辑器中取消勾选 *Follow Tempo and Pitch*，保持 *Enable Flex* 关闭 [G10]。
* **录音：** 单声道音频轨，输入为话筒。Logic 的软件监听默认开启，会播放录音轨的输入 [G6]：请将其关闭（Settings ▸ Audio ▸ General）或把该轨推子拉到底。关闭 Cycle。Logic 的录音文件（CAF、WAVE/BWF 或 AIFF）可以直接分析 [G7]。
* **导出：** Logic：选中录好的片段，File ▸ Export ▸ *1 Region as Audio File*，WAV 或 AIFF，关闭 *Normalize*，勾选 *Bypass Effect Plug-ins* [G11]。GarageBand：静音扫描轨，关闭 *Export projects at full volume*（Settings ▸ Advanced；它会把导出标准化）[G12]，然后用 Share ▸ Export Song to Disk 导出 WAVE 或 AIFF [G13]。该导出会裁掉工程首尾的静音 [G13]；扫描前话筒录到的房间底噪不是数字静音，但请确认导出文件在扫描之前开始。

## Steinberg Cubase 与 Nuendo

* **采样率：** Project ▸ Project Setup [C1]。
* **导入：** File ▸ Import ▸ Audio File [C2]。当 Preferences ▸ Editing ▸ Audio ▸ *On Import Audio Files* 设为 *Open Options Dialog* 时会弹出导入选项，文件采样率或位深不同时会提供 *Convert to Project Settings* [C2]；按工程采样率生成扫描即可避免采样率转换。
* **时间伸缩：** 扫描片段保持 *Musical Mode* 关闭（在 Sample Editor 或 Pool 中；带 ACID 标记的文件会自动开启）[C3]。
* **录音：** 单声道音频轨，输入为话筒。除 *Manual* 外，所有 Auto Monitoring 模式（Preferences ▸ VST）在轨道录音待命时都会打开监听 [C4]：请设为 *Manual*。确认 Control Room 的监听链路上没有插入效果或房间校正插件，或将其旁通 [C5]。
* **导出：** File ▸ Export ▸ Selected Events，*Processing* 选 *Dry* [C6]；或把定位点设在这段录音上，用 File ▸ Export ▸ Audio Mixdown，*Channel Selection* 选 *Single* 并选话筒通道 [C7]。（Audio ▸ Bounce Selection 也可以；它把新文件写入工程的 Audio 文件夹，并应用事件的淡入淡出和音量 [C8]。）

## Fender Studio Pro（原 PreSonus Studio One）

Studio One 自第 8 版（2026 年 1 月）起更名为 Fender Studio Pro，“Song”改称“Session” [S1, S2]；括号中为旧版菜单名。

* **采样率：** Session ▸ Session Setup（v8 之前为 Song ▸ Song Setup）[S2, S6]。
* **导入：** 从浏览器把 WAV 拖到音频轨 [S3]。
* **时间伸缩：** 在**轨道**检查器中把轨道的 *Tempo* 模式设为 *Don't Follow* [S4]；在事件检查器中保持 *Speedup* 为 1、*Transpose* 和 *Tune* 为 0，关闭 *Normalize*。事件上出现齿轮图标表示它正在被重采样或伸缩 [S4]。
* **录音：** 单声道轨，输入为话筒。开启录音时监听会自动打开 [S5]：武装后请关闭 Monitor 按钮。
* **导出：** 右键录好的事件 ▸ *Export Selection* [S7]；或 Session ▸ Export Stems（v8 之前为 Song ▸ Export Stems），只选话筒轨（分轨包含该轨的插入效果）[S7]。WAV、工程采样率、不标准化。

## Ableton Live

* **采样率：** Settings（Windows 为 Options ▸ Settings，macOS 为 Live ▸ Settings）▸ Audio ▸ *In/Out Sample Rate* [L1]。采样率不同的文件会被 Live 实时转换，其 Audio Fact Sheet 称之为“非中性”处理 [L2]：这也是要按 Set 采样率生成扫描的原因之一。
* **导入：** 把 WAV 拖到编曲视图中的音频轨。
* **时间伸缩：** 打开片段，在 Clip View 中**关闭 Warp** [L3]。*Auto-Warp Long Samples*（Settings ▸ Record, Warp & Launch）默认开启 [L4]，所以较长的测试文件若不手动关闭就会被 Warp。
* **录音：** 第二条音频轨，*Audio From* 选话筒输入（单声道），Monitor 设为 *Off*，开启录音待命，在编曲视图中录音 [L5]。
* **导出：** 在编曲视图中选中整段录音，File ▸ Export Audio/Video，*Rendered Track* 选话筒轨，关闭 *Include Return and Main Effects*，WAV 或 AIFF，Set 的采样率，关闭 *Normalize* [L6]。*Create Fades on Clip Edges* 最多加 4 ms 的淡入淡出 [L2]；测试文件首尾都是静音，不会影响扫描。

## Cockos REAPER

* **采样率：** File ▸ Project Settings ▸ 勾选 *Project sample rate* [R1，第 32 页]，并在 Preferences ▸ Audio ▸ Device 中开启 *Allow projects to override device sample rate*，让声卡跟随工程采样率 [R2]。采样率不同的对象会被 REAPER 实时转换 [R1，第 32 页]。
* **导入：** Insert ▸ Media file [R1，第 90 页]。
* **时间伸缩：** 在对象属性（F2）中保持 *Playback rate* 为 1.0，关闭 *Preserve pitch*，并删除伸缩标记 [R1，第 134 页]。
* **录音：** 武装一条轨道，输入为话筒单声道，关闭录音监听。
* **导出：** File ▸ Render，*Source* 选 *Selected media items*（或 *Stems (selected tracks)*），WAV、工程采样率；除非在 *Postprocess…* 中设置，否则不做标准化 [R1，第 411–415 页]。默认的对象淡入淡出（Preferences ▸ Project ▸ Item Fade Defaults）落在测试文件首尾的静音上。

## Image-Line FL Studio

* **采样率：** Options ▸ Audio settings（F10）▸ *Sample Rate*；导出使用该采样率 [F1]。
* **导入：** 把 WAV 拖进 Playlist 作为音频片段。
* **时间伸缩：** 在片段的通道设置中保持模式为 *Resample*、*Time* 旋钮为 *(none)*，这是默认值 [F2]。默认的去咔嗒处理会加 10 ms 淡出 [F2]，落在测试文件末尾的静音上。
* **回放链路：** 自 FL Studio 20.7 起默认模板为“Basic 808 with limiter” [F3]；测量时请旁通 Master 插槽上的限幅器。
* **录音：** 把话筒输入路由到一个空闲的 Mixer 插槽。默认情况下实时输入会经 Master 回到输出 [F4]，因此请把该插槽的 *Monitor external input* 设为 *Off*（否则可能回授），并关闭默认开启、会叠加多次录音的 *Loop record* [F4]。武装该插槽，把音频录进 Playlist。
* **导出：** File ▸ Export ▸ Wave file，勾选 *Split mixer tracks*，使用话筒插槽对应的文件（被静音的轨道会被跳过）[F5]。WAV、工程采样率。

## Bitwig Studio

* **采样率：** Dashboard ▸ Settings ▸ Audio [B1]。
* **导入：** 把 WAV 拖到编排器中的音频轨。可在 Dashboard ▸ Settings ▸ Audio Import 中设为 *Original speed [Raw]* [B2]。
* **时间伸缩：** 在检查器中把片段的 *Stretch* ▸ *Mode* 设为 *Raw*，它忽略伸缩数据、按原速播放 [B2]。（没有 *Off* 模式。）
* **录音：** 音频轨，输入为话筒，关闭监听。
* **导出：** File ▸ Export Audio，只选话筒轨，WAV，采样率选 *Current*（不转换）[B3]。

## Audacity

* **采样率：** Audio Setup ▸ Audio Settings 中 *Quality* 部分的 *Project Sample Rate* [A1]。
* **导入：** File ▸ Import ▸ Audio [A2]。
* **录音：** 在 Transport ▸ Transport Options 中打开 *Hear other tracks during recording*，关闭 *Enable audible input monitoring*（旧版本中分别叫 *Overdub* 和 *Software Playthrough*）[A3]。把 Audio Setup ▸ Recording Channels 设为 1（单声道），光标放在开头，使用 **Record New Track**（Shift+R）：普通 Record 会从所选轨道末尾开始录，扫描已经播完 [A4]。
* **导出：** 选中录音轨，File ▸ Export Audio…，*Export Range* 选 *Current Selection*，WAV，*Signed 24-bit PCM* 或 *32-bit float* [A5]。（Audacity 3.4 已移除 *Export Selected Audio* [A6]。）

## 报告提示有问题时

| RoomScope 提示 | DAW 里发生了什么 | 解决办法 |
| --- | --- | --- |
| *“a file generated at 48000 Hz was played at 44100 Hz”* | 工程或导出采样率与扫描不同，且未转换 | 按工程采样率生成扫描 |
| *“the DAW time-stretched it”* | 扫描片段开启了 Warp / Flex / Follow Tempo / 伸缩 | 关闭该片段的时间伸缩 |
| *“the recording starts ... after the sweep began”* | 录音开始得太晚，或导出时被裁切 | 在扫描开始前录音；完整导出片段 |
| *“harmonic ... was folded back”* | 回放链路上有限幅器、削波器或过载的总线 | 旁通主输出和轨道插件；降低扫描轨电平 |
| *“flat-topped peaks ... probable clipping”* | 话放增益过高 | 降低输入增益 |
| *“the recording contains N sweep passes”* | 循环录音，或扫描放了两次 | 只录一遍 |
| *“recording is silent”* | 输入选错、轨道被静音，或导出了扫描轨 | 检查输入和导出的是哪条轨 |
| *“direct-sound detection confidence is low”* 且不属于以上情况 | 参考扫描不对、房间很吵，或扬声器严重失真 | 使用实际播放的扫描；降低回放电平 |

## 来源

以上菜单名称与默认值依据以下页面核对（2026-09），完整列表见英文版 [daw-setup.md](daw-setup.md#sources)：[P1] Pro Tools Reference Guide 2026.4；[G1]–[G13] Apple Logic Pro / GarageBand 用户指南；[C1]–[C8] Steinberg Cubase Pro / Nuendo 15 帮助；[S1]–[S7] Fender Studio Pro 8.1 手册；[L1]–[L6] Ableton Live 12 手册；[R1] REAPER User Guide 7.80，[R2] RØDE REAPER 多轨指南；[F1]–[F5] FL Studio 手册与 20.7 发布说明；[B1]–[B3] Bitwig Studio 用户指南；[A1]–[A6] Audacity 手册与论坛。
