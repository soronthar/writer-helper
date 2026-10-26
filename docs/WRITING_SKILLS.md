# Changing or adding a skill

For anyone working on this repository. The short rules are in [AGENTS.md](../AGENTS.md); this is the longer version.

## Shape of a skill

```
skills/<name>/
├── SKILL.md          the procedure
└── references/       long material loaded only at the step that needs it (optional)
```

`SKILL.md` starts with frontmatter that has **only** `name` and `description` (the format the four target agents share):

```yaml
---
name: planner
description: "Plan a single chapter scene by scene. Use after ... "
---
```

- `name` is lowercase letters, digits and single hyphens, up to 64 characters, and **equals the folder name**.
- `description` is a **double-quoted** string of at most 1024 characters. It is how the agent decides to load the skill, so say what the skill does, when to use it, what it reads and writes, and what it does not do. It must be quoted: unquoted text containing `: ` is invalid YAML and some agents then drop all of the skill's metadata silently.
- No `model:`, no `tools:`, no other keys.

## Writing the body

- **Procedure, not prose.** Numbered steps, explicit checks, and the exact output format. Keep `SKILL.md` under about 300 lines; move category lists, long examples and rarely used procedures into `references/` and tell the reader when to open them.
- **No agent-specific wording.** No tool names (read, write, edit, glob, grep, bash), no model ids, no subagent calls ("invoke the X agent"), no slash commands, no `Writing_Room/` paths. Say "list the folders in `worlds/`", "search for the name", "follow the `planner` skill". The lint enforces most of this.
- **Scripts are optional.** Skills reach the runtime at `../writing-room/` (scripts, templates, shared references). Every script call needs a "Without a shell" alternative that produces the same result by reading and writing files. The runtime lives inside the `writing-room` skill because every agent installs skills side by side, so the relative path works wherever they are installed.
- **Hand-offs.** A skill never needs a subagent: when it needs another skill's work (for example creating a missing character) it follows that skill itself and returns. End with a `**Next step:**` line naming the next skill.
- **Template headings and registry names are data.** `Notes for the Draft Writer`, `Reviewer Notes`, `Draft-Fixer-Log.md`, ledger columns and status values are read by other skills and by existing projects. Never reword them.
- **Be explicit about writes.** Say what is created, what is changed in place, what is never touched, and what needs the user's confirmation.

## Tools

```bash
python tools/lint_skills.py                  # frontmatter, naming, quoting, wording, referenced paths (also in references/)
python -m unittest discover -s tests         # includes fidelity, fallback and pipeline tests
python tools/convert_legacy.py <old agent>   # a mechanical first pass over a legacy agent or command; finish by hand
```

The fidelity tests keep a list of phrases per skill (template headings, field names) and check the skill still contains at least as many as the legacy agent did. When you rename or move text, run them; add phrases to `PROTECTED` in `tests/test_skills.py` when you introduce a new format other skills depend on.

## Adding a skill

1. Create `skills/<name>/SKILL.md`; add `references/` if needed.
2. Add the name to `skills/writing-room/shared/skills.json` (a test keeps it equal to the folders), mention it in the router's table in `skills/writing-room/SKILL.md`, and add a row to [PIPELINE.md](PIPELINE.md).
3. If it is part of the chapter loop, add its place to the next-step chain test in `tests/test_loop.py` and teach `wr_next.py` its state.
4. Run the lint and the tests. They also run the installer against a temporary folder, so a new skill is installed and cross-checked automatically.

## Changing the project layout

Don't, without a plan. Layout v1 is frozen ([LAYOUT_V1.md](LAYOUT_V1.md)): existing projects must keep working. A format change needs a new layout number, a migration in `wr_migrate.py`, golden-file updates and a changelog entry.

## Changing scripts

The four original scripts (`load_bible`, `load_world`, `query_position`, `create_snapshot`) must keep producing the recorded output: `python tools/golden.py check --scripts skills/writing-room/scripts` must pass. New scripts use only the standard library and Python 3.9 syntax, find the project through `common.setup()`, accept `--root`, and have tests.
