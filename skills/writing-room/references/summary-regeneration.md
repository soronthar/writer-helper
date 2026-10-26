# Regenerating SUMMARY.md

Shared by `writing-assistant` (after every create or update) and `world-archivist` (Operation 1, and after consolidation). SUMMARY.md is always rebuilt from scratch, never edited in place. Paths are relative to the project root.

1. Read `templates/world/summary.md` fresh.
2. List all four entity directories under `worlds/<World>/`: `characters/`, `factions/`, `points_of_interest/`, `mythology/`.
3. Read every entity file in each directory.
4. Read `worlds/<World>/DESCRIPTION.md` for the Overview and Active Tensions sections.
5. Construct the full SUMMARY.md content:
   - Set `Last synchronized` to the current date and what triggered the regeneration (e.g., "after creating [[Mara Quill]]" or "manual regeneration").
   - **World Overview:** condense DESCRIPTION.md Overview to 2–3 sentences.
   - **Active Tensions:** copy/condense DESCRIPTION.md Current State to 3–6 sentences.
   - **Characters table:** one row per character file — Name (wiki link), Role (from Identity > Occupation/Role), Description (single most defining trait from Personality), Location/Status (from Current Status).
   - **Factions table:** one row per faction file — Name, Type (from Identity > Type), Current Standing (one sentence from Current Status > Standing + Internal condition).
   - **Locations table:** one row per POI file — Name, Type (from Overview > Type), Description (one line; include current condition if changed from baseline).
   - **Active Mythology table:** one row per mythology file — Name, Type (from Overview > Type), Relevance (why this element matters in the current world state — not a summary of the myth itself).
6. Write the completed file to `worlds/<World>/SUMMARY.md` as a full overwrite.

If the entity directories are empty (a newly created world with no elements yet), write single `—` rows in each table.

All references to named characters, locations, factions and myths use `[[Name]]` format, with no folder paths inside the brackets.

Report the result as `**SUMMARY.md:** Regenerated — N characters, N factions, N locations, N myths`.
