# RoomScope 发布计划（中文摘要）

英文版 [RELEASE_PLAN.md](RELEASE_PLAN.md) 为准，本文只是摘要。2026-09-24 采纳。

没有日期：达到退出条件才发版（ARCHITECTURE_V1.md §10）。

## 1. 现状

* `main` 已经包含 v0.1 基础 + 0.2（重开与对比）+ 0.3（信任测量链）+ 0.4（面向所有人）+ 1.0-rc 的纯软件部分。四个里程碑 PR（#5、#6、#7、#8）在 2026-09-24 审查后合并，审查发现记录为 issue #9–#16。
* 还没有任何 tag 或 GitHub Release，仓库仍是私有。
* 需要人在真实房间完成的事情都没做：硬件矩阵（HARDWARE_TESTS.md）没有一格 PASS，验证活动（VALIDATION.md）没有跑。维护者近期没有测量设备，所以这些排在最后，也可以在开源之后由贡献者补。
* 签名证书、PyPI 项目名与可信发布、公开仓库，都是维护者决定，目前全部未定。

## 2. 版本阶梯

| 版本 | 目的 | 切版前必须成立 | 不声称 |
| --- | --- | --- | --- |
| **0.4.0** | 第一个预发布：把 `main` 上的东西做成草稿 Release 和未签名安装包，供维护者自测 | 三个系统、Python 3.12–3.14 的 CI 全绿；ruff、mypy、schema、打包门禁通过；许可证包含 LGPL-3.0 / GPL-3.0 / PortAudio 原文；CHANGELOG 有 `[0.4.0]` 节；STATUS 有带日期的快照 | 任何硬件结果；真人安装过安装包；PyPI；公开可用 |
| **0.4.x** | 审查后续修复 | 每个补丁至少关闭 #9–#17 之一并带合成测试；不加功能（0.4.1 一次关闭全部九项） | — |
| **0.5.0** | “有人用过”：Standalone 和 DAW 流程第一次在真实硬件上跑通 | 至少一个平台上硬件矩阵每格都有带日期的 PASS；#12、#13、#14、#15 关闭 | 验证活动；API/schema 冻结；签名 |
| **1.0.0rc1** | 冻结并证明 | ARCHITECTURE_V1.md §3.1 的 MUST 项无一开放：硬件矩阵每个平台至少跑过一次、验证活动连数据一起发布、签名或维护者明确决定不签、公开仓库清单执行完、API 与 schema 冻结 | — |
| **1.0.0** | 正式版 | 只含候选版之后的修复；发布说明写明验证结果和已知限制 | — |

## 3. 一次发布怎么产生

流水线是 `.github/workflows/release.yml`，由 `pyproject.toml` 里的版本号驱动，最后一步始终由维护者点击。

> **工作流状态（2026-09-24）**：按版本号发布的 `.github/workflows/release.yml`
> 已加入 PR #18。PR 验证运行会在 Linux、macOS、Windows 上构建安装包并执行
> 门禁及冒烟测试，不创建草稿 Release，也不上传 PyPI。PR 合并后，新工作流才
> 在 `main` 生效；合并带来 `pyproject.toml` 的 0.4.1 版本变更，发布任务
> 通过后应生成第一个 v0.4.1 草稿。发布前核对合并提交的 CI 和草稿附件。
> 在旧的只认 tag 的工作流仍位于 `main` 时，不要推送 tag。

1. **在 `main` 上准备发布提交**：把 `project.version` 改成新版本（不带 `.dev`），把 CHANGELOG 的 `[Unreleased]` 挪到 `## [版本] - 日期` 下，在 `docs/STATUS.md` 加一条写明“实际跑了什么”的快照，依赖版本有变时复查 DEPENDENCIES.md §3–§4。提交并推送。
2. **CI 自动开草稿**：`pyproject.toml` 在 `main` 上变了、且还没有 `v<版本>` 这个 tag，工作流就会跑 lint/类型检查/测试，构建 sdist 和 wheel，在三个系统上构建未签名安装包（许可证包 → PyInstaller → 剥掉 GPL-only Qt 模块和 ASIO DLL → 门禁 → 冒烟测试 → 打包 → 校验和），生成 SBOM，然后开一个名为 `v<版本>` 的**草稿** Release，把 CHANGELOG 对应段落作正文、所有压缩包作附件。**此时还没有 tag。** 带 `.dev` 的版本不会开草稿。
3. **维护者决定**：从草稿下载安装包在真机上试；发布（publish）或删除草稿。发布这一下会在发布提交上创建 tag `v<版本>` —— 这就是项目简报里保留给维护者的“正式 Release”决定。
4. **tag 触发的运行**：tag 被创建后再跑一遍质量门禁；只有当仓库变量 `ROOMSCOPE_PUBLISH_PYPI` 为 `true`、`pypi` 环境和 PyPI 可信发布都配好了，才会把 wheel 传到 PyPI。在此之前不会有任何东西到 PyPI。

由此得出的规则：`pyproject.toml` 是版本号的唯一来源；tag 名与它不一致时工作流失败；tag 只来自发布草稿或维护者自己推送；已发布的历史永不重写。

## 4. 每次发布都适用的门禁

CI 全绿（lint、mypy、文档链接检查、文档站点构建、`check_src_safety.py`、schema、测试矩阵、`core`/`models` 85% 覆盖率、打包、已安装 Essentials 的 GPL 门禁）；发布工作流全绿（`--strip --require-licenses` 门禁、每个系统的冒烟测试）；DEPENDENCIES.md §6 没有影响所发二进制的 UNKNOWN / NEEDS REVIEW；STATUS 如实写明跑了什么、没跑什么，硬件格保持空白直到有人填上日期和声卡型号；CHANGELOG 有该版本段落，审查发现的夸大说法在同一版本里更正（0.4.0：中文目录只覆盖七个 profile 中的三个，见 #14，0.4.1 已补全）。

## 5. 仍待维护者决定

公开仓库（§9.1 清单）；Apple Developer ID + 公证、Windows 签名，或明确决定不签名发 1.0；PyPI 注册 `roomscope`、配可信发布、建 `pypi` 环境、设 `ROOMSCOPE_PUBLISH_PYPI=true`；验证活动的房间、参考工具（REW 只作对比仪器）和执行人；是否要求 DCO 签署；Dependabot 的 #3 / #4 在它重新 rebase 到 SHA 固定的工作流并且 CI 绿之后合并。

## 6. 2026-09-24 审查后续（issue）

#9 频响对比先插值再平滑（混叠）；#10 `analyze-ir` 无测试；#11 会话加载跟随绝对路径；#12 环回 FIR 窗把补偿后的响应提前约 5 ms；#13 PortAudio 在实时回调里报进度、回调异常被吞；#14 中文目录不全、安全提示未翻译、`.mo` 未随包发布；#15 ISO 3382-2 表 1 未注明来源、engineering 等级不检查话筒数；#16 `check_src_safety.py` 漏检、覆盖率数字未记录。#17 打包门禁按文件名认不出虚拟键盘的 QML 插件。

**更新（2026-09-24 稍晚）：** 以上九项都已在分支 `v0.4.1-review-followups` 修好（版本号 0.4.1，每项都有在 0.4.0 上会失败的合成测试，见 CHANGELOG `[0.4.1]`）。因为 #17 必须在发布任何安装包之前关闭（§4），0.4.0 不再单独发 Release：这个 PR 在 CI 全绿后合并，第一个草稿 Release 就是 v0.4.1。

## 7. 本计划不做的事

不公开仓库、不创建正式 Release、不改许可证、不手动推 tag、不重写历史、不声称任何硬件结果。这些要么是维护者的一次点击，要么需要有人站在房间里。
