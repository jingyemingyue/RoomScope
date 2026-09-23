# PyInstaller one-directory spec (ARCHITECTURE_V1.md §6.2).
# Builds are unsigned until the maintainer holds signing identities.
# -*- mode: python ; coding: utf-8 -*-

import sys
import plistlib
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821
MACOS_INFO = plistlib.loads((ROOT / "packaging" / "macos" / "Info.plist").read_bytes())

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
        "PySide6.QtQuickTimeline",
        "PySide6.QtVirtualKeyboard",
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

# macOS .app wrapper (ARCHITECTURE_V1.md §6.2). Unsigned until the maintainer
# holds a Developer ID. The microphone string is required; without it the
# system denies the input device silently. Linux and Windows keep the
# one-directory layout at dist/roomscope so release.yml does not change.
if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        coll,
        name="RoomScope.app",
        icon=None,
        bundle_identifier="org.roomscope.RoomScope",
        info_plist=MACOS_INFO,
    )
