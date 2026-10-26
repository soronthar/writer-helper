#!/usr/bin/env python3
"""wr_migrate.py — Bring an existing (legacy layout v1) project under the portable framework

Usage:
  python "<WR>/scripts/wr_migrate.py" [--root DIR] [--apply] [--force] [--retire-legacy]

Dry run by default: prints what would change and changes nothing.

With --apply it adds the writing-room.toml marker to the project root. That alone is a complete
migration: no worlds, stories, styles or templates are moved, renamed, or rewritten.

Optionally, --retire-legacy also moves the old framework files that live inside a legacy project
and are now provided by the installed skills, so an agent does not see two generations of the same
agents and commands:

  .claude/agents  .claude/commands  CLAUDE.md  README.md  room_rules/  scripts/

They are MOVED (never deleted) to .writing-room-legacy/ inside the project, keeping their relative
paths, so undoing it is moving them back. Your worlds, stories, writing_concepts/ (styles, tropes,
archetypes) and templates/ are never touched, and neither is .claude/settings*.json. After retiring,
AGENTS.md and CLAUDE.md (which imports it) are added if absent. Install the new skills first
(wr_install.py), because the old scripts folder is among what is retired.

Safe to re-run: steps already done are reported and skipped. If the project is inside a git work
tree with uncommitted changes, --apply refuses unless --force is given, so the migration is never
mixed into unrelated work.
"""

import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (FRAMEWORK_DIR, MARKER, SUPPORTED_LAYOUT, ProjectNotFound, find_root,  # noqa: E402
                    is_legacy_root, make_parser, read_marker)
from wr_init import MARKER_TEXT  # noqa: E402

LEGACY_FRAMEWORK = (".claude", "CLAUDE.md", "README.md", "room_rules", "scripts", "templates")
RETIRE = (".claude/agents", ".claude/commands", "CLAUDE.md", "README.md", "room_rules", "scripts")
ARCHIVE = ".writing-room-legacy"
INSTALL_DIRS = (".claude/skills", ".agents/skills", ".opencode/skills", ".hermes/skills")


def git_dirty(root):
    """True/False if root is in a git work tree; None if git is unavailable or not a repo."""
    try:
        inside = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True)
        if inside.returncode != 0:
            return None
        # The folders wr_install puts skills into do not count: installing first is the documented order.
        excludes = [f":(exclude){d}" for d in INSTALL_DIRS]
        status = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", ".", *excludes],
                                capture_output=True, text=True)
        return bool(status.stdout.strip())
    except OSError:
        return None


def plan_retire(root):
    """Return (to_move, blocked): relative paths that exist, and those whose archive target already exists."""
    to_move, blocked = [], []
    for rel in RETIRE:
        if not (root / rel).exists():
            continue
        (blocked if (root / ARCHIVE / rel).exists() else to_move).append(rel)
    return to_move, blocked


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    p = make_parser("Migrate a legacy Writing Room project")
    p.add_argument("--apply", action="store_true", help="actually make the changes (default: dry run)")
    p.add_argument("--force", action="store_true", help="proceed even if the git work tree is dirty")
    p.add_argument("--retire-legacy", action="store_true",
                   help="also move the old framework files inside the project to .writing-room-legacy/")
    a = p.parse_args()

    try:
        root, how = find_root(explicit=a.root)
    except ProjectNotFound as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    print(f"Project root: {root}  (found via {how})")

    marker = root / MARKER
    need_marker = not marker.is_file()
    if not need_marker:
        layout = read_marker(marker).get("layout")
        if layout != SUPPORTED_LAYOUT:
            print(f"{MARKER} declares layout {layout!r}; this framework understands layout "
                  f"{SUPPORTED_LAYOUT}. No migration path is available.", file=sys.stderr)
            return 1
        print(f"Marker: {MARKER} already declares layout {layout}.")
    elif not is_legacy_root(root):
        print("Not a layout-v1 project (needs worlds/ and stories/). Use wr_init.py for a new project.",
              file=sys.stderr)
        return 1

    to_move, blocked = plan_retire(root) if a.retire_legacy else ([], [])
    word = "Would" if not a.apply else "Will"
    if need_marker:
        print(f"{word} write {MARKER} (layout = {SUPPORTED_LAYOUT}).")
    for rel in to_move:
        print(f"{word} move {rel} -> {ARCHIVE}/{rel}")
    for rel in blocked:
        print(f"Skipping {rel}: {ARCHIVE}/{rel} already exists.")
    guidance = [n for n in ("AGENTS.md", "CLAUDE.md")
                if a.retire_legacy and (not (root / n).exists() or n in to_move)]
    for n in guidance:
        print(f"{word} add {n}" + (" (the old one is archived)" if n in to_move else ""))
    if not a.retire_legacy:
        left = [n for n in LEGACY_FRAMEWORK if (root / n).exists()]
        if left:
            print("Left untouched (old framework files inside the project): " + ", ".join(left))
            print("  Use --retire-legacy once the new skills are installed to archive the agents, commands and scripts.")
    print("No worlds, stories, styles or templates are modified.")

    if not (need_marker or to_move):
        print("\nNothing to do.")
        return 0
    if not a.apply:
        print("\nDry run. Re-run with --apply to make the changes.")
        return 0

    dirty = git_dirty(root)
    if dirty and not a.force:
        print("\nThe git work tree has uncommitted changes. Commit or stash them first, or pass --force.",
              file=sys.stderr)
        return 1
    if dirty is None:
        print("Note: not a git work tree, so there is no history to roll back; "
              + ("retired files are kept in " + ARCHIVE + "/." if to_move else "the only change is the new marker file."))

    if need_marker:
        marker.write_text(MARKER_TEXT, encoding="utf-8", newline="\n")
    for rel in to_move:
        dest = root / ARCHIVE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root / rel), str(dest))
    for n in guidance:
        src = FRAMEWORK_DIR / "shared" / "project" / n
        if src.is_file() and not (root / n).exists():
            shutil.copy2(src, root / n)

    print("\nDone." + (f" Added {marker.name}." if need_marker else ""))
    if to_move:
        print(f"Moved {len(to_move)} item(s) to {ARCHIVE}/. To undo, move them back to their original places.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
