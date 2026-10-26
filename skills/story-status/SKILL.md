---
name: story-status
description: "Show where a story stands. Use at the start of any writing session, or when the user asks about progress, what is in progress, or what to do next. Read-only dashboard of chapters complete, the chapter in progress and which reviews exist, recent timeline entries, in-flight schemes, story facts, pending payoffs and open hooks. Reports the next step in the chapter pipeline."
---

# Story Status

Your job is to read the current state of a story and present a clean, scannable dashboard. This is entirely read-only — you change nothing. Shared rules: `../writing-room/references/conventions.md`.

---

## Step 1 — Identify the Story

List files matching `stories/*/CONCEPT.md` to find all stories. Filter to those whose Status is `In Development`, `Active`, or `Complete`.

- **One qualifying story:** use it.
- **Multiple qualifying stories:** list them with their Status and ask the user to pick.
- **No qualifying stories:** report "No stories found with Status In Development, Active, or Complete."
- **Book Series:** List files matching `stories/*/Book */OUTLINE.md` to detect books. If a series is chosen, ask which book to report on (or report on all books briefly).

---

## Step 2 — Read All Inputs

Read the following files for the chosen story. Missing files are noted as "not found" in the dashboard — do not stop on a missing file.

1. `CONCEPT.md` — Status, Format, World, Logline, POV
2. `OUTLINE.md` — chapter entries (to get total chapter count and the list of chapter titles); also count `#### Payoff Annotations` bullets under entries for chapters not yet in `chapters/` (pending payoffs), and note whether a `## Unscheduled Payoff Setups` section exists and how many items it contains
3. `chapters/` — List the files to count completed chapter files
4. `current_chapter/CHAPTER_PLAN.md` — if present: chapter number and title in progress
5. `current_chapter/CONTENT.md` — check existence only (yes/no)
6. `current_chapter/current_reviews/` — List the files to list which review reports are present
7. `state/Timeline.md` — read the last 3 entries
8. `state/ACTIVE_SCHEMES.md` — count ledger rows by status (Active / Complicated / Exposed / Resolved). Ignore the `—` placeholder row if it is the only row.
9. `state/STORY_FACTS.md` — count Current / Superseded rows. Ignore the `—` placeholder row if it is the only row. Record up to 5 Current entries (ID, Category, Fact one-liner) for the dashboard.
10. `worlds/<World>/HOOKS.md` — count hooks by status (Open / In Use / Archived)

---

## Step 3 — Present the Dashboard

Output a clean, scannable status block:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Story Status — <Story Name>
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  World:    <World Name>
  Format:   <Short Story / Novelette / Book / Book Series>
  Status:   <Concept / In Development / Active / Complete>
  POV:      <POV character(s)>

  Logline:
  <Logline text, wrapped if long>

──────────────────────────────────────
  Progress
──────────────────────────────────────

  Chapters complete:  N of N
  <If OUTLINE.md has chapter titles, list remaining chapters as:>
  Next up:  Chapter N — <Title> (<Structure Stage>)

──────────────────────────────────────
  Current Chapter
──────────────────────────────────────

  <If current_chapter/ is empty:>
  Nothing in progress. Ready to plan Chapter N.

  <If CHAPTER_PLAN.md exists but no CONTENT.md:>
  Chapter N — <Title> is planned. Ready for `draft-writer`.

  <If CONTENT.md exists:>
  Chapter N — <Title> draft exists.
  Reviews present:  <list: Reviewer-Consistency ✓ / Reviewer-Character ✓ / Draft-Fixer-Log ✗>
  <If all reviews done and log present:>
  → Ready for `story-analyzer`, then `promote-chapter`.
  <If no reviews yet:>
  → Ready for `reviewer`.

──────────────────────────────────────
  Recent Timeline
──────────────────────────────────────

  <Last 3 Timeline entries, or "No entries yet." if Timeline is empty>

──────────────────────────────────────
  Active Schemes
──────────────────────────────────────

  Active: N   Complicated: N   Exposed: N   Resolved: N

  In flight:
  - [Sx] <Owner> → <Target(s)>: <Nature>   (Origin: Ch. N)
  <List each Active/Complicated row; omit Exposed/Resolved. If none: "None in flight.">

  <If any Current facts exist in STORY_FACTS.md:>
──────────────────────────────────────
  Story Facts
──────────────────────────────────────

  Current: N   Superseded: N

  - [Fy] <Category>: <Fact one-liner>
  <List up to 5 Current entries; if more, append "(+ N more)">

  <If N > 0 annotation bullets on undrafted chapters OR any unscheduled setups exist:>
──────────────────────────────────────
  Pending Payoffs
──────────────────────────────────────

  In-flight annotations:  N  (across N undrafted chapters)
  <If unscheduled setups exist:>
  Unscheduled setups:    N  ← assign a target chapter

──────────────────────────────────────
  Hooks — <World Name>
──────────────────────────────────────

  Open: N   In Use: N   Archived: N

  Open hooks:
  - <Hook title>
  - <Hook title>
  <List up to 5; if more, append "(+ N more)">

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Formatting Rules

- Keep the dashboard width consistent (around 40 characters wide for the content area).
- If a file is missing (e.g., no OUTLINE.md yet), replace that section's content with "— not yet created."
- Do not show sections that have no useful information (e.g., do not show a "Current Chapter" section if `current_chapter/` is completely empty AND nothing is planned). If `ACTIVE_SCHEMES.md` is absent or contains only the `—` placeholder row, omit the Active Schemes section entirely rather than showing zeros. If `STORY_FACTS.md` is absent or contains only the `—` placeholder row, omit the Story Facts section entirely.
- Keep Timeline entries to one line each — truncate at 100 characters if needed.
- The hooks list shows only Open hooks by title. Do not show full hook text.

**Next step:** after showing the dashboard, name the skill the pipeline points to (see the Current Chapter section), or `planner` if nothing is in progress.
