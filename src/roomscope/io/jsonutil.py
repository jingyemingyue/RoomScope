"""JSON reads with a size cap so untrusted session files cannot fill memory."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from roomscope.errors import SessionError

#: Refused before ``json.loads``. 32 MiB is well above a result with curves.
MAX_JSON_BYTES = 32 * 1024 * 1024


def read_json_object(path: Path, *, kind: str = "JSON") -> dict[str, Any]:
    """Read a JSON object, refusing oversized or non-object files."""
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise SessionError(f"cannot read {path}: {exc}") from exc
    if size > MAX_JSON_BYTES:
        raise SessionError(
            f"{path.name} is {size} bytes; {kind} files larger than "
            f"{MAX_JSON_BYTES} bytes are refused"
        )
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise SessionError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SessionError(f"{path} is not a JSON object")
    return data
