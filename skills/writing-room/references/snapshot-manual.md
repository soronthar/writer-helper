# Creating a snapshot without a shell

Use this only when you cannot run `create_snapshot.py`. The result must be identical in shape to what the script writes.

1. Let `<N>` be the story's position in WORLD_ORDER (a positive integer). Target folder: `worlds/<World>/snapshots/<N>/`. If it already exists, tell the user it is being overwritten and delete its contents first.
2. Copy every `.md` file directly inside `worlds/<World>/characters/`, `factions/`, `points_of_interest/` and `mythology/` into the same-named subfolders of the target (create all four, even if empty). Copy `worlds/<World>/DESCRIPTION.md` to the target. Do **not** copy `HOOKS.md`.
3. Write `<target>/manifest.md`:

```
# Snapshot Manifest — Position <N>

> **Created:** <today, YYYY-MM-DD>
> **Captures world state AFTER this story completed.**
> Stories at position <N+1> and beyond should use this as their baseline.

## Story
- **Story:** [[<Story Name>]]
- **Unit:** <unit>
- **Position:** <N>

## Contents
- **Characters:** <count> file(s)
- **Factions:** <count> file(s)
- **Locations (Points of Interest):** <count> file(s)
- **Mythology:** <count> file(s)
- **Total entities:** <sum>

## Notes

This snapshot was created automatically by the Story Analyzer after chapter completion.
World consolidation (merging state/bible/ into worlds/) should occur before this snapshot
is taken so that the snapshot reflects all story-driven world changes.

If consolidation has not yet occurred, this snapshot reflects the pre-story world state only.
Invoke the World Archivist → Consolidate, then re-run create_snapshot.py to update.
```

4. Update `worlds/<World>/snapshots/manifest.md`, the index. If it does not exist, create it with this header, then the row:

```
# World Snapshots — Index

> Maintained by create_snapshot.py. Do not edit manually.
> Each entry records the world state AFTER the story at that position completed.
> The story at position N+1 uses snapshot N as its world baseline.

| Position | Story | Unit | Date Created | Notes |
|----------|-------|------|--------------|-------|
```

   The row is `| <N> | [[<Story Name>]] | <unit> | <today> | Auto-created by Story Analyzer |`. Replace an existing row for the same position; otherwise insert the row so rows stay in position order.
