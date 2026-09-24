"""``python -m roomscope`` entry point for desktop bundles."""

from __future__ import annotations

import sys

from roomscope.cli.main import COMMANDS, main

#: Windowed launcher next to the console ``roomscope`` in the Windows and Linux
#: bundles. Explorer, the Start menu and desktop files start it without
#: arguments, which must open the GUI instead of printing CLI help.
GUI_LAUNCHER_STEM = "roomscope-gui"


def desktop_args() -> list[str] | None:
    """``["gui"]`` for a frozen desktop launch, else ``None`` (the CLI parses ``sys.argv``).

    Finder starts the macOS app, and Explorer / a desktop file start the
    windowed ``roomscope-gui`` launcher, without command-line arguments (or,
    for the launcher, with a dropped file). The console ``roomscope``
    executable keeps its CLI behaviour.
    """
    if not getattr(sys, "frozen", False):
        return None
    args = sys.argv[1:]
    if sys.platform == "darwin" and ".app/Contents/MacOS/" in sys.executable:
        return ["gui"] if not args else None
    name = sys.executable.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if name.removesuffix(".exe") != GUI_LAUNCHER_STEM:
        return None
    # The windowed launcher has no console to show a usage error on: a file
    # dropped on it or opened with it ("Open with") opens the GUI instead of
    # failing silently. A real command or option keeps the CLI.
    if not args or (args[0] not in COMMANDS and not args[0].startswith("-")):
        return ["gui"]
    return None


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(desktop_args()))
