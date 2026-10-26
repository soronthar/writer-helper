# Writing Room project

This folder is a Writing Room project: fiction written with a world bible, story concepts, outlines, chapter plans, drafts, reviews and continuity tracking. The work is done by skills; you stay in the author's seat and make the creative decisions.

## Start here

Use the **`writing-room`** skill. It finds this project, works out where each story stands, and names the next skill to run. Ask it "where am I?" or "continue my story" at the start of any session.

If the skills are not available in your tool, they are the folders named `writing-room`, `create-world`, `story-ideator`, `planner` and so on, wherever your tool installs skills. The Writing Room installation notes explain where.

## The project

- `worlds/<World>/` — world bibles (characters, factions, places, myths, hooks, summary, story order, timeline, snapshots)
- `stories/<Story>/` — `CONCEPT.md`, `OUTLINE.md`, `chapters/`, `current_chapter/`, and `state/` (timeline, active schemes, story facts, story-local bible). A Book Series adds `Book NN - <Title>/` folders.
- `writing_concepts/styles/` — your prose styles
- `writing-room.toml` — marks the project root; do not delete it

## The loop

`planner` → `draft-writer` → `reviewer` → `draft-fixer` → `story-analyzer` → `promote-chapter`, then repeat. Before it: `create-world`, `story-ideator`, `outliner`. After the last chapter: `world-archivist` (consolidate).

## Rules every skill follows

- A story's world is the `**World:**` field of its `CONCEPT.md`. Never assume one.
- The world bible holds what things are. In-flight facts (lies, promises, concealments, quantities) live in the story's `state/ACTIVE_SCHEMES.md` and `state/STORY_FACTS.md` and are never merged into the world.
- During a story only `stories/<Story>/state/` changes; `worlds/` changes when a finished story is consolidated (plus hooks and edits made through `writing-assistant`).
- Ask before overwriting or deleting. Report exactly which files changed.
- Do not do the work of a skill that is not installed; say which one is missing.
- Keep names with spaces and apostrophes, and `[[wiki links]]`, exactly as they are in the files.
