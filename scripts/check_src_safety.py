"""Refuse network imports and shell-outs under ``src/`` (ARCHITECTURE_V1.md §2, §8)."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

BANNED_MODULES = frozenset({"socket", "urllib", "http", "requests", "ssl", "subprocess", "pickle"})
BANNED_CALLS = frozenset(
    {"eval", "exec", "os.system", "os.popen", "pickle.loads", "pickle.load", "numpy.load"}
)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def check(root: Path) -> list[str]:
    bad: list[str] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            else:
                names = []
            hits = [name for name in names if name in BANNED_MODULES]
            if hits:
                bad.append(f"{path}:{node.lineno}: import {hits}")
            if isinstance(node, ast.Call):
                called = _call_name(node.func)
                bare = isinstance(node.func, ast.Name)
                if called in {"eval", "exec"} and not bare:
                    called = ""
                if called in BANNED_CALLS:
                    bad.append(f"{path}:{node.lineno}: {called}")
                for keyword in node.keywords:
                    if (
                        keyword.arg == "shell"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                    ):
                        bad.append(f"{path}:{node.lineno}: shell=True")
                    if (
                        keyword.arg == "allow_pickle"
                        and isinstance(keyword.value, ast.Constant)
                        and keyword.value.value is True
                    ):
                        bad.append(f"{path}:{node.lineno}: allow_pickle=True")
    return bad


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("src"), help="Python tree to scan")
    args = parser.parse_args(argv)
    errors = check(args.root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"src safety ok under {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
