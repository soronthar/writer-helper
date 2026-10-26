# Writing Room

An agent-based framework for writing fiction, built on Claude Code subagents. Writing Room manages the full pipeline from world creation through completed chapters: world bible, story concept, outlining, chapter planning, drafting, reviewing, fixing, and recording.

Each stage is handled by a specialized agent. You stay in the author's seat — making creative decisions, approving plans, reviewing output — while the agents do the structural and mechanical work.

---

## Requirements

- [Claude Code](https://claude.ai/code) (CLI or desktop app)
- Optionally: [Obsidian](https://obsidian.md) as a knowledge management interface over the same directory

---

## Getting Started

Open Claude Code with this directory as your working directory (`Writing_Room/`). The agents and skills are immediately available.

If you are starting from scratch:

1. Run `/create-world` to build your world bible
2. Run `/create-style` to define your prose style
3. Invoke the **Story Ideator** to generate your first story concept
4. Follow the chapter loop below

---

## Workflow

### Phase 1 — World Setup *(once per world)*

| Step | What to do | Output |
|------|-----------|--------|
| 1 | `/create-world` — guided interview | `worlds/<World>/DESCRIPTION.md` + `HOOKS.md` |
| 2 | **Writing Assistant** — add characters, factions, locations, mythology | World bible files in `worlds/<World>/` |
| 3 | `/create-style` — guided interview | `writing_concepts/styles/<Style>.md` |

The world bible and style file can be built incrementally. You do not need a complete world before starting a story.

---

### Phase 2 — Story Creation *(once per story)*

| Step | Agent | Output |
|------|-------|--------|
| 4 | **Story Ideator** | `stories/<Story>/CONCEPT.md`, `state/Timeline.md` skeleton |
| 5 | **Outliner** | `stories/<Story>/OUTLINE.md` (chapter-by-chapter map) |

Both agents support **Autonomous** mode (agent drives, you approve) and **Collaborative** mode (you steer interactively).

After the Outliner runs, CONCEPT.md Status is set to `In Development`. You are ready to write.

---

### Phase 3 — Chapter Loop *(repeated for every chapter)*

```
/story-status               ← run at the start of each session to orient yourself
        |
        v
   Planner                  ← scene-by-scene breakdown of the next chapter
        |                      (CHAPTER_PLAN.md)
        v
   Draft Writer              ← prose, following the plan and style file
        |                      (current_chapter/CONTENT.md)
        v
   Reviewer                  ← consistency + character review in one pass;
        |                      outputs both Reviewer-Consistency.md and
        |                      Reviewer-Character.md to current_reviews/
        v
   Draft Fixer               ← applies reviewer corrections to CONTENT.md
        |
        v
   Story Analyzer            ← records what changed: updates state/bible/,
        |                      appends to Timeline, suggests new hooks
        v
   /promote-chapter          ← moves CONTENT.md → chapters/Chapter_NN.md
                               clears current_chapter/ for next chapter
```

Repeat from **Planner** for the next chapter.

---

### Phase 4 — World Maintenance *(as needed)*

Run the **Writing Assistant** any time to:
- Flesh out character or location stubs flagged by the Story Analyzer
- Add new world elements that emerge from the story
- Update existing elements if plot decisions require changes

Run the **World Archivist** any time to:
- Rebuild `SUMMARY.md` after editing entity files directly in Obsidian
- Add, reorder, or update entries in `WORLD_ORDER.md` outside the normal Story Ideator / Story Analyzer flow
- **Consolidate a completed story** — merge `state/bible/` changes into the master world bible, update `TIMELINE.md`, and refresh the world snapshot

---

## Agent Reference

| Agent                 | When to invoke                                                                                                                      | Key output                                                                          |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| **Writing Assistant** | Any time you need to create or update world bible elements                                                                          | World bible files in `worlds/<World>/`                                              |
| **World Archivist**   | Rebuild `SUMMARY.md` (Obsidian edits), manage `WORLD_ORDER.md`, or **consolidate a completed story** into the master world bible      | Updated `SUMMARY.md`, `WORLD_ORDER.md`, `TIMELINE.md`, snapshots, merged entities   |
| **Story Ideator**     | After the world bible has enough material to support a story                                                                        | `CONCEPT.md`                                                                        |
| **Outliner**          | After Story Ideator produces a concept (Status: Concept)                                                                            | `OUTLINE.md`                                                                        |
| **Planner**           | Once per chapter, before writing begins — writes plan directly by default; add `preview: true` to see it first                      | `current_chapter/CHAPTER_PLAN.md`                                                   |
| **Draft Writer**      | After Planner produces a chapter plan — writes prose directly by default; add `preview: true` to see the full draft first           | `current_chapter/CONTENT.md`                                                        |
| **Reviewer**          | After Draft Writer, before Draft Fixer — runs consistency and character review in a single pass                                     | `current_reviews/Reviewer-Consistency.md` + `current_reviews/Reviewer-Character.md` |
| **Draft Fixer**       | After the Reviewer has run                                                                                                          | Corrected `CONTENT.md` + fix log                                                    |
| **Story Analyzer**    | After Draft Fixer, before promoting the chapter                                                                                     | Updated `state/bible/`, Timeline entry, new hooks, world snapshot (on story complete)|

### Skill Reference

| Skill              | When to use                                                                                                                                                                   |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/create-world`    | Start a new world bible from scratch. Runs a guided interview and produces `worlds/<World>/DESCRIPTION.md` and `HOOKS.md`.                                                    |
| `/create-style`    | Create a new writing style file. Runs a guided interview and produces `writing_concepts/styles/<Style Name>.md`.                                                              |
| `/story-status`    | Display the current state of a story: chapters complete, what is in `current_chapter/`, open hooks, and recent Timeline entries. Run at the start of any session.             |
| `/promote-chapter` | Promote `current_chapter/CONTENT.md` to `chapters/Chapter_NN.md` and clear `current_chapter/`. Run after the Story Analyzer has completed. Confirms before deleting anything. |

---

## Directory Structure

```
Writing_Room/
├── .claude/
│   ├── agents/             ← Subagent definitions (invoked by name)
│   └── commands/           ← Slash command skills (/create-world, etc.)
├── templates/
│   ├── world/              ← Templates for world bible elements
│   └── story/              ← Templates for story-level documents
├── worlds/                 ← One subdirectory per world bible
│   └── <World Name>/
│       ├── DESCRIPTION.md
│       ├── HOOKS.md
│       ├── SUMMARY.md              ← 1–2 page world index; auto-maintained by Writing Assistant
│       ├── WORLD_ORDER.md          ← Chronological story order across all stories in the world
│       ├── TIMELINE.md             ← World-level event log; built during story consolidation
│       ├── characters/
│       ├── factions/
│       ├── mythology/
│       ├── points_of_interest/
│       └── snapshots/              ← World state captured after each story completes
│           ├── manifest.md         ←   Index of all snapshots
│           └── <N>/                ←   Snapshot at position N (entity files + manifest)
├── writing_concepts/       ← Story craft reference (read-only for agents)
│   ├── archetypes/
│   ├── story_structure/    ← 7 structure frameworks + Format Reference
│   ├── styles/             ← Your style files (created with /create-style)
│   └── tropes/
└── stories/
    └── <Story Name>/
        ├── CONCEPT.md
        ├── OUTLINE.md                  ← Includes World Order Position + Story before/after
        ├── chapters/                   ← Completed chapters
        ├── current_chapter/
        │   ├── CHAPTER_PLAN.md
        │   ├── CONTENT.md
        │   └── current_reviews/
        └── state/
            ├── Timeline.md             ← Chronological event log
            └── bible/                  ← Story-local world bible (diverges from worlds/ as story progresses)
```

Book Series use a nested structure under `stories/<Series Name>/Book 01 - <Title>/`.

---

## Key Design Decisions

**The world bible is the ground truth, updated deliberately.** During story production, the Story Analyzer writes only to `stories/<Story>/state/bible/` — the master `worlds/<World>/` stays clean. Once a story is complete, the World Archivist **Consolidate** operation merges those verified changes into the master world and refreshes the world snapshot. This means `worlds/<World>/` reflects the fully canon world state after every consolidated story, while in-progress stories stay isolated in `state/bible/`.

**The Planner is the creative checkpoint.** Before any prose is written, the Planner produces a scene-by-scene breakdown — every beat, every structural question answered, every subplot threaded through. This is the lowest-cost moment to redirect the story.

**Preview is opt-in, not the default.** The Planner and Draft Writer write their output directly to disk by default — no approval gate. Add `preview: true` to the prompt when you want to see the content before it is saved. The review cycle (Reviewer → Draft Fixer) is the quality gate; a manual preview doubles the token cost of every chapter without adding much protection.

**The Reviewer runs before the Story Analyzer.** It checks the draft against the *pre-chapter* world state across two passes — consistency (geography, world rules, prop continuity, character knowledge, cause-and-effect) and character (voice, personality, arc, motivation, relationships). The Story Analyzer records the *post-chapter* state only after fixes are applied. This ordering ensures errors are caught before they are enshrined in the bible.

**Both review passes run in a single agent session.** The Reviewer reads CONTENT.md, CHAPTER_PLAN.md, and the previous chapter once, then executes both passes sequentially — eliminating duplicate reads and saving significant tokens per chapter.

**Knowledge state is the most important update.** The Story Analyzer appends `Knows (as of Chapter N): <fact>` entries to character Notes after each chapter. This is what makes the consistency pass useful in chapter 10 — it can check whether a character acts on information they actually have.

**SUMMARY.md is the world index, not a replacement for entity files.** The Story Ideator and Outliner read `SUMMARY.md` first to understand the world's entity inventory, then read full entity files only for entities central to the story being developed. This reduces entity reads from 26+ per session (for a mature world) to 5–8 for typical stories. The summary is always regenerated from scratch by the Writing Assistant — never edited in place. A staleness check (file count vs. table row count) catches additions and deletions; users who edit entity files directly in Obsidian should request a regeneration from the Writing Assistant.

**The world grows alongside the story.** Hooks suggested by the Story Analyzer feed back into `HOOKS.md`. A world bible at chapter 10 is richer than at chapter 1, and that richness is available to any future story set in the same world.

**WORLD_ORDER.md is the chronological backbone.** Each world has one `WORLD_ORDER.md` recording every story and chapter in world-history order, at chapter-level granularity — which makes it possible to interleave short stories between book chapters. Concurrent stories share a Position number. Story Ideator adds a placeholder entry at concept creation; Story Analyzer updates per chapter; World Archivist handles repositioning and renumbering.

**Snapshots capture world state at each position.** When a story completes, the Story Analyzer automatically creates a snapshot at `worlds/<World>/snapshots/<N>/`. When you later write a story at position N+1 (or insert one at an earlier point), the Planner and all pipeline agents load entities from the relevant snapshot — ensuring character knowledge, location state, and faction standing are historically accurate for that moment in the world's chronology. World baseline flows through OUTLINE.md and CHAPTER_PLAN.md so every agent in the pipeline stays synchronized.

**TIMELINE.md is the consolidated world event log.** Each consolidation merges a story's `state/Timeline.md` entries into a single world-level `TIMELINE.md`, ordered by WORLD_ORDER position. Over time this becomes a complete record of every significant event across all stories in the world.

---

## Example World

`worlds/Example World/` contains a reference implementation — *Harrowmere*, a grounded low-fantasy setting — demonstrating correct template usage for all world bible element types.
