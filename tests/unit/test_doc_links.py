from __future__ import annotations

import importlib.util
from pathlib import Path


def _load():
    path = Path("scripts") / "check_doc_links.py"
    spec = importlib.util.spec_from_file_location("check_doc_links", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_docs_relative_links_resolve() -> None:
    errors = _load().check(Path("docs"))
    assert errors == []


def test_docs_index_lists_user_guide_and_architecture() -> None:
    text = Path("docs/index.md").read_text(encoding="utf-8")
    assert "user-guide/en.md" in text
    assert "ARCHITECTURE_V1.md" in text
    assert "VALIDATION.md" in text
    assert "build_docs_site.py" in text


def test_fixtures_readme_states_cc0_and_empty_table() -> None:
    text = Path("tests/fixtures/README.md").read_text(encoding="utf-8")
    assert "CC0" in text
    assert "No real recordings are checked in yet" in text
