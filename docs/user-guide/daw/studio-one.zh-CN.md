# Studio One Pro 方案

状态：**草案（DRAFT）——尚未实测。** 依据 PreSonus 的 Studio One 参考手册与知识库编写；菜单名称须在矩阵测试时按
[../../DAW_COMPATIBILITY.md](../../DAW_COMPATIBILITY.md) 记录的版本逐项确认。该产品自第 7 版起叫 *Studio One Pro*
（此前为 *Studio One Professional*）；本方案应同样适用于 Studio One Artist，但未测试。通用流程见 [README.zh-CN.md](README.zh-CN.md)。英文版：[studio-one.md](studio-one.md)。

## 1. 音频设备与采样率

* *Studio One › 设置 › 音频设置（Audio Setup）*：音频设备 = 你的声卡；此处显示设备采样率。
* *Song › Song Setup › General*：**Sample Rate** = 声卡采样率。歌曲与设备采样率不一致时 Studio One 会警告；让两者一致，并用该采样率生成扫频。

## 2. 导入扫频且不被拉伸

Studio One 在知道（或猜到）文件速度时会把导入的音频拉伸到歌曲速度。测量用的歌曲里要关掉：

1. 新建歌曲时，在 *New Song* 对话框取消勾选 **Stretch Audio Files to Song Tempo**；已有歌曲则 *Song › Song Setup › General* → 取消勾选 **Stretch audio files to Song tempo**。
2. 导入：从 *Browser › Files* 把 WAV 拖到一条空音频轨，或 *Song › Import File…*。不要接受采样率转换。
3. 选中事件，打开 **Inspector**（*F4* / *i* 按钮），检查事件参数：**Tempo：Don't Follow**（另两个取值是 *Follow* 与 *Timestretch*）；**Speedup：1.00**（Speedup 是与速度无关的时间拉伸，必须保持 ×1）；**Transpose 0**、**Tune 0**。
4. 关闭 Loop（循环按钮）。

## 3. 路由与录音

* 轨道 1（扫频）：输出 **Main**。轨道上不放插入效果。
* **Main** 通道：测量时不放插入效果。在 *Song › Song Setup › Audio I/O Setup › Outputs* 里 Main 输出必须是声卡送往监听音箱的那对输出。若你的版本有独立的监听总线（Listen bus / 类似 Control Room 的路由），其插入效果也要清空：它们在通往音箱的路径上。
* 轨道 2：*Track › Add Tracks…*，Audio，单声道，**Input：Input M**（若不存在，先在 *Audio I/O Setup › Inputs* 定义该单声道输入）。录音预备。蓝色的 **Monitor** 按钮保持**关闭**：开着的话录音时麦克风信号会被送到监听音箱。
* 播放头放在事件之前；**Record**；扫频结束约三秒后停止。

## 4. 取出录音

**方式 A（最佳）：录音文件本身。** *Browser › Pool*：右键该 take → *Show in Finder*。Studio One 把 WAV 录到 *<歌曲文件夹>/Media*。这个文件没经过任何处理。

**方式 B：导出轨道。** *Song › Export Stems…*：

| 选项 | 取值 |
| --- | --- |
| Sources | *Tracks* → 只勾选麦克风轨 |
| Format | **Wave** |
| Resolution | **32 Bit Float**——Studio One 在导出低于 32 bit float 的格式时默认加抖动，用浮点可避免；若选 24 Bit，确认 *Dither* 关闭 |
| Sample Rate | 歌曲采样率 |
| Export Range | 整首歌曲，或围绕该 take 设置的循环范围 |
| Import to Track | 关 |

对麦克风轨 Solo 后用 *Song › Export Mixdown* 也可以（格式设置相同），但它经过 Main 总线渲染；Export Stems（或方式 A）更干净。

## 5. Studio One 特有的陷阱

| `roomscope check` 报告的症状 | 要检查的 Studio One 设置 |
| --- | --- |
| 被时间拉伸 x % | Inspector 的 *Tempo* 设成了 Follow 或 Timestretch；*Stretch audio files to Song tempo* 开着；*Speedup* ≠ 1.00 |
| 错速播放 x % | 歌曲采样率 ≠ 扫频采样率；导入时接受了转换；*Tape* 拉伸模式下的 *Speedup*（同时改变音高与速度） |
| 第 k 次谐波 x dB / 响应偏差 x dB | Main 或监听 / Listen 总线上有插入效果；扫频轨上有插件 |
| 高频本底抬高 | 低于 32 bit float 的导出加了抖动 |
| n 次播放 | Loop 开着，或同一事件里录了两个 take |

## 6. 矩阵测试时的确认清单

- [ ] 记录 Studio One Pro 版本与 macOS 版本
- [ ] 在该版本上确认以上菜单路径（记下任何改名的项目）
- [ ] 记录新歌曲里 *Stretch audio files to Song tempo* 的默认状态
- [ ] 记录导入时是静默转换采样率还是询问
- [ ] 确认或更正"*Export Stems* 低于 32 bit float 时默认加抖动"这一说法
- [ ] 方式 A **和** 方式 B 的链路检查都 PASS
- [ ] 回环录音连同 README 存入 `tests/fixtures/daw/studio-one/`
