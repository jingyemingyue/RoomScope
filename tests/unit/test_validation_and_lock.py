from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_lock_script():
    path = Path("scripts") / "compile_bundle_lock.py"
    spec = importlib.util.spec_from_file_location("compile_bundle_lock", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_validation_protocol_states_tolerances_before_results() -> None:
    text = Path("docs/VALIDATION.md").read_text(encoding="utf-8")
    assert "protocol written; not yet run" in text.lower()
    assert "5 % or 0.02 s" in text
    assert "0.2 ms" in text
    assert "1.0 dB" in text
    assert "5 cm" in text
    assert "Same WAV" in text
    assert "| Room | Position | Take |" in text
    assert "Nothing below is filled from the fake backend" in text


def test_bundle_lock_is_runtime_only() -> None:
    lock = Path("requirements/bundle.lock").read_text(encoding="utf-8")
    assert "numpy==" in lock
    assert "scipy==" in lock
    assert "matplotlib==" in lock
    lowered = lock.lower()
    for forbidden in ("mypy==", "pytest==", "ruff==", "coverage=="):
        assert forbidden not in lowered
    compiled = _load_lock_script().compile_lock()
    names = {line.split("==", 1)[0].lower().replace("_", "-") for line in compiled}
    assert "numpy" in names
    assert "mypy" not in names
