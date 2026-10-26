"""Generate the sample world and stories used by the fixtures, the example project and the tests.

    python tools/build_sample.py --dest DIR [--marker]
    python tools/build_sample.py --fixtures        # rebuild fixtures/legacy-v1 content and examples/sample-project

Writes into DIR: worlds/Harrowmere/, stories/The Tallow Ledger/, stories/Salt and Signal/ and
writing_concepts/styles/Default Style.md (copied from the framework). With --marker also writes
writing-room.toml. Everything is invented for this repository; it is not anyone's real project.
Output is fully deterministic (fixed dates) so the golden files stay stable.

The sample is a complete layout-v1 project at the end of two stories:
  position 1  The Tallow Ledger  (3 chapters, Fichtean Curve)   -> snapshot 1
  position 2  Salt and Signal    (4 chapters, Freytag's Pyramid) -> snapshot 2, with story-local bible,
                                  active schemes and story facts
Both are Complete and consolidated into the world TIMELINE.md.
"""

import argparse
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "skills" / "writing-room" / "scripts"))

WORLD = "Harrowmere"
S1 = "The Tallow Ledger"
S2 = "Salt and Signal"
DATE1, DATE2 = "2026-01-15", "2026-02-20"


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((text.strip("\n") + "\n").encode("utf-8"))


# ----------------------------------------------------------------------------- world entities
# name -> (kind, fields). `v1` overrides apply to the snapshot taken after story 1; `since` is the story
# in which the entity first exists.
CHARACTERS = {
    "Mara Quill": dict(since=1, role="Ledger-keeper at the Tally House", age="34", gender="Female",
                       look="Narrow, ink-stained hands; a grey wool coat she never takes off in the Tally House; hair pinned with a pencil.",
                       personality="Methodical and dry-humoured. Cannot leave an unanswered question alone. Distrusts anything that adds up too neatly. Afraid of being the person who looked away.",
                       background="Born in the Flats to a family of reed-cutters. Trained as a tallier at fourteen and has kept the Guild's tallow-tax ledger for eleven years.",
                       rel=[("Doran Pike", "Mentor", "Taught her to read a ledger for what is missing"), ("Hesk Varrow", "Superior", "Acting harbor-master; signs everything she keeps")],
                       loc1="Harrowmere, lower quay", loc2="Harrowmere, lower quay", status1="Healthy, under-slept", status2="Healthy, under-slept",
                       notes1="**Knows (as of The Tallow Ledger — Chapter 3):** Forty-seven tallow casks were entered in the ledger and never landed.",
                       notes2="**Knows (as of The Tallow Ledger — Chapter 3):** Forty-seven tallow casks were entered in the ledger and never landed.\n**Knows (as of Salt and Signal — Chapter 4):** The original entry survives in the Tally House sealed room, and Hesk Varrow knows she knows."),
    "Doran Pike": dict(since=1, role="Senior archivist, Tally House", age="61", gender="Male",
                       look="Tall, stooped, with a clerk's permanent squint and a habit of straightening whatever is nearest.",
                       personality="Principled to a fault and quietly stubborn. Indispensable to every faction because he refuses to take a side.",
                       background="Thirty years among the Tally House records; the last person who can read the pre-Charter shorthand.",
                       rel=[("Mara Quill", "Protege", "The best tallier he has trained")],
                       loc1="The Tally House, records room", loc2="The Tally House, records room", status1="Healthy", status2="Healthy",
                       notes1="**Knows (as of The Tallow Ledger — Chapter 3):** The ledger page was replaced, not corrected.",
                       notes2="**Knows (as of The Tallow Ledger — Chapter 3):** The ledger page was replaced, not corrected."),
    "Hesk Varrow": dict(since=1, role="Acting harbor-master", age="52", gender="Male",
                        look="Broad and unhurried, with a seal-ring he turns when listening.",
                        personality="Measured and controlled. Manages trouble through paperwork and deniable wording. Believes every problem is a document problem.",
                        background="A purser who rose when the last harbor-master died without an heir. Holds the post only until the Guild votes.",
                        rel=[("Mara Quill", "Subordinate", "He needs her signature and fears her care"), ("Ilsa Brandt", "Patron", "Her Union money keeps him in post")],
                        loc1="Harrowmere, harbor-master's office", loc2="Harrowmere, harbor-master's office", status1="Healthy", status2="Healthy",
                        notes1="Has asked Mara Quill to sign an amended tallow ledger.",
                        notes2="Has asked Mara Quill to sign an amended tallow ledger.\n**Knows (as of Salt and Signal — Chapter 4):** Mara Quill has seen the sealed original."),
    "Ilsa Brandt": dict(since=1, role="Factor for the Tidewright Union", age="40", gender="Female",
                        look="Always dressed for rain; carries a folding rule she uses as a pointer.",
                        personality="Patient and observant. Asks questions she already knows the answers to. Deniable by design.",
                        background="Came to Harrowmere eight years ago to buy tallow and stayed to buy the people who count it.",
                        rel=[("Hesk Varrow", "Client", "Pays for his quiet")],
                        loc1="Harrowmere, Union counting-house", loc2="Harrowmere, Union counting-house", status1="Healthy", status2="Healthy",
                        notes1="Wants to learn what Mara Quill knows.", notes2="Wants to learn what Mara Quill knows."),
    "Tamsin O'Rook": dict(since=2, role="Clerk, harbor-master's office", age="23", gender="Female",
                          look="Small and quick, copper hair cut short, ink on both cuffs.",
                          personality="Eager to be useful and slow to ask why. Loyal to whoever gave her the post.",
                          background="Hired by Hesk Varrow the winter the tallow casks went missing.",
                          rel=[("Hesk Varrow", "Employer", "Does what the wording of an errand implies")],
                          loc1="", loc2="Harrowmere, harbor-master's office", status1="", status2="Healthy",
                          notes1="", notes2="Sent to the Tally House to retrieve a document she was not told the contents of."),
}

FACTIONS = {
    "Harbor Guild": dict(since=1, type="Guild", hq="The Tally House", sphere="Harrowmere's quays and the lower canals", founded="Under the Charter of Three Seals",
                         public="Keeps honest weights, honest ledgers and open water.", actual="Keeps the Guild's own members solvent first.",
                         members=[("Hesk Varrow", "Acting harbor-master"), ("Mara Quill", "Ledger-keeper"), ("Doran Pike", "Archivist")],
                         rel=[("Tidewright Union", "Rival", "Competes for the tallow trade"), ("Fen Wardens", "Neutral", "Escorts the Guild's convoys")],
                         standing1="Nominally dominant on the quays", standing2="Nominally dominant on the quays",
                         cond1="Divided over who should be harbor-master", cond2="Openly divided; the vote has been postponed"),
    "Tidewright Union": dict(since=1, type="Merchant union", hq="The Union counting-house", sphere="Tallow, rope and lamp-oil trade", founded="Forty years ago by dissident Guild members",
                             public="Free trade and fair prices.", actual="Control of the tallow supply.",
                             members=[("Ilsa Brandt", "Factor")], rel=[("Harbor Guild", "Rival", "Buys its way into Guild offices")],
                             standing1="Gaining ground", standing2="Gaining ground", cond1="Unified", cond2="Unified"),
    "Fen Wardens": dict(since=1, type="Militia", hq="The Marrowfen Reach", sphere="The canals beyond the quays and the Flats", founded="After the Drowned Bell",
                        public="Keeps the roads and channels open.", actual="Keeps whichever faction pays its muster.",
                        members=[], rel=[("Harbor Guild", "Client", "Escorts convoys")],
                        standing1="Neutral, watching", standing2="Neutral, watching", cond1="Stretched thin", cond2="Stretched thin"),
}

LOCATIONS = {
    "Harrowmere": dict(since=1, type="City", located="The Marrowfen Reach", size="Major port", controlled="Harbor Guild",
                       desc="A city of brackish canals and stilt-houses where every bridge has a toll and every quay a clerk. The air smells of tallow smoke and wet rope.",
                       history="Founded on the Charter of Three Seals, which divided the harbor between guild, union and wardens.",
                       features=["The lower quay", "The Warden's Stair", "The harbor-master's office"],
                       inhabitants=[("Harbor Guild", "Governing guild", "Holds the harbor-master's seal")], cond1="Thriving", cond2="Thriving"),
    "The Tally House": dict(since=1, type="Building", located="Harrowmere", size="Large", controlled="Harbor Guild",
                            desc="A long brick hall with narrow windows, built so that no ledger ever sits in direct sun. Corridors of shelved volumes lead to a sealed room at the back.",
                            history="Raised in the first year of the Charter to hold the three seals' accounts.",
                            features=["The records room", "The sealed room", "The ledger desk"],
                            inhabitants=[("Doran Pike", "Archivist", "Keeps the keys"), ("Mara Quill", "Ledger-keeper", "Works at the long desk")],
                            cond1="Orderly", cond2="Orderly; the sealed room has been opened once"),
    "The Drowned Flats": dict(since=2, type="Region", located="The Marrowfen Reach", size="Vast wetland", controlled="None",
                              desc="Mile on mile of reed and standing water that floods twice a day. Fishers know the paths; nobody else should.",
                              history="Where the old bell-tower stands half sunk. See the Drowned Bell.",
                              features=["The bell-tower", "Reed-cutters' paths"], inhabitants=[("Fen Wardens", "Patrol", "Rarely seen")],
                              cond1="Flooded", cond2="Flooded"),
    "The Marrowfen Reach": dict(since=1, type="Region", located="The coast", size="A province", controlled="Harbor Guild (nominally)",
                                desc="A low coast of fen and salt-pan, cut by canals, with a single deep harbor at Harrowmere.",
                                history="Settled by reed-cutters, then chartered.", features=["Salt-pans", "The canal network"],
                                inhabitants=[("Harbor Guild", "Chartered authority", "Holds the charter")], cond1="Quiet", cond2="Quiet"),
}

MYTHS = {
    "The Charter of Three Seals": dict(since=1, type="Foundation document", culture="Harrowmere", age="Two centuries",
                                       summary="Three founding seals, held by guild, union and wardens, must all agree before the harbor's law can change.",
                                       truth="Partially True", explain="Only two of the three seals ever agreed; the third was forged."),
    "The Tithe Ledger Clause": dict(since=1, type="Legal clause", culture="Harbor Guild", age="Centuries old",
                                    summary="Any entry in the tithe ledger, once sealed, may only be corrected by a visible strike-through, never by replacement.",
                                    truth="Literally True", explain="It is why a replaced page is a crime and a corrected one is not."),
    "The Drowned Bell": dict(since=1, type="Cautionary tale", culture="The Flats", age="Ancient",
                             summary="A bell that rang itself under the water the night the tower sank, warning boats off the shallows.",
                             truth="Symbolic", explain="The sound is a hollow reed-bed in the wind."),
    "The Ink-Debt Rumor": dict(since=2, type="Institutional rumor", culture="Tally House", age="Recent",
                               summary="Clerks whisper that anyone who falsifies a sealed entry owes the ledger a debt that outlives them.",
                               truth="Fabricated", explain="Started by Doran Pike to keep young clerks honest."),
}


def entity_text(kind, name, d, ver):
    since = d["since"]
    if kind == "characters":
        loc, status = (d["loc1"], d["status1"]) if ver == 1 else (d["loc2"], d["status2"])
        notes = d["notes1"] if ver == 1 else d["notes2"]
        rel = "\n".join(f"| [[{n}]] | {r} | {x} |" for n, r, x in d["rel"])
        return f"""# {name}

## Identity
- **Full Name:** {name}
- **Age:** {d['age']}
- **Gender:** {d['gender']}
- **Occupation / Role:** {d['role']}

## Appearance
{d['look']}

## Personality
{d['personality']}

## Background
{d['background']}

## Relationships
| Person | Relationship | Notes |
|--------|-------------|-------|
{rel}

## Current Status
- **Location:** {loc}
- **Physical condition:** {status}
- **Story state:** Alive
- **Last updated in:** {S1 if ver == 1 else S2} — Chapter {3 if ver == 1 else 4}

## Notes
{notes or 'None at this time.'}
"""
    if kind == "factions":
        standing, cond = (d["standing1"], d["cond1"]) if ver == 1 else (d["standing2"], d["cond2"])
        members = "\n".join(f"| [[{n}]] | {r} | — |" for n, r in d["members"]) or "| — | — | — |"
        rel = "\n".join(f"| [[{n}]] | {r} | {x} |" for n, r, x in d["rel"])
        return f"""# {name}

## Identity
- **Type:** {d['type']}
- **Headquarters:** {d['hq']}
- **Sphere of Influence:** {d['sphere']}
- **Founded:** {d['founded']}

## Goals
- **Public position:** {d['public']}
- **Actual agenda:** {d['actual']}

## Power Base
Control of the offices and records it staffs.

## Structure
A small council with one acting head.

## Key Members
| Person | Role | Notes |
|--------|------|-------|
{members}

## Relationships
| Faction / Entity | Relationship | Notes |
|-----------------|-------------|-------|
{rel}

## Current Status
- **Standing:** {standing}
- **Internal condition:** {cond}
- **Last updated in:** {S1 if ver == 1 else S2} — Chapter {3 if ver == 1 else 4}

## Notes
None at this time.
"""
    if kind == "points_of_interest":
        cond = d["cond1"] if ver == 1 else d["cond2"]
        feats = "\n".join(f"- {f}" for f in d["features"])
        inh = "\n".join(f"| [[{n}]] | {r} | {x} |" for n, r, x in d["inhabitants"])
        return f"""# {name}

## Overview
- **Type:** {d['type']}
- **Located in:** {d['located']}
- **Size / Scale:** {d['size']}
- **Controlled by:** {d['controlled']}

## Description
{d['desc']}

## History
{d['history']}

## Notable Features
{feats}

## Key Inhabitants / Factions
| Name | Role | Notes |
|------|------|-------|
{inh}

## Current Status
- **Condition:** {cond}
- **Last updated in:** {S1 if ver == 1 else S2} — Chapter {3 if ver == 1 else 4}

## Notes
None at this time.
"""
    return f"""# {name}

## Overview
- **Type:** {d['type']}
- **Origin culture:** {d['culture']}
- **Age:** {d['age']}

## Summary
{d['summary']}

## Full Text
> {d['summary']}

## Characters Involved
| Name | Role in Myth | Notes |
|------|-------------|-------|
| — | — | — |

## Truth Level
- **Classification:** {d['truth']}
- **Explanation:** {d['explain']}

## Connections
- **Related locations:** None
- **Related characters:** None
- **Related myths:** None

## Notes
None at this time.
"""


def world_entities(ver):
    """Yield (kind, name, text) for the world as it stands after story `ver`."""
    for kind, group in (("characters", CHARACTERS), ("factions", FACTIONS), ("points_of_interest", LOCATIONS), ("mythology", MYTHS)):
        for name, d in group.items():
            if d["since"] <= ver:
                yield kind, name, entity_text(kind, name, d, ver)


DESCRIPTION = f"""# {WORLD}

## Overview
Harrowmere is a fenland port-republic of brackish canals, stilt-houses and guild charters, grounded and slightly damp, where accounts matter more than swords. There is no magic; power is held by whoever keeps the records.

## Geography
- **Major regions:** The Marrowfen Reach (the inhabited coast), the Drowned Flats (reed and tidal marsh to the east), the harbor at Harrowmere
- **Climate:** Cool, wet, windy. Fog most mornings, salt on everything.
- **Notable natural features:** The canal network, the salt-pans, the half-sunk bell-tower in the Flats.

## History

| Era / Period | Key Events |
|-------------|-----------|
| The Reed Years | Scattered reed-cutters settle the Reach. |
| The Charter | The Charter of Three Seals divides the harbor between guild, union and wardens. |
| The Long Audit | Two centuries of quiet, in which the ledgers are trusted and rarely read. |

## Population
- **Total (approximate):** Moderate; about forty thousand in the Reach
- **Major species / peoples:** Humans only; reed-cutters, guild families, Union merchants
- **Major factions / nations:** Harbor Guild (governs the quays), Tidewright Union (tallow and rope trade), Fen Wardens (militia)

## Economy
Tallow, rope, salt and lamp-oil, carried on barges and taxed at the quay. The tallow-tax ledger is the republic's main revenue record.

## Religion / Belief Systems
No organised religion. The Drowned Bell is a folk belief; the Charter is treated with something close to reverence.

## Current State
The last harbor-master died without an heir and Hesk Varrow holds the seal as acting head until the Guild votes. The Union is buying influence in the Guild offices, and a replaced page in the tallow ledger has made every record suspect.

## Notes
Tone: quiet, procedural, morally grey. Avoid swashbuckling; conflict is paper and consequence.
"""

HOOKS = f"""# Story Hooks — {WORLD}

Story hooks are narrative seeds: situations, tensions, questions, or character dynamics that could grow into a story. They are collected here so the Story Ideator can browse them.

**Who adds hooks:** The user (at any time) and the Story Analyzer (after a chapter is completed, if events reveal new possibilities).
**Status values:** `Open` · `In Use` · `Archived`

---

### The Replaced Page
- **Source:** User-defined
- **Status:** `In Use ({S1})`
- **Hook:** A ledger page is replaced rather than corrected, and the one clerk who notices refuses to sign.
- **Related:** [[Mara Quill]], [[The Tally House]], [[The Tithe Ledger Clause]]

### The Sealed Room
- **Source:** Story Analyzer — {S1}, Chapter 3
- **Status:** `In Use ({S2})`
- **Hook:** The Tally House keeps a sealed room that only the archivist has opened in thirty years. What else is in it?
- **Related:** [[Doran Pike]], [[The Tally House]]

### The Third Seal
- **Source:** Story Analyzer — {S2}, Chapter 4
- **Status:** `Open`
- **Hook:** If the third seal of the Charter was forged, every law passed under it is open to challenge. Who knows, and who profits?
- **Related:** [[The Charter of Three Seals]], [[Tidewright Union]]

### The Bell Under the Water
- **Source:** User-defined
- **Status:** `Archived`
- **Hook:** Boatmen swear the Drowned Bell still rings. Retired: the sound was explained as reeds.
- **Related:** [[The Drowned Bell]], [[The Drowned Flats]]
"""

SUMMARY_TMPL = """# SUMMARY — {world}

> **Last synchronized:** {date} — after consolidating [[{story}]] (Position {pos})
> This file is auto-maintained by the Writing Assistant. Do not edit manually.

---

## World Overview

Harrowmere is a damp fenland port-republic where accounts matter more than swords, with no magic and power held by whoever keeps the records. Three bodies share the harbor under the Charter of Three Seals.

## Active Tensions

{tensions}

---

## Characters

| Name | Role | Description | Location / Status |
|------|------|-------------|-------------------|
{characters}

---

## Factions

| Name | Type | Current Standing |
|------|------|-----------------|
{factions}

---

## Locations

| Name | Type | Description |
|------|------|-------------|
{locations}

---

## Active Mythology / Beliefs

| Name | Type | Relevance |
|------|------|-----------|
{myths}
"""


def summary(ver):
    chars = "\n".join(
        f"| [[{n}]] | {d['role']} | {d['personality'].split('.')[0]} | {d['loc1'] if ver == 1 else d['loc2']} · Alive |"
        for n, d in CHARACTERS.items() if d["since"] <= ver)
    facs = "\n".join(f"| [[{n}]] | {d['type']} | {d['standing1'] if ver == 1 else d['standing2']} |" for n, d in FACTIONS.items())
    locs = "\n".join(f"| [[{n}]] | {d['type']} | {d['desc'].split('.')[0]} |" for n, d in LOCATIONS.items() if d["since"] <= ver)
    myths = "\n".join(f"| [[{n}]] | {d['type']} | {d['summary'].split('.')[0]} |" for n, d in MYTHS.items() if d["since"] <= ver)
    tensions = ("The last harbor-master died without an heir and Hesk Varrow holds the seal as acting head until the Guild votes. "
                "A replaced page in the tallow ledger has made every record suspect, and the Union is buying influence in the Guild offices.")
    if ver == 2:
        tensions += " Mara Quill has seen the sealed original, and Hesk Varrow knows it."
    return SUMMARY_TMPL.format(world=WORLD, date=DATE1 if ver == 1 else DATE2, story=S1 if ver == 1 else S2, pos=ver,
                               tensions=tensions, characters=chars, factions=facs, locations=locs, myths=myths)


WORLD_ORDER = f"""# World Order — {WORLD}

> **Last synchronized:** {DATE2} — after {S2} Chapter 4 analyzed (story complete)
> Maintained by the World Archivist and updated by Story Ideator and Story Analyzer.
> Do not reorder rows manually — invoke World Archivist to renumber positions.

**What this records:** The chronological sequence of all stories and chapters set in this world, at chapter-level granularity.

**Concurrency:** Units with the same Position number happen at the same in-world time. Table sorted by Position ascending.

**Status:** `Not Started` · `In Progress` · `Complete`

**Unit:** `Full Story` (Short Story / Novelette) · `Ch. N` (Book) · `Bk. N Ch. M` (Book Series) · `TBD` (pre-outline placeholder)

---

## Story Order

| Position | Story | Unit | In-World Date | Status | Notes |
|----------|-------|------|---------------|--------|-------|
| 1 | [[{S1}]] | Full Story | Autumn, the year the harbor-master died | Complete | The replaced page |
| 2 | [[{S2}]] | Full Story | Early winter, the same year | Complete | The sealed room |

---

## Notes

No in-world calendar is established; dates are prose descriptions relative to world events.
"""

TIMELINE = f"""# World Timeline — {WORLD}

> **Last synchronized:** {DATE2}
> Maintained by the World Archivist (Consolidate operation).
> Entries are added from each story's state/Timeline.md during consolidation.
> Do not edit manually — invoke World Archivist → Consolidate to add entries.

**What this records:** All significant events across every story set in this world, ordered by WORLD_ORDER.md position.

**Format:** Entries are grouped by story. Within each story, chapters are listed in order.

---

## Events

### [[{S1}]] (Position 1)
- **[Position 1: Chapter 1 — The Amended Page]** Autumn — Mara Quill is asked to countersign a corrected tallow ledger and notices the page was replaced, not struck through.
- **[Position 1: Chapter 2 — Forty-Seven Casks]** Autumn — She traces forty-seven casks entered but never landed; Ilsa Brandt approaches her.
- **[Position 1: Chapter 3 — The Strike-Through]** Autumn — Mara refuses to sign, and Doran Pike confirms the replacement.

### [[{S2}]] (Position 2)
- **[Position 2: Chapter 1 — The Errand]** Early winter — Hesk Varrow sends Tamsin O'Rook to retrieve the original entry.
- **[Position 2: Chapter 2 — The Sealed Room]** Early winter — Mara and Doran open the sealed room.
- **[Position 2: Chapter 3 — The Audit]** Early winter — Hesk orders a public audit he expects to clear him.
- **[Position 2: Chapter 4 — The Original]** Early winter — The original entry is found; Hesk is exposed but still holds the seal.
- **[Position 2: open thread]** story close — Ilsa Brandt's scheme to learn what Mara knows remains unresolved at story end.

---

## Notes

None at this time.
"""


def snapshot_manifest(pos, story, date, counts):
    total = sum(counts.values())
    return f"""# Snapshot Manifest — Position {pos}

> **Created:** {date}
> **Captures world state AFTER this story completed.**
> Stories at position {pos + 1} and beyond should use this as their baseline.

## Story
- **Story:** [[{story}]]
- **Unit:** Full Story
- **Position:** {pos}

## Contents
- **Characters:** {counts['characters']} file(s)
- **Factions:** {counts['factions']} file(s)
- **Locations (Points of Interest):** {counts['points_of_interest']} file(s)
- **Mythology:** {counts['mythology']} file(s)
- **Total entities:** {total}

## Notes

This snapshot was created automatically by the Story Analyzer after chapter completion.
World consolidation (merging state/bible/ into worlds/) should occur before this snapshot
is taken so that the snapshot reflects all story-driven world changes.

If consolidation has not yet occurred, this snapshot reflects the pre-story world state only.
Invoke the World Archivist → Consolidate, then re-run create_snapshot.py to update.
"""


def build_world(dest):
    w = Path(dest) / "worlds" / WORLD
    write(w / "DESCRIPTION.md", DESCRIPTION)
    write(w / "HOOKS.md", HOOKS)
    write(w / "WORLD_ORDER.md", WORLD_ORDER)
    write(w / "TIMELINE.md", TIMELINE)
    write(w / "SUMMARY.md", summary(2))
    for kind, name, text in world_entities(2):
        write(w / kind / f"{name}.md", text)
    index_rows = []
    for ver, story, date in ((1, S1, DATE1), (2, S2, DATE2)):
        snap = w / "snapshots" / str(ver)
        counts = {k: 0 for k in ("characters", "factions", "points_of_interest", "mythology")}
        for kind, name, text in world_entities(ver):
            write(snap / kind / f"{name}.md", text)
            counts[kind] += 1
        write(snap / "DESCRIPTION.md", DESCRIPTION)
        write(snap / "manifest.md", snapshot_manifest(ver, story, date, counts))
        index_rows.append(f"| {ver} | [[{story}]] | Full Story | {date} | Auto-created by Story Analyzer |")
    write(w / "snapshots" / "manifest.md", """# World Snapshots — Index

> Maintained by create_snapshot.py. Do not edit manually.
> Each entry records the world state AFTER the story at that position completed.
> The story at position N+1 uses snapshot N as its world baseline.

| Position | Story | Unit | Date Created | Notes |
|----------|-------|------|--------------|-------|
""" + "\n".join(index_rows))


# ----------------------------------------------------------------------------- stories
def concept(story, structure, fmt, logline, premise, chars, tensions, hooks, n):
    ch = "\n".join(f"| [[{c}]] | {r} | — |" for c, r in chars)
    hk = "\n".join(f"- [[worlds/{WORLD}/HOOKS#{h}]] — used" for h in hooks)
    return f"""# {story}

## Overview
- **World:** {WORLD}
- **Format:** {fmt} ({n} chapters)
- **Status:** `Complete`

## Logline
{logline}

## Premise
{premise}

## Themes
- The cost of keeping an honest record.
- Who is protected by a neat page.

## Point of View
- **Protagonist:** [[Mara Quill]]
- **POV type:** Third limited
- **Notes:** One POV throughout.

## Suggested Story Structure
- **Structure:** [[{structure}]]
- **Rationale:** Suits a short, escalating procedural story.

## Key Characters
| Character | Role | Notes |
|-----------|------|-------|
{ch}

## Central Conflict
Mara wants the record to stay true; Hesk Varrow needs it to say something else.

## Key Tensions
{tensions}

## Hooks Used
{hk}

## Tropes
- **Incorporating:** None specified
- **Avoiding:** None specified

## Open Questions
- None at this time.

## Notes
Default Style.
"""


def outline(story, structure, n, pos, before, after, chapters):
    ch = "\n".join(
        f"""### Chapter {i} — {title}
- **Structure stage(s):** {stage}
- **POV:** [[Mara Quill]]
- **Location(s):** [[The Tally House]]
- **Characters present:** [[Mara Quill]]
- **Chapter goal:** {goal}
- **Summary:** {goal}
- **Key beats:**
  1. A document is examined.
  2. Someone leans on someone.
- **Ending beat:** {end}
- **Notes:** None.
""" for i, (title, stage, goal, end) in enumerate(chapters, 1))
    return f"""# Outline — {story}

## Overview
- **World:** {WORLD}
- **Format:** Novelette
- **Structure:** [[{structure}]]
- **Total chapters:** {n}
- **Target word count:** 5,000-15,000 words
- **World Order Position:** {pos}
- **Story before:** {before}
- **Story after:** {after}

## Subplot Threads
| Thread | Description | Chapters Active | Resolution Chapter |
|--------|-------------|----------------|--------------------|
| The replaced page | Who replaced it and why | Ch. 1-{n} | Ch. {n} |

---

## Chapters

{ch}"""


def chapter(n, title, text):
    return f"# Chapter {n} — {title}\n\n{text}\n"


CH1 = [
    ("The Amended Page", "Mara Quill read the corrected page twice. The figures were right; that was the trouble. A struck-through entry shows its scar. This one had none.\n\nShe turned the page over and held it to the lamp, and the fibres told her what the clerk's hand had not: it was newer than the book."),
    ("Forty-Seven Casks", "Forty-seven casks of tallow had been entered in the ledger and never landed. Mara counted them by the quay-tally, by the toll-book and by the barge-masters' slips, and the three sources agreed with each other and with nothing else.\n\nIlsa Brandt found her at the lower quay at dusk, folding rule in hand, and asked how the work was going as though she did not already know."),
    ("The Strike-Through", "'The Clause says correct, never replace,' Mara said, and set the pen down.\n\nHesk Varrow turned his seal-ring once. 'It says a great deal. Sign.' She did not. Behind her, Doran Pike straightened a shelf that did not need it, which was how she knew he agreed."),
]
CH2 = [
    ("The Errand", "Tamsin O'Rook was told to fetch a folio from the Tally House and not to read it. She did not ask which folio, because the wording of the errand made it obvious, and that was the whole point of the wording."),
    ("The Sealed Room", "Doran Pike had not opened the sealed room in thirty years. He did it with a key he kept on a cord under his shirt, and Mara Quill, standing behind him, realised the key was warm."),
    ("The Audit", "Hesk Varrow announced a public audit of the tallow ledger. It was a good move: a man who calls for the audit is, for a day or two, the one being wronged."),
    ("The Original", "The original entry lay in the sealed room under a bell-jar, untouched. Mara read it aloud so there would be a witness. Hesk Varrow, in the doorway, turned his ring and asked who else knew."),
]


def build_story1(dest):
    s = Path(dest) / "stories" / S1
    write(s / "CONCEPT.md", concept(S1, "Fichtean Curve", "Novelette", "A ledger-keeper who will not countersign a replaced page is left alone with what she knows.",
                                    "Mara Quill discovers that a page in the tallow ledger was replaced rather than corrected. Refusing to sign costs her the goodwill of every faction that benefits from a neat record.",
                                    [("Mara Quill", "Protagonist"), ("Hesk Varrow", "Antagonist"), ("Doran Pike", "Supporting"), ("Ilsa Brandt", "Supporting")],
                                    "- A refusal is also an accusation.\n- The replaced page protects someone in every faction.", ["The Replaced Page"], 3))
    write(s / "OUTLINE.md", outline(S1, "Fichtean Curve", 3, 1, '"none — first entry"', f"[[{S2}]]", [
        ("The Amended Page", "Rising Action", "Mara finds the page was replaced.", "She holds the page to the lamp."),
        ("Forty-Seven Casks", "Rising Action", "Mara counts what never landed.", "Ilsa Brandt asks how the work is going."),
        ("The Strike-Through", "Climax", "Mara refuses to sign.", "Doran Pike straightens a shelf.")]))
    for i, (title, text) in enumerate(CH1, 1):
        write(s / "chapters" / f"Chapter_{i:02d}.md", chapter(i, title, text))
    write(s / "chapters" / "Chapter_03_original.md", chapter(3, "The Strike-Through (first draft)", "'Sign,' said Hesk Varrow. She signed. The draft ended there, and the author threw it away in all but name."))
    write(s / "state" / "Timeline.md", f"""# Timeline — {S1}

> Maintained by the Story Analyzer. A new entry is appended after each completed chapter.

## Events

- **[Chapter 1 — The Amended Page]** Autumn — Mara Quill is asked to countersign a corrected tallow ledger and notices the page was replaced, not struck through.
- **[Chapter 2 — Forty-Seven Casks]** Autumn — She traces forty-seven casks entered but never landed; Ilsa Brandt approaches her.
- **[Chapter 3 — The Strike-Through]** Autumn — Mara refuses to sign, and Doran Pike confirms the replacement.
""")
    write(s / "state" / "ACTIVE_SCHEMES.md", f"""# Active Schemes — {S1}

> **What this is:** a live registry of deceptions in flight within this story.
>
> **Maintained by:** Story Analyzer (updates after each chapter).

---

## Active Ledger

| ID | Owner | Target(s) | Nature | Status | Origin | Last touched |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | [[Hesk Varrow]] | [[Mara Quill]] | Replaced ledger page presented as a correction | Exposed | Chapter 1 | Chapter 3 |

---

## Detail

---

## Resolution Log

### S1 — The replaced page
→ Exposed at Chapter 3: Mara refused to sign and Doran Pike confirmed the replacement.

- **Owner:** [[Hesk Varrow]]
- **Target(s):** [[Mara Quill]]
- **Nature:** Replaced ledger page presented as a correction
- **Status:** Exposed
- **Origin:** Chapter 1
- **Last touched:** Chapter 3
- **Specifics:** The page is newer than the binding and carries no strike-through.
- **Knowledge gaps:** Mara Quill did not know until Chapter 1.
""")
    write(s / "state" / "STORY_FACTS.md", f"""# Story Facts — {S1}

> **What this is:** a live ledger of plot-consequential facts.
>
> **Maintained by:** Story Analyzer (updates after each chapter).

---

## Ledger

| ID | Category | Fact | Status | Origin | Last touched |
| -- | -------- | ---- | ------ | ------ | ------------ |
| F1 | Quantity | Forty-seven tallow casks were entered and never landed | Current | Chapter 2 | Chapter 3 |

---

## Detail

### F1 — The missing casks

- **Category:** Quantity
- **Fact:** Forty-seven tallow casks were entered and never landed.
- **Specifics:** Quay-tally, toll-book and barge slips agree with each other and not with the ledger.
- **Status:** Current
- **Origin:** Chapter 2
- **Last touched:** Chapter 3
- **Related:** [[Mara Quill]]

---

## Superseded Log

*(Facts that changed on-page.)*
""")
    for kind, name in (("characters", "Mara Quill"), ("characters", "Doran Pike"), ("characters", "Ilsa Brandt")):
        d = CHARACTERS[name]
        write(s / "state" / "bible" / kind / f"{name}.md", entity_text(kind, name, d, 1))


def build_story2(dest):
    s = Path(dest) / "stories" / S2
    write(s / "CONCEPT.md", concept(S2, "Freytag's Pyramid", "Novelette", "An acting harbor-master who cannot let a page be found sends a clerk who does not know what she is looking for.",
                                    "Hesk Varrow tries to retrieve the original entry before the audit he called can reach it, while Mara Quill and Doran Pike open the sealed room.",
                                    [("Hesk Varrow", "Antagonist"), ("Tamsin O'Rook", "Supporting"), ("Mara Quill", "Protagonist"), ("Doran Pike", "Supporting")],
                                    "- A man who calls for an audit is briefly the one being wronged.\n- A clerk follows the wording of an errand.", ["The Sealed Room"], 4))
    write(s / "OUTLINE.md", outline(S2, "Freytag's Pyramid", 4, 2, f"[[{S1}]]", '"none — last entry"', [
        ("The Errand", "Introduction", "Hesk sends Tamsin for the folio.", "Tamsin leaves for the Tally House."),
        ("The Sealed Room", "Rising Action", "Mara and Doran open the sealed room.", "The key is warm."),
        ("The Audit", "Climax", "Hesk calls a public audit.", "The audit is announced."),
        ("The Original", "Catastrophe", "The original entry is found.", "Hesk asks who else knows.")]))
    for i, (title, text) in enumerate(CH2, 1):
        write(s / "chapters" / f"Chapter_{i:02d}.md", chapter(i, title, text))
    write(s / "state" / "Timeline.md", f"""# Timeline — {S2}

> Maintained by the Story Analyzer. A new entry is appended after each completed chapter.

## Events

- **[Chapter 1 — The Errand]** Early winter — Hesk Varrow sends Tamsin O'Rook to retrieve the original entry.
- **[Chapter 2 — The Sealed Room]** Early winter — Mara and Doran open the sealed room.
- **[Chapter 3 — The Audit]** Early winter — Hesk orders a public audit he expects to clear him.
- **[Chapter 4 — The Original]** Early winter — The original entry is found; Hesk is exposed but still holds the seal.
""")
    write(s / "state" / "ACTIVE_SCHEMES.md", f"""# Active Schemes — {S2}

> **What this is:** a live registry of deceptions in flight within this story.
>
> **Maintained by:** Story Analyzer (updates after each chapter).

---

## Active Ledger

| ID | Owner | Target(s) | Nature | Status | Origin | Last touched |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | [[Hesk Varrow]] | [[Tamsin O'Rook]] | Errand worded so she does not know what she fetches | Resolved | Chapter 1 | Chapter 2 |
| S2 | [[Ilsa Brandt]] | [[Mara Quill]] | Union money keeps the acting harbor-master in post | Active | Chapter 3 | Chapter 4 |

---

## Detail

### S2 — The quiet money

- **Owner:** [[Ilsa Brandt]]
- **Target(s):** [[Mara Quill]], [[Doran Pike]]
- **Nature:** Union money keeps the acting harbor-master in post
- **Status:** Active
- **Origin:** Chapter 3
- **Last touched:** Chapter 4
- **Specifics:** Paid as "lamp-oil subsidy" in the Guild's own books.
- **Knowledge gaps:** Everyone in the Guild except Hesk Varrow.
- **Notes:** Fragile after the audit.

---

## Resolution Log

### S1 — The worded errand
→ Resolved at Chapter 2: Tamsin returned empty-handed and unaware.

- **Owner:** [[Hesk Varrow]]
- **Target(s):** [[Tamsin O'Rook]]
- **Nature:** Errand worded so she does not know what she fetches
- **Status:** Resolved
- **Origin:** Chapter 1
- **Last touched:** Chapter 2
- **Specifics:** "Fetch the folio and do not read it."
- **Knowledge gaps:** Tamsin O'Rook.
""")
    write(s / "state" / "STORY_FACTS.md", f"""# Story Facts — {S2}

> **What this is:** a live ledger of plot-consequential facts.
>
> **Maintained by:** Story Analyzer (updates after each chapter).

---

## Ledger

| ID | Category | Fact | Status | Origin | Last touched |
| -- | -------- | ---- | ------ | ------ | ------------ |
| F1 | Logistics | The sealed room has one key, kept by Doran Pike on a cord | Current | Chapter 2 | Chapter 4 |
| F2 | Fingerprint | The replaced page is newer than the binding | Superseded | Chapter 1 | Chapter 4 |
| F3 | Fingerprint | The original entry survives in the sealed room under a bell-jar | Current | Chapter 4 | Chapter 4 |

---

## Detail

### F1 — The only key

- **Category:** Logistics
- **Fact:** The sealed room has one key, kept by Doran Pike on a cord.
- **Specifics:** It is warm because he wears it.
- **Status:** Current
- **Origin:** Chapter 2
- **Last touched:** Chapter 4
- **Related:** [[Doran Pike]], [[The Tally House]]

### F3 — The surviving original

- **Category:** Fingerprint
- **Fact:** The original entry survives in the sealed room under a bell-jar.
- **Specifics:** Forty-seven casks, in the original hand.
- **Status:** Current
- **Origin:** Chapter 4
- **Last touched:** Chapter 4
- **Related:** [[Mara Quill]]

---

## Superseded Log

### F2 — The replaced page
→ Superseded at Chapter 4; see F3 for updated value.

- **Category:** Fingerprint
- **Fact:** The replaced page is newer than the binding.
- **Status:** Superseded
""")
    for kind, name in (("characters", "Mara Quill"), ("characters", "Hesk Varrow"), ("characters", "Tamsin O'Rook"),
                       ("factions", "Harbor Guild"), ("points_of_interest", "The Tally House")):
        group = {"characters": CHARACTERS, "factions": FACTIONS, "points_of_interest": LOCATIONS}[kind]
        write(s / "state" / "bible" / kind / f"{name}.md", entity_text(kind, name, group[name], 2))


def build_sample(dest, marker=False):
    dest = Path(dest)
    build_world(dest)
    build_story1(dest)
    build_story2(dest)
    styles = dest / "writing_concepts" / "styles"
    styles.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO / "skills" / "writing-room" / "shared" / "craft" / "styles" / "Default Style.md", styles / "Default Style.md")
    if marker:
        from wr_init import MARKER_TEXT
        (dest / "writing-room.toml").write_bytes((MARKER_TEXT).encode("utf-8"))


def rebuild_fixtures():
    """Replace the sample content in fixtures/legacy-v1/ (no marker, like a legacy project) and rebuild
    examples/sample-project/ (with marker). The legacy framework files in fixtures/legacy-v1/ are not touched."""
    legacy = REPO / "fixtures" / "legacy-v1"
    for d in ("worlds", "stories"):
        shutil.rmtree(legacy / d, ignore_errors=True)
    build_sample(legacy)
    example = REPO / "examples" / "sample-project"
    shutil.rmtree(example, ignore_errors=True)
    build_sample(example, marker=True)
    print(f"rebuilt {legacy} and {example}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dest")
    ap.add_argument("--marker", action="store_true", help="also write writing-room.toml")
    ap.add_argument("--fixtures", action="store_true", help="rebuild fixtures/legacy-v1 content and examples/sample-project")
    a = ap.parse_args()
    if a.fixtures:
        rebuild_fixtures()
    elif a.dest:
        build_sample(a.dest, a.marker)
        print(f"sample written to {a.dest}")
    else:
        ap.error("give --dest DIR or --fixtures")


if __name__ == "__main__":
    main()
