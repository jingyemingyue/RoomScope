"""``python -m roomscope`` entry point for desktop bundles."""

from __future__ import annotations

import sys

from roomscope.cli.main import main


def desktop_args() -> list[str] | None:
    """Finder launches the frozen macOS app without command-line arguments."""
    if (
        sys.platform == "darwin"
        and getattr(sys, "frozen", False)
        and ".app/Contents/MacOS/" in sys.executable
        and len(sys.argv) == 1
    ):
        return ["gui"]
    return None


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(desktop_args()))
