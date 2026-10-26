---
name: create-world
description: "Create a new world bible through a guided interview. Use when the user wants to start a new fictional world or setting for their stories. Asks about overview, geography, history, population, economy, magic or technology, belief systems, current state and notes one question at a time, lets any question be skipped, then writes DESCRIPTION.md, HOOKS.md, WORLD_ORDER.md and SUMMARY.md (plus optional starter characters, factions, places and myths) under worlds/<World Name>/ after the user confirms."
---

# Create World

You are helping the user initialize a new world bible for the Writing Room framework. World bibles live in `worlds/<World Name>/` and are the source of truth for every other skill (`story-ideator`, `outliner`, `planner`, `draft-writer`, `reviewer`).

Shared rules and where templates are found: `../writing-room/references/conventions.md`.

Before starting the interview, read these two templates fresh:
- `templates/world/world_description.md`
- `templates/world/hooks.md`

---

## Rules

- Work through all 9 sections in order.
- Ask each question clearly. Where options exist, list them explicitly.
- **If the user types "skip"**, leave that field's `<placeholder>` text in place — do not invent an answer.
- **If the user types "skip section"**, skip all remaining questions in the current section and move to the next.
- After all sections are complete, offer to collect initial world elements (factions, characters, locations, myths).
- Show a summary table and ask for confirmation before writing anything.
- Write files only after the user confirms.

---

## Opening

Greet the user and explain that you'll build a new world bible together, one section at a time. Any question can be skipped and filled in manually later. At the end you'll review everything before any files are created.

Then ask:

1. **World name** — What is this world called? *(Becomes the directory name: `worlds/<World Name>/`)*
2. **One-line pitch** — In one sentence, what kind of world is this? *(Used to anchor the Overview section)*

---

## Section 1 — Overview

*Maps to `## Overview` in the world description template.*

1. How would you describe this world's character and tone? What would you tell someone in 2–3 sentences?
2. What makes it distinctive — what sets it apart from the obvious defaults for its genre?

---

## Section 2 — Geography

*Maps to `## Geography`.*

1. **Major regions** — Describe your key regions one at a time. For each, give a name and a one-line description. Say **"done"** when you've listed them all.
2. **Climate** — What is the overall climate character? Any notable regional variations?
3. **Notable natural features** — Any significant mountains, rivers, coastlines, magical zones, or landmarks? *(Skip if nothing notable.)*

---

## Section 3 — History

*Maps to the `## History` era table.*

Walk through the world's historical eras one at a time. For each era:
- What is the era called?
- What were the key events?

After each era, ask: **"Add another era? (yes / done)"** — continue until the user says done. At least one era is required.

---

## Section 4 — Population

*Maps to `## Population`.*

1. **Scale** — How many people live in this world? *(sparse / moderate / dense, or a rough number)*
2. **Peoples** — What are the major species or human groups?
3. **Factions / nations** — What are the key political or cultural groups? For each: name + one-line description. These are world-level summary entries — full faction files can be created separately. Say **"done"** when finished.

---

## Section 5 — Economy

*Maps to `## Economy`.*

1. What does this world produce, export, or trade in?
2. How does wealth work? Key resources, currencies, trade routes?

---

## Section 6 — Magic / Technology

*Maps to `## Magic / Technology`.*

First ask: **Does this world have magic or advanced technology?** *(yes / no / skip section)*

If **yes**:
1. How does it work — what are the rules?
2. How prevalent is it? *(rare / uncommon / common / pervasive)*
3. What are its limitations or costs?

If **no**, note the section as "Not applicable" and move on.

---

## Section 7 — Religion / Belief Systems

*Maps to `## Religion / Belief Systems`.*

1. Are there major religions, pantheons, philosophical traditions, or spiritual practices?
2. What role do they play in everyday life and in political or social structures?

---

## Section 8 — Current State

*Maps to `## Current State`.*

1. What is the political and social situation at the opening of stories set in this world?
2. What is the central tension or conflict that defines the present moment?

---

## Section 9 — Notes

*Maps to `## Notes`.*

1. Any tone guidance — what should stories in this world feel like?
2. Anything to avoid — tropes, tones, or directions that would break this world?
3. Any other author notes worth recording?

---

## Initial Elements (Optional)

After the interview, ask if the user wants to create any starting world elements now. These will be written as stubs — the user's description goes in the `## Notes` field; all other fields are set to `To be determined` or `Unknown`.

Ask each type separately (user may skip any):

1. **Factions or organizations** — Any to add now? For each: name + one-line description.
2. **Characters** — Any to create now? For each: name + brief description.
3. **Locations** — Any to record now? For each: name + brief description.
4. **Myths or legends** — Any to note now? For each: title + one-line summary.

Read the appropriate template fresh before creating each stub:
- Factions → `templates/world/faction.md` → `worlds/<World Name>/factions/<Name>.md`
- Characters → `templates/world/character.md` → `worlds/<World Name>/characters/<Name>.md`
- Locations → `templates/world/point_of_interest.md` → `worlds/<World Name>/points_of_interest/<Name>.md`
- Myths → `templates/world/mythology.md` → `worlds/<World Name>/mythology/<Name>.md`

When filling a stub:
- Replace `<World Name>` placeholders with the actual world name
- Put the user's one-line description in `## Notes`
- Set all `<placeholder>` fields to `To be determined` or `Unknown` — never leave angle-bracket placeholders in the final file
- Use `[[Name]]` wiki link format wherever the template calls for linked names

---

## Summary and Confirmation

Before writing anything, display a summary table:

| Section | Status |
|---------|--------|
| World name | `<name>` |
| Overview | Filled / **Skipped** |
| Geography | Filled / **Skipped** |
| History | N eras / **Skipped** |
| Population | Filled / **Skipped** |
| Economy | Filled / **Skipped** |
| Magic / Technology | Filled / Not applicable / **Skipped** |
| Religion | Filled / **Skipped** |
| Current State | Filled / **Skipped** |
| Notes | Filled / **Skipped** |
| Initial elements | N factions, N characters, N locations, N myths |

Ask: *"Does this look right? Type **'yes'** to create the world, or tell me what to change."*

---

## File Creation (on confirmation)

1. **Existence check** — List files matching `worlds/` to confirm this world name does not already exist. If it does, stop and warn the user — do not overwrite.
2. **DESCRIPTION.md** — Read `templates/world/world_description.md` fresh. Fill every section with the user's answers. For skipped sections, leave the original `<placeholder>` text exactly as it appears in the template. Write to `worlds/<World Name>/DESCRIPTION.md`.
3. **HOOKS.md** — Read `templates/world/hooks.md` fresh. Replace `<World Name>` with the world name. Write to `worlds/<World Name>/HOOKS.md` (entries section left empty).
3a. **WORLD_ORDER.md** — Read `templates/world/world_order.md` fresh. Replace `<World Name>` with the world name. Set `Last synchronized` to today's date and "World created — <World Name> baseline." Write to `worlds/<World Name>/WORLD_ORDER.md` (Story Order table left with the `—` placeholder row).
4. **Initial element stubs** — For each element the user provided, read the appropriate template fresh and write the stub file as described above.
4a. **SUMMARY.md** — Read `templates/world/summary.md` fresh. Construct the summary from the content just written:
   - Set `Last synchronized` to the current date and "World created — <World Name> baseline".
   - **World Overview:** condense DESCRIPTION.md Overview to 2–3 sentences.
   - **Active Tensions:** copy/condense DESCRIPTION.md Current State to 3–6 sentences.
   - **Entity tables:** populate from any initial element stubs created in step 4. If no elements were created, leave each table with a single `—` row.
   Write to `worlds/<World Name>/SUMMARY.md`.
5. **Report** — List all files created and all fields still requiring manual completion.

---

## Closing Report Format

```
### create-world — World Created

**World:** <World Name>
**Directory:** worlds/<World Name>/

**Files created:**
- worlds/<World Name>/DESCRIPTION.md
- worlds/<World Name>/HOOKS.md
- worlds/<World Name>/WORLD_ORDER.md
- worlds/<World Name>/SUMMARY.md
- [any stub files]

**Sections requiring manual completion:**
- [List of skipped sections or placeholder fields — or "None"]

**Next steps:**
- Add characters, factions, locations, and myths with the `writing-assistant` skill
- Add story hooks to HOOKS.md with the `writing-assistant` skill, or edit the file directly
- When ready to write a story, run the `story-ideator` skill
```

**Next step:** `writing-assistant` to flesh out the world, or `story-ideator` to start a story.
