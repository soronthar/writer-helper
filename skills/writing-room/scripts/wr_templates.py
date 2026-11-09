#!/usr/bin/env python3
"""wr_templates.py — Find project templates and craft files that hide the framework's current ones

Usage:
  python "<WR>/scripts/wr_templates.py" [--root DIR] [--retire]

A project's own templates/ and writing_concepts/ (story_structure, archetypes, tropes) win over
the framework's copies, so that an author's edits are used. A copy nobody edited wins too: an
old project that carried the framework's templates over keeps using them after the framework
improves them. This lists every such file in one of three groups:

  older    an unchanged copy of an older framework version: it hides the current one
  same     identical to the framework's current copy: harmless now, but hides later updates
  edited   changed by the author, or the project's own file: always kept

With --retire, the older and same files are MOVED (never deleted) to .writing-room-legacy/,
keeping their relative paths, so the framework's copies are used; undoing it is moving them
back. Edited files are never touched. Writing styles (writing_concepts/styles/) are the
author's own and are not looked at.

The fingerprints of every shipped version are in <WR>/shared/template_history.json.
"""

import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import _FALLBACKS as LOGICAL  # noqa: E402
from common import FRAMEWORK_DIR, ProjectNotFound, find_root, make_parser  # noqa: E402

HISTORY_FILE = FRAMEWORK_DIR / "shared" / "template_history.json"
ARCHIVE = ".writing-room-legacy"


def fingerprint(data):
    """Short hash of a file's bytes, with CRLF read as LF so a checkout's line endings do not matter."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()[:16]


def classify(root, framework=FRAMEWORK_DIR):
    """{"older": [...], "same": [...], "edited": [...]}: project-relative paths of the project's own
    template and craft files, by how they relate to the shipped versions of `framework` (a writing-room
    skill folder; by default this one)."""
    root, framework = Path(root), Path(framework)
    try:
        history = json.loads((framework / "shared" / HISTORY_FILE.name).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        history = {}
    groups = {"older": [], "same": [], "edited": []}
    for logical, shared in LOGICAL:
        d = root / logical
        if not d.is_dir():
            continue
        for f in sorted(d.rglob("*.md")):
            rel = f"{logical}/{f.relative_to(d).as_posix()}"
            mine = fingerprint(f.read_bytes())
            current = framework / "shared" / shared / f.relative_to(d)
            if current.is_file() and fingerprint(current.read_bytes()) == mine:
                groups["same"].append(rel)
            elif current.is_file() and mine in history.get(rel, ()):
                groups["older"].append(rel)
            else:
                groups["edited"].append(rel)
    return groups


def retire(root, paths):
    """Move paths to the archive; return (moved, skipped because the archive already has them)."""
    root = Path(root)
    moved, skipped = [], []
    for rel in paths:
        dest = root / ARCHIVE / rel
        if dest.exists():
            skipped.append(rel)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(root / rel), str(dest))
        moved.append(rel)
        parent = (root / rel).parent
        while parent != root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    return moved, skipped


def summary(groups, limit=6):
    """One-line warnings for wr_doctor, or []."""
    lines = []

    def names(paths):
        return ", ".join(paths[:limit]) + (f" and {len(paths) - limit} more" if len(paths) > limit else "")

    if groups["older"]:
        lines.append(f"{len(groups['older'])} project template/craft file(s) are unchanged copies of an older "
                     f"framework version and hide the current one ({names(groups['older'])}); "
                     "`wr_templates.py --retire` moves them aside (reversible)")
    if groups["same"]:
        lines.append(f"{len(groups['same'])} project template/craft file(s) are identical to the framework's and "
                     f"will hide its later updates ({names(groups['same'])}); "
                     "`wr_templates.py --retire` moves them aside (reversible)")
    return lines


def main():
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", newline="\n")
    p = make_parser("Find project templates and craft files that hide the framework's current ones")
    p.add_argument("--retire", action="store_true", help=f"move the older and same files to {ARCHIVE}/")
    a = p.parse_args()
    try:
        root, _ = find_root(explicit=a.root)
    except ProjectNotFound as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    groups = classify(root)
    labels = {"older": "Older framework version (hides the current one)",
              "same": "Same as the framework's current copy",
              "edited": "Edited or your own (kept)"}
    for kind, label in labels.items():
        if groups[kind]:
            print(f"{label}: {len(groups[kind])}")
            for rel in groups[kind]:
                print(f"  {rel}")
    if not any(groups.values()):
        print("The project has no templates or craft files of its own; the framework's are used.")
    stale = groups["older"] + groups["same"]
    if not a.retire:
        if stale:
            print(f"\nRe-run with --retire to move the {len(stale)} older and same file(s) to {ARCHIVE}/.")
        return 0
    moved, skipped = retire(root, stale)
    if moved:
        print(f"\nMoved {len(moved)} file(s) to {ARCHIVE}/. To undo, move them back to their original places.")
    for rel in skipped:
        print(f"Skipped {rel}: {ARCHIVE}/{rel} already exists.")
    if not stale:
        print("\nNothing to retire.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
