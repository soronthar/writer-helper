# Writing Room (portable) — contributor guide

This repository builds a harness-neutral Writing Room: skills that take an author from a world bible to finished chapters. It targets Claude Code, Devin, Hermes Agent and OpenCode. For the full plan see `docs/development/DISTRIBUTION_PLAN.md`; decisions are in `docs/development/DECISIONS.md`.

(The text an *author's project* gets is `skills/writing-room/shared/project/AGENTS.md`. This file is for people working on the framework.)

## Layout

- `skills/<name>/SKILL.md` — one skill each; long material in `skills/<name>/references/`
- `skills/writing-room/` — the router skill **and the runtime**: `scripts/` (Python, stdlib only), `shared/` (templates, craft reference, project guidance), `references/` (conventions, layout, shared procedures). Other skills reach it as `../writing-room/…`.
- `fixtures/legacy-v1/` — frozen copy of the original framework and sample content; `fixtures/golden/` — recorded output of its scripts; `fixtures/synthetic-v1/` — small project covering what the sample lacks
- `examples/sample-project/` — a complete layout-v1 project
- `tests/`, `tools/` — development only; not installed

## Commands

```bash
python -m unittest discover -s tests                 # all tests
python tools/lint_skills.py                          # skill portability lint
python tools/golden.py check --scripts skills/writing-room/scripts   # scripts reproduce legacy output
```

## Rules

- **Layout v1 is frozen** (`docs/LAYOUT_V1.md`). Existing projects must keep working; a format change needs a new layout number and a migration.
- **The harness depends on the skills.** The separate `writing-room-harness` repository reads `SKILL.md` files as prompts and imports `load_bible` (`collect`, `render`), `common` (`find_root`, `in_project`, `lookup`, `check_layout`, `md_files`, `DIV`) and `wr_next.project_state`, and runs `create_snapshot`, `promote_chapter`, `query_position` and `wr_doctor`. Changing those, the reviewer or story-analyzer references, or the templates means running its tests too (`WR_REPO` pointing here).
- **Skills are portable.** Frontmatter is `name` and `description` only. No tool names, no model ids, no subagent calls, no slash commands, no `Writing_Room/` paths. Scripts are optional: every script call needs a without-a-shell path. `tools/lint_skills.py` enforces most of this.
- **Template headings and registry names are data** (for example `Notes for the Draft Writer`, `Reviewer Notes`). Never rename them when converting wording; `tests/test_skills.py` guards the important ones.
- **Do not edit `fixtures/legacy-v1/` or `fixtures/golden/` by hand.** Regenerate the sample with `tools/build_sample.py --fixtures` and then `tools/golden.py capture`, and say why in the commit.
- Multi-line patches are safer as files than as shell heredocs; shell quoting has bitten this repo more than once.
- **No private fiction in this repository.** Everything shipped (samples, fixtures, examples in skill text) is invented for this project. Before publishing, run `tools/check_public_clean.py --source <the author's own project>`; it must report clean, and the history must be clean too (publish with `tools/export_public.py`).
