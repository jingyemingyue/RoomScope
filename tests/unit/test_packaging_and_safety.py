from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_installed_wheels_match_the_bundle_gate() -> None:
    """Installed-wheel layout differs by OS (DEPENDENCIES.md §6)."""
    module = _load("audit_wheel_contents", Path("scripts") / "audit_wheel_contents.py")
    reports = {item.name: item for item in module.audit_required()}
    numpy = reports["numpy"]
    scipy = reports["scipy"]
    soundfile = reports["soundfile"]
    sounddevice = reports["sounddevice"]
    matplotlib = reports["matplotlib"]
    numpy_libs = module.bundled_shared_libs(numpy)
    soundfile_libs = module.bundled_shared_libs(soundfile)

    assert matplotlib.ttconv == ()
    assert not any("ttconv" in name.lower() for name in matplotlib.natives)
    assert any("qhull" in name.lower() for name in scipy.licenses)
    assert any("openblas" in name.lower() for name in numpy_libs)
    assert any("libsndfile" in name.lower() for name in soundfile_libs)

    if sys.platform.startswith("linux"):
        assert any("quadmath" in name.lower() for name in numpy_libs)
        assert sounddevice.asio == ()
    elif sys.platform == "win32":
        assert not any("quadmath" in name.lower() for name in numpy_libs)
        assert sounddevice.asio
    else:
        # macOS: OpenBLAS + GCC runtime live under .dylibs/; the sounddevice
        # wheel also lists Windows *-asio.dll files that the bundle gate strips.
        assert any("quadmath" in name.lower() for name in numpy_libs)


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
    assert module.smoke_gui_argv(fake) == [str(fake), "gui", "--smoke"]


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
