"""Developer edition and installer edition (docs/EDITIONS.md).

One code base, two defaults:

* **developer** — a source checkout or a ``pip`` install: debugging tools are
  on (the GUI's Developer menu with the audio-device inspector and the
  environment report, advanced stream options in Standalone Mode). Developers
  extend RoomScope through its entry points (``roomscope.exporters``) and the
  Python API.
* **user** — the desktop bundles and installers: the same measurement, with
  the everyday settings only (language, theme, default profile, backend).

``ROOMSCOPE_EDITION=developer|user`` overrides the default, and a user can
switch the developer tools on in Settings.
"""

from __future__ import annotations

import os
import sys

ENV_EDITION = "ROOMSCOPE_EDITION"
DEVELOPER = "developer"
USER = "user"


def edition() -> str:
    """``developer`` or ``user`` for this process."""
    forced = os.environ.get(ENV_EDITION, "").strip().lower()
    if forced in {DEVELOPER, USER}:
        return forced
    try:
        from roomscope.settings import load_settings

        if load_settings().developer_tools:
            return DEVELOPER
    except Exception:
        pass
    return USER if getattr(sys, "frozen", False) else DEVELOPER


def is_developer() -> bool:
    return edition() == DEVELOPER
