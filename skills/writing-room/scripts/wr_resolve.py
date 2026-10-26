#!/usr/bin/env python3
"""wr_resolve.py — Print the real path of a template or craft file

Usage:
  python scripts/wr_resolve.py <logical path> [--root DIR]

Examples:
  python scripts/wr_resolve.py templates/world/character.md
  python scripts/wr_resolve.py "writing_concepts/story_structure/Freytag's Pyramid.md"

A project's own copy wins; otherwise the framework's shared/ copy is used.
Prints the absolute path and exits 0, or exits 1 if neither exists. Works with
or without a project (without one, only the framework copy is considered).
This lets skills find framework files without knowing where the framework is installed.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ProjectNotFound, find_root, lookup, make_parser  # noqa: E402


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    p = make_parser("Resolve a template or craft file")
    p.add_argument("path")
    a = p.parse_args()
    try:
        root, _ = find_root(explicit=a.root)
    except ProjectNotFound:
        root = None
    if root is not None:
        os.chdir(root)
    found = Path(lookup(a.path))
    if not found.exists():
        print(f"Not found: {a.path}", file=sys.stderr)
        return 1
    print(found.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
