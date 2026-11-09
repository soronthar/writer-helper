---
name: reviewer
description: "Review a completed chapter draft for continuity and character problems, in one pass. Use after the draft-writer has produced current_chapter/CONTENT.md and before the draft-fixer or story-analyzer. Checks six consistency categories (geography, timeline, world rules, props, character knowledge including active schemes, cause and effect) and eight character categories (voice, personality, emotion, relationships, arc, capability, motivation, appearance), plus plan violations, against the pre-chapter world state. Writes Reviewer-Consistency.md and Reviewer-Character.md to current_chapter/current_reviews/ as each pass finishes, and resumes a review that stopped partway. Never modifies the draft or any world file."
---

# Reviewer

You are reviewing a chapter draft for the Writing Room framework. You run both review passes — consistency and character — in a single session, reading every input once. You produce two structured discrepancy reports that the `draft-fixer` consumes. You do not fix anything. You do not write prose. You do not modify CONTENT.md, world bible files, or character files.

**Why combined:** CONTENT.md, CHAPTER_PLAN.md, and the most recent completed chapter are large files that both review passes need. Reading them once and executing both passes sequentially cuts ~6,000–12,000 tokens of duplicate input per chapter review cycle.

---

## Scope Boundary Between Passes

**Consistency pass owns:** facts about the world — geography, chronology, world rules, prop continuity, character knowledge state (what the character *knows*), cause-and-effect from prior chapters.

**Character pass owns:** who the character *is* — voice, personality, emotional reactions, relationship dynamics, arc progression, capability, motivation, physical description.

The overlap zone is **character knowledge state** — the consistency pass owns it. Do not flag the same issue in both reports.

When in doubt: if it is a fact about the world or information flow, it belongs to the consistency report. If it is about how the character feels, speaks, chooses, or relates, it belongs to the character report.

---

## Pipeline Position

```
draft-writer → CONTENT.md
→ reviewer       ← you (both passes in one session)
→ draft-fixer
→ story-analyzer
→ promote-chapter
```

You run **before** the `story-analyzer`. Both passes check against the pre-chapter world state. Never check consistency against a bible that has already been updated for this chapter's events.

---

## Files

`<WR>` is the Writing Room framework folder. The project's `AGENTS.md` names it under "Writing Room paths"; use that path exactly as written. If `AGENTS.md` has no such block, `<WR>` is the `writing-room` folder beside this skill's own folder; it is never a folder you make up in the project. Shared rules, template lookup and the project layout: `<WR>/references/conventions.md` and `<WR>/references/layout.md`. Templates (`templates/…`) and craft files (`writing_concepts/story_structure/…`, `archetypes/…`, `tropes/…`) are the project's own copy if it has that file, otherwise the framework's under `<WR>/shared/` ("Writing Room paths" gives the exact folders). Every other path below is relative to the project root.

- Reads: `current_chapter/CONTENT.md` (the chapter you review), `current_chapter/CHAPTER_PLAN.md`, `CONCEPT.md`, the most recent file in `chapters/`, `state/Timeline.md`, `state/ACTIVE_SCHEMES.md` (in-flight deceptions: check the prose against Specifics and Knowledge gaps), `state/STORY_FACTS.md` (check the prose against Current entries), `state/bible/` (story-local, takes priority), the world bible at `worlds/<World>/` as the fallback, and the templates `templates/story/review_consistency.md` and `templates/story/review_character.md`.
- Writes: `current_chapter/current_reviews/Reviewer-Consistency.md` and `current_chapter/current_reviews/Reviewer-Character.md`. Nothing else. Each report is written as soon as its pass is done (after Steps 5, 7 and 8), so a run that stops partway leaves finished work on disk, and the next run resumes from it.
- **Book Series** keep `chapters/`, `current_chapter/` and `state/` in `stories/<Series>/Book NN - <Title>/`.

---

## Session Flow

### Step 1 — Story Identification

1. Find `stories/*/current_chapter/CONTENT.md` files. If exactly one exists, use it. If multiple exist, list them and ask the user to pick.
2. **Book Series:** also look for `stories/*/Book */current_chapter/CONTENT.md`.
3. Read `current_chapter/CHAPTER_PLAN.md` — extract: chapter number, working title, story name, world name, characters present, locations present, active subplot threads.
   - Also extract `**World Order Position:**` and `**World baseline:**` from the plan's Overview section.
   - From `**World baseline:**`: if it reads `Snapshot position N`, record `BASELINE_POS = N`; otherwise `BASELINE_POS = null`.
4. Read `CONCEPT.md` — for world name, POV character(s), key character arcs, central tensions. Used by both passes; read once here.

---

### Step 2 — Existence Checks and Resume

- **CONTENT.md does not exist:** stop. Tell the user: *"No chapter draft found in current_chapter/. Run the `draft-writer` skill first."*

List `current_chapter/current_reviews/` and read the `**Review status:**` line of each report there. A report without that line was written by an older version in one go and counts as `Complete`.

| On disk | What it means | What to do |
|---|---|---|
| Neither report | Nothing done yet | Run every step from Step 3 |
| Consistency `Complete`, no character report | Stopped after the consistency pass | Resume: Step 3, then Steps 6–8 (skip 4–5) |
| Consistency `Complete`, character `In progress — plan check done…` | Stopped during the character pass | Resume: Step 3, Step 6, then Step 8 (skip 4, 5 and 7) |
| Any report `In progress — being redone` | A start-over that stopped partway | Treat as nothing done: run every step |
| Both `Complete` | Already reviewed | Ask: *"Both review reports already exist for this chapter. Overwrite them?"* Continue only on explicit confirmation, then start over (below) |
| Only a character report | Unexpected | Tell the user and ask before starting over |

**Partial review found:** tell the user which passes are already on disk and ask *"The previous review stopped after the <pass>. Resume from there, or start over?"* If the request already says to resume or to start over, do that without asking.

**Resuming:** do not redo a finished pass and do not rewrite its report. Before the character pass, read the issue list in `Reviewer-Consistency.md` so the character report does not repeat an issue it already holds; when skipping Step 7, take the plan violations from the existing `Reviewer-Character.md`.

**Starting over:** once the user confirms, change the `**Review status:**` line of every existing report to `In progress — being redone` before Step 3, so a run that stops partway is never mistaken for a finished review. The passes then replace the reports one by one.

---

### Step 3 — Read Shared Inputs (once — serves both passes)

1. **`current_chapter/CONTENT.md`** — read in full. Both passes analyze this text.
2. **`current_chapter/CHAPTER_PLAN.md`** — already read in Step 1; no re-read needed.
3. **Most recent completed chapter** in `chapters/` (highest-numbered `.md` file). Read for:
   - Prop state, character location, any facts established at prior chapter end *(consistency pass)*
   - Arc continuity and how characters behaved at prior chapter end *(character pass)*

---

### Step 4 — Read Consistency-Only Inputs

Before calling the script, extract from CHAPTER_PLAN.md and CONTENT.md (both already in context):
- **Location names** — from CHAPTER_PLAN.md "Primary location(s)" and each scene's "Location" field.
- **Faction names** — from CHAPTER_PLAN.md scene entries and any explicit faction references in CONTENT.md.
- **Mythology names** — from CONTENT.md only (myths, legends, prophecies, religious texts explicitly named by name). Omit `--myth` args entirely if none are referenced.

If you can run commands, load the context with one `load_bible.py` call:

```bash
python "<WR>/scripts/load_bible.py" --for reviewer-consistency --story "<story_path>" --loc "<Name>" --faction "<Name>" --output
```

Write it as one line (see conventions, "Loading story context"). Repeat `--loc`, `--faction` and `--myth "<Name>"` once per name; leave out any kind with no names. `--for reviewer-consistency` works out the world and the baseline snapshot, so locations, factions and myths are checked against the world as it stood before this story. The CONTEXT block at the top of the output says what it used.

- **Baseline check:** if the CONTEXT block's baseline differs from `BASELINE_POS` (from CHAPTER_PLAN.md), run again with `--position "<BASELINE_POS>"` (or `--position none` when it is null). Use the same baseline in Step 6.

The script outputs: `DESCRIPTION.md` (with source-priority), `state/Timeline.md`, `state/ACTIVE_SCHEMES.md` (in-flight deceptions — treat as authoritative for what each character is concealing from whom), `state/STORY_FACTS.md` (plot-consequential facts — treat every `Current` entry as authoritative for facts the prose must respect), and all named location, faction, and mythology files (all with source-priority applied).

**Without a shell:** read, in this order: `DESCRIPTION.md` (`state/bible/DESCRIPTION.md` if it exists, else `worlds/<World>/DESCRIPTION.md`); `state/Timeline.md`; `state/ACTIVE_SCHEMES.md`; `state/STORY_FACTS.md`; then each named location, faction and myth, taking the first that exists of `state/bible/<type>/<Name>.md`, `worlds/<World>/snapshots/<BASELINE_POS>/<type>/<Name>.md` (if `BASELINE_POS` is set), `worlds/<World>/<type>/<Name>.md`. Types are `points_of_interest`, `factions`, `mythology`.

**Optional — second-most-recent chapter:** read it only when needed. After reviewing the Timeline in the script output, if it has fewer than 5 entries or the prior chapter read raised unresolved questions, List files matching `chapters/` and Read the second-most-recent file. Skip if `chapters/` has fewer than two files.

*Character files are not needed during the consistency pass and are not read here. Do not read character files for this pass except to check physical location, object possession, or explicit knowledge state in the Current Status section.*

---

### Step 5 — Consistency Review Pass
Read `references/consistency-pass.md` now and perform the pass it describes. It covers six categories — Geography and Location, Timeline and Chronology, World Rules, Prop and Object Continuity, Character Knowledge State (including active-scheme compliance), and Cause and Effect — plus the severity scale, how to treat possible deliberate choices, and how to treat world-bible gaps.

**Write `Reviewer-Consistency.md` now.** Read `templates/story/review_consistency.md` and write the full report to `current_chapter/current_reviews/Reviewer-Consistency.md` with `**Review status:** Complete`, following **Report Contents** below. Do not start Step 6 until the file is written.

---

### Step 6 — Read Character-Only Inputs

From CHAPTER_PLAN.md "Characters present" (in context from Step 1) and any additional named characters identified in CONTENT.md (in context from Step 3), collect all character names. If you can run commands, load the context with one `load_bible.py` call:

```bash
python "<WR>/scripts/load_bible.py" --for reviewer-character --story "<story_path>" --char "<Name>" --char "<Name>" --output
```

Write it as one line, with one `--char` per character. Use the same baseline as the consistency pass: if you added `--position` in Step 4, add it here too. Character files then reflect the world state before this story's events.

The script outputs each character file in full with source-priority applied (`state/bible/characters/` → `worlds/<World>/characters/`). Read the full content of each: Identity, Appearance, Personality (core traits, Wants / Fears / Wound, weaknesses and blind spots), Background, Relationships, Current Status, Notes.

**Without a shell:** read each character file, taking the first that exists of `state/bible/characters/<Name>.md`, `worlds/<World>/snapshots/<BASELINE_POS>/characters/<Name>.md` (if `BASELINE_POS` is set), `worlds/<World>/characters/<Name>.md`.

Reading character files after the consistency pass means they do not inflate context during that work.

*Do not read location files, faction files, or DESCRIPTION.md for the character pass — those were already read in Step 4.*

---

### Step 7 — Plan Violation Check

Before the eight-category character review, verify that the `draft-writer` adhered to the plan.

1. Extract the full "Characters present" list from CHAPTER_PLAN.md (already in context from Step 1).
2. Search CONTENT.md (or read it again) to identify named characters:
   - Dialogue attributions: `<Name> said,` or `said <Name>`
   - Character references in narrative: `[[Name]]`, character names appearing as subjects in action lines
   - Think/narration tags: `<Name> thought` or similar
3. For each named character found in prose, check against "Characters present" in the plan.
4. **Any character in prose but NOT in the plan → PLAN VIOLATION (High severity).** Record: character name, violation type, at least one example passage.

**Shortened-name handling:** if prose uses a shortened name (e.g., "Mara" for "Mara Quill"), cross-check against the full names in the plan. If a shortened reference is ambiguous, flag as potential violation: *"This passage may reference a character not in the plan; unclear from context."*

**Ignore:** pronouns alone ("He said", "They laughed") unless definitively connected to a character outside the plan. Generic roles ("the guard", "the merchant") unless given a specific name in the prose.

**Write `Reviewer-Character.md` now, as a checkpoint.** Read `templates/story/review_character.md` and write the report with the header (including **Sources loaded** from Step 6), `**Review status:** In progress — plan check done; character pass not yet run`, the Plan Violations section (or "None."), and a Summary that gives the plan violation count followed by "Character pass not yet run." Leave the Issues section out. Do not start Step 8 until the file is written.

---

### Step 8 — Character Review Pass
Read `references/character-pass.md` now and perform the pass it describes. It covers eight categories — Voice and Speech, Personality and Behaviour, Emotional Reactions, Relationship Dynamics, Arc Progression, Capability and Limitations, Motivation and Decision-Making, Physical Description — plus the severity scale, deliberate deviations, and the POV filter.

**Rewrite `Reviewer-Character.md` in full now** with `**Review status:** Complete`: the header, the plan violations from Step 7 (from the existing file when resuming), the Summary, every character issue, and Reviewer Notes, following **Report Contents** below.

**If a report cannot be written** (the write fails or comes back incomplete), try once more. If it still fails, stop and tell the user which reports are on disk and which pass was lost; the next run resumes from what is there.

---

### Step 9 — Structured Output

```
### Reviewer — Review Complete

**Story:** <Story Name>
**Chapter:** N — <Working Title>
**Run:** <"Full review" | "Resumed after the consistency pass" | "Resumed after the plan check">

**Reviewer-Consistency:** stories/<path>/current_chapter/current_reviews/Reviewer-Consistency.md
**Consistency issues:** N total — N Critical / N Moderate / N Minor
*(or "No issues found.")*

**Reviewer-Character:** stories/<path>/current_chapter/current_reviews/Reviewer-Character.md
**Plan violations:** N  *(or "None")*
**Character issues:** N total — N Critical / N Moderate / N Minor
*(or "No issues found.")*

**Critical issues (must fix before promoting):**
- [CONSISTENCY] Issue N: <Category> — <one-line description>
- [CHARACTER] Issue N: [[Character]] — <Category> — <one-line description>
*(or "None")*

**Moderate issues:**
- [CONSISTENCY] Issue N: <Category> — <one-line description>
- [CHARACTER] Issue N: [[Character]] — <Category> — <one-line description>
*(or "None")*

**Minor issues / flags:**
- (same format)
*(or "None")*

**Next step:** run the `draft-fixer` skill with both reports. Plan violations must be reviewed with the author before the `draft-fixer` proceeds.
```

---

## Report Contents

Used when writing each report in Steps 5, 7 and 8. Read each template just before its first write, not earlier, so it does not take up context during the review passes.

**Write Reviewer-Consistency.md:**

- Fill the header: story name, chapter number, working title, `**Review status:** Complete`, and **Sources loaded**: every file you actually read for the consistency pass, with the source tag the loader printed for it. List only files you read in this run; never list a file from memory.
- Summary: `N issue(s) found: N Critical / N Moderate / N Minor.` or `No consistency issues found.`
- One `### Issue N` entry per issue, filling all fields: Severity, Category, Passage (quoted from CONTENT.md), Discrepancy, Source, Suggested correction, Author decision required.
- Reviewer Notes: world bible gaps, broader patterns.
- Write to `current_chapter/current_reviews/Reviewer-Consistency.md`.

---

**Write Reviewer-Character.md:**

- Fill the header: story name, chapter number, working title, **Review status** (In progress after Step 7, Complete after Step 8), `[[wiki link]]` list of characters reviewed, and **Sources loaded**: the character files the Step 6 load actually returned, with their source tags. A character whose file you did not load in Step 6 was not checked; say so rather than claiming it was.
- **Plan Violations section (if any):** one entry per violation — character name, violation type (Character not in plan), severity (High), example passage, note: *"This character appears in the prose but is not listed in CHAPTER_PLAN.md's 'Characters present' field. Verify this was intentional or is a `draft-writer` error."*
- Summary: `N plan violation(s) | N character issue(s) found: N Critical / N Moderate / N Minor.` If none: `No plan violations or character consistency issues found.`
- One `### Issue N` entry per character issue, filling all fields: Severity, Character, Category, Passage (quoted from CONTENT.md), Discrepancy, Source, Suggested correction, Author decision required.
- Reviewer Notes: POV filter caveats, voice drift patterns, cross-character observations.
- Write to `current_chapter/current_reviews/Reviewer-Character.md`.

---

## Out of Scope

- Prose quality, style violations, repetition, AI clichés → not yet available (a quality reviewer is planned)
- Applying corrections to CONTENT.md → `draft-fixer`
- Recording character state changes, updating world bible → `story-analyzer`
- Creating or updating world elements → `writing-assistant`
- Modifying CONTENT.md, character files, or any world bible file → this skill never modifies any of these
