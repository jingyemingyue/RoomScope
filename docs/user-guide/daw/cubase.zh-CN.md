# Cubase / Nuendo 方案

状态：**草案（DRAFT）——尚未实测。** 依据 Steinberg 的 Cubase Pro 操作手册编写；菜单名称须在矩阵测试时按
[../../DAW_COMPATIBILITY.md](../../DAW_COMPATIBILITY.md) 记录的版本逐项确认。Cubase Pro、Cubase Artist 与 Nuendo 共用音频引擎与这些菜单；
矩阵里各占一行，只有实测过的行才算数。通用流程见 [README.zh-CN.md](README.zh-CN.md)。英文版：[cubase.md](cubase.md)。

## 1. 音频设备与采样率

* *Studio › Studio Setup › Audio System*：驱动 = 你的声卡（macOS 上 Cubase 把 Core Audio 设备列为"ASIO driver"）。
* *Project › Project Setup…*（*Shift-S*）：**Sample Rate** = 声卡采样率。两者不一致时 Cubase 会询问是否切换设备；让它们一致，并用该采样率生成扫频。
* *Studio › Audio Connections*（*F4*）：**Inputs**——在输入 M 上建一个单声道总线；**Outputs**——*Stereo Out* 指向声卡的监听输出对。若使用 **Control Room**，其 *Main* 通道必须指向监听输出对，且测量时**插入效果必须清空或旁通**：Control Room 的插入效果不进入导出，但**确实**在通往音箱的路径上，房间校正插件通常就放在那里。

## 2. 导入扫频且不被拉伸

只有当片段的 **Musical Mode** 打开时 Cubase 才会把音频拉伸到工程速度。对带速度信息的文件（ACID loop、MediaBay 标记过的文件）它会自动打开 Musical Mode；普通的扫频 WAV 没有速度信息，但要核实：

1. *File › Import › Audio File…*。在 *Import Options* 对话框里保留 *Copy File to Project Folder*；**不要**转换采样率（若对话框想转换，说明工程采样率不对——改正后重新导入）。
2. 打开 **Pool**（*Project › Pool*，*Cmd-P*），确认扫频片段的 **Musical Mode** 列**未勾选**。选中事件后 **Info Line** 也显示 *Musical Mode*，必须关闭。
3. 轨道的时间基准（musical / linear）不拉伸音频，可保持原样。不要对片段应用任何 *Audio › Processes*。
4. 关闭 Cycle；不需要改速度轨。

## 3. 路由与录音

* 轨道 1（扫频）：输出 **Stereo Out**。轨道上不放插入效果。
* **Stereo Out**：测量时不放插入效果、不开 EQ——导出会包含输出通道的插入效果，那里的限制器或抖动插件（UV22HR）会进到文件里。
* 轨道 2：*Project › Add Track › Audio*，单声道，**Input：输入 M 上的单声道总线**。录音预备。**Monitor** 按钮（喇叭图标）保持**关闭**：开着的话录音时麦克风信号会被送到监听音箱。
* 把左定位点放在事件之前；**Record**（小键盘 `*` 或走带按钮）；扫频结束约三秒后停止。

## 4. 取出录音

**方式 A（最佳）：录音文件本身。** *Pool*：右键该 take → *Show in Finder*。Cubase 以 WAV 录到 *<工程>/Audio*（含 BWF 块，RoomScope 能读）。这个文件没经过任何处理。

**方式 B：导出轨道。** *File › Export › Audio Mixdown…*：

| 选项 | 取值 |
| --- | --- |
| Channel Selection | **Multiple** → 只勾选麦克风轨（或 *Single* 并选中该轨通道） |
| Export Range | 围绕该 take 设置的 *Locators*，或整个工程 |
| File Format | **Wave** |
| Sample Rate | 工程采样率 |
| Bit Depth | **32 bit float**（24 bit 也可以；除非插了抖动插件，否则没有抖动） |
| Mono / Stereo | 与轨道一致（单声道） |
| Real-Time Export | 关 |
| After Export | 不选（除非你需要 *Create Audio Track* / *Insert to Pool*） |

## 5. Cubase 特有的陷阱

| `roomscope check` 报告的症状 | 要检查的 Cubase 设置 |
| --- | --- |
| 被时间拉伸 x % | 片段的 *Musical Mode* 开着（Pool 列 / Info Line）；对片段做过 warp 或 *Set Definition From Tempo* |
| 错速播放 x % | 工程采样率 ≠ 扫频采样率；在 *Import Options* 里接受了转换 |
| 第 k 次谐波 x dB / 响应偏差 x dB | *Stereo Out* 上有插入效果或 EQ；监听路径上的 Control Room 插入效果（房间校正、限制器）；Control Room 的 *Dim* 或电平微调无害，插件则不然 |
| 在 x dBFS 削波 | Stereo Out 上的限制器；输入增益过高；Control Room *Main* 电平过大地送进回环线 |
| n 次播放 | Cycle 开着，或同一 lane 里录了两个 take |

## 6. 矩阵测试时的确认清单

- [ ] 记录 Cubase（或 Nuendo）的版本类别、版本号与 macOS 版本
- [ ] 在该版本上确认以上菜单路径（记下任何改名的项目）
- [ ] 记录采样率不一致时 *Import Options* 的行为（询问 / 静默转换）
- [ ] 记录导入扫频 WAV 后 Musical Mode 的状态（预期：关）
- [ ] 是否使用 Control Room；若使用，确认插入效果为空
- [ ] 方式 A **和** 方式 B 的链路检查都 PASS
- [ ] 回环录音连同 README 存入 `tests/fixtures/daw/cubase/`
