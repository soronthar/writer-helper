# Installing the Writing Room

The Writing Room is a set of skills (14 folders, each with a `SKILL.md`). Installing means putting those folders where your coding agent looks for skills. `wr_install.py` does that for Claude Code, Devin, OpenCode and Hermes Agent. It copies (never symlinks), never touches your worlds and stories, and only ever replaces folders it installed itself.

You need Python 3.10 or newer (developed on 3.11; the test suite also passes on 3.12 under Linux).

## Quick start

From a checkout of this repository, inside or next to your writing project:

```bash
# one project, one agent
python skills/writing-room/scripts/wr_install.py --harness claude --project path/to/my-novel

# every agent that reads project skills, plus short AGENTS.md / CLAUDE.md instructions
python skills/writing-room/scripts/wr_install.py --harness all --project path/to/my-novel --guidance

# for all your projects instead (user level)
python skills/writing-room/scripts/wr_install.py --harness claude --user
```

Add `--dry-run` first to see exactly what would happen. Then start your agent in the project and say **"use the writing-room skill"** (or "where am I?"). If the project does not exist yet, create one first:

```bash
python skills/writing-room/scripts/wr_init.py path/to/my-novel
```

An existing project from the original Writing Room needs nothing except, optionally, `wr_migrate.py` (which only adds a `writing-room.toml` marker). See `docs/LAYOUT_V1.md`.

## Project level or user level

| | Project level (`--scope project`, the default) | User level (`--scope user` or `--user`) |
|---|---|---|
| Skills available | only in that project | in every project you open |
| Lives in | the project folder (can be committed, so collaborators and cloud sessions get it) | your home / config folder |
| Update | re-run in each project | re-run once |
| Good for | a novel you share, or one version per project | your own machine, one copy to maintain |

The installer prints which scope it used. Both can coexist; each has its own manifest, and `--uninstall` only affects the scope you name. Avoid installing the same skills at both levels for one tool, since it may then see two copies.

## Where the skills go

| Harness | Project level | User level |
|---|---|---|
| Claude Code | `<project>/.claude/skills` | `~/.claude/skills` |
| Devin | `<project>/.agents/skills` | `~/.config/devin/skills` (Windows: `%APPDATA%\devin\skills`) |
| OpenCode | `<project>/.opencode/skills` | `~/.config/opencode/skills` |
| Hermes Agent | `<project>/.hermes/skills` | `~/.hermes/skills` |

These come from each tool's own documentation (checked 2026-10-02). Tools change; if a folder stops working, `--target DIR` installs anywhere.

**Shared folders.** Several tools read each other's folders: `.claude/skills` is read by Claude Code, Devin and OpenCode; `.agents/skills` by Devin, OpenCode and Hermes. When you ask for several harnesses at project level the installer uses the fewest folders that cover them all and gives no tool two copies, because two copies of the same skill names in folders one tool reads would clash. For example `--harness all` gives `.claude/skills` (Claude Code, Devin, OpenCode) plus `.hermes/skills`; `--harness devin,hermes` gives a single `.agents/skills`. At user level OpenCode reuses `~/.claude/skills` when Claude Code is also requested.

**Where the tool thinks the project is.** Project-level skills are looked up from the repository, not from an arbitrary folder:

- **Hermes** treats the nearest ancestor containing `.git` as the project root and reads `.hermes/skills` (and `.agents/skills`) there. It also asks you to approve project skills once: the first time you run Hermes in the repository it shows a notice, and you run `hermes skills trust`. Hermes scans project skills for dangerous patterns before loading them.
- **Devin** discovers project skills in git repositories.
- **OpenCode** walks up from the working directory to the git root, so a project in a subfolder is found when you work inside it.
- **Claude Code** reads `.claude/skills` of the project it is started in.

If your writing project is not the repository root (for example it is a `novel/` subfolder of a larger repository), the installer warns for Hermes and Devin and tells you the repository root. Install there instead:

```bash
python skills/writing-room/scripts/wr_install.py --harness hermes --project path/to/repo-root
```

The scripts installed at the repository root still find your writing project from where you work (they look for `writing-room.toml`, or `worlds/` plus `stories/`, upward from the working directory, or take `--root`). If you cannot install at the repository root, use user level, or list the folder in Hermes's `config.yaml` (the installer prints the exact snippet):

```yaml
skills:
  external_dirs:
    - /path/to/my-novel/.hermes/skills
```

If the project is not in a git repository at all, run `git init` (Hermes and Devin need one) or use user level.

## Claude Code plugin

This repository is also a Claude Code plugin (`.claude-plugin/plugin.json`, with `skills/` beside it). The manifest passes `claude plugin validate`. No marketplace listing exists yet (see `docs/development/DECISIONS.md`, D5), so for now install by the folder route above.

## Running on a local LLM with pi

To run the Writing Room on a model on your own machine (LM Studio, Ollama, llama.cpp, vLLM), we recommend [pi](https://pi.dev) (`pi-coding-agent`). The installer has no `--harness pi` yet; `--target` installs it.

**Why pi.** On local hardware, reading the prompt (prefill) is usually the slow part: on a 64 GB unified-memory box running a 27B model it was about 220 tokens per second. That is roughly 4.5 seconds for every thousand tokens before the model writes a word. pi's own system prompt is well under a thousand tokens, it has only four tools (read, write, edit, bash), and it loads a skill only when it is used. Its prompt also stays the same from call to call, so the local server's prompt cache keeps working. OpenCode works too, but its system prompt and tool definitions add roughly ten thousand tokens to every session. Hermes Agent rewrites its memory and skills between sessions, which defeats the cache. If you have fast prefill (a large GPU, or a hosted endpoint), OpenCode is a fine alternative.

**1. Install pi** (see its site for the current command):

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

**2. Install the skills where pi looks.** pi reads `.pi/skills/` in the project and `~/.pi/agent/skills/` for the user. It also reads `.agents/skills/` (walking up to the repository root) and `~/.agents/skills/`. With `--target`, the `--harness` value only changes the notes printed; the copy is the same.

```bash
# project level
python skills/writing-room/scripts/wr_install.py --harness claude --target path/to/my-novel/.pi/skills

# user level
python skills/writing-room/scripts/wr_install.py --harness claude --target ~/.pi/agent/skills
```

The shell expands `~`, not the installer. In PowerShell write `$HOME/.pi/agent/skills`; in cmd write `%USERPROFILE%\.pi\agent\skills`.

If you already installed for Devin or Hermes into `.agents/skills`, pi finds that copy and you can skip this step. Do not install into both: when a skill name appears twice, pi keeps the first one it finds and warns, and you may be editing the copy it ignores. `wr_update.py --target <that folder>` and `--uninstall --target <that folder>` work as for any other install.

**3. Point pi at your local server.** Add the server to `~/.pi/agent/models.json` (`PI_CODING_AGENT_DIR` moves that folder). For LM Studio:

```json
{
  "$schema": "https://pi.dev/schemas/models.schema.json",
  "providers": {
    "lmstudio": {
      "baseUrl": "http://localhost:1234/v1",
      "api": "openai-completions",
      "apiKey": "lmstudio",
      "models": [
        { "id": "your-model-id" }
      ]
    }
  }
}
```

For Ollama, use `http://localhost:11434/v1`. The model `id` must match what the server lists, and the API key can be any value when the server does not check it. In pi, `/model` picks the model and `/thinking` sets the thinking level; `Ctrl+S` in either saves the choice as the default. See pi's models documentation for llama.cpp and for the full list of fields.

**4. Run a skill.** Start `pi` in the project and type `/skill:writing-room` (or `/skill:planner`, and so on). Smaller models often fail to load a skill from its description alone, so typing the command is more reliable than asking in plain words. Anything you type after the command is passed to the skill as your request.

**Settings that matter on a local model:**

- **Context length.** A chapter stage sends about 17–20 thousand tokens. Load the model with at least 32k context. A smaller window may be cut off silently, and the output gets worse without an error.
- **Thinking.** Reasoning models spend a long time thinking before drafting prose, and it rarely helps the prose. Set pi's thinking level to off for drafting stages. On LM Studio, reasoning is only turned off when the request sends `reasoning_effort: "none"`; check in the server log that your model honours it.
- **One stage per session.** Starting a fresh pi session for each stage keeps the prompt small, which matters more locally than with a hosted model.

Not verified yet: the steps above follow pi's documentation (checked 2026-11-03). Running the whole pipeline in pi against a local model is part of the smoke tests described below.

## Updating

When a new version is built (a new checkout or release), run **its** `wr_update.py`. It finds the installs that `wr_install.py` made, compares them with the new build, and brings them up to date:

```bash
git pull                                                  # or check out / unpack the new version
python skills/writing-room/scripts/wr_update.py --check   # which installs are out of date? (changes nothing)
python skills/writing-room/scripts/wr_update.py --dry-run # what would change
python skills/writing-room/scripts/wr_update.py           # update the project you are in
python skills/writing-room/scripts/wr_update.py --user    # also update user-level installs
python skills/writing-room/scripts/wr_update.py --project path/to/my-novel --target ~/somewhere/skills
```

What it does, for each install:

- **Replaces** skills whose content changed, **adds** skills new in the build, and **removes** skills the build no longer has (only ones the installer put there). Your own skill folders are never touched; a new skill whose name collides with one of yours is skipped and reported (`--force` replaces it).
- **Saves your edits.** If you edited an installed skill, a copy is saved to `<skills folder's parent>/.writing-room-backups/<time>/` before it is replaced (`--no-backup` to skip). Installs made before this feature cannot tell edits from originals, so everything they replace is saved.
- **Shows what changed**: the CHANGELOG entries since the version you had, when the build has a changelog.
- **Never touches your project**: worlds, stories, styles and templates stay as they are. `AGENTS.md` and `CLAUDE.md` are compared with the shipped versions and reported if they differ (yours may be customised); `--guidance` replaces them, keeping `AGENTS.md.bak`.
- **Refuses** to install an older build over a newer one (`--allow-downgrade` overrides) and to touch a project whose layout is newer than the build understands.
- **Works from an installed copy too**: `python <skills folder>/writing-room/scripts/wr_update.py --source path/to/new/skills`.

Afterwards, start a fresh agent session so it reloads the skills, and run `wr_doctor.py`. A new layout number would come with a migration (see [MIGRATING.md](MIGRATING.md)); there has been none yet.

## Removing

```bash
python skills/writing-room/scripts/wr_install.py --harness claude --project path/to/my-novel --list
python skills/writing-room/scripts/wr_install.py --harness claude --project path/to/my-novel --uninstall
```

The installer records what it installed, with a content hash of each skill folder, in `.writing-room-install.json` inside the target folder; the updater and the uninstaller use it, and only ever touch what it lists. Running `wr_install.py` again over an existing install also replaces our folders (and nothing else), but it does not remove skills a newer build dropped or save your edits, which is what `wr_update.py` is for.

## Check the installation

```bash
python <skills-folder>/writing-room/scripts/wr_doctor.py --root path/to/my-novel
```

It checks the project layout, that every skill sits next to `writing-room`, and that the project's `AGENTS.md` names an existing framework folder.

Skills write `<WR>` for the framework folder (the installed `writing-room` skill, with its scripts, templates and shared references). Models could not reliably work that folder out from the skill they were running: some read a path relative to the running skill, others relative to the project root. So `wr_install.py`, `wr_update.py` and `wr_init.py` write a "Writing Room paths" block into the project's `AGENTS.md` (which `CLAUDE.md` imports) naming `<WR>`, the conventions, the scripts and where templates come from. The path is relative to the project root when the skills are installed inside the project, absolute for a user-level install. Only that block is ever changed; the rest of your `AGENTS.md` is kept. If the install moves, or the project is opened on another machine, the doctor reports it and `python "<WR>/scripts/wr_paths.py"` rewrites the block. A project without `AGENTS.md` still works: skills then look for `writing-room` beside their own folder.

## What has and has not been verified

Verified by tests (Windows with Python 3.11, Ubuntu with Python 3.12): every install location above for every harness, copying only our folders, updates, uninstall, refusal to overwrite foreign folders, and that an installed copy runs on its own (its scripts reproduce the recorded legacy output, its cross-skill references resolve, its doctor is clean). `claude plugin validate` passes.

Not verified, because it needs the real tools and a model: that each agent actually discovers the installed skills and triggers them from their descriptions, how Devin cloud sessions run the bundled Python scripts, and Hermes Agent's handling of `AGENTS.md`. Hermes's project-level folders and its `hermes skills trust` step are taken from its official documentation and have not been run. These are the smoke tests, the last phase of the plan.

## Name clashes

The skill names are short and generic (`planner`, `reviewer`, `outliner`). If another skill with the same name is installed in a folder the same tool reads, the installer refuses to overwrite it, but the tool may still see both. Remove or rename the other one; renaming ours would break the `../writing-room/` references.
