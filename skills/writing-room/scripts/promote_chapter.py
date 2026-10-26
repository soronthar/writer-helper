#!/usr/bin/env python3
"""promote_chapter.py — Promote current_chapter/CONTENT.md to chapters/Chapter_NN.md

Usage:
  python "<WR>/scripts/promote_chapter.py" --story "stories/<Story>" --chapter N \\
    [--overwrite] [--dry-run]

Copies <story>/current_chapter/CONTENT.md to <story>/chapters/Chapter_NN.md (NN zero-padded),
verifies the copy is byte-identical, and only then deletes CONTENT.md, CHAPTER_PLAN.md and
the current_reviews/ folder from current_chapter/. Nothing else is ever deleted;
current_chapter/ itself is kept, empty.

Refuses to overwrite an existing chapter file unless --overwrite is given. The calling
skill is responsible for getting the user's confirmation before running this.

Paths are relative to the project root (found via --root, WRITING_ROOM_ROOT,
a writing-room.toml marker, or the legacy worlds/ + stories/ layout).
"""

import shutil
import sys
from pathlib import Path

from common import make_parser, setup


def main():
    setup()
    p = make_parser("Promote the current chapter draft to chapters/")
    p.add_argument("--story", required=True, help="story (or book) folder, relative to the project root")
    p.add_argument("--chapter", required=True, type=int, help="chapter number")
    p.add_argument("--overwrite", action="store_true", help="replace an existing chapter file")
    p.add_argument("--dry-run", action="store_true", help="print the plan and change nothing")
    a = p.parse_args()

    if a.chapter < 1:
        print("Error: --chapter must be a positive integer.", file=sys.stderr)
        return 2
    story = Path(a.story)
    cur = story / "current_chapter"
    content = cur / "CONTENT.md"
    dest = story / "chapters" / f"Chapter_{a.chapter:02d}.md"

    if not content.is_file():
        print(f"Error: {content} not found. Run the draft-writer skill first.", file=sys.stderr)
        return 1
    if dest.exists() and not a.overwrite:
        print(f"Error: {dest} already exists. Re-run with --overwrite to replace it.", file=sys.stderr)
        return 1

    to_delete = [x for x in (content, cur / "CHAPTER_PLAN.md", cur / "current_reviews") if x.exists()]
    reviews = cur / "current_reviews"
    review_count = len([f for f in reviews.rglob("*") if f.is_file()]) if reviews.is_dir() else 0

    print(f"Copy:   {content.as_posix()}\n    ->  {dest.as_posix()}")
    for x in to_delete:
        print(f"Delete: {x.as_posix()}" + (f"  ({review_count} file(s))" if x == reviews else ""))
    if a.dry_run:
        print("\nDry run: nothing changed.")
        return 0

    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(content, dest)
    if dest.read_bytes() != content.read_bytes():
        print(f"Error: copy to {dest} does not match the source; nothing was deleted.", file=sys.stderr)
        return 1
    for x in to_delete:
        if x.is_dir():
            shutil.rmtree(x)
        else:
            x.unlink()
    print(f"\nPromoted chapter {a.chapter} to {dest.as_posix()}. current_chapter/ is ready for the next chapter.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
