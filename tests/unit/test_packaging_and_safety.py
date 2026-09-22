from __future__ import annotations

import importlib.util
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_src_safety_script_is_clean() -> None:
    module = _load("check_src_safety", Path("scripts") / "check_src_safety.py")
    assert module.check(Path("src")) == []


def test_inno_setup_and_linux_desktop_files_exist() -> None:
    iss = Path("packaging/windows/roomscope.iss").read_text(encoding="utf-8")
    assert "roomscope.exe" in iss
    assert "dist\\roomscope" in iss or "dist/roomscope" in iss
    desktop = Path("packaging/linux/roomscope.desktop").read_text(encoding="utf-8")
    assert "Exec=roomscope" in desktop
    apprun = Path("packaging/linux/AppRun").read_text(encoding="utf-8")
    assert "roomscope" in apprun
    dmg = Path("packaging/macos/make_dmg.sh").read_text(encoding="utf-8")
    assert "hdiutil" in dmg


def test_smoke_bundle_finds_explicit_binary(tmp_path: Path) -> None:
    module = _load("smoke_bundle", Path("scripts") / "smoke_bundle.py")
    fake = tmp_path / "roomscope"
    fake.write_text("#!/bin/sh\n", encoding="utf-8")
    assert module.find_binary(tmp_path, None) == fake
    assert module.find_binary(None, fake) == fake


def test_settings_refuse_deep_json_and_fall_back(tmp_path: Path, monkeypatch) -> None:
    from roomscope.io.jsonutil import MAX_JSON_DEPTH
    from roomscope.settings import load_settings, settings_path

    monkeypatch.setenv("ROOMSCOPE_HOME", str(tmp_path / "home"))
    settings_path().parent.mkdir(parents=True, exist_ok=True)
    depth = MAX_JSON_DEPTH + 3
    settings_path().write_text("{" * depth + "}" * depth, encoding="utf-8")
    loaded = load_settings()
    assert loaded.language == ""
    assert loaded.copy_recording is True
