# Consolidate a completed story (Steps 3.1–3.10)

Used by Operation 3. Paths are relative to the project root. Never skip the approval gate in Step 3.3.

#### Step 3.1 — Story Selection and Validation

1. Ask: *"Which story to consolidate?"* List stories found in `stories/` via List files.
2. Read `stories/<Story>/CONCEPT.md` — extract story name, world name, format.
3. Verify the story is in WORLD_ORDER and check its status. If you can run commands, run `query_position.py`:

   ```bash
   python "<WR>/scripts/query_position.py" \
     --world "worlds/<World Name>" \
     --story "<Story Name>" \
     --format json
   ```

   **Without a shell:** read `worlds/<World>/WORLD_ORDER.md` and find the story's row; `position` and `status` are its Position and Status cells, and no row is the same as `"found": false`.

   - If `"found": false` → warn: *"Story not found in WORLD_ORDER.md. Has the `story-analyzer` run for all chapters?"* Stop.
   - If `status` is not `Complete` → warn: *"Story is not marked Complete in WORLD_ORDER.md. Consolidate only after all chapters are analyzed."* Ask the user whether to proceed anyway.
   - Record `position` for the snapshot step.

4. Check that `stories/<Story>/state/bible/` exists and has at least one file. If empty, warn: *"state/bible/ is empty — nothing to consolidate. Has the `story-analyzer` run?"*

---

#### Step 3.2 — Conflict Detection

Before merging anything, identify conflicts.

A **conflict** exists when:
- An entity file exists in BOTH `worlds/<World>/<type>/<Name>.md` AND `stories/<Story>/state/bible/<type>/<Name>.md`
- AND the world version was last modified AFTER the story started (i.e., another story or a manual edit changed the world version while this story was in production)

To detect this: for each entity in `state/bible/`, read both the state/bible version and the worlds/ version. Compare their `Last updated in:` fields. If the worlds/ version references a different story than this one, it was updated externally — flag as a conflict.

**Build two lists:**

- **Clean merges:** entity exists only in state/bible/ (new entity created during this story), or entity exists in worlds/ but was last updated by this story only.
- **Conflicts:** entity exists in both, and worlds/ version has changes from a different source.

---

#### Step 3.3 — Present Consolidation Plan

Present the full plan to the user before touching any file:

```
Consolidation Plan — [[<Story Name>]] → worlds/<World Name>/

Clean merges (N):
[1] characters/Mara Quill
    Changes: Current Status (location, knowledge state), Notes (3 new "Knows" entries)
[2] factions/Harbor Guild
    Changes: Current Status (internal condition)
[3] points_of_interest/The Archive
    NEW entity — created during this story (stub from `story-analyzer`)
    Note: run the `writing-assistant` skill to flesh out after consolidation.

Conflicts requiring your decision (N):
[4] characters/Doran Pike
    worlds/ version:  Last updated in "The Tallow Ledger — Chapter 2" (a different story)
    state/bible/ version: Last updated in "The Tallow Ledger — Chapter 3" (this story)
    → Choose: (a) Keep worlds/ version  (b) Use state/bible/ version  (c) Review both and edit manually

Timeline: state/Timeline.md → TIMELINE.md (N entries to insert at position <P>)

Approve all clean merges? Conflicts handled interactively.
```

Wait for user approval before proceeding.

---

#### Step 3.4 — Apply Clean Merges

For each entity in the clean merge list:

- **Entity exists in worlds/ (updating):** Read `state/bible/<type>/<Name>.md`. Write its full content to `worlds/<World>/<type>/<Name>.md` as a complete file. This overwrites the world version with the story-local version.
- **New entity (not in worlds/):** Write `state/bible/<type>/<Name>.md` content to `worlds/<World>/<type>/<Name>.md` as a complete file.

Always write the full file rather than patching it, since the world version may have different sections than the state/bible version.

---

#### Step 3.5 — Resolve Conflicts Interactively

For each conflicting entity, present both versions side by side (or a summary of their differences in the key fields: Current Status, Notes). Ask:

> *"Conflict: characters/Doran Pike*
> *  worlds/ version: [Current Status / key Notes summary]*
> *  state/bible/ version: [Current Status / key Notes summary]*
> *  (a) Keep worlds/ version unchanged  (b) Use state/bible/ version  (c) I'll edit manually — skip for now"*

- **(a):** Skip this entity — do not overwrite worlds/.
- **(b):** Write `state/bible/<type>/<Name>.md` content to `worlds/<World>/<type>/<Name>.md`.
- **(c):** Skip and note in the consolidation report for manual follow-up.

---

#### Step 3.6 — Consolidate Timeline

1. Check if `worlds/<World>/TIMELINE.md` exists.
   - If absent: Read `templates/world/timeline.md` fresh. Replace `<World Name>`. Set `Last synchronized`. Write to `worlds/<World>/TIMELINE.md`.

2. Read `stories/<Story>/state/Timeline.md` in full. Extract all entries.

3. Run `query_position.py` (already done in Step 3.1) — use the story's `position` to determine where these entries belong in the world timeline.

4. Format entries for the world timeline:
   - Story-local format: `- **[Chapter N — Title]** <date> — <event>`
   - World timeline format: `- **[Position <P>: Chapter N — Title]** <date> — <event>`
   - Group entries under: `### [[<Story Name>]] (Position <P>)`

5. Find the correct insertion point in `worlds/<World>/TIMELINE.md` (by position number — insert in ascending order). Insert the story's section into `TIMELINE.md` in the right place.

---

#### Step 3.6b — Active Schemes Audit

Read `stories/<Story>/state/ACTIVE_SCHEMES.md`. Scan the Active Ledger table.

- If every row has status `Resolved` or `Exposed`, or the ledger is empty / shows only the `—` placeholder row: continue.
- If any row is still `Active` or `Complicated`: surface them. A story closing with live deceptions means either (a) the story genuinely ends with the deception unresolved on-page (valid — but the world baseline for position N+1 must preserve this fact), or (b) a scheme was never promoted to Resolved/Exposed in analysis (a bug).

Present the list:

```
Active Schemes at story close:

[S2] Owner: [[Hesk]] — Target(s): [[Marelle]]
     Status: Active — Nature: conceals origin of the Archive key
     Last touched: Chapter 7 (final)

Choose: (a) Persist — story ends with this live; keep in world TIMELINE as an open thread
        (b) Resolve now — mark Exposed/Resolved in state/ACTIVE_SCHEMES.md before archiving
        (c) Escalate — stop consolidation; author should run the `story-analyzer` over the
             final chapter again, or decide what happened off-page
```

For **(a) Persist**: append a one-line note under the story's TIMELINE section (inserted in Step 3.6) — `- **[Position <P>: open thread]** <date or "story close"> — <Owner>'s deception of <Target> (<Nature>) remains unresolved at story end.` This keeps the unresolved scheme discoverable to future-story planning without silently vaporizing it when the story folder is archived.

For **(b) Resolve now**: stop consolidation. Tell the user to run the `story-analyzer` against the appropriate chapter to transition the scheme, then run Consolidate again.

For **(c) Escalate**: stop consolidation. Report the finding; do not proceed.

`ACTIVE_SCHEMES.md` itself is never merged into `worlds/<World>/` — it is a story-scoped working document. It stays with the story directory (which is not deleted by consolidation).

`STORY_FACTS.md` is similarly story-scoped and never merged into `worlds/<World>/`. Plot-consequential facts are already reflected in character and location entity files (which are merged in Steps 3.4–3.5). There is no lifecycle audit for STORY_FACTS.md entries, and Current facts are not automatically persisted to the world TIMELINE — they are implied by the merged entity state.

---

#### Step 3.7 — Consolidate HOOKS.md

`HOOKS.md` always lives only in `worlds/<World>/HOOKS.md` — it is never copied into snapshots. It is a forward-looking list of narrative seeds that grows across all stories; freezing it in time would be incorrect.

Read `worlds/<World>/HOOKS.md`. Any hooks added during this story (Source: "`story-analyzer` (Chapter N)") are already there — the `story-analyzer` adds them directly. No action needed unless state/bible/ has a separate HOOKS.md.

If `stories/<Story>/state/HOOKS.md` exists and has entries not in `worlds/<World>/HOOKS.md`: present them and ask which to append.

---

#### Step 3.8 — Post-Consolidation Snapshot

After all merges are applied, update the world snapshot. If you can run commands, run `create_snapshot.py`:

```bash
python "<WR>/scripts/create_snapshot.py" \
  --world    "worlds/<World Name>" \
  --position <position>            \
  --story    "<Story Name>"        \
  --unit     "<Full Story|Ch. N|...>"
```

**Without a shell:** follow `../writing-room/references/snapshot-manual.md`.

This creates (or overwrites) the snapshot at `worlds/<World>/snapshots/<position>/` with the now-consolidated world state. The snapshot now reflects the post-story, post-consolidation world — the correct baseline for any story at position N+1.

---

#### Step 3.9 — Regenerate SUMMARY.md

Run Operation 1 (Regenerate SUMMARY.md, see `../writing-room/references/summary-regeneration.md`) automatically after consolidation completes. This ensures the entity index reflects all newly merged entities.

---

#### Step 3.10 — Report

```
### World Archivist — Consolidation Complete

**World:** <World Name>
**Story consolidated:** [[<Story Name>]] (Position <N>)

**Entities merged:** N
  - N characters
  - N factions
  - N locations
  - N mythology entries

**Conflicts:**
  - N resolved (kept worlds/ / used state/bible/ / deferred)
  - N deferred for manual editing

**Timeline:** N entries inserted into worlds/<World>/TIMELINE.md at position <N>

**Snapshot:** Updated — worlds/<World>/snapshots/<N>/ now reflects post-consolidation world state

**SUMMARY.md:** Regenerated

**Files modified:**
  - worlds/<World>/characters/<Name>.md  (× N)
  - worlds/<World>/points_of_interest/<Name>.md  (× N)
  - worlds/<World>/factions/<Name>.md  (× N)
  - worlds/<World>/TIMELINE.md
  - worlds/<World>/SUMMARY.md
  - worlds/<World>/snapshots/<N>/  (snapshot updated)

**Follow-up needed:**
  - N new entity stubs require `writing-assistant` to flesh out
  - N conflict(s) deferred — manual editing needed
```

---
