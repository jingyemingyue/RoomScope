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


def test_bundle_gate_rejects_asio_and_qtcharts(tmp_path: Path) -> None:
    gate = _load("check_bundle_contents")
    tree = tmp_path / "bundle"
    (tree / "ok").mkdir(parents=True)
    (tree / "ok" / "QtCore.so").write_text("", encoding="utf-8")
    assert gate.check(tree) == []
    (tree / "libportaudio-asio.dll").write_text("", encoding="utf-8")
    charts = tree / "PySide6"
    charts.mkdir()
    (charts / "QtCharts.abi3.so").write_text("", encoding="utf-8")
    errors = gate.check(tree)
    assert any("ASIO" in item for item in errors)
    assert any("GPL-only" in item or "QtCharts" in item for item in errors)
