# Write rules (Step 9a–9g)

Used in Step 9 in both modes. Paths are relative to the project root.

**9a — Character files:**
- File exists in `state/bible/characters/`: update it in place — change the Current Status block and append to Notes, as one change covering the affected section.
- File only in `worlds/<World>/characters/`: read the full content, make all changes, and write the full updated content to `state/bible/characters/<Name>.md` (a new file; never modify the world copy).

**9b — Location files:** Same pattern, targeting `state/bible/points_of_interest/`.

**9c — Faction files:** Same pattern, targeting `state/bible/factions/`.

**9d — Timeline:**
Append the new entry to `state/Timeline.md` at the end of the Events section. Never overwrite existing entries. Format:

```
- **[Chapter N — <Working Title>]** <in-world date or period if the story has established one; otherwise omit the date portion> — <2–3 sentences: what happened, what changed, how the story moved. Include the most significant plot event, the most significant character state change, and the chapter's final beat.>
```

**9d-bis — ACTIVE_SCHEMES.md:**

Apply all scheme changes identified in Step 5:

- **New entries:** in `state/ACTIVE_SCHEMES.md`, append a new row to the Active Ledger table and a new Detail block (next available `SN` ID). Remove the `—` placeholder row on first real entry.
- **Status updates and Last touched updates:** update the affected row in the Active Ledger and the matching Detail block.
- **Moves to Resolution Log:** cut the Detail block from the Detail section, paste it under `## Resolution Log` with a leading one-line resolution summary, and update the Ledger row's Status. If the Resolution Log still contains its `*(No resolved schemes yet.)*` placeholder, remove it on the first move.

If no scheme changes were identified, skip this step — do not touch the file.

For non-trivial restructurings (many status changes at once, reordering), rewrite the whole file rather than chaining many small changes.

**9d-ter — STORY_FACTS.md:**

Apply all fact changes identified in Step 5 — Story Facts:

- **New entries:** in `state/STORY_FACTS.md`, append a new row to the Ledger table and a new Detail block (next available `Fy` ID). Remove the `—` placeholder row on first real entry.
- **Last touched updates:** update the affected row in the Ledger and the matching Detail block.
- **Supersessions:** cut the Detail block from the Detail section, paste it under `## Superseded Log` with a one-line pointer (`→ Superseded at Chapter N; see Fy for updated value.`), update the Ledger row's Status to `Superseded`, and create the replacement entry as a new `Fy` ID. If the Superseded Log still contains its `*(Facts that changed on-page...)*` placeholder text as the only content, replace it on the first real move.

If no fact changes were identified, skip this step — do not touch the file.

For non-trivial restructurings (many supersessions at once), rewrite the whole file rather than chaining many small changes.

**9e — WORLD_ORDER.md:**

1. Read `worlds/<World>/WORLD_ORDER.md`. If absent: note in structured output ("WORLD_ORDER.md not found — skipped") and skip the remaining sub-steps.

2. Check `CONCEPT.md` Format field to determine the unit type:
   - Short Story / Novelette → `Full Story`
   - Book → `Ch. N` (N = current chapter number)
   - Book Series → `Bk. N Ch. M`

3. Search the Story Order table for rows matching this story name:

   **Case A — No matching row:**
   Append a new row (insert before the closing `---`):
   `| <last_position + 1> | [[<Story>]] | <unit> | — | Complete | |`
   Note in output: "New row at position N (default). Run the `world-archivist` skill to reposition if needed."

   **Case B — Matching row with Unit = `TBD`:**
   Replace that row's Unit and Status values:
   - Short Story / Novelette: Unit → `Full Story`, Status → `Complete`
   - Book Ch. 1 / Book Series Bk. N Ch. 1: Unit → `Ch. 1` / `Bk. N Ch. 1`, Status → `In Progress`
   - All other chapters: Unit → `Ch. N` / `Bk. N Ch. M`, Status → `Complete`

   **Case C — Matching row for this exact chapter unit (e.g., `Ch. 3`):**
   Update Status to `Complete`.

   **Case D — Processing Ch. N where Ch. N-1 row exists but Ch. N row does not:**
   Insert a new row immediately below the Ch. N-1 row at position = (Ch. N-1 position) + 1.
   If that position is already occupied by another entry, shift all rows at that position and above by +1 and rewrite the full table.
   Set Status to `Complete` for the new row.

   **Default position behavior (Cases A and D):** Always default silently. Never prompt the user for a position number during `story-analyzer` runs. Flag in structured output and instruct the user to reposition via `world-archivist` if the default is wrong.

4. Update the `Last synchronized` line.

5. Add to structured output: `**WORLD_ORDER.md:** <action taken — e.g., "Ch. 3 → Complete" | "New row at position N (default)" | "TBD → Ch. 1 In Progress" | "File not found — skipped">`

---

**9f — Story Completion Check and Snapshot:**

After step 9e, determine whether the story (or book, for a series) is now fully complete:

- **Short Story / Novelette:** complete when the `Full Story` row in WORLD_ORDER.md has Status `Complete`. (Always true after 9e for a short story.)
- **Book:** complete when all chapters listed in OUTLINE.md have Status `Complete` in WORLD_ORDER.md. Read OUTLINE.md's `**Total chapters:**` field and compare against `Complete` rows.
- **Book Series:** complete when all books are marked `Complete`. Out of scope for automatic detection — skip for series.

**If the story is complete:**

1. Find this story's position in WORLD_ORDER. If you can run commands, run `query_position.py`:

   ```bash
   python "<WR>/scripts/query_position.py" \
     --world "worlds/<World Name>" \
     --story "<Story Name>" \
     --format json
   ```

   Extract `position` from the JSON output. **Without a shell:** read `worlds/<World>/WORLD_ORDER.md` and take the Position cell of this story's row.

2. Automatically create a world state snapshot. If you can run commands, run `create_snapshot.py`:

   ```bash
   python "<WR>/scripts/create_snapshot.py" \
     --world    "worlds/<World Name>" \
     --position <position>            \
     --story    "<Story Name>"        \
     --unit     "<Full Story|Ch. N|...>"
   ```

   **Without a shell:** follow `../writing-room/references/snapshot-manual.md`.

   This runs without user prompting. Note: the snapshot captures the **current world state** (before consolidation). If the user consolidates the story's state/bible/ into worlds/ later, they should re-run `create_snapshot.py` to update the snapshot.

3. Add to structured output:
   `**Snapshot:** Created at worlds/<World>/snapshots/<position>/ — world state captured after [[<Story>]] completed.`
   `  ⚠ This snapshot reflects the pre-consolidation world. After running `world-archivist` → Consolidate, re-run create_snapshot.py to update.`

**If the story is NOT yet complete** (mid-book): skip 9f entirely. No snapshot is created mid-story.

After completing a story, add this completion hint to the structured output:
```
**Story complete!** Run the `world-archivist` skill's Consolidate operation to merge state/bible/ changes into the master world bible.
Then re-run `create_snapshot.py` to update the snapshot with the consolidated world state.
```

---

**9g — OUTLINE.md Payoff Annotations:**

Apply all annotation changes identified in Step 5 — Outline Payoff Annotations. If no annotation changes were identified, skip this step — do not touch OUTLINE.md.

1. **Read `OUTLINE.md`** (the per-book file for Book Series; the story-root file otherwise). If absent, note "OUTLINE.md not found — skipping annotations" in the structured output and skip the remaining sub-steps.

2. **New annotation bullets — target chapters:** For each qualifying setup identified in Step 5, locate the target chapter's entry in OUTLINE.md.
   - If a `#### Payoff Annotations` subsection does not yet exist under that entry, create it immediately below the `outliner`'s entry text:
     ```
     #### Payoff Annotations
     _Appended by `story-analyzer` as prose commits to specifics. Additive only — the `planner` must honour these alongside the entry above._
     ```
   - Append the new bullet at the bottom of the subsection.
   - Change each target chapter's entry in place; rewrite the whole file only if several structural insertions make that simpler.

3. **Resolution notes — current chapter's own annotations:** Locate the *current chapter's* entry and its `#### Payoff Annotations` subsection (if any). For each bullet that was honoured or retired (as determined in Step 5), append the resolution note on a new indented line directly below the bullet. Do not modify bullets that remain unresolved.

4. **Unscheduled setups:** For each unscheduled setup identified in Step 5, locate the `## Unscheduled Payoff Setups` section at the top of OUTLINE.md (before the first chapter entry). If it does not exist, create it there:
   ```
   ## Unscheduled Payoff Setups
   _Setups detected by `story-analyzer` with no identifiable target chapter. Assign each to a chapter or ask the `outliner` to revise the outline._
   ```
   Append the new bullet at the bottom of the section.

5. **Cross-book setups:** if a setup's payoff clearly belongs in a different book's OUTLINE.md, do not auto-annotate. Surface it in the structured output as `⚠ Cross-book setup` with the mechanism description and the likely target book, asking the user to decide.
