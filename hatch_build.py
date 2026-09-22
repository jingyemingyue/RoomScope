"""Hatch hook: compile gettext ``.po`` catalogs to ``.mo`` at packaging time."""

from __future__ import annotations

import sys
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


class CustomBuildHook(BuildHookInterface):
    def initialize(self, _version: str, build_data: dict[str, object]) -> None:
        from roomscope.i18n import compile_catalogs

        compile_catalogs()
        build_data.setdefault("force_include", {})
