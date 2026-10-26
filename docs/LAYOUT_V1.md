# Writing Room — Project Layout v1 (frozen)

Status: **Frozen** as of 2026-10-01. Describes the layout in use by every existing Writing Room project. Anything that reads or writes a project must keep working with it. Changes require a new layout number (`layout = 2`) and a migration in `wr_migrate.py`; see `development/DISTRIBUTION_PLAN.md` §6.

Derived from `room_rules/Directory_Structure.md`, the legacy `CLAUDE.md`, the agents, and the real files in `fixtures/legacy-v1/`. Where those disagreed, the on-disk reality was followed.

## Project root

The directory that contains `worlds/` and `stories/`. In legacy projects this is the framework directory itself (`Writing_Room/`); scripts `chdir` there and all paths are relative to it.

The portable scripts (Phase 1) find the root in this order: `--root DIR` → `WRITING_ROOM_ROOT` → nearest ancestor of the working directory containing `writing-room.toml` or both `worlds/` and `stories/` → the folder above `scripts/` if it has `worlds/` and `stories/` (legacy installs). The marker is optional for layout 1. Its format is `layout = 1` (plain `key = value` lines, `#` comments); a marker declaring a layout newer than the framework understands is refused.

## Tree

```
<root>/
├── worlds/<World Name>/
│   ├── DESCRIPTION.md              required   world overview, entry point
│   ├── HOOKS.md                    required   story hooks (status: Open | In Use (<Story>) | Archived)
│   ├── SUMMARY.md                  optional*  entity index (regenerated, never edited in place)
│   ├── WORLD_ORDER.md              optional*  chronological story order (table, see below)
│   ├── TIMELINE.md                 optional   consolidated world event log
│   ├── characters/*.md             optional   one file per character
│   ├── factions/*.md               optional
│   ├── mythology/*.md              optional
│   ├── points_of_interest/*.md     optional
│   └── snapshots/                  optional   written by create_snapshot
│       ├── manifest.md                        index of snapshots
│       └── <N>/                               position N, a positive integer
│           ├── manifest.md
│           ├── DESCRIPTION.md
│           └── characters/ factions/ mythology/ points_of_interest/   (HOOKS.md is never snapshotted)
├── stories/<Story Name>/           single story (Short Story | Novelette | Book)
│   ├── CONCEPT.md                  required   has "**World:**" and "**Status:**" fields
│   ├── OUTLINE.md                  after Outliner
│   ├── chapters/Chapter_NN.md      promoted chapters (NN zero-padded)
│   ├── current_chapter/            in-flight chapter; absent between chapters
│   │   ├── CHAPTER_PLAN.md
│   │   ├── CONTENT.md
│   │   └── current_reviews/        Reviewer-Consistency.md, Reviewer-Character.md, draft-fixer log
│   └── state/
│       ├── Timeline.md
│       ├── ACTIVE_SCHEMES.md       story-scoped registry (never merged into worlds/)
│       ├── STORY_FACTS.md          story-scoped registry (never merged into worlds/)
│       └── bible/{characters,factions,mythology,points_of_interest}/*.md   story-local world bible
├── stories/<Series Name>/          book series
│   ├── CONCEPT.md
│   ├── SERIES_OUTLINE.md
│   ├── state/Timeline.md
│   └── Book NN - <Title>/          same shape as a single story, minus CONCEPT.md
│       ├── OUTLINE.md  chapters/  current_chapter/
│       └── state/{Timeline.md, ACTIVE_SCHEMES.md, STORY_FACTS.md, bible/}
├── writing_concepts/               craft reference; a project may add its own
│   ├── styles/<Style Name>.md      project content (created by /create-style)
│   └── story_structure/  archetypes/  tropes/
├── templates/{world,story,writing_concepts}/   framework templates; a project copy overrides
└── (legacy only) .claude/  CLAUDE.md  README.md  room_rules/  scripts/   framework files living inside the project
```

\* *Optional for the scripts and for opening a project, but the skills depend on them: without `SUMMARY.md` they read every entity file, and without `WORLD_ORDER.md` there are no position lookups and no world baseline. `wr_doctor` warns (not an error) and names the fix. A world created with the `create-world` skill has both.*

## Conventions that skills and scripts depend on

- **Story → world link:** the `**World:**` field in CONCEPT.md. Never default a world from memory.
- **Story status lifecycle:** `Concept` → `In Development` → `Active` → `Complete` | `Archived`.
- **WORLD_ORDER.md:** a Markdown table `| Position | Story | Unit | In-World Date | Status | Notes |`. Story cells are wiki-links (`[[Story]]`). Units are `Full Story`, `Ch. N`, `Bk. N Ch. M`, `TBD`. `query_position` parses it.
- **Snapshot N** = world state *after* the story at position N completed; the story at N+1 loads from it.
- **State resolution order for an entity:** story `state/bible/` → `snapshots/<prev-position>/` → `worlds/<World>/`.
- **Names with spaces and apostrophes** are normal (`Freytag's Pyramid.md`, `The Tallow Ledger`); tools must not assume slugs.
- **Identity vs. operational state:** the world bible holds identity; `ACTIVE_SCHEMES.md` and `STORY_FACTS.md` hold in-flight operational facts and stay story-local.
- **Wiki-links** (`[[...]]`) appear in project files; they are data to preserve, not something to rewrite.
- **Encoding / newlines:** UTF-8; scripts emit LF.

## Script interface (frozen)

Scripts can be invoked from any directory; they locate the project root themselves. Every script also accepts `--root DIR` (added in Phase 1; purely additive). All paths in arguments are relative to the root. These flags must keep working.

| Script | Flags |
|---|---|
| `load_bible` | `--story --world [--style --structure --reviews-dir --position --no-style --no-last-chapter --no-timeline --no-schemes --no-facts --description --hooks --char --loc --faction --myth]` (`--char`, `--loc`, `--faction`, `--myth` are repeatable) |
| `load_world` | `--world [--structure --position --entity --all-entities]` |
| `query_position` | `--world --story [--format json\|text]` |
| `create_snapshot` | `--world --position --story --unit` |

Behaviour is pinned by `fixtures/golden/` (`python tools/golden.py check`).

## Known quirks (preserved, not fixed)

These were seen in real older projects; tools must tolerate them.

- A CONCEPT.md may link to hooks under `Writing_Room/worlds/<World>/…`: the path embeds the legacy root directory name, and the world named there may be an older name for the world.
- A story can have every chapter promoted and consolidated while CONCEPT.md still says `Status: Active` (`wr_next` flags this).
- Templates once contained a hard-coded `[[Writing_Room/worlds/...]]` link prefix.
- Leftovers such as `chapters/Chapter_03_original.md` can sit next to real chapters; tools must treat only `Chapter_NN.md` as chapters.
- Older CONCEPT.md files (for example one created before the Status lifecycle existed) may have no `**Status:**` field; tools must tolerate that.
- Stray artefacts (for example a `.tgz` of old chapters) can exist in project folders and must be ignored.

## Coverage in the fixtures

`examples/sample-project/` (and the content of `fixtures/legacy-v1/`) is a finished project: two complete, consolidated stories with snapshots, one of them with a story-local bible, active schemes and story facts. It also has the stray `Chapter_03_original.md` quirk. `fixtures/synthetic-v1/` covers what the sample does not: an in-flight `current_chapter/` with reviews, and a Book Series. Both are invented for this repository (see `tools/build_sample.py`).
