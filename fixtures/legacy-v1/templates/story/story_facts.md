# Story Facts — <Story Name>

> **What this is:** a live ledger of plot-consequential facts that cross-cut multiple entities or belong to the story's ongoing situation — quantities, forensic fingerprints, logistical specifics, and in-force commitments. Character bibles hold who a character *is*; world bibles hold world identity; this file tracks what is currently *true* about the story world in ways downstream agents must respect.
>
> **Maintained by:** Story Analyzer (updates after each chapter).
> **Read by:** Planner (first input alongside ACTIVE_SCHEMES.md), Draft Writer, Reviewer, Draft Fixer.
>
> **Status values:**
> - `Current` — the fact holds as written; prose must not contradict it.
> - `Superseded` — a later chapter changed the fact on-page; entry moved to Superseded Log with a pointer to the replacement entry.
>
> **Admission (both required):**
> 1. Plot-consequential — a contradiction would be a noticeable continuity error.
> 2. Cross-cuts entities OR belongs to the story's ongoing situation — does not belong naturally in any single character/faction/location bible file.
>
> **Scheme/fact disambiguation:** if a character is actively concealing the fact from a Target, it belongs in `ACTIVE_SCHEMES.md` under Specifics, not here. If the fact is simply true of the story world, independent of any deceiver, it belongs here.
>
> **Scope:** story-local. Never merged into `worlds/<World>/`. Fact IDs are stable across supersessions.

---

## Ledger

| ID | Category | Fact | Status | Origin | Last touched |
| -- | -------- | ---- | ------ | ------ | ------------ |
| —  | —        | —    | —      | —      | —            |

---

## Detail

<!-- One block per entry in the Ledger. Entries whose Status becomes Superseded move to the Superseded Log below. -->

### F1 — <short title>

- **Category:** <Quantity / Fingerprint / Logistics / Commitment / Other>
- **Fact:** <one-line canonical form of the fact>
- **Specifics:** <verbatim prose detail when precision matters — e.g., the exact formatting markers on the forged code>
- **Status:** Current
- **Origin:** Chapter N
- **Last touched:** Chapter N
- **Related:** <[[Name]] entities this fact concerns, if any>
- **Notes:** <optional>

---

## Superseded Log

*(Facts that changed on-page. Keep the record so downstream chapters can reason about the before/after. Example: "47 keys" at Chapter 2 → "46 keys" at Chapter 5.)*
