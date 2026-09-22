# PyInstaller one-directory spec (ARCHITECTURE_V1.md §6.2).
# Builds are unsigned until the maintainer holds signing identities.
# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821

a = Analysis(
    [str(ROOT / "src" / "roomscope" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[
        (str(ROOT / "src" / "roomscope" / "schemas"), "roomscope/schemas"),
        (str(ROOT / "src" / "roomscope" / "locale"), "roomscope/locale"),
    ],
    hiddenimports=["roomscope.cli.main", "roomscope.ui.app"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PySide6.QtCharts",
        "PySide6.QtDataVisualization",
        "PySide6.QtGraphs",
        "PySide6.QtLottie",
        "PySide6.QtQuick3D",
        "PySide6.QtHttpServer",
        "PySide6.QtNetworkAuth",
        "PySide6.QtShaderTools",
    ],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="roomscope",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="roomscope",
)
