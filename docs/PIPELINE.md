# The skills and the pipeline

Fourteen skills. Paths are relative to your project root. "Modes" are what the skill asks you at the start. Details of each file's format are in [FILE_FORMATS.md](FILE_FORMATS.md).

## The order of work

1. **Once per world:** `create-world`, then `create-style`, then grow the world with `writing-assistant` as you like.
2. **Once per story:** `story-ideator` (concept) → `outliner` (chapter map).
3. **Once per chapter:** `planner` → `draft-writer` → `reviewer` → `draft-fixer` → `story-analyzer` → `promote-chapter`.
4. **When a story is finished:** `world-archivist` consolidates it into the world.

At any point `writing-room` (the router) tells you where you are, and `story-status` shows a dashboard. Skills that need to know which story or chapter you mean will ask, or work it out when only one qualifies.

## Reference

| Skill | Use it when | Modes | Reads | Writes |
|---|---|---|---|---|
| `writing-room` | You start a session, ask "where am I?", or say "continue" | | the whole project (read-only) | `CONCEPT.md` Status when a story finishes (after you confirm) |
| `create-world` | Starting a new world | guided interview, any question can be skipped | templates | `worlds/<W>/DESCRIPTION.md`, `HOOKS.md`, `WORLD_ORDER.md`, `SUMMARY.md`, optional starter characters, factions, places, myths |
| `create-style` | You want to define how your prose should sound | guided interview (10 sections) | template | `writing_concepts/styles/<Style>.md` |
| `writing-assistant` | Adding or changing characters, factions, places, myths, hooks; checking world consistency; applying an archetype or trope | | the world, `writing_concepts/archetypes` and `tropes` | entity files, `HOOKS.md`, `DESCRIPTION.md`, `SUMMARY.md` |
| `story-ideator` | You need a story idea or concept from your world | autonomous, collaborative | the world, hooks, story structures | `stories/<S>/CONCEPT.md`, skeleton `state/` files, a row in `WORLD_ORDER.md`, hook statuses |
| `outliner` | A concept exists and needs a chapter map | autonomous, collaborative | concept, world, story structure | `OUTLINE.md` (series: `SERIES_OUTLINE.md` and the first book folder), concept Status → `In Development` |
| `planner` | Next chapter is not planned | autonomous, collaborative; `preview: true` | outline, structure, style, world, schemes, facts, timeline | `current_chapter/CHAPTER_PLAN.md`; concept Status → `Active` at chapter 1 |
| `draft-writer` | A plan exists and you want the prose | autonomous, scene-by-scene; `preview: true` | plan, style, world, schemes, facts, previous chapter | `current_chapter/CONTENT.md` |
| `reviewer` | A draft exists | one session, two passes | draft, plan, previous chapter, world, schemes, facts | `current_reviews/Reviewer-Consistency.md`, `Reviewer-Character.md` |
| `draft-fixer` | Review reports exist | autonomous, preview all, interactive | reports, draft, style, schemes, facts | the draft (minimal exact-text fixes), `current_reviews/Draft-Fixer-Log.md` |
| `story-analyzer` | The draft is fixed | preview all, autonomous | draft, outline, world, schemes, facts | `state/bible/`, `state/Timeline.md`, `state/ACTIVE_SCHEMES.md`, `state/STORY_FACTS.md`, `OUTLINE.md` annotations, `WORLD_ORDER.md`, new hooks (after your approval), a world snapshot when the story completes |
| `promote-chapter` | The chapter is analyzed | confirms first | `current_chapter/` | `chapters/Chapter_NN.md`; clears `current_chapter/` |
| `story-status` | You want the full picture | read-only | everything about one story | nothing |
| `world-archivist` | The index is stale; story order needs changing; a story is finished | choose an operation | the world, stories | `SUMMARY.md`, `WORLD_ORDER.md`, `TIMELINE.md`, snapshots, merged entity files (consolidate) |

## Guarantees the skills try to keep

- **The world bible stays clean during a story.** While a story is in progress only its own `state/` changes; the world changes when you consolidate (plus hooks, and edits you ask the `writing-assistant` for).
- **Review before recording.** The reviewer checks the draft against the world as it was *before* the chapter; the story-analyzer records what changed *after* the fixes.
- **Plans are contracts.** The draft-writer follows the plan's opening and closing beats; a character who appears in the prose but not in the plan is reported as a plan violation.
- **Nothing silent.** Fixes that cannot be placed exactly are skipped and reported in three places; deletions are shown before they happen; "verify with author" items always stop for you.

## Helper scripts

Skills use these when the agent can run commands (all in `skills/writing-room/scripts`, installed with the skills). You can run them yourself too.

| Script | Does |
|---|---|
| `wr_init.py` | Create a project |
| `wr_migrate.py` | Add the project marker to an older project; `--retire-legacy` also moves the old agents, commands and scripts aside (dry run by default; see [MIGRATING.md](MIGRATING.md)) |
| `wr_doctor.py` | Diagnose the project and the installation: layout, a missing or stale `SUMMARY.md`, a missing `WORLD_ORDER.md` or story missing from it, completed stories without a snapshot, promoted chapters without a Timeline entry, leftover old framework files |
| `wr_next.py` | Say which skill comes next, per story |
| `wr_install.py` | Install the skills for an agent |
| `wr_update.py` | Update installed skills from a new build: replace, add, remove, save your edits, show the changelog ([INSTALL.md](INSTALL.md#updating)) |
| `wr_resolve.py` | Find a template or craft file (your copy first, then the framework's) |
| `load_bible.py`, `load_world.py`, `query_position.py` | Load only the context a skill needs |
| `create_snapshot.py`, `promote_chapter.py` | Snapshot the world; promote a chapter (copy, verify, then delete) |
