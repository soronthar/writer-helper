#!/usr/bin/env python3
"""load_world.py — World bible context loader

Used by the Story Ideator and Outliner to load world bible and story craft
files in a single call. Three operating modes, selected automatically based on
the flags provided.

MODE 1 — Overview  (Story Ideator, Pass 1)

  python "Writing_Room/scripts/load_world.py" --world "worlds/<World Name>"

  Outputs: DESCRIPTION.md, SUMMARY.md, HOOKS.md, WORLD_ORDER.md,
           ALL writing_concepts/story_structure/ files.

MODE 2 — Structure  (Outliner, Pass 1)

  python "Writing_Room/scripts/load_world.py" \\
    --world "worlds/<World Name>" --structure "Three-Act Structure"

  Outputs: DESCRIPTION.md, SUMMARY.md, story_structure/GUIDE.md,
           story_structure/Format Reference.md, the named structure file.
  Skips:   HOOKS.md, WORLD_ORDER.md, all other structure files.
  --structure is the filename stem (no .md extension).

MODE 3 — Entities  (Ideator & Outliner, Pass 2)

  Pass 2a — selective:
    python "Writing_Room/scripts/load_world.py" --world "worlds/<World Name>" \\
      --entity "characters/Mara Quill" --entity "factions/Harbor Guild"

  Pass 2b — staleness fallback (SUMMARY.md absent or stale):
    python "Writing_Room/scripts/load_world.py" --world "worlds/<World Name>" --all-entities

  --entity accepts "type/Name" where type is one of:
    characters | factions | points_of_interest | mythology
  The name is the filename stem (no .md extension).
  When --entity or --all-entities is given, ONLY entity files are output.

Notes
  - Run from anywhere; paths are relative to Writing_Room/ (the script cd's there).
  - Missing files emit a ⚠ warning line rather than crashing.
  - --position <N>: entity reads prefer worlds/<World>/snapshots/<N>/ over the
    current worlds/<World>/ directory (historical world state).
"""

from pathlib import Path

from common import DIV, md_files, make_parser, out, print_file, resolve_snapshot, setup, stem

ENTITY_DIRS = ("characters", "factions", "points_of_interest", "mythology")


def load_all_entities(world, snapshot_dir, position):
    for d in ENTITY_DIRS:
        seen = set()

        # Snapshot files first, then world files not already covered.
        snap_files = md_files(f"{snapshot_dir}/{d}") if snapshot_dir else []
        for f in snap_files:
            seen.add(stem(f))
            print_file(f"{d}/{stem(f)}  [snapshot pos {position}]", f)

        world_files = md_files(f"{world}/{d}")
        for f in world_files:
            if stem(f) not in seen:
                print_file(f"{d}/{stem(f)}  [world bible]", f)

        if not seen and not world_files:
            out()
            out(DIV)
            out(f"DIRECTORY: {world}/{d}/  (empty or not found)")
            out(DIV)


def load_entities(world, entities, snapshot_dir, position):
    for entry in entities:
        snap = f"{snapshot_dir}/{entry}.md" if snapshot_dir else ""
        if snap and Path(snap).is_file():
            print_file(f"{entry}  [snapshot pos {position}]", snap)
        else:
            print_file(entry, f"{world}/{entry}.md")


def load_structure(world, structure):
    print_file("DESCRIPTION.md", f"{world}/DESCRIPTION.md")
    print_file("SUMMARY.md", f"{world}/SUMMARY.md")
    print_file("story_structure/GUIDE.md", "writing_concepts/story_structure/GUIDE.md")
    print_file("story_structure/Format Reference.md", "writing_concepts/story_structure/Format Reference.md")
    print_file(f"story_structure/{structure}", f"writing_concepts/story_structure/{structure}.md")


def load_overview(world):
    print_file("DESCRIPTION.md", f"{world}/DESCRIPTION.md")
    print_file("SUMMARY.md", f"{world}/SUMMARY.md")
    print_file("HOOKS.md", f"{world}/HOOKS.md")
    print_file("WORLD_ORDER.md", f"{world}/WORLD_ORDER.md")

    structure_files = md_files("writing_concepts/story_structure")
    if not structure_files:
        out()
        out(DIV)
        out("STORY STRUCTURE: ⚠ No files found in writing_concepts/story_structure/")
        out(DIV)
    else:
        for f in structure_files:
            print_file(f"story_structure/{Path(f).name}", f)


def main():
    setup()
    parser = make_parser("World bible context loader")
    parser.add_argument("--world", required=True)
    parser.add_argument("--structure", default="")
    parser.add_argument("--position", default="")
    parser.add_argument("--entity", action="append", default=[])
    parser.add_argument("--all-entities", action="store_true")
    args = parser.parse_args()

    snapshot_dir = resolve_snapshot(args.world, args.position)

    if args.entity or args.all_entities:
        if args.all_entities:
            load_all_entities(args.world, snapshot_dir, args.position)
        else:
            load_entities(args.world, args.entity, snapshot_dir, args.position)
    elif args.structure:
        load_structure(args.world, args.structure)
    else:
        load_overview(args.world)


if __name__ == "__main__":
    main()
