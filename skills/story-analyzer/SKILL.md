---
name: story-analyzer
description: "Record what happened in a chapter. Use after the draft-fixer has corrected the chapter and before promote-chapter. Reads CONTENT.md and the relevant world bible files, works out what changed for each character, location and faction (above all what each character now knows), updates the story-local state/bible/, appends to state/Timeline.md, maintains the active-schemes and story-facts registries, adds payoff annotations to OUTLINE.md, updates WORLD_ORDER.md, creates a world snapshot when a story completes, and proposes hooks for approval. Never modifies the master worlds/ bible except to append approved hooks. Preview All or Autonomous."
---

# Story Analyzer

You are recording a chapter for the Writing Room framework. You close the chapter loop: after a chapter has been written, reviewed, and fixed, you record what happened. You update the story-local world bible, append to the Timeline, and surface new narrative possibilities as hooks.

Getting this right matters more than most of your work — every future Reviewer-Consistency run, every `planner` session and every `draft-writer` chapter depends on the accuracy of the records you maintain.

---

## The State/Bible Architecture

You **never write to `worlds/<World>/`**. That directory is the pre-story world state and must stay clean.

When updating a file:
1. **Exists in `state/bible/<type>/`** → update it in place.
2. **Loaded from a snapshot or `worlds/<World>/<type>/`** → take that loaded file in full and write the updated version to `state/bible/<type>/<Name>.md`.
3. **Doesn't exist anywhere** → Auto-stub it in `state/bible/<type>/` (see Step 7).

`state/bible/` uses the same subdirectory structure as `worlds/<World>/`: `characters/`, `points_of_interest/`, `factions/`, `mythology/`.

The only exception: approved hooks are appended to `worlds/<World>/HOOKS.md` — hooks are world-level assets available to all future stories.

---

## Pipeline Position

```
draft-fixer → CONTENT.md (corrected)
→ story-analyzer   ← you
→ promote-chapter (CONTENT.md → chapters/Chapter_N.md)
→ planner (next chapter)
```

---

## Files

`<WR>` is the Writing Room framework folder. The project's `AGENTS.md` names it under "Writing Room paths"; use that path exactly as written. If `AGENTS.md` has no such block, `<WR>` is the `writing-room` folder beside this skill's own folder; it is never a folder you make up in the project. Shared rules, template lookup and the project layout: `<WR>/references/conventions.md` and `<WR>/references/layout.md`. Templates (`templates/…`) and craft files (`writing_concepts/story_structure/…`, `archetypes/…`, `tropes/…`) are the project's own copy if it has that file, otherwise the framework's under `<WR>/shared/` ("Writing Room paths" gives the exact folders). Every other path below is relative to the project root.

- Reads: `current_chapter/CONTENT.md` (the chapter to analyze), `current_chapter/CHAPTER_PLAN.md`, `CONCEPT.md`, `OUTLINE.md`, `state/Timeline.md`, `state/ACTIVE_SCHEMES.md`, `state/STORY_FACTS.md`, `state/bible/`, the world bible, `worlds/<World>/HOOKS.md` and `WORLD_ORDER.md`, and the templates `templates/world/character.md`, `point_of_interest.md`, `faction.md` for new entity stubs.
- Writes: `state/bible/{characters,points_of_interest,factions,mythology}/` (never `worlds/`), `state/Timeline.md` (append), `state/ACTIVE_SCHEMES.md` and `state/STORY_FACTS.md` (maintain), `OUTLINE.md` (additive annotations), `worlds/<World>/WORLD_ORDER.md`, `worlds/<World>/HOOKS.md` (approved hooks only), and a snapshot under `worlds/<World>/snapshots/` when a story completes.
- **Book Series** keep `OUTLINE.md`, `chapters/`, `current_chapter/` and `state/` in `stories/<Series>/Book NN - <Title>/`.

---

## Session Flow

### Step 1 — Mode Selection

If the request already names a mode, use it. Otherwise ask the user: **Preview All** or **Autonomous**?

- **Preview All** — all proposed story-state updates are presented as a numbered list before any file is touched. User can exclude specific items by number. Single approval gate. Hooks follow in Step 9.
- **Autonomous** — story-state updates (Step 8) are applied without a preview.

**Both modes:** nothing is written to `worlds/<World>/HOOKS.md` (new hooks or status changes) until the user approves it in Step 9. Autonomous covers routine record-keeping only; it never stands in for the author's approval of a hook.

---

### Step 2 — Story Identification

1. Find `stories/*/current_chapter/CONTENT.md` files. One match → use it. Multiple → ask the user to pick.
2. **Book Series:** also look for `stories/*/Book */current_chapter/CONTENT.md`.
3. Read `current_chapter/CHAPTER_PLAN.md` — extract: chapter number, working title, story name, world name, and `BASELINE_POS` from `**World baseline:**` (`Snapshot position N` → N; anything else → none).
4. Read `CONCEPT.md` — confirm world name; note key characters and central conflict.

---

### Step 3 — Existence Checks

- **CONTENT.md does not exist:** stop. Tell the user to run the `draft-writer` and `draft-fixer` skills first.
- **Already analyzed:** read `state/Timeline.md`. If an entry for this chapter number already exists, warn: *"The Timeline already has an entry for Chapter N — this skill may have already run. Analyze again and overwrite?"* Continue only on explicit confirmation.

---

### Step 4 — Read All Inputs

**4a — Two direct reads** (must come first, in order):

1. **`current_chapter/CONTENT.md`** — read in full. This is the primary analysis subject.
2. **`OUTLINE.md`** — for this chapter's goal and ending beat; confirms what was supposed to happen.

CHAPTER_PLAN.md is already in context from Step 2 — do not re-read it.

---

**4b — Load the entity files and registries.**

Before loading, extract from CONTENT.md and CHAPTER_PLAN.md (already in context):
- Every **named character** who appears in the chapter → `--char` arguments
- Every **named location** featured in the chapter → `--loc` arguments
- Every **faction** involved in a significant political or organizational event → `--faction` arguments (only if faction-level events occur; omit otherwise)

If you can run commands, run `load_bible.py` once:

```bash
python "<WR>/scripts/load_bible.py" --for story-analyzer --story "<story_path>" --char "<Name>" --loc "<Name>" --output
```

Write it as one line (see conventions, "Loading story context"). Repeat `--char`, `--loc` and `--faction` once per name. `--for story-analyzer` skips the style file and the previous chapter (the Timeline gives continuity), and adds `worlds/<World>/HOOKS.md` for deduplication before hook suggestions (Step 9). It works out the world and the baseline snapshot; the CONTEXT block at the top of the output says what it used.

The script outputs in a single result: all character files (source-priority applied), all location files, any faction files, `state/Timeline.md`, `state/ACTIVE_SCHEMES.md`, `state/STORY_FACTS.md`, and `worlds/<World>/HOOKS.md`.

- **Baseline check:** the baseline must be the same `BASELINE_POS` the planner, draft-writer and reviewer used. If the CONTEXT block's differs from CHAPTER_PLAN.md's `**World baseline:**`, run again with `--position "<BASELINE_POS>"` (or `--position none` when the plan has none). Otherwise you would write from a different file than the chapter was written against.
- ACTIVE_SCHEMES.md is loaded by default — you need the current registry to detect new entries, status changes, and last-touched updates in Step 6.
- Note each entity's source tag (`[story-local]`, `[snapshot pos N]`, `[world bible]`). Step 8 writes from exactly that file.

**Without a shell:** read each named character, location and faction file, taking the first that exists of `state/bible/<type>/<Name>.md`, `worlds/<World>/snapshots/<BASELINE_POS>/<type>/<Name>.md` (if `BASELINE_POS` is set), `worlds/<World>/<type>/<Name>.md` (types are `characters`, `points_of_interest`, `factions`); note which one you used. Then read `state/Timeline.md`, `state/ACTIVE_SCHEMES.md`, `state/STORY_FACTS.md` and `worlds/<World>/HOOKS.md`.

---

### Step 5 — Analyze the Chapter
Read CONTENT.md carefully from beginning to end. For each entity, identify what state they are in at the chapter's close, and compare it to what their current file records.

Read `references/analysis-rules.md` now and apply it. It defines what to record, and what to leave alone, for each of:

- **Characters** — location, physical condition, story state, durable relationship changes, and the highest-priority item, **knowledge state** (`Knows (as of … — Chapter N): …` lines appended to Notes).
- **Locations** and **Factions** — update only for material changes, never merely because a scene was set there or a faction was mentioned.
- **Active Schemes** — advance, complicate, expose or resolve existing entries; draft new `SN` entries; ignore trivial lies.
- **Story Facts** — admit only plot-consequential facts that cross-cut entities; mark supersessions; when in doubt, omit.
- **Outline Payoff Annotations** — additive notes on future chapters' OUTLINE.md entries, resolution notes on this chapter's own annotations, and an Unscheduled Payoff Setups holding area.
---

### Step 6 — Build the Change List

Compile every proposed update into a structured list:

- One entry per changed entity
- For each entry: entity name, which fields change, from-value → to-value
- For Knowledge State additions: the exact text to append
- One Timeline entry (always present — even if few entities changed, the Timeline always gets an entry)
- New entity flags (from Step 7)
- **ACTIVE_SCHEMES.md changes** (from Step 5 — Active Schemes subsection): new entries, status changes, last-touched updates, moves to Resolution Log
- **STORY_FACTS.md changes** (from Step 5 — Story Facts subsection): new entries, supersessions (fact changed on-page), last-touched updates
- **OUTLINE.md payoff annotations** (from Step 5 — Outline Payoff Annotations subsection): new annotation bullets for target chapters, resolution notes for any of the current chapter's own annotations that were honoured or retired, unscheduled setups for the holding area

Entities with no changes are noted as "Skipped — no material changes" and are not included in the Preview list.

---

### Step 7 — Handle New Entities

Before building the preview, identify new entities.

List:
- `state/bible/characters/`
- `worlds/<World>/characters/`
- `state/bible/points_of_interest/`
- `worlds/<World>/points_of_interest/`

For every named character or named location in the chapter that has no file in either location:

1. Read the appropriate template fresh (`templates/world/character.md` or `templates/world/point_of_interest.md`).
2. Fill every field that the chapter provides: name, any appearance details mentioned, their role in the scene, where they end up, their condition. Be faithful to the chapter — do not invent.
3. Set all unknown fields to `<placeholder>`.
4. Set `Last updated in` to `<Story Name> — Chapter N`.
   - For a Book Series: `<Series Name> — Book N — Chapter M`.
   - The story name is already in context from Step 2 (extracted from CHAPTER_PLAN.md).
5. Write the stub as a new file at `state/bible/<type>/<Name>.md`.

New entity stubs are created immediately in both modes — no preview gate. They are additions, not changes, and they always need `writing-assistant` follow-up. List them in the output under "New entity stubs."

---

### Step 8 — Apply Story-State Changes (per mode)

#### Preview All Mode

Present the full numbered change list before touching any file, in the format shown in `references/preview-format.md` (entity updates with from → to values, Knowledge State lines, the Timeline entry, Active Schemes, Outline Annotations and Story Facts changes), ending with: *"Apply updates [list]? Exclude any by number, or approve all."*

On approval, apply all confirmed updates using the write rules below.

#### Autonomous Mode

Apply all updates using the write rules below.

#### Write rules (both modes)

Read `references/write-rules.md` now and follow it. It covers, in order: **8a–8c** character, location and faction files (edit in place if the loaded copy was story-local; otherwise write the loaded snapshot or world copy, updated, into `state/bible/`); **8d** the Timeline entry (append only); **8d-bis** `ACTIVE_SCHEMES.md`; **8d-ter** `STORY_FACTS.md`; **8e** `WORLD_ORDER.md`; **8f** the story-completion check and world snapshot; **8g** OUTLINE.md payoff annotations. Untouched files are never rewritten: skip a step when it identified no changes.

These rules never touch `HOOKS.md`. That is Step 9.

---

### Step 9 — Hooks (one approval gate, both modes)

Work through 9a and 9b, then present everything in one gate (9c). Do not edit `worlds/<World>/HOOKS.md` before the gate.

#### 9a — Existing hooks now in use

`worlds/<World>/HOOKS.md` is already in context from Step 4b. For each hook with Status `Open`, look for evidence in the chapter that it is actively being used (events unfold that the hook describes, characters involved in the hook take center stage, a question the hook poses is being explored). Each one clearly in use becomes a proposed status change from `Open` to `In Use (<Story Name>)`.

#### 9b — New hooks

Review the chapter for events, revelations, or new tensions that could seed a future story or subplot.

A good hook:
- Emerges from something that actually happened or was revealed in this chapter
- Raises a question rather than answering one
- Is specific enough to spark a story idea, not generic ("the conspiracy deepens")
- Does not duplicate any existing entry in HOOKS.md

Propose 1–3 hooks. If no new hooks feel warranted, say so — do not generate weak hooks to fill the quota.

#### 9c — The gate

Present the status changes and new hooks as one numbered list, then stop and wait for the user's answer:

```
**Hook status updates (proposed):**

[1] "The Replaced Page" — `Open` → `In Use (The Tallow Ledger)`

**Suggested hooks (proposed):**

[2] "<Title>"
<Hook text — 2–4 sentences in the same style as existing HOOKS.md entries: specific, grounded in the world, pointing at an open question.>
Related: [[Name]], [[Name]]

Approve all? Exclude any by number, or approve all.
```

If there is nothing to propose, skip the gate and say so.

#### 9d — Write approved items only

After the user answers, change the Status of each approved existing hook in `worlds/<World>/HOOKS.md`, and append each approved new hook:

```markdown
### <Title>
- **Source:** `story-analyzer` — <Story Name> — Chapter N
- **Status:** `Open`
- **Hook:** <Hook text>
- **Related:** [[Name]], [[Name]]
```

Excluded items are not written. In the output, report each hook as proposed, approved or excluded; never call a hook "added" unless it was approved and written.

---

### Step 10 — Structured Output

```
### Story Analyzer — Chapter Recorded

**Story:** <Story Name>
**Book:** <Book N — Title>  *(Book Series only)*
**Chapter:** N — <Working Title>
**Mode:** <Preview All / Autonomous>

**Entities updated:** N
**New entity stubs created:** N
**Timeline entry:** appended
**Active Schemes:** <"+N new, N status change(s), N moved to Resolution Log" | "No changes">
**Story Facts:** <"+N new, N superseded" | "No changes">
**Outline Annotations:** <"N new on N chapter(s); N resolved; N unscheduled added to holding area" | "No payoff setups detected">
**WORLD_ORDER.md:** <action>
**Snapshot:** <"Created at worlds/<World>/snapshots/<N>/ — re-run after consolidation" | "Not created (story in progress)">
**Hooks:** <"N proposed, N approved and written, N excluded" | "None proposed">  (status updates and new hooks)

**Updates applied:**
- [[Name]]: <fields changed — one line per entity>

**New entity stubs (run the `writing-assistant` skill to flesh these out):**
- state/bible/<type>/<Name>.md — <one-line description from chapter>

**Approved hooks written to worlds/<World>/HOOKS.md:**
- "<Title>" — <new | Open → In Use>

**Files written or edited:**
- state/bible/characters/<Name>.md  (× N)
- state/bible/points_of_interest/<Name>.md  (× N)
- state/bible/factions/<Name>.md  (× N)
- state/Timeline.md  (appended)
- state/ACTIVE_SCHEMES.md  (updated — if any scheme changes)
- state/STORY_FACTS.md  (updated — if any fact changes)
- OUTLINE.md  (annotations appended — if any payoff setups detected)
- worlds/<World>/WORLD_ORDER.md  (updated)
- worlds/<World>/HOOKS.md  (appended, N hooks)

**Next step:** run the `promote-chapter` skill to move `current_chapter/CONTENT.md` to `chapters/Chapter_N.md` and clear `current_chapter/`. Then run the `planner` skill for the next chapter.
```

---

## Out of Scope

- Writing or fixing prose → `draft-writer` / `draft-fixer`
- Reviewing prose → **`reviewer`**
- Creating fully developed world bible entries for new entities → `writing-assistant` (`story-analyzer` creates stubs only)
- Promoting chapters → `promote-chapter` skill
- Writing to `worlds/<World>/characters/`, `points_of_interest/`, or `factions/` → `story-analyzer` never modifies the master world bible (only `HOOKS.md`)
