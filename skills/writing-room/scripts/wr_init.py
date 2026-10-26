#!/usr/bin/env python3
"""wr_init.py — Create a new Writing Room project

Usage:
  python scripts/wr_init.py [DIR] [--dry-run] [--force] [--no-guidance]

Creates in DIR (default: the current directory):
  writing-room.toml            project marker (layout = 1)
  worlds/                      world bibles
  stories/                     stories and series
  writing_concepts/styles/     your prose styles (a starter style is copied in if none exist)
  Stories.base                 Obsidian Bases view of the stories grouped by world (only if absent)
  AGENTS.md, CLAUDE.md         short instructions for coding agents that read them (only if absent;
                               skip with --no-guidance). CLAUDE.md just imports AGENTS.md.

Never overwrites anything. An existing layout-v1 project (worlds/ + stories/) is
not re-initialised; use wr_migrate.py to add the marker to it. Refuses to
create a project inside another project unless --force is given.
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import FRAMEWORK_DIR, MARKER, SUPPORTED_LAYOUT, find_root, is_legacy_root, make_parser, ProjectNotFound  # noqa: E402

MARKER_TEXT = f"""# Writing Room project marker. Do not delete: scripts and skills find the project by it.
layout = {SUPPORTED_LAYOUT}
"""


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    p = make_parser("Create a new Writing Room project")
    p.add_argument("dir", nargs="?", default=".")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--force", action="store_true", help="allow creating a project inside another project")
    p.add_argument("--no-guidance", action="store_true", help="do not add AGENTS.md and CLAUDE.md")
    a = p.parse_args()

    target = Path(a.dir).resolve()
    if (target / MARKER).is_file():
        print(f"{target} is already a Writing Room project ({MARKER} present). Nothing to do.")
        return 0
    if is_legacy_root(target):
        print(f"{target} already has worlds/ and stories/ (layout v1). Use wr_migrate.py to add the marker.",
              file=sys.stderr)
        return 1
    if not a.force:
        try:
            outer, _ = find_root(start=target.parent if not target.exists() else target)
        except ProjectNotFound:
            outer = None
        if outer is not None and outer != FRAMEWORK_DIR:
            print(f"{target} is inside an existing project ({outer}). Use --force to create a nested one.",
                  file=sys.stderr)
            return 1

    actions = []
    for rel in ("worlds", "stories", "writing_concepts/styles"):
        if not (target / rel).is_dir():
            actions.append(("mkdir", rel))
    styles = target / "writing_concepts" / "styles"
    starter = FRAMEWORK_DIR / "shared" / "craft" / "styles"
    if not (styles.is_dir() and any(styles.glob("*.md"))) and starter.is_dir():
        for f in sorted(starter.glob("*.md")):
            actions.append(("copy", f"writing_concepts/styles/{f.name}", f))
    if not a.no_guidance:
        for name in ("AGENTS.md", "CLAUDE.md"):
            src = FRAMEWORK_DIR / "shared" / "project" / name
            if src.is_file() and not (target / name).exists():
                actions.append(("copy", name, src))
    base = FRAMEWORK_DIR / "shared" / "project" / "Stories.base"
    if base.is_file() and not (target / "Stories.base").exists():
        actions.append(("copy", "Stories.base", base))   # Obsidian Bases view: stories grouped by world
    actions.append(("write", MARKER))

    for act in actions:
        print(f"{'would ' if a.dry_run else ''}{act[0]:5} {act[1]}")
        if a.dry_run:
            continue
        if act[0] == "mkdir":
            (target / act[1]).mkdir(parents=True, exist_ok=True)
        elif act[0] == "copy":
            dst = target / act[1]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copy2(act[2], dst)
        else:
            (target / MARKER).write_bytes((MARKER_TEXT).encode("utf-8"))
    if not a.dry_run:
        print(f"\nProject created at {target}. Next: build a world (the create-world skill), then a story.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
