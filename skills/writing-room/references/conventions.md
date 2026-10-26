# Writing Room conventions

Shared rules every Writing Room skill follows. Skills point here instead of repeating them.

## Where things are

- **Project root**: the folder that holds the author's `worlds/` and `stories/` (and usually a `writing-room.toml` marker). Every path in every skill is relative to it. Work from inside the project, or pass `--root <dir>` to a script.
- **`<WR>`**: the directory of the `writing-room` skill. Every skill is installed as a sibling of it, so from any skill's own directory it is `../writing-room/`. It contains `scripts/` (Python helpers), `shared/` (templates and craft reference) and `references/` (this file and others). Use the full path of the skill folder as your harness reports it; do not assume a fixed install location.
- **Layout**: see `layout.md` in this folder for the project file layout.

## Templates and craft reference

Templates (`templates/world/…`, `templates/story/…`, `templates/writing_concepts/…`) and craft reference (`writing_concepts/story_structure/…`, `archetypes/`, `tropes/`) resolve in this order: the project's own copy, then the framework copy under `<WR>/shared/`. Writing styles (`writing_concepts/styles/`) are the author's own and are never defaulted.

To find the real path of one: `python "<WR>/scripts/wr_resolve.py" templates/world/character.md` prints it. Without a shell, check the project path first, then `<WR>/shared/templates/world/character.md` (craft files live under `<WR>/shared/craft/…`).

## Scripts are optional

Scripts load context in fewer steps; they are never required. Run them as `python "<WR>/scripts/<name>.py" <args>` from inside the project. Every skill that uses one states what to read instead if you cannot run commands. Scripts: `load_bible.py`, `load_world.py`, `query_position.py`, `create_snapshot.py`, `wr_resolve.py`, `wr_next.py`, `promote_chapter.py`, `wr_doctor.py`, `wr_init.py`, `wr_migrate.py`, `wr_install.py`, `wr_update.py`.

## Working rules

- Identify the world before touching the world bible. A story's world is the `**World:**` field of its `CONCEPT.md`; never assume one.
- Preserve names with spaces and apostrophes, and `[[wiki links]]`, exactly as written in project files.
- Ask before overwriting or deleting. Report exactly which files you created, changed, or removed.
- Do not do the work of a skill that is not available; tell the user which skill is missing.
- `CONCEPT.md` may start with frontmatter (`world:` and `status:`) so Obsidian Bases can query stories. The body lines `**World:**` and `**Status:**` are the truth that skills and scripts read; the frontmatter mirrors them. Whoever changes the Status line changes `status:` too; `wr_doctor` warns when they differ. Frontmatter is optional.
- Identity lives in the world bible; in-flight operational facts (deceptions, promises, concealments) live in the story's `state/` registries and are never merged into the world.

## Chapter pipeline

`planner` → `draft-writer` → `reviewer` → `draft-fixer` → `story-analyzer` → `promote-chapter`. Each skill ends with a **Next step** line naming the following skill. `story-status` shows where a story is.
