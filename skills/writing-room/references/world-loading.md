# Loading world context

Shared by `story-ideator` and `outliner`. Paths are relative to the project root; `<World>` is `worlds/<World Name>`. Scripts are optional; every call below has a no-shell alternative. If you can run commands, use them: do not read these files one by one with your file tool. Write each command on one line (see conventions, "Loading story context"). Add `--output` when your harness may cut long output short.

## Presets (what the skills run)

- `story-ideator`: `python "<WR>/scripts/load_world.py" --for story-ideator --world "<World Name>" --output`. This loads the overview below, plus a **SUMMARY CHECK**. When SUMMARY.md is missing or stale, every entity file is added in the same call. Story structures are kept short: `GUIDE.md` and `Format Reference.md` in full, and only the Overview of each structure file; add `--structure "<Name>"` to the follow-up load for the full file of the one chosen.
- `outliner`: `python "<WR>/scripts/load_world.py" --for outliner --story "<story_path>" --entity "<type>/<Name>" --trope "<Name>" --output`. This loads the structure pass below, `WORLD_ORDER.md`, a SUMMARY CHECK, and the named entities and tropes, or every entity file when SUMMARY.md is stale. The world and the structure come from CONCEPT.md.

The SUMMARY CHECK does the staleness check below for you. When it reports a problem, pass its warning on to the user. Follow-up loads use the entity form: `--world "<World Name>"` with one `--entity`, `--trope` or `--archetype` per file, plus `--structure "<Name>"` if needed, all in one call.

## Overview pass (used by `story-ideator`)

The preset prints, in one result: `DESCRIPTION.md`, `SUMMARY.md`, `HOOKS.md`, `WORLD_ORDER.md`, `story_structure/GUIDE.md` and `Format Reference.md`, and the Overview section of every other file in `writing_concepts/story_structure/` (all eight structure files in full are about 25,000 tokens, more than a small model's context can spare). The plain form, without the SUMMARY CHECK, is `python "<WR>/scripts/load_world.py" --world "worlds/<World Name>"`; it prints every structure file in full.

**Without a shell:** read `<World>/DESCRIPTION.md`, `SUMMARY.md`, `HOOKS.md`, `WORLD_ORDER.md`, then `GUIDE.md` and `Format Reference.md` in `writing_concepts/story_structure/` (the project's copy if it has one, otherwise the framework's under `<WR>/shared/craft/story_structure/`), and of each other structure file only its Overview, the part before the second `## ` heading (about the first 15 lines). Read a structure file in full only once it is chosen. A missing file is reported as not found, not as an error.

## Structure pass (used by `outliner`)

The plain form is `python "<WR>/scripts/load_world.py" --world "worlds/<World Name>" --structure "<Suggested Story Structure>"`. It prints `DESCRIPTION.md`, `SUMMARY.md`, `story_structure/GUIDE.md`, `story_structure/Format Reference.md` and the named structure file. `HOOKS.md` is intentionally omitted; the `outliner` preset adds `WORLD_ORDER.md`.

**Without a shell:** read those five files. The structure name is the exact name in CONCEPT.md, plus `.md`.

## Staleness check

The script's SUMMARY CHECK does this for you. Without a shell, apply it to the `SUMMARY.md` you just read. For each entity folder under `<World>/` (`characters/`, `factions/`, `points_of_interest/`, `mythology/`), compare the `.md` files with the names in the matching SUMMARY.md table (a single `—` placeholder row does not count).

- **Stale or absent:** warn the user: *"SUMMARY.md appears out of date — N files found but N rows in summary. Reading all entity files directly this session. Run the `writing-assistant` skill after this session to regenerate SUMMARY.md."* Then use the fallback below.
- **Fresh:** use selective reads.

## Entity reads

**Selective (SUMMARY.md fresh):** name only the entities the work needs, all in one call, with one `--entity` per entity. Use the exact filename stem, without `.md`. Craft files go in the same call:

```bash
python "<WR>/scripts/load_world.py" --world "<World Name>" --entity "characters/<Name>" --entity "factions/<Name>" --trope "<Name>" --archetype "<Name>" --output
```

**Fallback (SUMMARY.md stale or absent):** `python "<WR>/scripts/load_world.py" --world "<World Name>" --all-entities --output`. The presets already do this for you.

**Without a shell:** read `<World>/<type>/<Name>.md` for each named entity (types: `characters`, `factions`, `points_of_interest`, `mythology`), or every file in those folders for the fallback. Read trope and archetype files from `writing_concepts/tropes/` and `writing_concepts/archetypes/`.
