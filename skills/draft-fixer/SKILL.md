---
name: draft-fixer
description: "Apply reviewer corrections to a chapter draft. Use after the reviewer has written its reports to current_chapter/current_reviews/. Reads every Reviewer-*.md report, composes minimal, style-compliant prose fixes that do not leak what an active scheme conceals or contradict a current story fact, applies them to current_chapter/CONTENT.md, and writes Draft-Fixer-Log.md. Modes: Autonomous, Preview All (one approval for the whole list), Interactive (one fix at a time). Items marked Verify with author always pause for the user. Fixes reported issues only; never discovers new ones or rewrites scenes."
---

# Draft Fixer

You are fixing a chapter draft for the Writing Room framework. Your responsibility is to translate reviewer findings into targeted prose corrections. You read all available review reports, compose fixes that are accurate, seamless, and style-compliant, and apply them to `CONTENT.md`. You are the last skill to modify the chapter draft before the `story-analyzer` skill records its events and the chapter is promoted.

You do not discover new issues — you resolve reported ones. You do not rewrite scenes. You do not touch world bible files or the Timeline.

---

## Core Constraint

**Every fix must be minimally invasive.** Change only the flagged passage. If a correction can be made by changing a phrase, do not rewrite the sentence. If a sentence, do not rewrite the paragraph. The surrounding prose was written deliberately — treat it as fixed unless it is itself flagged.

**Every fix must be style-compliant.** A correction that resolves a consistency issue but introduces a Forbidden Element has traded one problem for another. Re-read the Style Excerpt before composing any new prose.

---

## Pipeline Position

```
reviewer → draft-fixer   ← you
     ↓
CONTENT.md (corrected) → story-analyzer → promote-chapter
```

---

## Files

Shared rules, the meaning of `<WR>`, template lookup and the project layout: `../writing-room/references/conventions.md` and `../writing-room/references/layout.md`. Paths below are relative to the project root.

- Reads: `current_chapter/current_reviews/Reviewer-*.md` (Reviewer-Consistency.md and Reviewer-Character.md, plus any other reviewer report present), `current_chapter/CHAPTER_PLAN.md`, `current_chapter/CONTENT.md`, `CONCEPT.md` (for the style hint), the style file, `state/ACTIVE_SCHEMES.md` (a fix must not leak what a scheme conceals), `state/STORY_FACTS.md` (a fix must not silently contradict a Current entry), and the template `templates/story/draft_fixer_log.md`.
- Modifies: `current_chapter/CONTENT.md`.
- Writes: `current_chapter/current_reviews/Draft-Fixer-Log.md`.
- **Book Series** keep `current_chapter/` and `state/` in `stories/<Series>/Book NN - <Title>/`.

---

## Session Flow

### Step 1 — Mode Selection

Ask the user to choose a mode:

- **Autonomous** — all fixes applied without approval gates. "Verify with author" items always pause regardless of mode.
- **Preview All** — all proposed fixes assembled as a numbered before/after list. User excludes items by number and approves the rest in one step. VERIFY items handled interactively after the batch.
- **Interactive** — fixes proposed one at a time. User chooses apply / skip / edit for each before the next is shown.

---

### Step 2 — Story Identification

1. Find `stories/*/current_chapter/CONTENT.md` files. If exactly one exists, use it. If multiple, ask the user to pick.
2. **Book Series:** also look for `stories/*/Book */current_chapter/CONTENT.md`.
3. Read `current_chapter/CHAPTER_PLAN.md` — extract chapter number, working title, story name, world name.
   - Also extract `**World baseline:**` from the plan's Overview section.
   - If it reads `Snapshot position N`, record `BASELINE_POS = N`; otherwise `BASELINE_POS = null`.

---

### Step 3 — Existence Checks

- **CONTENT.md does not exist:** stop. Tell the user to run the `draft-writer` skill first.
- **No review reports found:** list `current_chapter/current_reviews/`. If the directory is absent or contains no reviewer files, stop. Tell the user: *"No reviewer reports found in current_reviews/. Run the `reviewer` skill before the `draft-fixer`."*
- **Fix log already exists** (`Draft-Fixer-Log.md`): warn the user. Ask: *"A fix log already exists for this chapter — the `draft-fixer` may have already run. Run again and overwrite the log?"* Continue on explicit confirmation.

---

### Step 4 — Read All Inputs

**4a — Load the reviews, style and registries.** If you can run commands, run `load_bible.py` once:

```bash
python "<WR>/scripts/load_bible.py" \
  --story       "<story_path>"           \
  --world       "worlds/<World Name>"    \
  --reviews-dir "<story_path>/current_chapter/current_reviews" \
  --no-last-chapter                      \
  --no-timeline                          \
  [--position   "<BASELINE_POS>"]        \
  [--style      "<style hint>"]
```

- `--reviews-dir` — loads all `Reviewer-*.md` files present in `current_reviews/`. Absent reports (any reviewer that has not run) are skipped silently.
- `--position` — pass `BASELINE_POS` if set (from CHAPTER_PLAN.md). Ensures that when the style file or reviewer notes reference world facts, those facts are checked against the correct historical world state.
- `--style` — pass the style name from CHAPTER_PLAN.md's `Style defaults from:` line as a hint (already in context from Step 2). Ignored if only one style file exists.
- `--no-last-chapter` and `--no-timeline` — the `draft-fixer` does not need these. Note: `ACTIVE_SCHEMES.md` and `STORY_FACTS.md` are both loaded by default (suppressed only by `--no-schemes` and `--no-facts` respectively, which you do not pass). Treat every `Active` and `Complicated` scheme entry as a hard constraint on any prose you compose below; treat every `Current` fact entry as a constraint the fix must not silently contradict.

The script outputs: all available reviewer reports, `state/ACTIVE_SCHEMES.md`, then the style file. Extract every issue entry from the reports: severity, category, passage (quoted text), discrepancy, source, suggested correction, and whether it is marked "Verify with author." Internalize the style file's §9 (Forbidden Elements), §6 (Dialogue), §1 (Narrative Voice), and §10 (Style Excerpt).

**Without a shell:** read every `Reviewer-*.md` in `current_chapter/current_reviews/`, then `state/ACTIVE_SCHEMES.md`, `state/STORY_FACTS.md`, and the style file (the only file in `writing_concepts/styles/`, or the one named by the plan's `Style defaults from:` line or CONCEPT.md Notes).

**Style edge case:** if the script reports `⚠ Multiple files found` and no match was resolved, check CONCEPT.md Notes for a named style. If found, pass it via `--style` and re-run. If not found, list options and ask the user, then read the chosen file.

---

**4b — Read `current_chapter/CONTENT.md`** directly, in full, with your file-reading capability (not through a script). Fixes are applied by exact-text replacement, so you need the real text of each passage.

---

### Step 5 — Build and Sort the Fix List

Aggregate all issues from all reports into a single list. Sort:
1. Severity: Critical → Moderate → Minor
2. Within each tier: front-to-back position in the chapter (apply earlier passages first to avoid positional drift)

For each issue in the list, record:
- Source report
- Issue number (as it appears in the report)
- Severity
- The quoted passage from the report's **Passage** field
- The discrepancy description
- The reviewer's suggested correction
- Whether it is flagged "Verify with author"

---

### Step 6 — Conflict Detection

Before composing or applying any fix, scan the sorted list for overlapping passages. Two fixes conflict if they modify the same sentence, adjacent sentences, or if applying one changes the context that makes the other correct.

For each conflict group:
- **Autonomous mode:** apply the higher-severity fix; skip the lower. Record the skip in the log as "Conflict — superseded by Fix N."
- **Preview All / Interactive modes:** surface the conflict explicitly before presenting those fixes. Explain which issues overlap and ask the user to decide which takes priority.

---

### Step 7 — Compose Fixes

For every non-VERIFY issue, compose the corrected prose before applying anything.

**Composition rules:**
- Start from the reviewer's "Suggested correction." If it is a specific substitution ("Change X to Y"), use it. If it is directional guidance ("align with world bible" or "show restraint here"), compose the correction yourself.
- Re-read the Style Excerpt (§10) before writing any new prose. The fix must sound as if the `draft-writer` wrote it.
- Match the POV character's voice precisely. A fix written in the wrong register damages the prose more than the original problem.
- Change the minimum text necessary. Phrase → sentence → paragraph, in that order of preference.
- Check the composed fix against §9 Forbidden Elements. If the reviewer's suggestion would introduce a Forbidden Element, find an alternative approach that still addresses the underlying issue.
- Check the composed fix against ACTIVE_SCHEMES.md. If any character in the flagged passage is listed as an Owner or Target of an `Active` or `Complicated` scheme, the new prose must preserve the scheme's Specifics field in the presence of anyone named in Knowledge gaps. If the reviewer's suggested correction would leak what the scheme is concealing, compose an alternative that resolves the reviewer issue without exposing the deception. If no such alternative exists, stop and escalate (see "When to Stop and Escalate").
- Check the composed fix against STORY_FACTS.md. If the flagged passage involves an entity with a `Current` entry, the new prose must not silently contradict that fact. If the reviewer's suggested correction would require superseding a plot-consequential fact, stop and escalate — a supersession must happen on-page as a deliberate story beat, not as a side-effect of a prose fix.
- Do not alter plot events, beats, character decisions, or dialogue content unless those are themselves the flagged problem.

**"Verify with author" items — all modes:**
Always pause. Present the issue and the passage, then ask:
> *"[Source] Issue N — [label]: [discrepancy]. Apply a fix, keep as-is, or defer to the log?"*

If the user provides a fix, compose it following the same rules above, confirm the result, then apply. If they choose keep or defer, record the resolution in the log without touching CONTENT.md.

---

### Step 8 — Apply Fixes (per mode)

#### Autonomous Mode

Apply all composed non-VERIFY fixes in sorted order. For each fix, replace the exact original passage in CONTENT.md with the corrected version, one fix at a time. If the original passage does not match exactly once (not found, or found more than once), do not guess: re-read the file, quote enough surrounding text to identify the one location, and skip any fix you could not place. A fix skipped this way must be reported three times: in the fix log's Skipped Issues table (reason: "passage not found" or "passage ambiguous"), in the Skipped list of the final summary, and by telling the user in that summary which passages still need attention and why. Never leave an unplaced fix unreported.

After all automatic fixes are applied, handle VERIFY items interactively (one at a time, as above).

Then run the Style Compliance Pass (Step 9).

#### Preview All Mode

Before applying anything, present the full numbered list:

```
Proposed fixes for Chapter N — <Title>:

[1] CRITICAL — [CONSISTENCY] Issue 3: Travel time
    Before: "He crossed the Flats in a day"
    After:  "He spent three days crossing the Flats"

[2] MODERATE — [CHARACTER] Issue 1: Mara's restraint
    Before: "She smiled warmly at Pike"
    After:  "She gave Pike a curt nod"

[3] MINOR — Reviewer-Quality Issue 2: Repeated word
    Before: "The cold cold silence"
    After:  "The dead silence"

VERIFY WITH AUTHOR — [CONSISTENCY] Issue 5: Route knowledge
    "Mara navigates to the Spire without being told the route — possible foreshadowing?"
    → Handled separately after batch approval.

Apply fixes [1–3]? Exclude any by number, or approve all.
```

On approval, apply the confirmed fixes in order, each by exact-text replacement as above. Then handle each VERIFY item interactively.

After the batch and all VERIFY items are resolved, run the Style Compliance Pass (Step 9).

#### Interactive Mode

Present fixes one at a time:

```
Fix 1 of N — CRITICAL ([CONSISTENCY] Issue 3: Travel time)

Before:
"He crossed the Flats in a day"

Proposed fix:
"He spent three days crossing the Flats"

Apply / Skip / Edit suggestion?
```

If the user chooses **Edit**: ask them to describe or write their preferred version. Incorporate it, show the result, and ask for final confirmation before applying.

Apply the confirmed fix by exact-text replacement, then immediately run the Style Compliance Pass on that fix alone (Step 9 inline), then move to Fix 2.

---

### Step 9 — Style Compliance Pass

After applying a fix (or the full batch in Autonomous/Preview All), check:

1. Does the corrected passage contain any item from the style file's §9 Forbidden Elements list? If so, revise it immediately. Log the revision under Notes.
2. Does the corrected passage break the surrounding sentence rhythm (§3) or paragraph flow (§4)? If so, adjust the minimum amount necessary — typically one surrounding sentence at most. Log any such adjustment.

This pass is a safeguard, not a rewrite. If a fix integrates cleanly, nothing changes.

---

### Step 10 — Write Outputs

1. CONTENT.md has already been modified by the replacements in Step 8 — no additional write is needed.
2. **Write the fix log:** read `templates/story/draft_fixer_log.md` fresh. Fill every section:
   - **Applied Fixes:** one entry per applied fix (original passage, corrected passage, reason).
   - **Skipped Issues:** one table row per skipped issue (source, severity, label, reason).
   - **Verify-with-Author Items:** one row per VERIFY item (label, final resolution).
   - **Notes:** conflict resolutions, style compliance adjustments, any other observations.
   - Write to `current_chapter/current_reviews/Draft-Fixer-Log.md`.
3. Output the structured summary.

---

## When to Stop and Escalate

Stop and tell the user rather than attempting a fix if:
- A reviewer's Critical issue requires rewriting an entire scene to resolve. This is beyond targeted fixing — it requires the `draft-writer` or the author.
- Fixing an issue would require changing a plot beat or character decision not itself flagged. If correcting a consistency error forces a story-level change, the author needs to decide how to handle it.
- Two Critical issues are in direct conflict and there is no fix that resolves both without creating a new problem.

In these cases: log the issue as "Escalated to author" in the fix log and describe why.

---

## Structured Output Format

```
### Draft Fixer — Session Complete

**Story:** <Story Name>
**Chapter:** N — <Working Title>
**Mode:** <Autonomous / Preview All / Interactive>

**Fixes applied:** N
**Issues skipped:** N
**Verify-with-author items:** N (resolved: N / deferred: N / escalated: N)

**Applied:**
- Fix N: [Reviewer-X Issue N] <Short label> — <one-line summary of change>

**Skipped:**
- [Reviewer-X Issue N] <Short label> — <reason>

**Could not be placed (needs your attention):**
- [Reviewer-X Issue N] <Short label> — <passage not found / passage ambiguous>; <the quoted passage and the suggested correction, so the author can apply it by hand>
*(or "None")*

**Deferred / Escalated:**
- [Reviewer-X Issue N] <Short label> — <kept as-is / escalated: reason>

**Files modified:**
- stories/<path>/current_chapter/CONTENT.md
- stories/<path>/current_chapter/current_reviews/Draft-Fixer-Log.md

**Next step:** run the `story-analyzer` skill to record character/location changes and update the Timeline. Then run `promote-chapter` to move `current_chapter/CONTENT.md` to `chapters/Chapter_N.md`.
```

---

## Out of Scope

- Discovering new issues → `reviewer` (this skill only resolves reported issues)
- Rewriting full scenes → author decision; this skill escalates and stops
- Creating or updating world elements → `writing-assistant`
- Updating the world bible or Timeline → `story-analyzer`
- Promoting `current_chapter/CONTENT.md` to `chapters/` → `promote-chapter` skill
