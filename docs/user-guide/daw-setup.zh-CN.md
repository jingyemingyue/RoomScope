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

* **采样率：** 创建工程时设定（Session Setup 中可见）。按该采样率生成扫描。
* **导入：** File ▸ Import ▸ Audio。若对话框出现 *Apply SRC*，说明采样率不同：请回去按工程采样率生成扫描。
* **时间伸缩：** 保持 Elastic Audio 关闭（轨道的 Elastic Audio 选择器显示 *None*）。
* **录音：** 新建单声道音频轨，输入为话筒，开启录音待命，关闭 TrackInput 监听。清空扫描轨道和主推子上的插入效果。
* **导出：** 选中录好的片段，在 Clip List 菜单中使用 *Export Clips as Files*（WAV、工程采样率、24 位）。Pro Tools 写出的是 Broadcast WAV，RoomScope 可直接读取。

## Apple Logic Pro 与 GarageBand

* **采样率：** File ▸ Project Settings ▸ Audio。按该采样率生成扫描。GarageBand 工程固定为 44.1 kHz：用 `--sample-rate 44100` 生成扫描。
* **导入：** File ▸ Import ▸ Audio File，或把 WAV 拖到新的音频轨。
* **时间伸缩：** 轨道保持 Flex 关闭，并在片段检查器中把 *Flex & Follow* 设为 *Off*，避免 Smart Tempo 改变扫描。
* **录音：** 单声道音频轨，输入为话筒，关闭输入监听。关闭 Cycle。Logic 的录音文件（CAF、WAV 或 AIFF）可以直接分析。
* **导出：** 选中录好的片段，File ▸ Export ▸ Region as Audio File，WAV 或 AIFF，工程采样率，关闭 *Normalize*。GarageBand 中请静音扫描轨，使用 Share ▸ Export Song to Disk（无压缩），并关闭主输出效果。

## Steinberg Cubase 与 Nuendo

* **采样率：** Project ▸ Project Setup。
* **导入：** File ▸ Import ▸ Audio File。若出现 *转换为工程采样率*（Convert to project sample rate），说明采样率不同：请按工程采样率生成扫描。
* **时间伸缩：** 扫描事件保持 *Musical Mode* 关闭。
* **录音：** 单声道音频轨，输入为话筒，关闭监听。确认 Control Room 的监听链路上没有插入效果或房间校正插件，或将其旁通。
* **导出：** 选中录好的事件，使用 Audio ▸ Bounce Selection；或 File ▸ Export ▸ Audio Mixdown，只选话筒通道（Channel Batch Export），WAV、工程采样率、不标准化。

## PreSonus / Fender Studio One

* **采样率：** Song ▸ Song Setup ▸ General。
* **导入：** 从浏览器把 WAV 拖到新的音频轨。
* **时间伸缩：** 在检查器中把扫描事件的 *Follow Tempo* 设为 *Don't Follow*（关闭 Timestretch）。
* **录音：** 单声道轨，输入为话筒，关闭输入监听。
* **导出：** Song ▸ Export Stems 只选话筒轨；或选中录好的事件执行 Event ▸ Bounce Selection 后导出该文件。WAV、歌曲采样率、不标准化。

## Ableton Live

* **采样率：** Settings ▸ Audio ▸ Sample Rate（整个 Set 使用同一采样率）。
* **导入：** 把 WAV 拖到编曲视图中的音频轨。
* **时间伸缩：** 打开片段并**关闭 Warp**。当 *Auto-Warp Long Samples*（Settings ▸ Record, Warp & Launch）开启时，Live 会自动对长采样做 Warp；Warp 播放是 Live 测量失败最常见的原因。
* **录音：** 第二条音频轨，*Audio From* 选话筒输入（单声道），Monitor 设为 *Off*，开启录音待命，在编曲视图中录音。
* **导出：** 在编曲视图中选中整段录音，File ▸ Export Audio/Video，*Rendered Track* 选话筒轨，WAV 或 AIFF，Set 的采样率，关闭 *Normalize*。

## Cockos REAPER

* **采样率：** Project Settings ▸ Project sample rate（勾选后设备会跟随工程采样率）。
* **导入：** Insert ▸ Media file。
* **时间伸缩：** 在对象属性（F2）中保持播放速率为 1.0，并删除伸缩标记。
* **录音：** 武装一条轨道，输入为话筒单声道，关闭录音监听。
* **导出：** File ▸ Render，*Source* 选 Selected media items（或 Selected tracks 作为分轨），*Bounds* 选该对象或整个工程，WAV、工程采样率、关闭标准化。

## Image-Line FL Studio

* **采样率：** Options ▸ Audio settings。
* **导入：** 把 WAV 拖进 Playlist 作为音频片段。
* **时间伸缩：** 音频片段设置中保持不伸缩（模式 *Resample*，不改变时长）。
* **回放链路：** 默认模板在 Master 插槽上有一个限幅器：测量时请旁通它。
* **录音：** 把话筒输入路由到一个空闲的 Mixer 插槽，开启录音待命，把音频录进 Playlist。
* **导出：** File ▸ Export ▸ Wave file，勾选 *Split mixer tracks*，使用话筒插槽对应的文件。WAV、工程采样率。

## Bitwig Studio

* **采样率：** Settings ▸ Audio。
* **导入：** 把 WAV 拖到编排器中的音频轨。
* **时间伸缩：** 在检查器中把片段的 *Stretch* 模式设为 *Off*。
* **录音：** 音频轨，输入为话筒，关闭监听。
* **导出：** File ▸ Export Audio，只选话筒轨，WAV、工程采样率。

## Audacity

* **采样率：** *Project Rate*（Audio Setup ▸ Audio Settings）。
* **导入：** File ▸ Import ▸ Audio。
* **录音：** 打开 *Overdub*（Transport ▸ Transport Options），让扫描在录音时播放；关闭 *Software Playthrough*。在新的单声道轨上录音。
* **导出：** 选中录音轨，File ▸ Export ▸ Export Selected Audio，WAV，24 位或 32 位浮点。

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
