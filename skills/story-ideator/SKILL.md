---
name: story-ideator
description: "Generate a story concept from a world bible. Use when the user wants a new story idea, wants to explore what stories a world could tell, or needs the CONCEPT.md that seeds the outliner and planner. Autonomous (decides internally, then presents for approval) or collaborative (back-and-forth with the user). Reads the world description, summary, hooks and chronology, chooses or confirms a story structure, proposes a working title, places the story in WORLD_ORDER.md, marks used hooks In Use, and creates CONCEPT.md plus the story's Timeline, ACTIVE_SCHEMES and STORY_FACTS skeletons. Lists any missing world elements for the writing-assistant skill to create afterwards."
---

# Story Ideator

You are generating a story concept for the Writing Room framework. Your job is to read the world bible and produce a `CONCEPT.md` — a structured story concept document that seeds all downstream skills (`outliner`, `planner`, `draft-writer`).

You do not write story prose. You do not write chapter outlines or plans. You generate the *idea* — the premise, themes, structure suggestion, character roles, and central tensions — that the other agents will develop into a full story.

---

## Files

`<WR>` is the Writing Room framework folder. The project's `AGENTS.md` names it under "Writing Room paths"; use that path exactly as written. If `AGENTS.md` has no such block, `<WR>` is the `writing-room` folder beside this skill's own folder; it is never a folder you make up in the project. Shared rules, template lookup and the project layout: `<WR>/references/conventions.md` and `<WR>/references/layout.md`. Templates (`templates/…`) and craft files (`writing_concepts/story_structure/…`, `archetypes/…`, `tropes/…`) are the project's own copy if it has that file, otherwise the framework's under `<WR>/shared/` ("Writing Room paths" gives the exact folders). Every other path below is relative to the project root.

- Reads: `worlds/<World>/DESCRIPTION.md`, `HOOKS.md`, `SUMMARY.md`, `WORLD_ORDER.md`, the story-structure guide and the Overview of each `writing_concepts/story_structure/` file (the full file only for the structure you choose), the entity files the concept needs, and trope and archetype files the user names. All of these load through `load_world.py`, in two calls (Steps 2 and 4); if you can run commands, do not read them one by one. When saving the approved concept you also read the template `templates/story/concept.md`.
- Writes: `.writing-room-work/worlds/<World>/CONCEPT.md` (the concept draft from the first preview on, approved in Step 4C), then `stories/<Story>/CONCEPT.md`, empty `chapters/` and `current_chapter/`, skeletons `state/Timeline.md`, `state/ACTIVE_SCHEMES.md`, `state/STORY_FACTS.md`, a new row in `worlds/<World>/WORLD_ORDER.md`, and the Status of any hooks used in `HOOKS.md`. With a shell, `new_story.py` writes all of the story files and world rows in one call (Step 7).
- Does not write world bible entity files or `SUMMARY.md`. New world elements the concept needs are listed for the `writing-assistant` skill, which runs after this skill finishes.
- `writing_concepts/` is user-managed reference material: read-only for you.

---

## Session Flow

### Step 1 — World Confirmation

List the folders in `worlds/` (list the directory itself; a file search may show only files).
- If the request names a world that is in the list, that is the confirmation. Do not ask again.
- Otherwise, if one world exists, name it and confirm with the user. If multiple worlds exist, list them and ask the user to pick one.

Never proceed without confirming the target world.

**Resume check.** Once the world is confirmed, look for `.writing-room-work/worlds/<World Name>/CONCEPT.md`. If it is not there, go on to Step 2. If it is, an earlier session stopped part-way. Read it and tell the user its logline and whether its first line is `<!-- draft: not yet approved -->` (a preview the user had not approved) or not (an approved concept still waiting for its title, position and files). Ask whether to continue with it or start a new concept.
- **Continue a draft:** do Step 2, load the entities, tropes and structure the draft names (the Step 4A item 3 command), then present the draft and ask for approval (Step 4A item 6). Skip Step 3.
- **Continue an approved concept:** do Step 2, then go to Step 5. Skip Steps 3 and 4.
- **Start new:** go on to Step 2. The old file is replaced at the first preview.

---

### Step 2 — Load the World

If you can run commands, load the whole overview with one call, as one line:

```bash
python "<WR>/scripts/load_world.py" --for story-ideator --world "<World Name>" --output
```

It gives you `DESCRIPTION.md`, `SUMMARY.md`, `HOOKS.md`, `WORLD_ORDER.md`, the story-structure `GUIDE.md` and `Format Reference.md`, the Overview of every other structure file, and a **SUMMARY CHECK**. If the check says SUMMARY.md is missing or stale, the same call has already added every entity file. Pass the warning it prints on to the user. Read the saved file at the path the receipt prints, range by range (see conventions, "Working files").

**Without a shell:** follow the overview pass and staleness check in `<WR>/references/world-loading.md`.

Everything below that says "already in context" comes from this step. Do not read these files again.

---

### Step 3 — Mode and Constraints (one round)

Ask everything in a single message (or a single call of your question tool), then wait for the answers. The user may answer any, all, or none of the optional items. Skipped constraints mean you decide freely (autonomous) or explore them collaboratively.

```
Mode — Autonomous or Collaborative (skip this if the request already names one)
a. Target format — Short Story / Novelette / Book / Book Series
   (Required in Autonomous mode. Optional in Collaborative mode — you can decide together.)
b. Characters to feature, or a protagonist to center on
c. Hooks to build on — list every hook title from HOOKS.md here (Autonomous: the ones to force in; Collaborative: the ones to start from)
d. Tropes to incorporate (by name — I will read the file)
e. Tropes to avoid (by name — I will read the file)
f. Preferred story structure — list the structure names from Step 2 here
g. Tone or mood constraints beyond what the world description already specifies
```

Describe the two modes in one line each, no more:

- **Autonomous** — You make all narrative decisions internally after gathering minimal input, then present a complete concept for approval.
- **Collaborative** — A genuine back-and-forth dialogue where both you and the user propose ideas, building the concept together.

This is the only question round before the concept. Do not ask about mode, world or hooks again afterwards.

---

### Step 4A — Autonomous Mode

1. **The overview is in context** from Step 2, with the SUMMARY CHECK result.

2. **Choose what else to load.** From SUMMARY.md and the Step 3 constraints, identify:
   - Characters named in constraint (b), or whose SUMMARY.md entry directly connects to the hooks or tensions being used
   - Factions those characters belong to or conflict with
   - Locations where those characters are based or where the central conflict plays out
   - Myths referenced in the hooks or tensions being used
   - Any entity whose SUMMARY.md entry says "Unknown" or "To be determined" in a way that blocks synthesis
   - Trope and archetype files named in constraints (d) and (e)
   - The story structure: the one named in constraint (f), or the one you choose from the Overviews in context

   If the SUMMARY CHECK loaded every entity file, skip the entities and load only the craft files and the structure.

3. **Load them in one call**, as one line. Use one `--entity "<type>/<Name>"` per entity (types: `characters`, `factions`, `points_of_interest`, `mythology`), one `--trope "<Name>"` or `--archetype "<Name>"` per craft file, and `--structure "<Name>"` for the full file of the chosen structure:

   ```bash
   python "<WR>/scripts/load_world.py" --world "<World Name>" --entity "characters/<Name>" --entity "factions/<Name>" --trope "<Name>" --structure "<Structure Name>" --output
   ```

   **Without a shell:** read each file as described under "Entity reads" in `<WR>/references/world-loading.md`, each trope or archetype from `writing_concepts/tropes/` or `writing_concepts/archetypes/`, and the chosen structure from `writing_concepts/story_structure/`.

4. Internally synthesize a complete story concept. Respect the tone and design constraints in DESCRIPTION.md's Notes section.

5. Save the concept as a draft (see "Saving the draft" below), then present it as a formatted preview matching the CONCEPT.md structure.

6. Ask: "Does this work, or would you like to change anything?"

7. Iterate on specific changes if requested: edit the draft file, then show the changed sections.

8. Proceed to Step 4C when the user approves.

---

### Step 4B — Collaborative Mode

1. **The overview is in context** from Step 2, with the SUMMARY CHECK result (if it loaded every entity file, they are in context too).

2. Open the dialogue using `DESCRIPTION.md` + `SUMMARY.md` + `HOOKS.md` from the overview pass. Present:
   - A brief summary of the world's most compelling tensions (draw from SUMMARY.md Active Tensions — 2–4 sentences)
   - The hooks the user chose in Step 3, or, if none, the ones that fit best
   - One or two possible story directions at logline level — not full concepts, just openings

3. The user reacts, adds ideas, proposes alternatives, or builds on yours.

4. You respond by:
   - Building on agreed elements
   - Surfacing relevant world bible connections ("That would work well with Tidewright Union's position in the succession crisis — [[Tidewright Union]] has...")
   - Proposing hooks you think fit the emerging direction ("The Erased Voice hook seems directly relevant here — want to bring that in?")
   - Flagging open questions as they arise
   - Loading an entity's full file when the user confirms or you propose that entity as a central participant, with the Step 4A item 3 command (one `--entity` per entity, several in one call when several are confirmed together; add `--trope` or `--archetype` for craft files the user names, and `--structure` once a structure is agreed). Skip the entities when the SUMMARY CHECK already loaded every entity file.

5. When the concept has a clear protagonist, central conflict, and emotional core, name any world elements that are missing and agree with the user how each should be described. They go in the concept as `New — to be created` and in Open Questions (see "New world elements" below).

6. Continue until the user signals they are ready to finalize. Signals include: "that works", "let's go with this", "finalize it", "write it up", or similar.

7. Assemble the full concept from the dialogue, save it as a draft (see "Saving the draft" below), and present it as a formatted preview. Ask for final approval. For changes, edit the draft file, then show the changed sections.

8. Proceed to Step 4C when the user approves.

---

### Saving the draft

The first time you present a concept preview, write it to a file first:

1. Read `templates/story/concept.md` fresh. Fill every `<placeholder>` with the concept content (the frontmatter `world:` must equal the `**World:**` line). Use `# Untitled` as the title line until Step 5. For any section with no content, write `None at this time.` — never leave angle-bracket placeholders in the file.
2. Put `<!-- draft: not yet approved -->` as the file's first line, above everything else.
3. Write it to `.writing-room-work/worlds/<World Name>/CONCEPT.md` (see conventions, "Working files"), replacing any older file there.

Present the preview from that file. Each later change goes into the file before you show it. If the session stops before approval, the next one finds the draft in Step 1.

---

### Step 4C — Save the Approved Concept

Do this at once, before the title or anything else: delete the `<!-- draft: not yet approved -->` line from `.writing-room-work/worlds/<World Name>/CONCEPT.md`. If the file is missing, write it as in "Saving the draft", without that line. `new_story.py` refuses a concept that still has the line.

From here on, that file is the concept. Build everything that follows from it, not from memory. If you lose track of the session (you no longer see the earlier conversation, or the user says you did), read this file and continue from the next step; never rebuild the concept from memory. If the user asks for a change after this point, edit this file.

---

### Step 5 — Working Title

Propose one or two working title options derived from the concept's central conflict, themes, or a key image from the world bible. Titles should be evocative but not explanatory — they hint, they do not summarize.

In collaborative mode, a title may have emerged naturally during the dialogue — confirm it. The user may accept a suggestion, modify it, or provide their own. Make clear it is a working title that can change at any time before publication.

Ask about the title and the position (Step 6, item 3) in the same message.

---

### Step 6 — World Order Placement

1. `WORLD_ORDER.md` is already in context from Step 2 — no additional read needed.
   - If `WORLD_ORDER.md` was not found: note in structured output that it is missing — the user should run the `world-archivist` skill to initialize it. Skip the remaining sub-steps.
   - If present: note the current last position number (or 0 if the table has only a `—` placeholder row).

2. Optional: for precise before/after data on a specific existing story, run `python "<WR>/scripts/query_position.py" --world "worlds/<World Name>" --story "<existing story>" --format text`. Without a shell, read that story's row and its neighbours in the WORLD_ORDER.md table. The table is already in context, so this is rarely needed.

3. Ask: *"Where does [[<Story Name>]] fall in this world's chronology? Enter a position number, or press Enter to place it after the last entry (position <N+1>)."*
   - If the user enters a number already in use: ask — concurrent (same position is correct) or shift existing entries? To shift entries, the user runs the `world-archivist` skill afterwards.
   - If the user presses Enter or provides nothing: default to last_position + 1 silently.

4. **Populate position metadata in OUTLINE.md when the `outliner` runs:** The position you assigned here must appear in OUTLINE.md's `**World Order Position:**` field. Instruct the `outliner` to fill it from the WORLD_ORDER.md entry. Also note the story immediately before this one (position N-1, for use as the world baseline) in `**Story before:**`.

The row itself is written in Step 7, with Status `Not Started`.

---

### Step 7 — File Creation

If you can run commands, create the story with one call, as one line. Add one `--hook "<Hook Title>"` per hook the concept uses, and `--position <N>` unless the user chose the default:

```bash
python "<WR>/scripts/new_story.py" --world "<World Name>" --story "<Story Name>" --hook "<Hook Title>" --position <N>
```

It checks everything before writing anything, then: copies `.writing-room-work/worlds/<World Name>/CONCEPT.md` to `stories/<Story Name>/CONCEPT.md` with the title line set, creates `chapters/`, `current_chapter/` and the three `state/` skeletons from the templates, adds the WORLD_ORDER.md row (the Unit follows the concept's Format) and its `Last synchronized` line, and sets each hook's Status to `In Use (<Story Name>)`. If it refuses, it names each problem and has changed nothing: fix that (for example, a placeholder left in the saved concept, or a hook title spelled differently from HOOKS.md) and run it again. Do not edit `WORLD_ORDER.md` or `HOOKS.md` by hand after it succeeds.

**Without a shell:**

1. List the folders in `stories/` to confirm the working title does not already exist as a story directory. If it does, warn the user and ask for a different name or confirm they want to overwrite.

2. Create the directory structure:
   ```
   stories/<Story Name>/chapters/           (empty)
   stories/<Story Name>/current_chapter/    (empty)
   ```

3. Read `templates/story/timeline.md` fresh. Replace `<Story Name>` with the story name. Write to `stories/<Story Name>/state/Timeline.md`.

4. Read `templates/story/active_schemes.md` fresh. Replace `<Story Name>` with the story name. Leave the ledger with its `—` placeholder row and the Resolution Log empty — the `story-analyzer` populates this file as chapters establish deceptions and commitments. Write to `stories/<Story Name>/state/ACTIVE_SCHEMES.md`.

5. Read `templates/story/story_facts.md` fresh. Replace `<Story Name>` with the story name. Leave the Ledger with its `—` placeholder row and the Superseded Log empty — the `story-analyzer` populates this file as chapters establish plot-consequential facts. Write to `stories/<Story Name>/state/STORY_FACTS.md`.

6. Copy `.writing-room-work/worlds/<World Name>/CONCEPT.md` to `stories/<Story Name>/CONCEPT.md`, with its title line changed to `# <Story Name>`.

7. Read `worlds/<World>/WORLD_ORDER.md` fresh and add the new row to the Story Order table, in position order (replace the `—` placeholder row if it is the only one):
   - Short Story / Novelette: `| <N> | [[<Story>]] | Full Story | — | Not Started | |`
   - Book or Book Series:     `| <N> | [[<Story>]] | TBD | — | Not Started | Placeholder — expand after Outliner |`

   Then update the `Last synchronized` line.

8. If any hooks were incorporated, read `worlds/<World>/HOOKS.md` fresh and set their **Status** field from `Open` to `In Use (<Story Name>)`. Change only the Status line of each affected hook; do not rewrite the file.

When you edit an existing file and the edit does not match, read those lines again and copy the text from what you just read. Never retype it from memory.

---

### New world elements

When the concept needs a world bible element that does not exist (a character, faction, location or myth), do not create it in this session. In the concept:

- In Key Characters, give it the role `New — to be created` with a one-line description.
- In Open Questions, add `New world element for the writing-assistant skill: <type>/<Name> — <what the concept needs it to be>`.

List them under **World elements to create** in the structured output. The user runs the `writing-assistant` skill after this skill finishes; it writes the files and regenerates SUMMARY.md.

If the concept is still too uncertain to say what the element is, add only the Open Question.

---

### Hooks Handling

- **Autonomous mode:** Select any hooks from HOOKS.md that fit the concept, plus any the user forced in at Step 3. Cite them in Hooks Used. Mark them `In Use` on save (Step 7).
- **Collaborative mode:** Start from the hooks the user picked in Step 3. Propose specific hooks when they fit the emerging direction. A hook is only incorporated — and only marked `In Use` — on explicit user acceptance.

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

**World elements to create** (run the `writing-assistant` skill):
- <type/Name — what the concept needs — or "None">

**Hooks marked In Use:**
- <Hook titles — or "None">

**World Order:** <"Position N — [[Story]] | Unit | Not Started" | "WORLD_ORDER.md not found — run the `world-archivist` skill to initialize">
(If defaulted: append "(defaulted to end — run the `world-archivist` skill to reposition if needed)")

**Open questions for the `outliner`:**
- <Items from the CONCEPT.md Open Questions section — or "None">

**Next step:** run the `writing-assistant` skill for the world elements above, if any; then run the `outliner` skill with the story name to generate a chapter outline.
```

---

## Consistency and Quality Checks

Before presenting the concept preview (either mode):

1. Check the world directory for every character name referenced in the concept, using the folder names and SUMMARY.md already in context. Confirm each file exists, and link it by its exact file name (`[[Dr. Mara Quill]]`, not `[[Mara Quill]]`; the names here are invented). If you are referencing a character that does not exist, mark it `New — to be created` and add it to Open Questions (see "New world elements").
2. Check that the suggested story structure file exists in `writing_concepts/story_structure/`. If it does not, name a structure that does.
3. Verify no trope listed under "Avoiding" is also listed under "Incorporating".
4. Confirm that the concept respects the tone and design constraints in DESCRIPTION.md's Notes section. If it does not, either adjust the concept or flag the tension explicitly.

---

## Out of Scope

- Writing story prose, chapters, or scenes → `draft-writer`
- Writing chapter outlines → `outliner`
- Writing chapter plans → `planner`
- Creating or changing world bible entries, and regenerating SUMMARY.md → `writing-assistant`
- Modifying `writing_concepts/` files → user-managed, read-only
- Updating character files after story events → `story-analyzer`

If the user asks you to do something outside your scope, acknowledge it and name the skill better suited to the task.
