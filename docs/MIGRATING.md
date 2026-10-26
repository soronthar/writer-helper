# Moving a project from the original Writing Room

For projects made with the original, single-folder Writing Room: one `Writing_Room/` directory that holds your `worlds/` and `stories/` **and** the framework itself (`.claude/agents/`, `.claude/commands/`, `scripts/`, `templates/`, `room_rules/`, `CLAUDE.md`).

**Your content is not converted.** The layout of worlds, stories, chapters, registries and snapshots is frozen ([LAYOUT_V1.md](LAYOUT_V1.md)); every file stays exactly as it is. What changes is the framework around it: the agents and slash commands become skills, and the scripts and templates now come from the installed skills.

On a real project (three worlds, three stories) the new scripts produced byte-for-byte the same output as the original scripts for every world, story and entity listing tried, and the same snapshot files. That is what "keeps working" means here, and it is checked by the same comparison you can run yourself (below).

## Before you start

Work on a **copy** the first time, or make sure the folder is committed in git. Every step below is a dry run unless it says `--apply`, and nothing deletes anything.

```bash
cp -r Writing_Room Writing_Room_try        # or commit first
```

## Steps

1. **Look at the project as it is.**
   ```bash
   python skills/writing-room/scripts/wr_doctor.py --root Writing_Room_try
   python skills/writing-room/scripts/wr_next.py --root Writing_Room_try
   ```
   Warnings are normal for older projects (a concept file without a Status field, a stray `Chapter_03_original.md`). The doctor lists anything that would break; `wr_next` says where each story stands.
2. **Install the new skills** into the project (see [INSTALL.md](INSTALL.md) for other agents and for user level):
   ```bash
   python skills/writing-room/scripts/wr_install.py --harness claude --project Writing_Room_try
   ```
3. **Preview the migration.**
   ```bash
   python skills/writing-room/scripts/wr_migrate.py --root Writing_Room_try --retire-legacy
   ```
   It lists what it would do: add `writing-room.toml`, move the old framework files aside, add `AGENTS.md` and `CLAUDE.md`.
4. **Apply it.**
   ```bash
   python skills/writing-room/scripts/wr_migrate.py --root Writing_Room_try --retire-legacy --apply
   ```
   Without `--retire-legacy` only the marker is added and the old agents, commands and scripts stay where they are; that works, but an agent then sees the old agents and the new skills side by side.
5. **Check again.** `wr_doctor.py` should report no errors and no "old framework files" warning, and `wr_next.py` should say the same as before.
6. **Open the project in your agent** and say: *"Use the writing-room skill and tell me where I am."* Then do one real chapter (or one real step, such as an outline) end to end before relying on it.

## What `--retire-legacy` moves, and what it never touches

| Moved to `.writing-room-legacy/` (same relative paths) | Never touched |
|---|---|
| `.claude/agents/`, `.claude/commands/`, `CLAUDE.md`, `README.md`, `room_rules/`, `scripts/` | `worlds/`, `stories/`, `writing_concepts/` (your styles, tropes, archetypes), `templates/`, `.claude/settings*.json` |

Your own `templates/` keep overriding the framework's; your own styles are used as before. If you customised an old agent or command, your version is in `.writing-room-legacy/.claude/`; the skills are organised differently, so port such changes by hand into the skill's `SKILL.md`.

**To undo**, move the folders back from `.writing-room-legacy/` and delete `AGENTS.md`, `writing-room.toml`, and the installed skills folder (`wr_install.py ... --uninstall`).

## What you will notice

- **Skills instead of agents and commands.** `/create-world`, `/create-style`, `/story-status` and `/promote-chapter` are skills now (`create-world` and so on); the "Writing Room Head" role is the `writing-room` skill, which also works out the next step from your files.
- **One reviewer.** `reviewer-consistency` and `reviewer-character` were already deprecated; `reviewer` does both passes.
- **No subagents needed.** A skill that needs another skill's work (for example creating a missing character) follows it in the same session.
- **Finishing a story** is handled by the router: it confirms and sets the story's Status to `Complete`, then offers to consolidate.
- **Unplaceable fixes are reported.** If the draft-fixer cannot place a fix exactly, it skips it and lists it prominently instead of guessing.
- **Scripts run from anywhere.** They find the project by its marker (or by `worlds/` and `stories/`), or take `--root`.

## Comparing the old and new scripts on your own project

If you want the same evidence on your data, run the original scripts and the new ones over the same copy and diff the output. For example, for one world and one story:

```bash
cd Writing_Room_try        # before step 4, while scripts/ is still in place
python scripts/load_world.py --world "worlds/<World>"                         > old.txt
python <skills>/writing-room/scripts/load_world.py --world "worlds/<World>"   > new.txt
diff old.txt new.txt && echo identical
```

Do the same for `load_bible.py` (with your usual flags) and `query_position.py --format json`. They should be identical apart from absolute paths.

## A first-real-chapter checklist

- [ ] `wr_doctor` reports no errors.
- [ ] The agent can see the skills (ask it to list them, or say "use the writing-room skill").
- [ ] `writing-room` names the same next step as `wr_next`.
- [ ] One planner run produced a `CHAPTER_PLAN.md` with the headings your old plans have (for example `Notes for the Draft Writer`).
- [ ] After a draft, `reviewer` wrote both reports and `draft-fixer` wrote its log.
- [ ] `story-analyzer` appended a Timeline entry and updated the ledgers; `promote-chapter` showed what it would delete before deleting.
- [ ] `git diff` (or a folder diff against your backup) shows only changes you expected.

If anything looks wrong, stop and keep the copy; the original folder is untouched.
