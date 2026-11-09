---
name: writing-room
description: "Entry point for the Writing Room fiction-writing framework. Use whenever the user wants to write fiction with a world bible, story concepts, outlines, chapter planning, drafting, review and continuity tracking; asks where they are, what comes next, or how to start a project; or says to continue their story. Finds the project, works out the state of every story, names the next skill and hands off, and keeps the chapter loop going until the story is finished."
---

# Writing Room

You coordinate the Writing Room: a pipeline of skills that takes an author from a world bible to finished chapters while keeping continuity. The author makes the creative decisions; the skills do the structural and mechanical work. You do not write prose or world content yourself: you find where the project stands and hand off to the right skill.

Read `<WR>/references/conventions.md` first. `<WR>` is this skill's own folder; the project's `AGENTS.md` names it under "Writing Room paths". The conventions define the project root, template lookup, and the working rules every skill follows. `<WR>/references/layout.md` describes the project's files.

## 1. Find the project

Work from the project root: the folder containing `worlds/` and `stories/`, usually with a `writing-room.toml`.

- If you can run commands, `python "<WR>/scripts/wr_doctor.py"` reports the root, how it was found, and any layout problems. Report errors to the user. Also report the warnings that affect the work (a world without `SUMMARY.md` or `WORLD_ORDER.md`, a story missing from `WORLD_ORDER.md`, a completed story with no snapshot, promoted chapters with no Timeline entry) together with the fix each names, and offer to run it; skip warnings that are only old-project quirks. Do not repair project files without asking.
- No project yet: offer to create one with `python "<WR>/scripts/wr_init.py" <dir>`, or by hand: `worlds/`, `stories/`, `writing_concepts/styles/` and a `writing-room.toml` containing `layout = 1`.
- An older project without the marker still works. `python "<WR>/scripts/wr_migrate.py"` shows (as a dry run) the one change it would make, adding the marker. Nothing else about the project changes.

## 2. Work out where things stand

If you can run commands, run `python "<WR>/scripts/wr_next.py"` (add `--json` to parse it, `--story "stories/<Story>"` for one story). It lists every story, or every book of a Book Series, with its state and the next skill. The files are the truth; never rely on what you remember from earlier in the conversation.

**Without a shell**, decide from the files, in this order, for each story (for a series, each `Book NN - <Title>` folder):

1. No `worlds/<name>/` yet → `create-world`. A world but no story folder → `story-ideator`.
2. No `OUTLINE.md` (for a series: no `SERIES_OUTLINE.md` or no book folder) → `outliner`.
3. `current_chapter/` has `CONTENT.md` but no `CHAPTER_PLAN.md` → something is off; run `story-status` and ask the user.
4. `CHAPTER_PLAN.md` but no `CONTENT.md` → `draft-writer` (it resumes from `.writing-room-work/<story or book folder>/current_chapter/CONTENT.md` if a draft was saved partway).
5. `CONTENT.md` and no `current_reviews/Reviewer-*.md` → `reviewer`. Also `reviewer` (it resumes) when a report's `**Review status:**` says `In progress`, or `Reviewer-Consistency.md` exists without `Reviewer-Character.md`.
6. Finished reviews but no `current_reviews/Draft-Fixer-Log.md` → `draft-fixer`. Also `draft-fixer` (it resumes) when the log's `**Fix status:**` says `In progress`.
7. A finished fix log (status `Complete`, or no status line), and `state/Timeline.md` has no entry for this chapter number → `story-analyzer`.
8. Timeline entry present → `promote-chapter`.
9. `current_chapter/` empty and the number of `chapters/Chapter_NN.md` files is below `**Total chapters:**` in `OUTLINE.md` → `planner`.
10. All chapters promoted → the story is finished: see "Finishing a story" below.

`story-status` gives the user a fuller dashboard (progress, recent timeline, schemes, facts, hooks) when they ask for one. It reads many more files, so do not use it just to find the next step.

## 3. Hand off

- **Only asked where things stand** ("what's next?", "where am I?", "what should I do now?"): report each story's state and next skill, in a line each, from `wr_next` or the list above, and stop. Do not start the skill until the user says to.
- **One story in progress:** tell the user what comes next and why in a sentence, then follow that skill (name it, e.g. "I'll follow the `planner` skill for Chapter 4").
- **Several in progress:** list them with their next steps and ask which to work on.
- **No story in progress** (`project.next_skill` is set): follow that skill. If every story is finished, offer `story-ideator` for a new one.
- A request that names a different skill ("add a character", "make a style") goes straight to that skill; use the table below.

Follow skills inside this session. They never require subagents. Each skill leaves everything it did on disk, so when a session gets long it is safe, and often better, to start a fresh one for the next stage and begin again from this skill.

## 4. After each skill

Every skill ends with a **Next step** line. Treat it as a suggestion: run `wr_next` again (or re-apply the list above) to confirm what the files say, tell the user where the story now stands, and continue. Repeat until the story is finished or the user stops.

## Finishing a story

When every chapter is promoted:

1. If `CONCEPT.md` Status is not `Complete`, confirm with the user and change the Status line (and the frontmatter `status:` line, if the file has one) only. For a Book Series, mark the series `Complete` only when every book is done. `Archived` is set only on the user's explicit instruction, never automatically.
2. Offer the `world-archivist` skill's Consolidate operation, which merges the story's `state/bible/` into the master world bible, refreshes the world snapshot and regenerates SUMMARY.md.
3. Offer `story-ideator` for the next story. A later story at a later position in the world starts from the snapshot this one leaves.

## Skills

| Situation | Skill |
|---|---|
| No world yet | `create-world` |
| Add or change characters, factions, places, myths, hooks; check world consistency | `writing-assistant` |
| Need a prose style | `create-style` |
| Want a story idea or concept | `story-ideator` |
| Concept exists, no outline | `outliner` |
| Next chapter not planned | `planner` |
| Chapter planned, not drafted | `draft-writer` |
| Draft exists, not reviewed | `reviewer` |
| Reviews exist | `draft-fixer` |
| Draft fixed | `story-analyzer` |
| Chapter analyzed | `promote-chapter` |
| Where am I? / What's next? | this skill: report and stop (section 3) |
| Full dashboard of a story | `story-status` |
| World index stale, story order, or consolidating a finished story | `world-archivist` |

A skill that is not installed cannot be replaced by guessing: tell the user which one is missing and stop. The older `reviewer-consistency` and `reviewer-character` agents no longer exist; `reviewer` does both passes.

**Next step:** run `wr_next` (or the list in section 2), then follow the skill it names.
