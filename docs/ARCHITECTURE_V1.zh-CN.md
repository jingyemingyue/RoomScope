# RoomScope v1.0 架构设计（中文摘要）：仅 macOS，兼容性优先

> 状态：**提案，2026-09-22 修订**。维护者已收窄范围：v1.0 **只针对 macOS**，必须是**实用的小工具**
> （GUI 保持朴素），并且**必须先兼容所有主流 DAW 和大家真正在用的音频硬件**。Windows / Linux
> 推迟到 1.0 之后；核心保持平台无关，届时只是打包与矩阵工作，不是重新设计。
>
> 本文是 [ARCHITECTURE_V1.md](ARCHITECTURE_V1.md) 的摘要而非逐字翻译，两者不一致时以英文版为准。
> [ARCHITECTURE.md](ARCHITECTURE.md) 描述 v0.1 已有的东西。除标注"已落地"或"PR #2 中"的条目外，
> 以下内容均尚未实现。只能由项目发起人决定的事项标注 **维护者决定**，汇总在第 11 节。

## 1. 核心判断

"兼容所有 DAW 和所有声卡"不能靠"WAV 进、WAV 出"的设计自动成立，必须**逐个 DAW、逐类设备去证明，
而且每次测量时由工具自己再验一遍**。v1.0 围绕这一点构建：

1. **链路检查（chain check）。** `roomscope check` 与 GUI 的"检查我的设置"按钮分析一段**电气回环**录音
   ——扫频由 DAW 或 RoomScope 播放，经线缆（或声卡内部 loopback）录回输入，不用音箱、不用麦克风——
   给出 PASS / FAIL 判定，并逐条说明是 DAW 侧还是硬件侧的哪个原因、怎么修。DAW 兼容矩阵和硬件矩阵
   都靠它填写，用户也靠它在测房间之前验证自己的设置。
2. **管线内置扫频完整性校验。** 每次分析都估计录到的扫频是否被以错误速度播放（采样率不匹配）、
   被时间拉伸（DAW 的 warp / flex / elastic / musical mode）、被两台设备的时钟漂移拖歪、被播放多次、
   削波或失真，并**拒绝报告指标而不是报告错误的指标**。只检测，永不校正。
3. **读得了 DAW 导出的所有格式。** WAV 各种变体、BWF、RF64、AIFF / AIFC、CAF、FLAC、分离单声道文件对、
   任意通道数；有损格式带理由拒绝。
4. **把 Core Audio 做对。** 默认使用声卡当前采样率，未经用户明确选择不改任何设备配置；输入输出分属
   两台设备（USB 测量麦克风）可用且做漂移检测；聚合设备写进指南；第一次扫频前有电平检查与实时输入表；
   "停止"立即静音。
5. **重新打开、对比、留存。** 会话可重开（PR #2）、两次会话按有效性对比、会话文件夹自包含并可打包求助。
6. **Developer ID 签名并公证的 macOS 应用**——强制要求，未签名的构建永不发布——以及 PyPI wheel，由发布流程构建，并同时生成 LGPL / FreeType / PortAudio 义务要求的许可证包。
7. **先有证据再叫 1.0**：DAW 矩阵、硬件矩阵、外来文件健壮性测试、与参考仪器的真实房间验证都是发布门槛。

需求书禁止的东西继续禁止：没有房间评分、自动 EQ、插件、云、账号、遥测，未校准不报 dB SPL，不报房间坐标。

## 2. 新增原则

* **兼容性靠证明，不靠假设。** 一个 DAW 或一类设备只有在矩阵里有带版本、日期的绿色行才算"支持"，工具每次测量都重新检查链路。
* **检测并拒绝，绝不悄悄修复。** 被重采样、拉伸、拖歪、削波或失真的录音得到判定与建议，不是被"修正"过的数字。
* 文件兼容性、会话自包含、从构造上离线（CI 禁止 `src/` 里出现网络 import）、"停止"是安全控制——与上一版一致。
* **朴素即可。** GUI 是工程工具：每个控件有标签、每个数字有单位、每张图有坐标轴。1.0 不安排视觉设计工作。

## 3. 范围

### 3.1 MUST（按优先级）

| # | 条目 |
| --- | --- |
| M1 | **DAW 兼容**：音频格式覆盖；扫频完整性校验（速度、拉伸、拖歪、多次播放、电平、失真）；DAW 形式的链路检查；逐 DAW 操作方案；需求书列出的九个 DAW 在 macOS 上的兼容矩阵全绿——**先做 Logic Pro、Studio One Pro、Cubase**（A 组），其余在 1.0-rc 之前 |
| M2 | **macOS 硬件兼容**：音频后端接口与 Core Audio 规则；默认设备当前采样率、不悄悄改配置；输入输出分属两台设备时的漂移检测；聚合设备；USB 测量麦克风；1–2 以外的通道映射；电平检查与实时输入表；停止；Standalone 形式的链路检查；§6.1 各类设备在硬件矩阵全绿 |
| M3 | 会话重开与浏览器（PR #2 中） |
| M4 | 两次会话对比（core、CLI、朴素的 GUI 表格） |
| M5 | 文件格式稳定性策略与一个小的公开 API |
| M6 | 自包含会话与求助打包 |
| M7 | macOS `.app`（arm64 与 x86_64），**Developer ID 签名并公证，无例外**；PyPI wheel；发布流程；许可证包；GPL 模块门禁 |
| M8 | 中英文用户指南，含逐 DAW 配方与硬件设置（聚合设备、USB 麦克风） |
| M9 | 质量门槛：CI 上有 macOS；外来文件健壮性测试；两个矩阵执行完毕；与参考仪器的真实房间验证 |
| M10 | 仓库公开检查清单执行完毕（**维护者决定**） |

### 3.2 SHOULD（延期不阻断）

双通道 loopback 补偿（麦克风 + 回环同录，去除声卡响应并给出音箱距离上界）；假后端上的演示模式（假后端本身是 CI 必需）；
`analyze-ir`；随包分发 JSON Schema 文件；Findings 与 GUI 的简体中文（指南的中文版是 MUST）；CSV 导出；GUI 的 Placement 标签页。

### 3.3 v1.0 不做

* **Windows 与 Linux。** 1.0 之后的打包工作；除 `audio/coreaudio_rules.py`、打包配方与硬件矩阵外没有任何 macOS 专有代码。
* **校正速度、拉伸或漂移。** 只估计用于拒绝。独立未同步设备间的采样率偏差校正是有效专利 US 10,816,391 B2 的主题，做校正功能须先做权利要求审查，目前不计划。
* 自动双扫频通带方案（US 9,959,883 B2）；插件（VST3 / AU / AAX，许可证性质不同）；dB SPL（模型里预留校准槽位，USB 测量麦克风自带的校准文件让这件事以后很便宜）；多位置平均与多位置摆位、项目、entry point 插件机制、核心诊断文本的国际化；房间评分、自动 EQ、模态识别、3D 建模、云、账号、遥测、更新检查。

## 4. 包布局变化要点

`core` 仍只有一个入口 `pipeline.analyze`，新增两个纯模块 `integrity`（扫频轨迹拟合、脉冲紧凑度）与 `compare`，
链路检查 `chain_check` 是作用于 `AnalysisResult` 的纯函数。其他新增：`io/wav.py` 的 `read_audio`；
`audio/backend.py`（协议）、`audio/portaudio.py`（回调流：进度、取消、多通道输入、纯输入监听流）、
`audio/coreaudio_rules.py`（唯一知道自己在 macOS 上的模块）、`audio/fake.py`；`models/comparison.py`；
`cli` 新增 `check`、`compare`、`session bundle`；`ui` 新增 `check_page.py`、`compare_view.py`；
文档新增 `DAW_COMPATIBILITY.md`、`HARDWARE_TESTS.md`、`user-guide/`。依赖方向不变。

## 5. DAW 兼容（M1）

### 5.1 从"导入 WAV"到"导出录音"之间会出什么错

| 故障模式（藏在哪） | 录音里的症状 | 检测 | 建议 |
| --- | --- | --- | --- |
| 导入或导出时的采样率转换 | 频率与时长同时按比例缩放（44.1 ↔ 48 kHz 为 8.8 %） | 轨迹拟合：速度因子 ≠ 1 | sidecar 会按录音采样率重新生成参考，干净的转换没问题；错速播放带比例拒绝 |
| 跟随速度的片段：warp / flex / elastic / musical mode / stretch，长片段常默认开启 | 时长缩放、频率不变；解卷积脉冲变成 chirp | 拉伸因子 ≠ 1；脉冲紧凑度 | 关掉片段的 warp / stretch 再导出 |
| 两台设备的时钟漂移（USB 麦克风 + 声卡） | 高频端脉冲被拖散（Farina 2007 §3.4） | 紧凑度低于理想值；小的速度因子 | 用一台声卡，或用带漂移校正的聚合设备 |
| 循环播放、count-in、同一文件里两个 take | 多个扫频通过 | `sweep_passes`（已落地） | 只录一次 |
| 播放或监听路径上的插件：总线限制器、饱和、房间校正软件、带响度补偿的监听控制器 | 谐波失真；频响偏差；数字削波的混叠产物 | 谐波与混叠指标（已落地）；链路检查的平坦度判据 | 测量时旁通扫频轨、总线与监听路径上的所有插件 |
| DAW、导出或转换器削波 | 平顶峰，可能在增益改变后低于满幅 | `ClippingCheck`（已落地） | 降电平，导出不做归一化 |
| 不同文件格式、位深、通道布局、分离单声道文件 | 读不了或读一半 | `read_audio` 格式覆盖 | 任何 §5.2 格式都可用；有损格式带理由拒绝 |
| 立体声导出、麦克风只在一侧 | 只有一个有用通道 | 通道自动选择（已落地） | GUI 里显式选择 |
| 导出时加抖动 / 噪声整形 | 高频本底抬高 | 噪声分析注明 | 导出 24 bit 或 32 bit float、不加抖动 |
| 扫频开始后才开始录 | 低频缺失 | 录音起点检查（已落地） | 先开录音；文件开头的静音就是为此 |
| 录音延迟补偿 | 恒定时移 | 无害：全录音解卷积具有时移不变性 | 无 |
| 蓝牙或有损编解码路径 | 带宽受限、编解码非线性 | 链路检查在平坦度与失真上 FAIL | 用有线声卡 |
| 内置麦克风的自动增益、"人声隔离"、降噪 | 时变增益、被门限切掉的尾音 | 衰减非线性与曲率标志；链路检查 | 用声卡或 USB 测量麦克风 |

### 5.2 音频格式覆盖

`read_wav` 变为 `read_audio`（旧名保留一个次版本作别名），通过 libsndfile 读 WAV 全部变体
（PCM 16 / 24 / 32、float 32 / 64、`WAVE_FORMAT_EXTENSIBLE`、带 `bext` 的 BWF、RF64）、AIFF / AIFC、CAF、FLAC、任意通道数；
分离单声道文件对（`take.L.wav` + `take.R.wav`）作为列表接受并合并；MP3 / AAC / Opus / Vorbis 带一句"有损格式会毁掉扫频"拒绝；
扫频无法在该采样率重新生成的奇怪采样率带说明拒绝。`AudioSignal` 记录容器、子类型、通道数、时长，写入会话，便于 bug 报告说明 DAW 到底导出了什么。

### 5.3 扫频完整性校验（`core/integrity.py`）

在 `analyze` 内对每个已知扫频定义的录音运行；纯 NumPy / SciPy，按 ESS 定义独立实现；只检测。

* **轨迹拟合。** 在定位到的扫频上（去掉淡入淡出段）用 STFT 脊线跟踪瞬时频率。ESS 满足 `f(t) = f1 · exp(t / L)`；
  播放速度因子 `r`（采样率不匹配）同时缩放频率与时间，拉伸因子 `s`（跟随速度的片段）只缩放时间：
  `f(t) = r · f1 · exp(r · t / (s · L))`。对 `ln f` 关于 `t` 做最小二乘得到 `a = ln(r · f1)`、`b = r / (s · L)`，
  于是 `r = exp(a) / f1`、`s = r / (b · L)`。先用基于中位数的拟合剔除脊线的倍频程错误。
* **脉冲紧凑度。** 解卷积直达声峰值 ±0.5 ms 内的能量占比，与 `reference_pulse(settings)` 的同一比例相比；
  两个时钟之间的漂移与小幅拉伸在轨迹拟合看见之前就会把脉冲拖散。
* **管线内判定。** `|r − 1|`、`|s − 1|` 超过容差（起点 0.1 %，在矩阵上调定后写入方法学文档 §2a）或紧凑度低于容差时，
  所有衰减、频响、反射、共振与摆位指标标为 UNRELIABLE，附一句说明原因类别与修法，与现在的削波、混叠失真处理方式一致。
  结果带 `impulse_response.integrity`，报告能说"被拉伸 3.2 %"而不只是"不可靠"。
* **不是什么。** 不重采样、不时间扭曲、不校正漂移：估计值只用于拒绝与解释，从构造上避开 US 10,816,391 B2。

### 5.4 链路检查（`core/chain_check.py`，`roomscope check`）

**电气回环**录音（DAW 形式由 DAW 播放，Standalone 形式由 RoomScope 播放，经线缆或声卡内部 loopback 录回，不接音箱和麦克风）
先走普通 `analyze`，再走 `check_chain(result, settings)`。判据（容差为起点，在矩阵上定下后写入文档）：

| # | 判据 | 起始容差 | 失败时的说明 |
| --- | --- | --- | --- |
| 1 | 找到参考扫频且只有一次 | 一次 | "n 次播放：只录一次" |
| 2 | 速度因子 | ±0.05 % | "错速播放 x %：文件被重采样或工程采样率不同" |
| 3 | 拉伸因子 | ±0.05 % | "被时间拉伸 x %：片段的 warp / flex / elastic / musical mode 开着" |
| 4 | 脉冲紧凑度 | ≥ 理想值的 0.9 | "脉冲被拖散：两个时钟（USB 麦克风 + 声卡？）——用一台声卡或聚合设备" |
| 5 | 削波 | 无 | "在 x dBFS 削波：降电平，导出不归一化" |
| 6 | 2–5 次谐波（相对直达声） | ≤ −50 dB | "第 k 次谐波 x dB：播放路径上有限制器、饱和或削波插件" |
| 7 | 混叠失真 | 不显著 | "转换器之前的数字削波" |
| 8 | 激励频带内频响平坦度（1/6 倍频程平滑，两端各去 1/3 倍频程） | 中位数 ±1.0 dB | "在 f Hz 偏差 x dB：路径上有 EQ、房间校正插件或监听控制器" |
| 9 | 峰值电平 | −40 … −1 dBFS | "太小 / 太大" |
| 10 | 直达声置信度 | high | "扫频不干净：检查路由" |
| 11 | 回环本底 | ≤ −70 dBFS（仅警告） | "回环有噪声：输入增益过高或经过了有噪声的模拟路径" |

判定 PASS / PASS with warnings / FAIL，以清单形式打印并存为 `chain_check.json`（DAW 形式记录 DAW 名称与版本，Standalone 形式记录设备名）。
GUI 的"检查我的设置"页运行同一函数、显示同一清单，UI 里不做任何判断。
用电气回环的理由：去掉了房间与音箱，剩下的每个缺陷都归属于 DAW、导出或声卡，而且期望结果精确已知（平坦 0 dB、单一脉冲）；成本是一根线、一分钟。

### 5.5 逐 DAW 配方与兼容矩阵

[DAW_COMPATIBILITY.md](DAW_COMPATIBILITY.md) 每个 DAW 一行，分两组：**A 组先做**——Logic Pro、Studio One Pro（Studio One Professional 自第 7 版起的名称）、Cubase（方案同时覆盖 Nuendo）；
**B 组在 1.0-rc 之前**——Pro Tools、Ableton Live、REAPER、FL Studio、Bitwig Studio、Digital Performer。每行记录 DAW 版本、macOS 版本、声卡、日期、文件获取方式、链路检查判定与方案链接。
方案（`docs/user-guide/daw/<name>.md`，中英文）**先依据厂商文档起草**，标为 DRAFT 并附确认清单，在测试该行时逐行确认；A 组三份草案已写好
（[logic-pro](user-guide/daw/logic-pro.zh-CN.md)、[studio-one](user-guide/daw/studio-one.zh-CN.md)、[cubase](user-guide/daw/cubase.zh-CN.md)），建立在通用流程 [user-guide/daw/README.zh-CN.md](user-guide/daw/README.zh-CN.md) 之上。方案写明：如何导入（不转换或用 DAW 的转换器）；该 DAW 的跟随速度模式在哪里、怎么对片段关掉；如何把轨道路由到声卡输出并录输入；
如何把一条轨道导出为 PCM 24 bit 或 float、不归一化、不抖动；要旁通哪些插件与监听工具。没有绿色判定的行标为 **untested**，绝不标为支持。
每次矩阵测试的回环录音（几秒、很小）作为 fixture 存入 `tests/fixtures/daw/<name>/`，附 DAW 版本说明，作为完整性与链路检查代码的真实回归样本。
社区提交的行（其他版本、其他 DAW）通过 measurement issue 模板附上会话打包接受。

**M1 退出标准：** 0.2 时 A 组全绿，1.0-rc 时九行全绿，每行有方案、fixture 与日期。

## 6. macOS 硬件兼容（M2）

### 6.1 设备类别

| 类别 | 要处理的问题 |
| --- | --- |
| 内置输出与麦克风 | 能做第一次尝试；新 Mac 的内置麦克风被系统处理过，指南说明它适合做电平检查而不是测量 |
| 类兼容 USB 声卡（2 进 2 出） | 最常见情况：一台设备、一个时钟、通道 1–2、设备当前采样率 |
| 多通道 USB / Thunderbolt 声卡 | 1–2 以外的通道映射、驱动带来的多个设备名、最高 192 kHz |
| USB 测量麦克风 | 输入设备 ≠ 输出设备：两个时钟；漂移检测；带漂移校正的聚合设备设置；1.0 不读其校准文件 |
| 聚合设备（音频 MIDI 设置） | 作为一个 Core Audio 设备出现；指南解释"漂移校正"复选框 |
| 蓝牙及其他编解码路径 | 不支持测量；链路检查带理由 FAIL；设备名或传输方式暗示蓝牙时列表里给提示 |

**M2 退出标准：** `docs/HARDWARE_TESTS.md` 中除蓝牙外每类至少一台设备在 44.1 与 48 kHz 各有绿色的 Standalone 链路检查行和一次完整 Standalone 测量，另有一次 96 kHz，记录型号、macOS 版本与日期。

### 6.2 音频后端协议与 Core Audio 规则

`AudioBackend` 协议：`list_devices`（含当前采样率与提示）、`check_sample_rate`、`play_and_record(... input_channels, progress, cancel)`、
`monitor_input`（纯输入流，供实时电平表）。`portaudio` 后端把阻塞的 `sd.playrec` 改为回调流：`cancel` 在下一个回调把输出置零并关闭流，
`progress` 报告播放进度，可同时采集多个输入通道；电平、−12 dBFS 确认与安全提示不变。`fake` 后端合成房间，支撑 CI 与演示模式。
Core Audio 规则（`audio/coreaudio_rules.py`，唯一知道自己在 macOS 上的模块）：

1. **测量默认采样率 = 输出设备当前标称采样率**，扫频按该采样率重新生成（参数化，零成本）；输入设备采样率不同则在播放前说明。
2. **不悄悄重新配置任何设备。** PortAudio 的 Core Audio 实现可能把设备标称采样率切到流的采样率；RoomScope 只在用户明确选了其他采样率时才请求，并先显示"本次测量将把声卡切到 96 kHz"。实现时核实相关 `paMacCore…` 流标志并记入 HARDWARE_TESTS.md。
3. **允许输入输出分属两台设备**（USB 麦克风情形），注明涉及两个时钟；链路检查与完整性校验决定结果是否可用；指南推荐带漂移校正的聚合设备。
4. **通道映射**从 1 开始并显示设备通道数；超出范围在打开流之前拒绝。
5. **只提示不决定：** 设备名含 "Aggregate"、"AirPods" 或蓝牙传输时旁边给提示，不隐藏、不禁用。

### 6.3 电平检查与实时输入表

Standalone 页在第一次扫频前显示**实时输入表**（dBFS 峰值与 RMS，每秒刷新几次），不播放任何东西即可设麦克风增益；
**电平检查**按钮以所选电平（默认 −20 dBFS）播放 0.5 s 扫频同频带的噪声并报告录到的峰值：低于 −40 dBFS "提高增益或电平"，高于 −3 dBFS "降低"，否则 "就绪"。
两者都只是后端之上的 UI 便利，不存储、不当作房间指标。检查与测量期间都有**停止**按钮。

### 6.4 麦克风权限

macOS 按应用授予麦克风权限：`.app` 带 `NSMicrophoneUsageDescription`；从终端运行 `roomscope` 时系统向终端应用询问，指南说明这一点，因为症状是一段无声录音。
RoomScope 只写入用户选择的文件夹与 `ROOMSCOPE_HOME`（默认 `~/.roomscope`，PR #2 引入）。

## 7. 产品的其余部分

* **重开与浏览（M3）：** PR #2 已提供 `AnalysisResult.from_dict`、`load_measurement`、`list_sessions`、最近列表、`roomscope show`、GUI 的打开会话；本设计只在其上增加字段与"与…对比"动作。
* **对比（M4）：** `compare(baseline, candidate)` 纯函数，双方都 VALID 才给差值，否则 `NOT_COMPARABLE` 附两边原因；双方须通过完整性校验；频响在公共激励频带内插值到同一对数网格后相减；早期反射按 ±0.5 ms 配对；噪声差值只在双方都有已验证的安静段且用户明确声明输入增益未变时才有效；报告引用 ISO 3382-1 给出的 T 可觉察差（约 5 %，条款待核对），从不自行宣称"显著"。CLI `roomscope compare`；GUI 一张两列表格加一张差值图。
* **格式稳定性与公开 API（M5）：** `schema_version` 只在 1.0 读取者可能误解时递增；读取宽松（未知键忽略并记日志，只拒绝更高版本）、写入严格（往返测试）；JSON Schema 文件是 SHOULD。新键：`result.json` 的 `roomscope_version`、`impulse_response.integrity`；`session.json` 的 `recording_profile`（PR #2）、`platform`、`daw`、设备名、文件元数据；新文件 `chain_check.json`、`comparison.json`。Findings 不存储，打开时按记录的 profile 重新生成。`roomscope` 顶层惰性导出一小组名字，遵守 1.x 的 SemVer；文本报告不是接口。
* **自包含会话与打包（M6）：** 总是复制 sidecar，按需复制 `recording.wav`（GUI 默认开），`roomscope session bundle [--no-audio]` 打包求助。
* **双通道 loopback 补偿（S1）：** 先用链路检查判据验证回环确实是电气脉冲，再在激励频带内用正则化除法去掉声卡响应，回环峰值作为电气时间零点，`distance_upper_bound_m = c · path_delay` 作为**上界**报告；卷尺距离超过上界则摆位标为不可靠；不做漂移估计，不去除音箱响应并明说。
* **GUI（朴素，只加功能）：** 首页加"检查我的设置"、打开会话、最近列表、Demo；检查页两种形式与判据清单；Standalone 页设备列表显示当前采样率与通道数、实时表、电平检查、进度、停止、"两个时钟"提示；DAW 页有配方链接与 DAW 名称/版本字段、接受所有格式与分离单声道对；结果概览顶部加一行完整性信息；对比视图；1.0 界面为英文。
* **CLI：** 新增 `check --recording … --sweep … [--daw …]`、`check --standalone …`、`compare`、`session bundle`、`analyze-ir`（S3）、`export`（S6）；全局 `--format text|json`、`--copy-recording`、`--backend`；退出码 0 成功、1 `RoomScopeError`、2 用法或安全拒绝、3 链路检查 FAIL、130 中断。

## 8. 分发（M7）

* PyInstaller one-dir 生成 `RoomScope.app`，用 `hdiutil` 装入 `.dmg`；arm64 与 x86_64 两个包（NumPy / SciPy 无 universal2 wheel），x86_64 包可在 Rosetta 下运行。
* `Info.plist`：`CFBundleIdentifier`、`LSMinimumSystemVersion`、`NSMicrophoneUsageDescription`。
* **签名与公证（强制）：** 每个发布的包都用 Developer ID Application 证书签名、开启 hardened runtime 并公证；未签名或未公证的包永不附到 Release 上，没有"未签名发布"的兜底；未签名构建只作为名为 `-unsigned` 的 CI 产物供内部测试。流水线：(1) 前置条件（维护者，0.4 之前）：Apple Developer Program、Developer ID Application 证书、供 `notarytool` 使用的 App Store Connect API key、bundle identifier；证书与 key 存放在只有维护者能批准的 GitHub environment `release`，作业导入临时钥匙串并在结束后删除；(2) 构建：PyInstaller 加 `--codesign-identity` 与 `--osx-entitlements-file`，给定身份即开启 hardened runtime 并签名所有收集到的二进制；entitlements 为 `com.apple.security.device.audio-input`、`com.apple.security.cs.allow-unsigned-executable-memory`，`disable-library-validation` 仅在冒烟测试证明必要时加入，其他任何 entitlement 需要 ADR；(3) 公证前核验：脚本遍历包内所有 Mach-O 确认签名 Team ID 一致，`codesign --verify --deep --strict`，entitlements 与预期集合完全一致；(4) `stapler staple` 应用、构建并签名 `.dmg`、`notarytool submit --wait`（非 Accepted 则取日志并失败）、`stapler staple` dmg；(5) 门禁：`spctl --assess` 对 dmg 与 app 都须报告 Notarized Developer ID，并在干净的 runner 用户下带 quarantine 属性启动冒烟；两个架构分别走完整流水线；(6) 用户指南里没有任何 Gatekeeper 绕过步骤，因为不需要。
* 打包门禁（CI 阻断）：不含 GPL-only Qt 模块（白名单 QtCore / QtGui / QtWidgets）；含 `scripts/build_license_bundle.py` 生成的 `THIRD_PARTY_LICENSES/`；DEPENDENCIES.md §6 中与 macOS wheel 有关的未决项先解决；用锁文件构建；每个包在 runner 上启动冒烟。
* PyPI：`roomscope` 名称 2026-09-22 核实可用，注册与 trusted publishing 是**维护者决定**；`pipx install "roomscope[gui]"`。`release.yml` 由维护者推 `v*` tag 触发：测试 → PyPI（rc 为预发布）→ 两个 macOS 包 → 门禁 → `SHA256SUMS`、SBOM、许可证包 → 草稿 Release，由维护者发布。
* 用户指南（M8）：`docs/user-guide/` 中英文：安装、DAW 流程与逐 DAW 配方、硬件设置（单声卡；USB 麦克风 + 声卡 + 聚合设备；不要用什么）、先"检查我的设置"、读懂每个结果页、对比两个位置、按症状排错（§5.1 每行一条）、如何发送打包。

## 9. 质量门槛（M9）

* CI：Ubuntu 3.12 / 3.13 照旧，**macOS arm64 与 x86_64 runner 在每次 push 与 PR 上必跑**（含离屏 GUI 与假后端 Standalone 流程）；健壮性作业；打包作业。
* 测试层级：合成单元（轨迹拟合还原已知速度与拉伸因子、理想与拖歪脉冲的紧凑度、合成回环上的链路判据）；合成集成（重采样、拉伸、漂移三种合成录音各以正确原因被拒绝；两个合成位置的对比）；离屏 GUI；健壮性（§5.2 每种格式与变体各一个小文件，截断 / 空 / 静音 / NaN / 有损 / 奇怪采样率，畸形 JSON 与会话文件，只能抛 `RoomScopeError`）；真实 fixture（两个矩阵的回环录音，CC0，回归证据）；手动矩阵。
* 验证活动：至少一个房间（最好一处理一未处理）、各两个位置，在矩阵里绿色的 DAW 与设备上；**同一个录音文件**分别交给 RoomScope 与参考仪器（REW 只作比较仪器，或许可证清晰的开源工具箱）；按频带比较 T20 / T30、EDT、最强早期反射延迟、频响；容差在测量前写下；不达标阻断 1.0 但照样发布；用卷尺核对摆位几何。

## 10. 里程碑（无日期，退出标准即时间表）

| 版本 | 主题 | 内容 | 退出标准 |
| --- | --- | --- | --- |
| 0.2 | 任何 DAW | `read_audio`；`core/integrity.py` 进管线；`core/chain_check.py` 与 `roomscope check`（DAW 形式）；DAW 页字段；方案与 `DAW_COMPATIBILITY.md`；逐 DAW fixture；健壮性层 | 当前 macOS 上 A 组（Logic Pro、Studio One Pro、Cubase / Nuendo）全绿，有方案、fixture 与日期；重采样、拉伸、漂移三种合成录音各以正确原因被拒绝 |
| 0.3 | 任何声卡 | `AudioBackend`、回调流的 `portaudio`、`fake`、`coreaudio_rules`；默认采样率与重配置需确认；两台设备 + 漂移检测；实时表、电平检查、进度、停止；`check --standalone`；`HARDWARE_TESTS.md`；CI 上的 macOS runner | §6.1 除蓝牙外每类在 44.1 与 48 kHz 全绿、另有一次 96 kHz；真机上"停止"在一个回调周期内静音；Standalone 流程在 macOS 与 Ubuntu 的 CI 上以假后端运行 |
| 0.4 | 重开、对比、留存、签名 | 合并 PR #2；`compare` 全链路；宽松读取、新会话键、公开 API 导出与测试；自包含会话与 `session bundle`；§8 的签名与公证流水线在每个 tag 上产出签名测试包；时间允许则做 loopback 补偿（S1）与演示模式（S2） | 任何 v0.1 会话能重开；两次会话可对比且每个差值带有效性；GUI 打包的会话在另一台 Mac 上能复现分析；`spctl` 在干净 runner 上接受已 staple 的测试包 |
| 1.0-rc | 冻结与证明 | 格式与 API 冻结；验证活动发布；九个 DAW 行全绿（B 组方案写好并测过）；含全部方案的中英文指南；SECURITY / CONTRIBUTING / STATUS 更新；仓库公开；PyPI 预发布；两个矩阵在候选版本上重跑 | 无未完成 MUST；§8–§9 所有门禁在 tag 上全绿，含公证门禁 |
| 1.0 | 发布 | 仅 rc 后的修复 | 同上；发布说明写明矩阵、验证结果与已知限制 |
| 1.0 之后 | | Windows 与 Linux 的包与矩阵；简体中文界面（S5）；来自麦克风校准文件的 dB SPL；`analyze-ir`、CSV 导出、项目、平均、entry point 插件机制；插件外壳的进程边界（先做许可证审查）；文档站 | |

## 11. 需要维护者决定的事项

1. **Apple Developer Program（前置条件，0.4 之前）：** 谁持有 Team ID 与 Developer ID Application 证书；供 `notarytool` 使用的 App Store Connect API key；bundle identifier（例如 `org.roomscope.app`）。未签名发布不是选项。
2. PyPI 名称 `roomscope` 的注册与 trusted publishing。
3. 仓库公开时机：1.0-rc（建议）还是 1.0？
4. 矩阵所需的 DAW 授权：先 Logic Pro、Studio One Pro、Cubase——维护者能运行哪些版本；试用版可用于填行（记录版本）；B 组没人能跑的行保持 untested 直到有贡献者补上。
5. 矩阵所需的硬件：§6.1 各类中手头有哪些设备；用哪款 USB 测量麦克风。
6. 验证活动：参考仪器、房间、执行人；是否允许 REW 作为比较仪器。
7. 是否要求 DCO 签署。
8. 是否默认把原始录音复制进每个会话。

## 12. 对现有代码的影响

`io/wav.py` 的 `read_audio`（别名 `read_wav`）、分离单声道对、有损拒绝、文件元数据；新增 `core/integrity.py`、`core/chain_check.py`、`core/compare.py`（S1 加 `core/loopback.py`），
`pipeline.analyze` 加完整性步骤，`_decay_unreliable_reasons` 加完整性原因；`models/result.py` 加 `SweepIntegrity`、`ChainCheck`、`LoopbackResult`、`roomscope_version`，新增 `models/comparison.py`，
`MeasurementSession` 宽松读取并加 `daw`、设备名、文件元数据、`platform`；`audio/devices.py` + `playrec.py` 合并为实现 `AudioBackend` 的 `audio/portaudio.py`（回调流、`input_channels`、`progress`、`cancel`、`monitor_input`），
新增 `coreaudio_rules.py`、`fake.py`，合成房间助手从 `tests/conftest.py` 搬出；解释层加 `interpret_comparison` 与链路检查建议文本；CLI 新增子命令与参数、退出码 3、`--json` 弃用；
UI 新增检查页、对比视图、Standalone 页的表 / 电平检查 / 停止、DAW 页字段、概览完整性行；`roomscope/__init__.py` 惰性导出与 `__main__.py`；
CI 加 macOS runner、健壮性作业、无网络门禁、打包作业与 `release.yml`、`scripts/build_license_bundle.py`；
文档新增 `DAW_COMPATIBILITY.md`、`HARDWARE_TESTS.md`、`VALIDATION.md`、`user-guide/`、`adr/`，方法学文档 §2a（完整性）、§2b（链路检查）、§11（对比），DEPENDENCIES.md 加 `jsonschema`、`cyclonedx-bom`、PyInstaller 行。
