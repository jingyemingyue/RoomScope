"""The macOS app opens the GUI when Finder passes no arguments."""

from __future__ import annotations

import sys
from unittest.mock import patch

from roomscope.__main__ import desktop_args


def test_finder_launch_opens_gui() -> None:
    with (
        patch.object(sys, "platform", "darwin"),
        patch.object(sys, "executable", "/Applications/RoomScope.app/Contents/MacOS/RoomScope"),
        patch.object(sys, "argv", ["RoomScope"]),
        patch.object(sys, "frozen", True, create=True),
    ):
        assert desktop_args() == ["gui"]


def test_mac_cli_keeps_cli_semantics() -> None:
    with (
        patch.object(sys, "platform", "darwin"),
        patch.object(sys, "executable", "/tmp/roomscope/roomscope"),
        patch.object(sys, "argv", ["roomscope"]),
        patch.object(sys, "frozen", True, create=True),
    ):
        assert desktop_args() is None
