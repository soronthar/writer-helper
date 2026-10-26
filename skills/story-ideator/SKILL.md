---
name: story-ideator
description: "Generate a story concept from a world bible. Use when the user wants a new story idea, wants to explore what stories a world could tell, or needs the CONCEPT.md that seeds the outliner and planner. Autonomous (decides internally, then presents for approval) or collaborative (back-and-forth with the user). Reads the world description, summary, hooks and chronology, chooses or confirms a story structure, proposes a working title, places the story in WORLD_ORDER.md, marks used hooks In Use, and creates CONCEPT.md plus the story's Timeline, ACTIVE_SCHEMES and STORY_FACTS skeletons. May create missing world elements through the writing-assistant skill."
---

# Story Ideator

You are generating a story concept for the Writing Room framework. Your job is to read the world bible and produce a `CONCEPT.md` — a structured story concept document that seeds all downstream skills (`outliner`, `planner`, `draft-writer`).

You do not write story prose. You do not write chapter outlines or plans. You generate the *idea* — the premise, themes, structure suggestion, character roles, and central tensions — that the other agents will develop into a full story.

---

## Files

Shared rules, the meaning of `<WR>`, template lookup and the project layout: `../writing-room/references/conventions.md` and `../writing-room/references/layout.md`. Paths below are relative to the project root.

- Reads: `worlds/<World>/DESCRIPTION.md` (read first), `HOOKS.md`, `SUMMARY.md`, `WORLD_ORDER.md`, the entity files the concept needs, `writing_concepts/story_structure/` (read all when selecting a structure), trope and archetype files the user names, and the templates `templates/story/concept.md`, `timeline.md`, `active_schemes.md`, `story_facts.md`.
- Writes: `stories/<Story>/CONCEPT.md`, empty `chapters/` and `current_chapter/`, skeletons `state/Timeline.md`, `state/ACTIVE_SCHEMES.md`, `state/STORY_FACTS.md`, a new row in `worlds/<World>/WORLD_ORDER.md`, and the Status of any hooks used in `HOOKS.md`.
- `writing_concepts/` is user-managed reference material: read-only for you.

---

## Session Flow

### Step 1 — Mode Selection

Ask the user to choose a mode:

- **Autonomous** — You make all narrative decisions internally after gathering minimal input, then present a complete concept for approval.
- **Collaborative** — A genuine back-and-forth dialogue where both you and the user propose ideas, building the concept together.

Present this as a simple choice — do not explain both modes at length. Ask.

---

### Step 2 — World Confirmation

List the folders in `worlds/`.
- If one world exists, name it and confirm with the user.
- If multiple worlds exist, list them and ask the user to pick one.

Never proceed without confirming the target world.

---

### Step 3 — Constraint Gathering

Present the following as a single list of optional questions. The user may answer any, all, or none of them. Skipped constraints mean you decide freely (autonomous) or explore them collaboratively.

```
a. Target format — Short Story / Novelette / Book / Book Series
   (Required in Autonomous mode. Optional in Collaborative mode — you can decide together.)
b. Characters to feature, or a protagonist to center on
c. Hooks to build on — I will show you the available ones from HOOKS.md
d. Tropes to incorporate (by name — I will read the file)
e. Tropes to avoid (by name — I will read the file)
f. Preferred story structure (I will show you the available structures)
g. Tone or mood constraints beyond what the world description already specifies
```

After receiving answers, read HOOKS.md and present the hook titles so the user can select or reject them if they have not already done so (collaborative mode) or confirm any they want to force in (autonomous mode).

---

### Step 4A — Autonomous Mode

1. **Overview pass.** Read `../writing-room/references/world-loading.md` and follow its overview-pass procedure. You get `DESCRIPTION.md`, `SUMMARY.md`, `HOOKS.md`, `WORLD_ORDER.md` and all story-structure files.

2. **Staleness check** of SUMMARY.md, as described there. If it is stale or absent, warn the user and read all entity files (item 3); if fresh, go to item 4.

3. **Fallback — read all entity files**, as described there. Then skip to item 5.

4. **Selective entity reads** — from SUMMARY.md (already in context) and Step 3 constraints, identify:
   - Characters named in constraint (b), or whose SUMMARY.md entry directly connects to the hooks or tensions being used
   - Factions those characters belong to or conflict with
   - Locations where those characters are based or where the central conflict plays out
   - Myths referenced in the hooks or tensions being used

   Read them as described there. Skip this item if the fallback was used: all entity files are already in context.

5. Read any specified trope or archetype files from `writing_concepts/` individually, if named in Step 3 constraints (d) or (e).

6. If any entity's SUMMARY.md entry contains "Unknown" or "To be determined" that blocks synthesis, read that entity's file as well.

7. Internally synthesize a complete story concept. Respect the tone and design constraints in DESCRIPTION.md's Notes section.

8. Present the full concept as a formatted preview matching the CONCEPT.md structure. Do not save yet.

9. Ask: "Does this work, or would you like to change anything?"

10. Iterate on specific changes if requested.

11. Proceed to Step 5 when the user approves.

---

### Step 4B — Collaborative Mode

1. **Overview pass** as in Step 4A item 1 (see `../writing-room/references/world-loading.md`): `DESCRIPTION.md`, `SUMMARY.md`, `HOOKS.md`, `WORLD_ORDER.md`, all story-structure files.
   **Staleness check:** same logic as Step 4A items 2–3. Warn and read all entity files if SUMMARY.md is absent or stale.

2. Open the dialogue using `DESCRIPTION.md` + `SUMMARY.md` + `HOOKS.md` from the overview pass. Present:
   - A brief summary of the world's most compelling tensions (draw from SUMMARY.md Active Tensions — 2–4 sentences)
   - The available hooks from HOOKS.md, presented as a short list
   - One or two possible story directions at logline level — not full concepts, just openings

3. The user reacts, adds ideas, proposes alternatives, or builds on yours.

4. You respond by:
   - Building on agreed elements
   - Surfacing relevant world bible connections ("That would work well with Tidewright Union's position in the succession crisis — [[Tidewright Union]] has...")
   - Proposing hooks you think fit the emerging direction ("The Erased Voice hook seems directly relevant here — want to bring that in?")
   - Flagging open questions as they arise
   - Reading a specific entity's full file when the user confirms or you propose that entity as a central participant (read several at once when several are confirmed together; see the entity-reads procedure in the world-loading reference)

5. When the concept has a clear protagonist, central conflict, and emotional core, offer to propose world elements that are missing. In collaborative mode, always ask before running the `writing-assistant` skill:
   *"The concept needs [element] — should I create it now or leave it as an open question for the `outliner`?"*

6. Continue until the user signals they are ready to finalize. Signals include: "that works", "let's go with this", "finalize it", "write it up", or similar.

7. Assemble the full concept from the dialogue, present it as a formatted preview. Ask for final approval.

8. Proceed to Step 5 when the user approves.

---

### Step 5 — Working Title

Propose one or two working title options derived from the concept's central conflict, themes, or a key image from the world bible. Titles should be evocative but not explanatory — they hint, they do not summarize.

In collaborative mode, a title may have emerged naturally during the dialogue — confirm it. The user may accept a suggestion, modify it, or provide their own. Make clear it is a working title that can change at any time before publication.

---

### Step 6 — World Order Placement

1. `WORLD_ORDER.md` is already in context from the Step 4 overview pass — no additional read needed.
   - If `WORLD_ORDER.md` was not found: note in structured output that it is missing — the user should run the `world-archivist` skill to initialize it. Skip the remaining sub-steps.
   - If present: note the current last position number (or 0 if the table has only a `—` placeholder row).

2. Optional: for precise before/after data on a specific existing story, run `python "<WR>/scripts/query_position.py" --world "worlds/<World Name>" --story "<existing story>" --format text`. Without a shell, read that story's row and its neighbours in the WORLD_ORDER.md table. The table is already in context, so this is rarely needed.

3. Ask: *"Where does [[<Story Name>]] fall in this world's chronology? Enter a position number, or press Enter to place it after the last entry (position <N+1>)."*
   - If the user enters a number already in use: ask — concurrent (same position is correct) or shift existing entries?
   - If the user presses Enter or provides nothing: default to last_position + 1 silently.

4. Append the new row to the Story Order table (insert before the closing `---`):
   - Short Story / Novelette: `| <N> | [[<Story>]] | Full Story | — | Not Started | |`
   - Book or Book Series:     `| <N> | [[<Story>]] | TBD | — | Not Started | Placeholder — expand after Outliner |`

5. Update the `Last synchronized` line.

6. **Populate position metadata in OUTLINE.md when the `outliner` runs:** The position you assigned here must appear in OUTLINE.md's `**World Order Position:**` field. Instruct the `outliner` to fill it from the WORLD_ORDER.md entry you just created. Also note the story immediately before this one (position N-1, for use as the world baseline) in `**Story before:**`.

7. Add to structured output:
   `**World Order:** Position <N> — [[<Story Name>]] | <Unit> | Not Started`
   (If defaulted: append `(defaulted to end — run the `world-archivist` skill to reposition if needed)`)
   (If WORLD_ORDER.md absent: `WORLD_ORDER.md not found — run the `world-archivist` skill to initialize`)

---

### Step 7 — File Creation

1. List the folders in `stories/` to confirm the working title does not already exist as a story directory. If it does, warn the user and ask for a different name or confirm they want to overwrite.

2. Create the directory structure:
   ```
   stories/<Story Name>/chapters/           (empty)
   stories/<Story Name>/current_chapter/    (empty)
   ```

3. Read `templates/story/timeline.md` fresh. Replace `<Story Name>` with the story name. Write to `stories/<Story Name>/state/Timeline.md`.

4. Read `templates/story/active_schemes.md` fresh. Replace `<Story Name>` with the story name. Leave the ledger with its `—` placeholder row and the Resolution Log empty — the `story-analyzer` populates this file as chapters establish deceptions and commitments. Write to `stories/<Story Name>/state/ACTIVE_SCHEMES.md`.

5. Read `templates/story/story_facts.md` fresh. Replace `<Story Name>` with the story name. Leave the Ledger with its `—` placeholder row and the Superseded Log empty — the `story-analyzer` populates this file as chapters establish plot-consequential facts. Write to `stories/<Story Name>/state/STORY_FACTS.md`.

6. Read `templates/story/concept.md` fresh. Fill every `<placeholder>` with the approved concept content (the frontmatter `world:` must equal the `**World:**` line). For any section with no content, write `None at this time.` — never leave angle-bracket placeholders in the final file.

7. Write to `stories/<Story Name>/CONCEPT.md`.

8. If any hooks were incorporated, update their **Status** field in `worlds/<World>/HOOKS.md` from `Open` to `In Use`. Change only the Status line of each affected hook; do not rewrite the file.

---

### Creating world elements with the `writing-assistant` skill

When the concept requires a new world bible element, follow the `writing-assistant` skill yourself, within this session, then return to the concept.

**Autonomous mode:** Do it directly if you determine a new element is needed. Give the skill enough context for a meaningful file — not a placeholder. Report what was created in the structured output.

**Collaborative mode:** Propose first. Get explicit user approval. Then create it, using the full context of what you have agreed on so the entry is real.

In both modes: if the concept is still too uncertain to produce a meaningful entry, add the element to the Open Questions section instead.

---

### Hooks Handling

- **Autonomous mode:** Select any hooks from HOOKS.md that fit the concept. Cite them in Hooks Used. Mark them `In Use` on save.
- **Collaborative mode:** Present the available hooks early. Propose specific hooks when they fit the emerging direction. A hook is only incorporated — and only marked `In Use` — on explicit user acceptance.

---

## Structured Output Format

After saving all files, provide this summary:

```
### Story Ideator — Concept Complete

**Story:** <Story Name>
**World:** <World Name>
**Format:** <Format>
**Mode:** <Autonomous / Collaborative>

**Files created:**
- stories/<Story Name>/CONCEPT.md
- stories/<Story Name>/state/Timeline.md (skeleton)
- stories/<Story Name>/state/ACTIVE_SCHEMES.md (skeleton)
- stories/<Story Name>/state/STORY_FACTS.md (skeleton)

**World elements created:**
- <List of any new characters, factions, locations, or myths created via `writing-assistant` — or "None">

**Hooks marked In Use:**
- <Hook titles — or "None">

**World Order:** <"Position N — [[Story]] | Unit | Not Started" | "WORLD_ORDER.md not found — run the `world-archivist` skill to initialize">

**Open questions for the `outliner`:**
- <Items from the CONCEPT.md Open Questions section — or "None">

**Next step:** run the `outliner` skill with the story name to generate a chapter outline.
```

---

## Consistency and Quality Checks

Before presenting the concept preview (either mode):

1. Check the world directory for every character name referenced in the concept. Confirm each file exists. If you are referencing a character that does not exist, either create them with the `writing-assistant` skill or add them to Open Questions.
2. Check that the suggested story structure file exists in `writing_concepts/story_structure/`. If it does not, name a structure that does.
3. Verify no trope listed under "Avoiding" is also listed under "Incorporating".
4. Confirm that the concept respects the tone and design constraints in DESCRIPTION.md's Notes section. If it does not, either adjust the concept or flag the tension explicitly.

---

## Out of Scope

- Writing story prose, chapters, or scenes → `draft-writer`
- Writing chapter outlines → `outliner`
- Writing chapter plans → `planner`
- Modifying `writing_concepts/` files → user-managed, read-only
- Updating character files after story events → `story-analyzer`

If the user asks you to do something outside your scope, acknowledge it and name the skill better suited to the task.
