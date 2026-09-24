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


def test_windows_gui_launcher_opens_gui() -> None:
    with (
        patch.object(sys, "platform", "win32"),
        patch.object(sys, "executable", r"C:\Program Files\RoomScope\roomscope-gui.exe"),
        patch.object(sys, "argv", [r"C:\Program Files\RoomScope\roomscope-gui.exe"]),
        patch.object(sys, "frozen", True, create=True),
    ):
        assert desktop_args() == ["gui"]


def test_linux_gui_launcher_opens_gui() -> None:
    with (
        patch.object(sys, "platform", "linux"),
        patch.object(sys, "executable", "/opt/roomscope/roomscope-gui"),
        patch.object(sys, "argv", ["roomscope-gui"]),
        patch.object(sys, "frozen", True, create=True),
    ):
        assert desktop_args() == ["gui"]


def test_console_executable_keeps_cli_semantics() -> None:
    with (
        patch.object(sys, "platform", "win32"),
        patch.object(sys, "executable", r"C:\Program Files\RoomScope\roomscope.exe"),
        patch.object(sys, "argv", ["roomscope.exe"]),
        patch.object(sys, "frozen", True, create=True),
    ):
        assert desktop_args() is None


def test_gui_launcher_passes_explicit_arguments_through() -> None:
    with (
        patch.object(sys, "platform", "win32"),
        patch.object(sys, "executable", r"C:\RoomScope\roomscope-gui.exe"),
        patch.object(sys, "argv", ["roomscope-gui.exe", "gui", "--smoke"]),
        patch.object(sys, "frozen", True, create=True),
    ):
        assert desktop_args() is None


def test_unfrozen_python_is_never_redirected() -> None:
    with (
        patch.object(sys, "executable", "/usr/bin/roomscope-gui"),
        patch.object(sys, "argv", ["roomscope-gui"]),
        patch.object(sys, "frozen", False, create=True),
    ):
        assert desktop_args() is None
