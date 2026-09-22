from __future__ import annotations

import re
from pathlib import Path

_SHA = re.compile(r"^[0-9a-f]{40}$")


def test_github_actions_are_pinned_by_sha() -> None:
    for path in Path(".github/workflows").glob("*.yml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped.startswith("uses:"):
                continue
            ref = stripped.split("uses:", 1)[1].strip().split()[0]
            if ref.startswith("./"):
                continue
            sha = ref.rsplit("@", 1)[-1]
            assert _SHA.match(sha), f"{path}: unpinned action {stripped}"
