from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(name: str):
    path = Path("scripts") / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_license_bundle_has_no_unresolved(tmp_path: Path) -> None:
    bundle_mod = _load("build_license_bundle")
    dest = tmp_path / "THIRD_PARTY_LICENSES"
    unresolved = bundle_mod.build(dest)
    required_present = {"numpy", "scipy", "soundfile", "sounddevice", "matplotlib"}
    missing_required = [name for name in required_present if name in unresolved]
    assert missing_required == []
    index = (dest / "INDEX.txt").read_text(encoding="utf-8")
    assert "ttconv: resolved" in index
    assert (dest / "_notices" / "pyside6.txt").is_file()
    if unresolved:
        assert "PySide6" not in "".join(unresolved)


def test_license_bundle_ships_verbatim_lgpl_gpl_and_portaudio_texts(tmp_path: Path) -> None:
    """DEPENDENCIES.md §3-§4: the wheels omit these texts, so the repo carries them."""
    bundle_mod = _load("build_license_bundle")
    dest = tmp_path / "THIRD_PARTY_LICENSES"
    bundle_mod.build(dest)
    lgpl = (dest / "_texts" / "LGPL-3.0.txt").read_text(encoding="utf-8")
    gpl = (dest / "_texts" / "GPL-3.0.txt").read_text(encoding="utf-8")
    portaudio = (dest / "_texts" / "PortAudio-LICENSE.txt").read_text(encoding="utf-8")
    assert "GNU LESSER GENERAL PUBLIC LICENSE" in lgpl and "Version 3, 29 June 2007" in lgpl
    assert "GNU GENERAL PUBLIC LICENSE" in gpl and "Version 3, 29 June 2007" in gpl
    assert "TERMS AND CONDITIONS" in gpl
    assert "Ross Bencina and Phil Burk" in portaudio
    assert "The above copyright notice and this permission notice" in portaudio
    assert "_texts/LGPL-3.0.txt" in (dest / "_notices" / "pyside6.txt").read_text(encoding="utf-8")


def test_license_bundle_reports_missing_qt_texts_when_pyside_is_installed(tmp_path: Path) -> None:
    bundle_mod = _load("build_license_bundle")
    dest = tmp_path / "THIRD_PARTY_LICENSES"
    unresolved = bundle_mod.build(dest, texts_dir=tmp_path / "no-such-dir")
    qt_installed = bundle_mod._installed("PySide6_Essentials") or bundle_mod._installed("PySide6")
    missing = {item for item in unresolved if item.startswith("text:")}
    if qt_installed:
        assert missing == {"text:LGPL-3.0.txt", "text:GPL-3.0.txt"}
    else:
        assert missing == set()


def test_macos_info_plist_declares_microphone() -> None:
    plist = Path("packaging/macos/Info.plist").read_text(encoding="utf-8")
    assert "NSMicrophoneUsageDescription" in plist
    assert "measurement microphone" in plist
    entitlements = Path("packaging/macos/entitlements.plist").read_text(encoding="utf-8")
    assert "com.apple.security.device.audio-input" in entitlements
    spec = Path("packaging/roomscope.spec").read_text(encoding="utf-8")
    assert "packaging" in spec and "Info.plist" in spec


def test_bundle_gate_rejects_asio_and_qtcharts(tmp_path: Path) -> None:
    gate = _load("check_bundle_contents")
    tree = tmp_path / "bundle"
    (tree / "ok").mkdir(parents=True)
    (tree / "ok" / "QtCore.so").write_text("", encoding="utf-8")
    (tree / "ok" / "QtCharts.pyi").write_text("", encoding="utf-8")
    assert gate.check(tree) == []
    (tree / "libportaudio-asio.dll").write_text("", encoding="utf-8")
    charts = tree / "PySide6"
    charts.mkdir()
    (charts / "QtCharts.abi3.so").write_text("", encoding="utf-8")
    errors = gate.check(tree)
    assert any("ASIO" in item for item in errors)
    assert any("GPL-only" in item or "QtCharts" in item for item in errors)


def test_bundle_gate_catches_versioned_qt6_libraries_and_frameworks(tmp_path: Path) -> None:
    """Library file names carry the Qt major version and, on Linux, a version suffix."""
    gate = _load("check_bundle_contents")
    tree = tmp_path / "bundle"
    lib = tree / "PySide6" / "Qt" / "lib"
    lib.mkdir(parents=True)
    (lib / "libQt6Widgets.so.6").write_text("", encoding="utf-8")
    assert gate.check(tree) == []
    (lib / "libQt6QuickTimeline.so.6").write_text("", encoding="utf-8")
    (tree / "Qt6VirtualKeyboard.dll").write_text("", encoding="utf-8")
    framework = tree / "Frameworks" / "QtCharts.framework" / "Versions" / "A"
    framework.mkdir(parents=True)
    (framework / "QtCharts").write_text("", encoding="utf-8")
    (framework / "Resources").mkdir()
    (framework / "Resources" / "Info.plist").write_text("", encoding="utf-8")
    errors = gate.check(tree)
    joined = "\n".join(errors)
    assert "libQt6QuickTimeline.so.6" in joined
    assert "Qt6VirtualKeyboard.dll" in joined
    assert str(framework / "QtCharts") in joined
    assert "libQt6Widgets" not in joined


def test_bundle_gate_strip_removes_offenders_and_then_passes(tmp_path: Path) -> None:
    gate = _load("check_bundle_contents")
    tree = tmp_path / "bundle"
    lib = tree / "PySide6" / "Qt" / "lib"
    lib.mkdir(parents=True)
    (lib / "libQt6Widgets.so.6").write_text("", encoding="utf-8")
    (lib / "libQt6QuickTimeline.so.6").write_text("", encoding="utf-8")
    (tree / "libportaudio64bit-asio.dll").write_text("", encoding="utf-8")
    framework = tree / "QtCharts.framework" / "Versions" / "A"
    framework.mkdir(parents=True)
    (framework / "QtCharts").write_text("", encoding="utf-8")
    removed = gate.strip(tree)
    assert {path.name for path in removed} == {
        "libQt6QuickTimeline.so.6",
        "libportaudio64bit-asio.dll",
        "QtCharts",
    }
    assert (lib / "libQt6Widgets.so.6").is_file()
    assert not (tree / "QtCharts.framework").exists()
    assert gate.check(tree) == []


def test_bundle_gate_require_licenses_needs_the_verbatim_texts(tmp_path: Path) -> None:
    gate = _load("check_bundle_contents")
    tree = tmp_path / "bundle"
    licenses = tree / "THIRD_PARTY_LICENSES"
    licenses.mkdir(parents=True)
    (licenses / "INDEX.txt").write_text("unresolved: none\n", encoding="utf-8")
    errors = gate.check(tree, require_licenses=True)
    assert any("LGPL-3.0.txt" in item for item in errors)
    texts = licenses / "_texts"
    texts.mkdir()
    for name in ("LGPL-3.0.txt", "GPL-3.0.txt", "PortAudio-LICENSE.txt"):
        (texts / name).write_text("x", encoding="utf-8")
    assert gate.check(tree, require_licenses=True) == []


def test_installed_essentials_mode_ignores_wheel_stubs_and_stock_plugins(
    tmp_path: Path,
) -> None:
    gate = _load("check_bundle_contents")
    root = tmp_path / "PySide6"
    plugins = root / "Qt" / "plugins" / "platforminputcontexts"
    qml = root / "Qt" / "qml" / "QtQuick" / "Timeline"
    lib = root / "Qt" / "lib"
    plugins.mkdir(parents=True)
    qml.mkdir(parents=True)
    lib.mkdir(parents=True)
    (root / "QtCharts.pyi").write_text("", encoding="utf-8")
    (plugins / "libqtvirtualkeyboardplugin.so").write_text("", encoding="utf-8")
    (qml / "libqtquicktimelineplugin.so").write_text("", encoding="utf-8")
    # Essentials 6.9+ ships this versioned library although RoomScope never loads it.
    (lib / "libQt6QuickTimeline.so.6").write_text("", encoding="utf-8")
    assert gate.check(root, installed_essentials=True) == []
    (root / "QtCharts.abi3.so").write_text("", encoding="utf-8")
    errors = gate.check(root, installed_essentials=True)
    assert any("QtCharts" in item for item in errors)
