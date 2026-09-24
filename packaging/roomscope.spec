# PyInstaller one-directory spec (ARCHITECTURE_V1.md §6.2).
# Builds are unsigned until the maintainer holds signing identities.
# -*- mode: python ; coding: utf-8 -*-

import sys
import plistlib
import tomllib
from pathlib import Path

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821
MACOS_INFO = plistlib.loads((ROOT / "packaging" / "macos" / "Info.plist").read_bytes())
VERSION = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
MACOS_INFO["CFBundleShortVersionString"] = VERSION
MACOS_INFO["CFBundleVersion"] = VERSION

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

# Keep the console executable for CLI users. Finder needs a separate windowed
# bootloader so the .app opens the GUI and receives normal macOS app events.
if sys.platform == "darwin":
    gui_exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="RoomScope",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
    )
    gui_coll = COLLECT(
        gui_exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="roomscope-gui",
    )
    app = BUNDLE(  # noqa: F821
        gui_coll,
        name="RoomScope.app",
        icon=None,
        bundle_identifier="org.roomscope.RoomScope",
        info_plist=MACOS_INFO,
    )
