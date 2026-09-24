# RoomScope documentation

This is the documentation hub. GitHub renders the Markdown. A themed HTML
site (S7) is generated from these files:

```bash
python scripts/build_docs_site.py --out site
```

The generator uses only the standard library. Open `site/index.html`.

## For users

- [User guide (English)](user-guide/en.md)
- [用户指南（中文）](user-guide/zh-CN.md)
- [Measuring through your DAW](user-guide/daw-setup.md) · [用 DAW 测量](user-guide/daw-setup.zh-CN.md)
- [How RoomScope compares](COMPARISON.md) · [与其他工具的比较](COMPARISON.zh-CN.md)
- [Audio devices and host APIs](AUDIO_DEVICES.md) · [音频设备与主机 API](AUDIO_DEVICES.zh-CN.md)
- [Developer and installer editions](EDITIONS.md) · [开发者版与安装包版](EDITIONS.zh-CN.md)
- [Compatibility review](COMPATIBILITY.md) · [兼容性](COMPATIBILITY.zh-CN.md)
- [Validation campaign protocol](VALIDATION.md)
- [Hardware test matrix](HARDWARE_TESTS.md)

## For developers

- [Release plan](RELEASE_PLAN.md)
- [Release plan (中文摘要)](RELEASE_PLAN.zh-CN.md)
- [Architecture (v0.1)](ARCHITECTURE.md)
- [Architecture v1.0](ARCHITECTURE_V1.md)
- [Architecture v1.0 (中文摘要)](ARCHITECTURE_V1.zh-CN.md)
- [Measurement methodology](MEASUREMENT_METHODOLOGY.md)
- [Status](STATUS.md)
- [ADR 0001 — v1 architecture decisions](adr/0001-v1-architecture-decisions.md)
- [Project brief (中文)](PROJECT_BRIEF.zh-CN.md)

## Licence and provenance

- [Dependencies](DEPENDENCIES.md)
- [License decision](LICENSE_DECISION.md)
- [Third-party review](THIRD_PARTY_REVIEW.md)
- [Code provenance](CODE_PROVENANCE.md)

## Research notes

- [Literature](research/literature.md)
- [Reference repositories](research/reference_repos.md)
- [Dependency research](research/dependencies.md)
