# File formats

The files the skills share. Everything is Markdown. The skills and scripts read only a few fields by pattern (marked **parsed** below); the rest is for you and the agent to read. Templates for each file are in `skills/writing-room/shared/templates/` (a project can override any template by placing its own copy in `templates/` at the project root). The full folder layout is in [LAYOUT_V1.md](LAYOUT_V1.md).

## Project

- **`writing-room.toml`** — marks the project root. One line that matters: `layout = 1`. Optional; a folder with both `worlds/` and `stories/` is also recognised.
- **Names** with spaces and apostrophes are normal. `[[Wiki links]]` are kept exactly as written; use `[[Name]]` with no folder path.

## World (`worlds/<World>/`)

| File | What it is | Parsed |
|---|---|---|
| `DESCRIPTION.md` | World overview: geography, history, population, economy, magic, beliefs, current state | |
| `HOOKS.md` | Story seeds. Each has Source, Status (`Open`, `In Use (<Story>)`, `Archived`), Hook, Related | Status |
| `SUMMARY.md` | Index of every entity, rebuilt from scratch (never edited by hand). Skills read it instead of every entity file; the doctor warns if it is missing or lists different names than the entity files | table rows |
| `WORLD_ORDER.md` | Chronological order of stories. Table `\| Position \| Story \| Unit \| In-World Date \| Status \| Notes \|`; Unit is `Full Story`, `Ch. N`, `Bk. N Ch. M` or `TBD`; Status is `Not Started`, `In Progress`, `Complete` | **yes** (`query_position.py`) |
| `TIMELINE.md` | Events of finished stories, grouped under `### [[Story]] (Position N)`; a story counts as consolidated when its heading is here | heading |
| `characters/`, `factions/`, `points_of_interest/`, `mythology/` | One file per element, named after its `# Heading` | |
| `snapshots/<N>/` | The world after the story at position N completed (entities, `DESCRIPTION.md`, `manifest.md`; never `HOOKS.md`). The story at N+1 starts from snapshot N | folder names |

A character file's `## Notes` collects **knowledge lines**: `**Knows (as of <Story> — Chapter N):** <fact>`. The reviewer uses them to check that characters act only on what they know.

## Story (`stories/<Story>/`; a Book Series nests `Book NN - <Title>/` folders)

| File | What it is | Parsed |
|---|---|---|
| `CONCEPT.md` | The idea. `**World:**` names the world; `**Status:**` is `Concept`, `In Development`, `Active`, `Complete` or `Archived` | **World, Status**. Optional frontmatter `world:` and `status:` mirrors them for Obsidian Bases; the body lines win, and `wr_doctor` warns on a mismatch |
| `OUTLINE.md` | Chapter map, subplot threads. `**Total chapters:**`, `**World Order Position:**`, `**Story before/after:**`. The story-analyzer later appends `#### Payoff Annotations` under future chapters; the outliner's own text is never changed | **Total chapters** |
| `current_chapter/CHAPTER_PLAN.md` | Scene-by-scene plan. `**Chapter:** N of M`; headings such as `Notes for the Draft Writer` are part of the format | **Chapter** |
| `current_chapter/CONTENT.md` | The draft | existence |
| `current_chapter/current_reviews/` | `Reviewer-Consistency.md`, `Reviewer-Character.md`, `Draft-Fixer-Log.md` | existence |
| `chapters/Chapter_NN.md` | Promoted chapters; anything else in the folder is ignored | name pattern |
| `state/Timeline.md` | One entry per analyzed chapter: `- **[Chapter N — Title]** <date> — <what happened>` | **entry per chapter** |
| `state/ACTIVE_SCHEMES.md` | Ledger of in-flight lies, promises and concealments: ID `S1…`, owner, targets, nature, status (`Active`, `Complicated`, `Exposed`, `Resolved`), origin, last touched, plus detail blocks and a Resolution Log. Never merged into the world | |
| `state/STORY_FACTS.md` | Ledger of plot-critical facts that cross-cut entities: ID `F1…`, category, fact, status (`Current`, `Superseded`), plus a Superseded Log. Never merged into the world | |
| `state/bible/<type>/` | The story's own working copy of world entities; read before `worlds/` | |

## Where an entity is read from

For a character, faction, place or myth, skills take the first that exists: the story's `state/bible/<type>/<Name>.md`, then `worlds/<World>/snapshots/<previous position>/<type>/<Name>.md` when the story has a position, then `worlds/<World>/<type>/<Name>.md`.

## Scripts' contracts

The scripts' command-line flags and output are pinned by recorded files in `fixtures/golden/` (checked by `tools/golden.py`), so projects and agents that rely on them keep working.
