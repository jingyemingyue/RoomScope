"""``python -m roomscope`` entry point for desktop bundles."""

from __future__ import annotations

import sys

from roomscope.cli.main import main

#: Windowed launcher next to the console ``roomscope`` in the Windows and Linux
#: bundles. Explorer, the Start menu and desktop files start it without
#: arguments, which must open the GUI instead of printing CLI help.
GUI_LAUNCHER_STEM = "roomscope-gui"


def desktop_args() -> list[str] | None:
    """Arguments for a frozen desktop launch that passed none, else ``None``.

    Finder starts the macOS app, and Explorer / a desktop file start the
    windowed ``roomscope-gui`` launcher, without command-line arguments. The
    console ``roomscope`` executable keeps its CLI behaviour.
    """
    if not getattr(sys, "frozen", False) or len(sys.argv) != 1:
        return None
    if sys.platform == "darwin" and ".app/Contents/MacOS/" in sys.executable:
        return ["gui"]
    name = sys.executable.replace("\\", "/").rsplit("/", 1)[-1].lower()
    if name.removesuffix(".exe") == GUI_LAUNCHER_STEM:
        return ["gui"]
    return None


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(desktop_args()))
