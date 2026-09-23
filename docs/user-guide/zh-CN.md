# RoomScope 用户指南

RoomScope 用来测量录音房间，让你听到房间对近距离拾音声源做了什么。它不给房间打分，也不做校正。

英文原文见 [en.md](en.md)。

## 安装

**用 Python（pipx）。** `pipx install "roomscope[gui]"` 会装好 `roomscope` 命令。从源码开发请用 `pip install -e ".[gui]"`。

**未签名桌面包。** `release.yml` 会为 macOS、Windows、Linux 打出一目录布局的包。在维护者持有签名证书之前，这些包都是**未签名**的：

* **macOS：** 右键打开，或在“隐私与安全性”里放行。系统询问麦克风权限时请允许。
* **Windows：** SmartScreen 可能拦截，选“更多信息”→“仍要运行”。
* **Linux：** 解压目录后运行 `roomscope`。

关于对话框和 `THIRD_PARTY_LICENSES/` 列出了 Qt、libsndfile 等许可证。

## 通用 DAW 模式

1. `roomscope sweep --out sweep.wav`（或界面里的生成按钮）。把 `.roomscope-sweep.json` 和 WAV 放在一起。
2. 把 WAV 导入 DAW 新轨道，路由到监听。
3. 用测量话筒录第二条轨道。导出时不要裁切。
4. 可选 loopback：导出双声道（话筒 + 电回送），使用 `--channel 0 --loopback-channel 1`。
5. `roomscope analyze --recording take.wav --sweep sweep.wav --out session/`，或在界面里打开这些文件。

## 独立模式与 loopback 线

`roomscope devices` 列出设备。`roomscope measure --out session/` 播放扫描并录音。`--input-channels 1,2 --loopback-channel 2` 在输入 2 记录电回送。

先把监听开低。超过 −12 dBFS 每次都要 `--acknowledge-level`；该确认永不保存。

**演示**（界面或 `roomscope --backend fake measure`）在合成房间上走同一流程，不会对扬声器发声。

## 读结果

每个指标都有有效性标记。`insufficient_decay_range` 表示数字被收回，不是零。没有总分。

核心诊断（`warnings` / `notes` / `reason`）在 `result.json` 里始终是英文，方便跨语言对比缺陷。界面在标明这一点的标题下原样显示。

## 对比两个位置

`roomscope compare baseline/ candidate/ --same-input-gain`（或界面的对比页）。只有两侧都是 VALID 时，衰减差值才是 VALID。噪声差值需要明确声明“输入增益未变”。变化从不被称为显著；ISO 3382-1 对 T 的刚可察觉差只作为背景引用。

## 项目与平均

项目文件夹包含 `project.json` 和普通会话文件夹。
`roomscope project init --out room/ --name Booth`，再
`roomscope project add room/ session/ --position desk`。
`roomscope project average room/` 只平均有效的 T 值，从不平均衰减曲线，并标出位置数量达到的 ISO 3382-2 等级。

## 导出与语言

`roomscope export session/ --format csv --out curves/` 导出每条曲线。
`--lang zh_CN`（或设置 → 语言，或 `ROOMSCOPE_LANG`）会翻译解读、报告标签、界面和命令行。单位不翻译；数字保持 ASCII。

## 排错

| 现象 | 检查 |
| --- | --- |
| 直达声置信度不高 | 扫频侧车文件不对；扬声器失真；不要裁切录音。 |
| 削波警告 | 降低回放或输入增益。 |
| 衰减范围不足 | 加长扫描、略提高回放，或换更安静的房间。 |
| 设备采样率不符 | 界面会在请求采样率旁边显示设备实际采样率。 |
| loopback 被拒绝 | 回送必须像电脉冲，不能是房间响应。 |

## 缺陷报告打包

`roomscope session bundle session/ --out report.zip` 打包会话。
`--no-audio` 可去掉 WAV，避免分享房间录音。把 zip 附在测量类 issue 上。设置和滚动日志在 `$ROOMSCOPE_HOME`（默认 `~/.roomscope`）。
