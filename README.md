# Writing Room

A set of skills that helps you write fiction with an AI coding agent, without losing the plot. You keep the creative decisions; the skills do the structural and bookkeeping work: a **world bible**, **story concepts**, **outlines**, **chapter plans**, **drafts**, **reviews**, and a running record of **who knows what** so chapter 12 does not contradict chapter 3.

It works with **Claude Code**, **Devin**, **OpenCode** and **Hermes Agent**. Everything lives in plain Markdown files in a folder you own, so you can read, edit and version them with any tool (Obsidian works well).

> **Status: pre-release (0.1.0).** The skills, scripts and installer are covered by automated tests on Windows and Linux, and the Claude Code plugin manifest validates. What has **not** been verified yet is how each real agent discovers and follows the skills; that testing comes last. Expect rough edges, and please report them. See [What is verified](#what-is-verified).

## What it does

```
create-world ─▶ story-ideator ─▶ outliner ─▶ chapter loop ─▶ world-archivist (consolidate)

chapter loop:  planner ─▶ draft-writer ─▶ reviewer ─▶ draft-fixer ─▶ story-analyzer ─▶ promote-chapter ─┐
                  ▲                                                                                      │
                  └──────────────────────────────────── next chapter ────────────────────────────────────┘
```

- **Plan before prose.** The planner breaks a chapter into scenes against the story structure (Three-Act, Fichtean Curve, Hero's Journey, and others are included) before anything is written.
- **Review before recording.** The reviewer checks the draft for continuity and character problems; the draft-fixer applies minimal corrections; only then does the story-analyzer record what changed.
- **Continuity as data.** After each chapter the story-analyzer updates what each character now *knows*, a ledger of active lies and promises, and a ledger of plot-critical facts. Later chapters are checked against them.
- **World that grows.** Finished stories merge into the world bible, with snapshots so a story set earlier in the world's history sees the world as it was then.

A router skill, `writing-room`, finds your project, works out where each story stands, and tells you (and the agent) what comes next, so you can just say "continue my story".

## Quick start

You need Python 3.9 or newer and one of the supported agents.

```bash
git clone https://github.com/soronthar/writer-helper.git
cd writer-helper

# 1. install the skills for your agent, into your writing project (use --user for all projects)
python skills/writing-room/scripts/wr_install.py --harness claude --project path/to/my-novel --dry-run   # preview
python skills/writing-room/scripts/wr_install.py --harness claude --project path/to/my-novel

# 2. create the project (skip if the folder already is one)
python skills/writing-room/scripts/wr_init.py path/to/my-novel
```

Then open `path/to/my-novel` in your agent and say: **"Use the writing-room skill. I want to start a new world."**

`--harness` takes `claude`, `devin`, `opencode`, `hermes`, a comma list, or `all`. Details, locations, and the project-versus-user choice are in [docs/INSTALL.md](docs/INSTALL.md); a longer walk-through is in [docs/USER_GUIDE.md](docs/USER_GUIDE.md). 

## What gets created in your project

```
my-novel/
├── writing-room.toml          marks the project root
├── AGENTS.md  CLAUDE.md       short instructions for agents (CLAUDE.md just imports AGENTS.md)
├── worlds/<World>/            the world bible: characters, factions, places, myths, hooks, summary, timeline, snapshots
├── stories/<Story>/           concept, outline, chapters/, current_chapter/, state/ (timeline, schemes, facts)
└── writing_concepts/styles/   your prose styles
```

Every file is Markdown you can edit by hand. A complete example, generated and invented for this repository, is in [examples/sample-project](examples/sample-project). The exact layout is in [docs/LAYOUT_V1.md](docs/LAYOUT_V1.md), and what each skill reads and writes is in [docs/PIPELINE.md](docs/PIPELINE.md).

## Supported agents

| Agent | Project-level skills | User-level skills | Verified in the real tool |
|---|---|---|---|
| Claude Code | `.claude/skills` | `~/.claude/skills` | Plugin manifest validates; skills not yet exercised end to end |
| Devin | `.agents/skills` | `~/.config/devin/skills` | Not yet |
| OpenCode | `.opencode/skills` | `~/.config/opencode/skills` | Not yet |
| Hermes Agent | `.hermes/skills` (then `hermes skills trust`) | `~/.hermes/skills` | Not yet |

Locations come from each tool's own documentation. The installer puts one copy where several tools read the same folder, so nothing is installed twice.

## Working with the skills

- **Modes.** Most skills offer an autonomous mode (the skill decides, you approve) and a collaborative or step-by-step mode. Add `preview: true` to see a plan or draft before it is saved.
- **You stay in charge.** Skills ask before overwriting, and nothing is deleted without showing you what will go. Review reports flagged "verify with author" always stop for your decision.
- **One stage per session is fine.** Everything a skill does is saved to files, so you can start a fresh session for the next stage and say "continue my story". This also keeps each session's context small.
- **Edit freely.** Change any file by hand between steps. The skills read the files, not their own memory.
- **Scripts are optional.** Small Python scripts load context faster and do mechanical jobs safely. Every skill also describes what to do without a shell, for agents that cannot run commands.

## Cost and context

Each stage reads some files and writes some. The stages that read the most are the reviewer and the story-analyzer on long chapters, because they need the draft, the plan, the registries and the relevant world files. The scripts exist to load only what is needed (named characters, locations and factions, not the whole world), and long reference material in the skills is loaded only at the step that needs it. Token use has not been measured across real runs. If cost matters, start a fresh session per stage, keep chapters to a sensible length, and use the autonomous modes with the review loop as your quality gate instead of previewing every plan and draft.

## Existing Writing Room projects

Projects from the original (single-folder) Writing Room keep working unchanged: the layout is frozen, and on a real project the new scripts reproduced the original scripts' output exactly. `wr_migrate.py` adds the `writing-room.toml` marker and, with `--retire-legacy`, moves the old agents, commands and scripts aside (reversibly). Always a dry run first. Step by step in [docs/MIGRATING.md](docs/MIGRATING.md); the layout is in [docs/LAYOUT_V1.md](docs/LAYOUT_V1.md).

## Troubleshooting

- **`wr_doctor.py` is the first stop.** It reports where the project root was found, layout problems, a possibly stale `SUMMARY.md`, and whether every skill sits next to `writing-room` (the skills refer to each other and to its scripts by relative path, so installing only some of them breaks things).

  ```bash
  python skills/writing-room/scripts/wr_doctor.py --root path/to/my-novel
  ```
- **The agent does not seem to know the skills.** Check the folder from the table above, restart the agent, and for Hermes run `hermes skills trust` in the repository. Hermes and Devin look for project skills at the git repository root; the installer warns when your project is not at the root.
- **"Which skill comes next?"** `python skills/writing-room/scripts/wr_next.py --root path/to/my-novel` answers from the files.
- **A skill name clashes with one you already have** (for example your own `planner`). The installer will not overwrite it unless you pass `--force`.

## What is verified

| Verified by automated tests (Windows and Linux; Python 3.11, 3.12, 3.14) | Not verified yet |
|---|---|
| Scripts reproduce the original framework's recorded output; project discovery; init, migrate, doctor, next-skill, promote; installer locations, updates, uninstall and refusal to overwrite; an installed copy runs on its own; skill files pass a portability lint; the whole chapter loop's state transitions | That each real agent finds and triggers the installed skills; Devin cloud sessions running the bundled scripts; Hermes's handling of `AGENTS.md`; macOS; Python 3.9 (syntax-checked only) |

## More

| | |
|---|---|
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | A first story, step by step |
| [docs/PIPELINE.md](docs/PIPELINE.md) | Every skill: when to use it, what it reads and writes |
| [docs/FILE_FORMATS.md](docs/FILE_FORMATS.md) | The files the skills share and the fields scripts rely on |
| [docs/INSTALL.md](docs/INSTALL.md) | Install, update, remove; project versus user level |
| [docs/MIGRATING.md](docs/MIGRATING.md) | Moving a project from the original Writing Room |
| [docs/WRITING_SKILLS.md](docs/WRITING_SKILLS.md) | How to change or add a skill |
| [CONTRIBUTING.md](CONTRIBUTING.md), [AGENTS.md](AGENTS.md) | Working on this repository |
| [docs/RELEASING.md](docs/RELEASING.md) | How a release is made |
| [docs/development/](docs/development/) | Design plan and decision log |
| [CHANGELOG.md](CHANGELOG.md) | What changed |

## License

MIT; see [LICENSE](LICENSE).
