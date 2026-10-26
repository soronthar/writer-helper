# Loading world context

Shared by `story-ideator` and `outliner`. Paths are relative to the project root; `<World>` is `worlds/<World Name>`. Scripts are optional; every call below has a no-shell alternative.

## Overview pass (used by `story-ideator`)

If you can run commands:

```bash
python "<WR>/scripts/load_world.py" --world "worlds/<World Name>"
```

It prints, in one result: `DESCRIPTION.md`, `SUMMARY.md`, `HOOKS.md`, `WORLD_ORDER.md`, and every file in `writing_concepts/story_structure/`.

**Without a shell:** read `<World>/DESCRIPTION.md`, `SUMMARY.md`, `HOOKS.md`, `WORLD_ORDER.md`, then each `*.md` in `writing_concepts/story_structure/` (the project's copy if it has one, otherwise the framework's under `<WR>/shared/craft/story_structure/`). A missing file is reported as not found, not as an error.

## Structure pass (used by `outliner`)

If you can run commands:

```bash
python "<WR>/scripts/load_world.py" \
  --world     "worlds/<World Name>" \
  --structure "<Suggested Story Structure>"
```

It prints `DESCRIPTION.md`, `SUMMARY.md`, `story_structure/GUIDE.md`, `story_structure/Format Reference.md` and the named structure file. `HOOKS.md` and `WORLD_ORDER.md` are intentionally omitted.

**Without a shell:** read those five files. The structure name is the exact name in CONCEPT.md, plus `.md`.

## Staleness check

Applies to the `SUMMARY.md` you just read. For each entity folder under `<World>/` (`characters/`, `factions/`, `points_of_interest/`, `mythology/`), count the `.md` files and compare with the number of data rows in the matching SUMMARY.md table (a single `—` placeholder row does not count).

- **Stale or absent:** warn the user: *"SUMMARY.md appears out of date — N files found but N rows in summary. Reading all entity files directly this session. Run the `writing-assistant` skill after this session to regenerate SUMMARY.md."* Then use the fallback below.
- **Fresh:** use selective reads.

## Entity reads

**Selective (SUMMARY.md fresh)** — name only the entities the work needs. If you can run commands:

```bash
python "<WR>/scripts/load_world.py" \
  --world  "worlds/<World Name>"      \
  --entity "characters/Name"          \
  --entity "factions/Name"            \
  --entity "points_of_interest/Name"  \
  --entity "mythology/Name"
```

Repeat `--entity` per entity, using the exact filename stem (no `.md`). Several entities go in one call.

**Fallback (SUMMARY.md stale or absent):**

```bash
python "<WR>/scripts/load_world.py" --world "worlds/<World Name>" --all-entities
```

**Without a shell:** read `<World>/<type>/<Name>.md` for each named entity (types: `characters`, `factions`, `points_of_interest`, `mythology`), or every file in those folders for the fallback.
