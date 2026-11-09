# Writing Room conventions

Shared rules every Writing Room skill follows. Skills point here instead of repeating them.

## Where things are

- **Project root**: the folder that holds the author's `worlds/` and `stories/` (and usually a `writing-room.toml` marker). Every path in every skill is relative to it. Work from inside the project, or pass `--root <dir>` to a script.
- **`<WR>`**: the Writing Room framework folder, which is the installed `writing-room` skill. It contains `scripts/` (Python helpers), `shared/` (templates and craft reference) and `references/` (this file and others). The project's `AGENTS.md` names it in a "Writing Room paths" block that the install and update scripts keep current; use that path exactly as written (it is relative to the project root unless it is absolute). If `AGENTS.md` has no such block, `<WR>` is the `writing-room` folder beside the running skill's own folder, wherever your harness installed the skills. `<WR>` is never a folder of the project you guess at, and never the running skill's folder: `<WR>/references/layout.md` is not `<skill>/references/layout.md`.
- **A skill's own files**: a skill's `references/…` files are in that skill's folder, beside `<WR>` ("Writing Room paths" names the folder).
- **Layout**: see `layout.md` in this folder for the project file layout.

## Templates and craft reference

Templates (`templates/world/…`, `templates/story/…`, `templates/writing_concepts/…`) and craft reference (`writing_concepts/story_structure/…`, `archetypes/`, `tropes/`) resolve in this order: the project's own copy, then the framework copy under `<WR>/shared/`. Use the copy that resolves, even when the other has more fields; if a project copy looks older than the framework's, tell the user that `wr_templates.py` finds such copies and `--retire` moves them aside. Writing styles (`writing_concepts/styles/`) are the author's own and are never defaulted.

To find the real path of one: `python "<WR>/scripts/wr_resolve.py" templates/world/character.md` prints it. Without a shell, check the project path first, then `<WR>/shared/templates/world/character.md` (craft files live under `<WR>/shared/craft/…`).

## Scripts are optional

Scripts load context in fewer steps; they are never required. Run them as `python "<WR>/scripts/<name>.py" <args>` from inside the project. Every skill that uses one states what to read instead if you cannot run commands. Scripts: `load_bible.py`, `load_world.py`, `query_position.py`, `create_snapshot.py`, `wr_resolve.py`, `wr_next.py`, `promote_chapter.py`, `wr_doctor.py`, `wr_init.py`, `wr_migrate.py`, `wr_install.py`, `wr_update.py`, `wr_paths.py`, `wr_templates.py`.

## Loading story context

Skills load a story's context with `load_bible.py --for <preset>`, one preset per skill step. Each skill gives its exact command. `python "<WR>/scripts/load_bible.py" --recipes` prints every preset, the arguments it takes and the flags it stands for.

- **One line.** Write the command on one line. Do not split it with `\` or `` ` ``: line continuations differ between shells.
- **Real values only.** Replace each `<…>` placeholder with a real value, in double quotes. Repeat a flag such as `--char` once per name. Never type square brackets or `...`.
- **Let the script work out the rest.** With `--for`, the script finds the world from CONCEPT.md and the baseline snapshot from WORLD_ORDER.md (and, for the planner, the structure). Do not add `--world` or `--position` unless a skill tells you to. The CONTEXT block at the top of the output says what was used and where it came from.
- **If it fails,** the error says what is missing. Fix that one argument and run again. Do not fall back to the long form or to reading files by hand while the script can run.

## Working files

Temporary working files go in `.writing-room-work/` at the project root, never in `stories/` or `worlds/`. Inside it, paths mirror the project: `.writing-room-work/stories/<Story>/…`, `.writing-room-work/worlds/<World>/…`. Nothing there is a source of truth, no skill reads it as story or world state, and it can be deleted at any time. The scripts create it with a `.gitignore` so it is never committed; Obsidian hides it because its name starts with a dot.

- **Long script output.** If your harness may not show a loader's output in full, add a bare `--output` to `load_bible.py` or `load_world.py`. The context is saved as UTF-8 under `.writing-room-work/` and the script prints only a receipt: the file's absolute path, then each item with its line range. Read the file at that exact path, range by range, until every item is read. Do not build the path yourself, and do not redirect output with the shell (`>`): some shells re-encode it.
- **Concept drafts.** The `story-ideator` writes its concept to `.writing-room-work/worlds/<World>/CONCEPT.md` from the first preview on, marked `<!-- draft: not yet approved -->` until the user approves it, and builds the story from that file, so the text survives if the session loses its earlier context or stops. A new ideator session for that world finds the file and offers to continue it. `new_story.py` refuses a file still marked as a draft, copies an approved one into the story and deletes it.
- **Chapter drafts.** The `draft-writer` saves each scene to `.writing-room-work/<story or book folder>/current_chapter/CONTENT.md` as soon as it is written, with a first line `<!-- draft: Chapter N, K of M scenes saved; self-check: … -->`, runs its self-check on that file, and writes `current_chapter/CONTENT.md` from it, deleting the working draft only after reading `CONTENT.md` back. A new session finds the working draft (`wr_next.py` reports it) and offers to resume.
- **Fix checkpoints.** Before its first fix the `draft-fixer` copies the draft to `.writing-room-work/<story or book folder>/current_chapter/Chapter_NN.before-fixes.md` and writes `Draft-Fixer-Log.md` with `**Fix status:** In progress` and a Fix Plan, updated after every fix and author decision. A log still `In progress` means the fixes stopped partway: the next session resumes from it (`wr_next.py` reports it), and the story-analyzer does not start.
- **WORLD_ORDER.md.** With a shell, change its rows with `world_order.py` (or `new_story.py` for a new story), never by hand.
- **Large documents you write.** If your harness may cut off a long write (a chapter plan, a chapter, a review), write the document to `.writing-room-work/<the same project path>` first, read it back to check it is complete, then write it to its real place.

## Working rules

- **Examples are not project files.** Names in skill examples and sample output (such as Harrowmere, Mara Quill, Doran Pike, Harbor Guild, Aethermoor) are invented to show a format. Never look for them in the project or treat them as facts; take names only from the project's own files and from the user.
- Identify the world before touching the world bible. A story's world is the `**World:**` field of its `CONCEPT.md`; never assume one.
- Preserve names with spaces and apostrophes, and `[[wiki links]]`, exactly as written in project files.
- Ask before overwriting or deleting. Report exactly which files you created, changed, or removed.
- Do not do the work of a skill that is not available; tell the user which skill is missing.
- `CONCEPT.md` may start with frontmatter (`world:` and `status:`) so Obsidian Bases can query stories. The body lines `**World:**` and `**Status:**` are the truth that skills and scripts read; the frontmatter mirrors them. Whoever changes the Status line changes `status:` too; `wr_doctor` warns when they differ. Frontmatter is optional.
- **Claims need sources.** When you say something is verified, consistent or established, name the file it comes from, read in this run. If you did not load the source, say "not checked". Never fill a gap from memory: a file, field, name or number you cannot point to in a loaded file does not exist for this task. Ask, or flag it.
- **Approval gates hold in every mode.** Autonomous modes skip previews of routine work; they never skip a step that a skill says needs the author (hooks, "Verify with author" items, overwrite confirmations). A change that merely fits the story is not approved.
- Identity lives in the world bible; in-flight operational facts (deceptions, promises, concealments) live in the story's `state/` registries and are never merged into the world.

## Chapter pipeline

`planner` → `draft-writer` → `reviewer` → `draft-fixer` → `story-analyzer` → `promote-chapter`. Each skill ends with a **Next step** line naming the following skill. `story-status` shows where a story is.
