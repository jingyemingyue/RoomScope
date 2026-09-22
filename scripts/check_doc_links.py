"""Check relative Markdown links under docs/ (ARCHITECTURE_V1.md §7.1)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _targets(markdown: str) -> list[str]:
    found: list[str] = []
    for match in LINK.finditer(markdown):
        raw = match.group(1).strip()
        if raw.startswith("<") and raw.endswith(">"):
            raw = raw[1:-1]
        href = raw.split()[0] if raw else ""
        href = href.split("#", 1)[0]
        if not href:
            continue
        if href.startswith(("http://", "https://", "mailto:", "ftp://")):
            continue
        found.append(href)
    return found


def check(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for href in _targets(text):
            target = (path.parent / href).resolve()
            try:
                target.relative_to(root.resolve().parent)
            except ValueError:
                errors.append(f"{path}: link escapes the repository: {href}")
                continue
            if not target.exists():
                errors.append(f"{path}: broken link {href}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("docs"), help="docs directory")
    args = parser.parse_args(argv)
    errors = check(args.root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"doc links ok under {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
