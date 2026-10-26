#!/usr/bin/env python3
"""
lm_studio_ideator.py
====================
A command-line Story Ideator that runs the Writing Room's concept-generation
workflow against a locally running LM Studio model instead of Claude.

HOW IT WORKS
------------
LM Studio exposes an OpenAI-compatible REST API at http://localhost:1234/v1.
This script uses the official `openai` Python library — pointed at that local
URL instead of api.openai.com — to send messages and receive responses.

All file I/O (reading world bibles, writing CONCEPT.md, updating HOOKS.md)
is handled by this script. The world bible is loaded into a single string and
injected as context at the start of the conversation. This mirrors what the
Claude agent does via its tool-use system, but in plain Python you can read
and modify yourself.

PREREQUISITES
-------------
1. LM Studio installed, with a model loaded.
2. LM Studio's local server enabled:
       LM Studio → Local Server tab → Start Server
   Default URL: http://localhost:1234
3. Python 3.9+ installed.
4. The `openai` Python library:
       pip install openai

USAGE
-----
    python scripts/lm_studio_ideator.py
    python scripts/lm_studio_ideator.py --world Harrowmere
    python scripts/lm_studio_ideator.py --world Harrowmere --mode autonomous
    python scripts/lm_studio_ideator.py --url http://localhost:1234 --temp 0.9
    python scripts/lm_studio_ideator.py --no-entities   # skip entity files

ARGUMENTS
---------
    --world       World name to use (skips interactive selection).
    --mode        'autonomous' or 'collaborative' (skips the opening prompt).
    --url         LM Studio server URL. Default: http://localhost:1234
    --model       Model ID as shown in LM Studio's model list.
                  If omitted, the script uses whatever model is currently loaded.
    --temp        Temperature: 0.0 (deterministic) to 1.0 (creative chaos).
                  Default: 0.8 — good for creative writing tasks.
    --no-entities Skip loading entity files (faster for large world bibles).

HOW TO READ THIS FILE
---------------------
The script is organised into clearly labelled sections. Read them top to bottom
to understand the full flow before looking at main() at the bottom, which ties
everything together. Each function has a docstring explaining not just *what*
it does but *why* it is written that way.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# DEPENDENCY CHECK
# ---------------------------------------------------------------------------
# We import the openai library here so we can give a clear, actionable error
# message if it is missing, rather than a confusing ModuleNotFoundError.
# The `try / except ImportError` pattern is the standard Python way to handle
# optional or not-yet-installed dependencies gracefully.
try:
    from openai import OpenAI
except ImportError:
    print("Error: The 'openai' library is not installed.")
    print("Fix it with:  pip install openai")
    sys.exit(1)


# ---------------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------------

# This script lives in Writing_Room/scripts/. __file__ is the script's own
# path, .parent is the scripts/ directory, .parent again is Writing_Room/.
# Using Path(__file__) instead of a hard-coded path means the script works
# regardless of where it's launched from.
WRITING_ROOM = Path(__file__).parent.parent

DEFAULT_URL     = "http://localhost:1234"
DEFAULT_API_KEY = "lm-studio"   # LM Studio ignores authentication; the library requires a non-empty value.
DEFAULT_TEMP    = 0.8           # 0 = deterministic / 1 = maximum randomness


# ---------------------------------------------------------------------------
# SYSTEM PROMPT
# ---------------------------------------------------------------------------
# The system prompt is the standing instruction set sent to the model at the
# start of every API request. It defines the model's role, constraints, and
# the exact output format it must use.
#
# In the Claude agent, this content is embedded in the agent's .md file.
# Here we define it as a Python string so a local model gets the same context.
#
# KEY FORMAT DECISION: We require the model to wrap its final approved concept
# in a ```concept ... ``` fenced code block. This gives us a reliable marker
# to detect when the concept is ready to save, without trying to parse free-
# form prose to figure out whether the model is "done".

SYSTEM_PROMPT = """\
You are a Story Ideator for a structured creative writing framework called the Writing Room.

YOUR ROLE
---------
Read world bible content provided by the user and produce a CONCEPT.md — a
structured story concept document that seeds all downstream agents (Outliner,
Planner, Draft Writer).

You do NOT write prose, chapters, or scenes. You generate the *idea*: premise,
themes, structure suggestion, character roles, and central tensions.

FINAL OUTPUT FORMAT
-------------------
When the user approves the concept, output it inside a fenced code block
labelled "concept" using EXACTLY this structure (fill every field):

```concept
# <Story Title>

## Story Details
- **World:** <World Name>
- **Format:** <Short Story | Novelette | Book | Book Series>
- **Suggested Structure:** <e.g. Three-Act, Hero's Journey, Five-Act>

## Logline
<One or two sentences — the story in its shortest form.>

## Premise
<A short paragraph expanding the logline: who, what, where, why it matters.>

## Central Conflict
<The core opposition driving the story. Be specific.>

## Protagonist(s)
<Name and one-sentence role for each.>

## Antagonist(s) / Opposing Force
<Name or description and one-sentence role.>

## Themes
- <Theme 1>
- <Theme 2>
- <Theme 3>

## Hooks Incorporated
<Titles of HOOKS.md entries woven into the concept, or "None".>

## Tropes
- **Incorporating:** <comma-separated list, or "None">
- **Avoiding:** <comma-separated list, or "None">

## Tone / Mood
<Brief description of emotional register and atmosphere.>

## Open Questions for the Outliner
- <Unresolved elements the Outliner should decide, or "None">
```

GUIDELINES
----------
- Ground every narrative choice in the world bible you are given.
- Do not invent facts that contradict the world bible.
- Respect tone and design constraints in DESCRIPTION.md.
- Present the concept as a formatted preview BEFORE outputting the final block.
- Only output the final ```concept block when the user says they approve.
- Never leave angle-bracket placeholders in the final output.
"""


# ---------------------------------------------------------------------------
# WORLD LOADING
# ---------------------------------------------------------------------------

def find_worlds() -> list[Path]:
    """
    Scan Writing_Room/worlds/ and return a list of world directory paths.

    Each immediate subdirectory of worlds/ is one world. We return Path
    objects rather than strings because Path gives us methods like .name
    (just the directory name) and / operator for joining paths.
    """
    worlds_dir = WRITING_ROOM / "worlds"
    if not worlds_dir.exists():
        return []
    return sorted(p for p in worlds_dir.iterdir() if p.is_dir())


def read_file_safe(path: Path) -> str:
    """
    Read a text file and return its contents, or '' if the file is missing.

    Many world bible files are optional (e.g. WORLD_ORDER.md might not exist
    for a brand-new world). Using a safe read avoids crashing on missing files
    and lets the caller decide what to do with an empty result.
    """
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def load_core_files(world_path: Path) -> dict[str, str]:
    """
    Load the four core world bible files into a label → content dictionary.

    Core files are always loaded regardless of constraints. They give the
    model the world's high-level description, entity index, story hooks, and
    chronological order.

    Returns a dict so the caller can format the content however it likes
    (e.g. as one big string, or selectively include only non-empty files).
    """
    candidates = {
        "DESCRIPTION.md":  world_path / "DESCRIPTION.md",
        "SUMMARY.md":      world_path / "SUMMARY.md",
        "HOOKS.md":        world_path / "HOOKS.md",
        "WORLD_ORDER.md":  world_path / "WORLD_ORDER.md",
    }
    result = {}
    for label, path in candidates.items():
        text = read_file_safe(path)
        # Always include the key so the caller knows whether the file existed
        result[label] = text if text else f"(File not found: {path.name})"
    return result


def load_entity_files(world_path: Path) -> dict[str, str]:
    """
    Load all entity markdown files from the four entity subdirectories.

    The Claude agent selectively loads only relevant entities using its Grep
    and Glob tools. Without those tools, we load everything and let the model
    pick what it needs from context.

    TRADE-OFF: More context = better grounding, but local models have finite
    context windows. Use --no-entities if the world bible is very large and
    the model seems to lose coherence mid-conversation.
    """
    entity_dirs = ["characters", "factions", "mythology", "points_of_interest"]
    entities: dict[str, str] = {}
    for subdir in entity_dirs:
        dir_path = world_path / subdir
        if not dir_path.exists():
            continue
        for md_file in sorted(dir_path.glob("*.md")):
            # Use "characters/Aldric.md" as the label for clarity in context
            label = f"{subdir}/{md_file.name}"
            entities[label] = read_file_safe(md_file)
    return entities


def format_world_context(world_name: str, core: dict[str, str], entities: dict[str, str]) -> str:
    """
    Serialise all loaded world content into a single plain-text string.

    Language models receive plain text — we cannot pass them Python dicts.
    This function formats everything with clear section headers so the model
    can locate specific files when reasoning about the world.

    We put core files first (they contain the world overview and entity index),
    then individual entity files. This ordering matters: models tend to
    weight earlier context more heavily, so the most important material goes
    up front.
    """
    parts = [f"# World Bible: {world_name}\n"]

    for label, content in core.items():
        parts.append(f"## {label}\n\n{content}\n")

    if entities:
        parts.append("## World Entities\n")
        for label, content in entities.items():
            parts.append(f"### {label}\n\n{content}\n")

    return "\n---\n".join(parts)


# ---------------------------------------------------------------------------
# LLM INTERFACE
# ---------------------------------------------------------------------------

def make_client(url: str) -> OpenAI:
    """
    Create an OpenAI client that talks to LM Studio instead of OpenAI's servers.

    The openai library is designed for api.openai.com but exposes a `base_url`
    parameter for overriding the endpoint. LM Studio speaks the same HTTP API
    format (the "OpenAI-compatible" API), so we just redirect the library to
    localhost. No changes to the calling code are needed.

    WHY USE THE OPENAI LIBRARY AT ALL?
    -----------------------------------
    We could make raw HTTP requests with urllib or requests. The openai library
    adds: automatic retries, clean Python objects for responses, and a well-
    documented interface. Since LM Studio intentionally mimics the OpenAI API,
    reusing the library costs nothing.
    """
    base_url = url.rstrip("/") + "/v1"
    return OpenAI(base_url=base_url, api_key=DEFAULT_API_KEY)


def chat(client: OpenAI, messages: list[dict], model: str, temperature: float) -> str:
    """
    Send the full conversation history to the model and return its reply.

    WHAT IS `messages`?
    -------------------
    LLM APIs are stateless — the model has no memory between requests. To
    simulate a multi-turn conversation, we accumulate every message in a list
    and resend the entire history on every request. Each entry is a dict with:

        {"role": "system",    "content": "..."}  ← standing instructions
        {"role": "user",      "content": "..."}  ← human turn
        {"role": "assistant", "content": "..."}  ← model turn

    The model uses this history to understand the conversation so far and
    generate the next reply in context.

    WHAT IS `temperature`?
    ----------------------
    Temperature controls the randomness of the model's token sampling:
    - 0.0  → always picks the single most likely next token (deterministic)
    - 1.0  → samples from the full probability distribution (very random)
    - 0.7–0.9 → standard range for creative writing tasks

    Higher temperature encourages novelty and creativity at the cost of
    occasional incoherence. Lower temperature favours precision at the cost
    of repetition and blandness.
    """
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
    )
    # response.choices is a list of completions (we requested 1, the default).
    # .message.content is the text the model produced.
    return response.choices[0].message.content


# ---------------------------------------------------------------------------
# CONCEPT PARSING
# ---------------------------------------------------------------------------

def extract_concept_block(text: str) -> Optional[str]:
    """
    Look for a ```concept ... ``` fenced code block in the model's response.

    When the model produces the final CONCEPT.md, it must wrap it in this
    block. We detect the block to know when the session is complete and the
    content is ready to write to disk.

    REGEX NOTES
    -----------
    re.DOTALL makes the `.` metacharacter match newline characters in addition
    to all other characters. Without it, the pattern would fail to match multi-
    line blocks because `.` stops at the end of each line by default.

    group(1) returns the content *inside* the parentheses in the pattern —
    i.e., just the concept text, without the opening/closing fence markers.

    Returns None if no such block is found (session still in progress).
    """
    match = re.search(r"```concept\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else None


def extract_story_title(concept_text: str) -> str:
    """
    Pull the story title from the first H1 heading in the concept markdown.

    The concept always starts with '# <Story Title>'. We parse that heading
    to derive the story directory name. Falls back to 'Untitled Story' if
    parsing fails (e.g. the model forgot the heading).

    re.MULTILINE makes ^ and $ match the start and end of each *line* rather
    than the start and end of the entire string.
    """
    match = re.search(r"^#\s+(.+)$", concept_text, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled Story"


def extract_story_format(concept_text: str) -> str:
    """
    Extract the **Format:** value from the concept's Story Details section.

    Used when writing the WORLD_ORDER.md row — the format determines whether
    we write 'Full Story' (short story / novelette) or 'TBD' (book / series).
    Defaults to 'Book' if the line is absent.
    """
    match = re.search(r"\*\*Format:\*\*\s*(.+)", concept_text)
    return match.group(1).strip() if match else "Book"


def extract_hooks_used(concept_text: str) -> list[str]:
    """
    Parse the 'Hooks Incorporated' section and return a list of hook titles.

    These titles are used to mark the corresponding hooks 'In Use' in
    HOOKS.md so other story concepts don't reuse them.

    The section may contain:
    - A single value like "None" or "None."  → return empty list
    - A comma-separated line like "The Erased Voice, The Sunken Accord"
    - A bullet list like:
        - The Erased Voice
        - The Sunken Accord

    We handle all three formats.
    """
    match = re.search(
        r"## Hooks Incorporated\n(.+?)(?=\n##|\Z)", concept_text, re.DOTALL
    )
    if not match:
        return []

    raw = match.group(1).strip()
    if not raw or raw.lower().rstrip(".") == "none":
        return []

    # Bullet list format
    if raw.startswith("-"):
        return [line.lstrip("- ").strip() for line in raw.splitlines() if line.strip()]

    # Comma-separated format
    return [h.strip() for h in raw.split(",") if h.strip()]


# ---------------------------------------------------------------------------
# FILE WRITING
# ---------------------------------------------------------------------------

def write_story_files(story_dir: Path, story_name: str, concept_text: str) -> tuple[Path, Path]:
    """
    Create the story directory structure and write CONCEPT.md and Timeline.md.

    Directory layout created:
        stories/<Story Name>/
            CONCEPT.md
            chapters/           ← empty; receives Chapter_NN.md files later
            current_chapter/    ← staging area for the active chapter draft
            state/
                Timeline.md     ← skeleton initialised from template

    WHY mkdir WITH parents=True AND exist_ok=True?
    -----------------------------------------------
    parents=True  → creates all intermediate directories in one call, like
                    `mkdir -p` in bash. Without it, you'd need to create
                    stories/, then the story dir, then state/ separately.
    exist_ok=True → suppresses the error if the directory already exists.
                    Safe to call multiple times.
    """
    (story_dir / "chapters").mkdir(parents=True, exist_ok=True)
    (story_dir / "current_chapter").mkdir(parents=True, exist_ok=True)
    state_dir = story_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    # Write CONCEPT.md
    concept_path = story_dir / "CONCEPT.md"
    concept_path.write_text(concept_text, encoding="utf-8")

    # Load timeline template and personalise it
    template_path = WRITING_ROOM / "templates" / "story" / "timeline.md"
    template = read_file_safe(template_path) or "# Timeline\n\n_No events yet._\n"
    timeline_content = template.replace("<Story Name>", story_name)
    timeline_path = state_dir / "Timeline.md"
    timeline_path.write_text(timeline_content, encoding="utf-8")

    return concept_path, timeline_path


def mark_hooks_in_use(world_path: Path, hook_titles: list[str]) -> None:
    """
    Update HOOKS.md to change the Status of incorporated hooks from Open → In Use.

    We do a targeted regex replacement rather than rewriting the entire file.
    The pattern anchors to the hook's section heading so we only modify the
    correct Status line and leave all other content untouched.

    WHY re.DOTALL HERE?
    -------------------
    A hook section spans multiple lines:
        ## The Erased Voice
        ...
        - **Status:** Open
    re.DOTALL lets `.+?` match across those newlines to reach the Status line.
    `?` (non-greedy) ensures we stop at the FIRST Status: Open after the title,
    not the last one in the file.
    """
    if not hook_titles:
        return

    hooks_path = world_path / "HOOKS.md"
    if not hooks_path.exists():
        print(f"  Warning: HOOKS.md not found — skipping hook status update.")
        return

    content = hooks_path.read_text(encoding="utf-8")
    original = content

    for title in hook_titles:
        pattern     = rf"(## {re.escape(title)}.+?Status:\s*)Open"
        replacement = r"\1In Use"
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if content != original:
        hooks_path.write_text(content, encoding="utf-8")
        print(f"  HOOKS.md updated — In Use: {', '.join(hook_titles)}")
    else:
        print(f"  Warning: hook titles not found in HOOKS.md: {hook_titles}")


def get_next_world_order_position(world_path: Path) -> int:
    """
    Read WORLD_ORDER.md and return the next available position number.

    Scans all existing position numbers (first column of the markdown table)
    and returns max + 1. Returns 1 if the file is missing or has no entries.
    """
    content = read_file_safe(world_path / "WORLD_ORDER.md")
    if not content:
        return 1
    positions = re.findall(r"^\|\s*(\d+)\s*\|", content, re.MULTILINE)
    return max((int(p) for p in positions), default=0) + 1


def update_world_order(world_path: Path, story_name: str, story_format: str, position: int) -> None:
    """
    Append a new row to WORLD_ORDER.md and update the Last synchronized date.

    The row format depends on story length:
    - Short Story / Novelette → unit column is "Full Story"
    - Book / Book Series      → unit column is "TBD" (Outliner fills it in)

    We find the closing '---' separator of the file and insert before it.
    If no separator exists we append to the end of the file.

    WHY NOT JUST APPEND?
    --------------------
    WORLD_ORDER.md typically ends with a '---' separator followed by metadata.
    Appending would put the new row after the metadata. Inserting before '---'
    keeps the table intact and the metadata at the bottom.
    """
    world_order_path = world_path / "WORLD_ORDER.md"
    if not world_order_path.exists():
        print("  Warning: WORLD_ORDER.md not found — skipping update.")
        print("  Invoke the Writing Assistant in Claude Code to initialise it.")
        return

    content = world_order_path.read_text(encoding="utf-8")
    fmt = story_format.lower()
    if "series" in fmt or "book" in fmt:
        unit  = "TBD"
        notes = "Placeholder — expand after Outliner"
    else:
        unit  = "Full Story"
        notes = ""

    new_row = f"| {position} | [[{story_name}]] | {unit} | — | Not Started | {notes} |"

    # Insert before the last '---' separator; append if none found
    if "\n---" in content:
        content = content.replace("\n---", f"\n{new_row}\n---", 1)
    else:
        content = content.rstrip() + f"\n{new_row}\n"

    # Refresh the Last synchronized date
    today = date.today().isoformat()
    content = re.sub(r"Last synchronized:.*", f"Last synchronized: {today}", content)

    world_order_path.write_text(content, encoding="utf-8")
    print(f"  WORLD_ORDER.md updated — position {position}: {story_name}")


# ---------------------------------------------------------------------------
# INTERACTIVE HELPERS
# ---------------------------------------------------------------------------

def select_world(args_world: Optional[str]) -> Optional[Path]:
    """
    Determine which world directory to use.

    If --world was passed on the command line, find and return it.
    Otherwise list all available worlds and ask the user to pick one.
    Returns None if no valid world is found or the user cancels.
    """
    worlds = find_worlds()
    if not worlds:
        print("Error: No worlds found in Writing_Room/worlds/")
        print("Create one first with /create-world in Claude Code.")
        return None

    if args_world:
        for w in worlds:
            if w.name.lower() == args_world.lower():
                return w
        print(f"Error: World '{args_world}' not found.")
        print(f"Available: {', '.join(w.name for w in worlds)}")
        return None

    if len(worlds) == 1:
        answer = input(f"World: {worlds[0].name} — use this? [Y/n]: ").strip().lower()
        return worlds[0] if answer in ("", "y", "yes") else None

    print("Available worlds:")
    for i, w in enumerate(worlds, 1):
        print(f"  {i}. {w.name}")
    raw = input("Select number: ").strip()
    try:
        return worlds[int(raw) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return None


def select_mode(args_mode: Optional[str]) -> str:
    """
    Return 'autonomous' or 'collaborative'.

    Autonomous  → model makes all narrative decisions internally, presents a
                  complete concept, and asks for a single approval.
    Collaborative → genuine back-and-forth: model proposes directions, user
                    reacts, both refine until ready to finalise.
    """
    if args_mode and args_mode.lower() in ("autonomous", "collaborative"):
        return args_mode.lower()

    print("\nSession mode:")
    print("  1. Autonomous   — model decides everything, presents a complete concept")
    print("  2. Collaborative — back-and-forth dialogue (default)")
    choice = input("Choose [1/2, Enter=2]: ").strip()
    return "autonomous" if choice == "1" else "collaborative"


def gather_constraints() -> dict[str, str]:
    """
    Collect optional story constraints from the user (mirrors Step 3 of the
    original Story Ideator agent).

    All fields are optional. Pressing Enter skips a field, leaving the model
    free to decide. We strip empty strings from the result so the context
    message only lists constraints the user actually provided.
    """
    print("\nOptional constraints (Enter to skip any):")
    fields = [
        ("format",         "a. Format [Short Story / Novelette / Book / Book Series]"),
        ("characters",     "b. Characters to feature or protagonist to centre on"),
        ("hooks",          "c. Specific hooks to build on (titles, comma-separated)"),
        ("tropes_use",     "d. Tropes to incorporate"),
        ("tropes_avoid",   "e. Tropes to avoid"),
        ("structure",      "f. Preferred story structure (e.g. Three-Act, Hero's Journey)"),
        ("tone",           "g. Tone or mood constraints"),
    ]
    constraints = {}
    for key, prompt in fields:
        value = input(f"  {prompt}: ").strip()
        if value:
            constraints[key] = value
    return constraints


def format_constraints_for_model(constraints: dict[str, str]) -> str:
    """
    Convert the constraints dict into a human-readable block to send to the model.
    """
    if not constraints:
        return "No constraints — make all narrative decisions freely."
    labels = {
        "format":       "Format",
        "characters":   "Characters to feature",
        "hooks":        "Hooks to incorporate",
        "tropes_use":   "Tropes to incorporate",
        "tropes_avoid": "Tropes to avoid",
        "structure":    "Preferred structure",
        "tone":         "Tone / mood",
    }
    lines = ["Story constraints:"]
    for key, value in constraints.items():
        lines.append(f"  - {labels.get(key, key)}: {value}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CONVERSATION LOOP
# ---------------------------------------------------------------------------

def run_conversation(
    client:       OpenAI,
    model:        str,
    temperature:  float,
    world_name:   str,
    world_context: str,
    mode:         str,
    constraints:  dict[str, str],
) -> Optional[str]:
    """
    Run the interactive conversation between the user and the local model.

    This is the core of the script. It:
    1. Builds the initial context message (world bible + constraints + mode).
    2. Gets the model's first response.
    3. Alternates between user input and model replies.
    4. Watches every model response for a ```concept block.
    5. Returns the concept text when found, or None if the user quits.

    CONVERSATION HISTORY
    --------------------
    `messages` accumulates all turns in the session. On every call to chat(),
    we send the full list. This is how "memory" works with stateless LLM APIs —
    by replaying history. The cost is that each call gets progressively more
    expensive (more tokens), but for a single interactive session this is fine.

    EXIT CONDITIONS
    ---------------
    - Model outputs a ```concept block  → session complete, return concept text.
    - User types 'quit' or 'exit'       → return None (no files written).
    """
    mode_instruction = (
        "Work AUTONOMOUSLY. Make all narrative decisions internally. "
        "Present a complete, fully-formed concept. Ask only one final question: "
        "'Does this work, or would you like to change anything?' "
        "Once approved, output the final ```concept block."
        if mode == "autonomous"
        else
        "Work COLLABORATIVELY. Open with the world's most compelling tensions "
        "(2–3 sentences), list available hooks briefly, then propose 2 possible "
        "story directions as loglines. Build on the user's reactions. Load entity "
        "details as characters are confirmed. Finalise only when the user signals "
        "readiness ('that works', 'finalise it', 'let's go with this'). "
        "Output the final ```concept block only after explicit approval."
    )

    initial_message = (
        f"Mode: {mode.capitalize()}\n\n"
        f"{mode_instruction}\n\n"
        f"{format_constraints_for_model(constraints)}\n\n"
        f"World bible for '{world_name}':\n\n"
        f"{world_context}\n\n"
        f"Begin the Story Ideator session now."
    )

    # Seed the conversation with the system prompt and the first user message.
    # The model has not responded yet — it will on the first chat() call below.
    messages: list[dict] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": initial_message},
    ]

    print(f"\n{'='*60}")
    print(f"  Story Ideator — {mode.capitalize()} Mode")
    print(f"  World: {world_name} | Model: {model}")
    print(f"  Type 'quit' at any prompt to exit without saving.")
    print(f"{'='*60}\n")

    while True:
        # --- Model turn ---
        print("Model:\n")
        response = chat(client, messages, model, temperature)
        print(response)
        print()
        messages.append({"role": "assistant", "content": response})

        # Detect the final concept block
        concept = extract_concept_block(response)
        if concept:
            print("[Concept block detected — ready to save.]\n")
            return concept

        # --- User turn ---
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Session ended — no files written.")
            return None

        messages.append({"role": "user", "content": user_input})


# ---------------------------------------------------------------------------
# ARGUMENT PARSING
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    """
    Define and parse command-line arguments.

    argparse is Python's standard library for CLI argument handling. It
    automatically generates --help output and type-checks values. Using it
    instead of sys.argv directly avoids a lot of manual parsing boilerplate.
    """
    parser = argparse.ArgumentParser(
        description="Story Ideator — generate a story concept with a local LM Studio model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/lm_studio_ideator.py\n"
            "  python scripts/lm_studio_ideator.py --world Harrowmere --mode autonomous\n"
            "  python scripts/lm_studio_ideator.py --url http://localhost:1234 --temp 0.9\n"
        ),
    )
    parser.add_argument("--world",      help="World name (skips interactive selection)")
    parser.add_argument("--mode",       choices=["autonomous", "collaborative"],
                        help="Session mode (skips the opening prompt)")
    parser.add_argument("--url",        default=DEFAULT_URL,
                        help=f"LM Studio server URL (default: {DEFAULT_URL})")
    parser.add_argument("--model",      default=None,
                        help="Model ID from LM Studio (default: auto-detect loaded model)")
    parser.add_argument("--temp",       type=float, default=DEFAULT_TEMP,
                        help=f"Temperature 0.0–1.0 (default: {DEFAULT_TEMP})")
    parser.add_argument("--no-entities", action="store_true",
                        help="Skip entity files — faster for large world bibles")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Entry point. Orchestrates all steps in order:

        1.  Connect to LM Studio and verify it is reachable.
        2.  Select the world.
        3.  Select the session mode.
        4.  Gather optional constraints.
        5.  Load world bible files into memory.
        6.  Run the conversation loop.
        7.  Prompt the user to confirm the story title and save location.
        8.  Write CONCEPT.md and Timeline.md.
        9.  Mark used hooks as In Use in HOOKS.md.
        10. Update WORLD_ORDER.md.
        11. Print a summary.
    """

    args = parse_args()

    # ------------------------------------------------------------------
    # Step 1 — Connect to LM Studio
    # ------------------------------------------------------------------
    print(f"Connecting to LM Studio at {args.url} ...")
    client = make_client(args.url)

    # Probe the /v1/models endpoint to verify connectivity and discover
    # which model is currently loaded. This fails fast with a clear message
    # instead of hanging silently when the server isn't running.
    try:
        loaded_models = [m.id for m in client.models.list().data]
    except Exception as exc:
        print(f"\nError: Could not reach LM Studio at {args.url}")
        print(f"Details: {exc}")
        print("\nCheck that:")
        print("  1. LM Studio is running.")
        print("  2. The local server is started (Local Server tab → Start Server).")
        print("  3. A model is loaded.")
        sys.exit(1)

    if not loaded_models:
        print("Error: LM Studio is running but no model is loaded.")
        print("Load a model in LM Studio and try again.")
        sys.exit(1)

    # Use the specified model, or default to whatever LM Studio has loaded.
    model = args.model or loaded_models[0]
    print(f"Connected. Model: {model}\n")

    # ------------------------------------------------------------------
    # Steps 2–4 — World, mode, constraints
    # ------------------------------------------------------------------
    world_path = select_world(args.world)
    if not world_path:
        sys.exit(1)
    world_name = world_path.name

    mode        = select_mode(args.mode)
    constraints = gather_constraints()

    # ------------------------------------------------------------------
    # Step 5 — Load world bible
    # ------------------------------------------------------------------
    print(f"\nLoading world bible for '{world_name}' ...")
    core     = load_core_files(world_path)
    entities = {} if args.no_entities else load_entity_files(world_path)

    if entities:
        print(f"  {len(entities)} entity file(s) loaded.")

    world_context = format_world_context(world_name, core, entities)
    char_count    = len(world_context)
    token_estimate = char_count // 4   # rough estimate: 1 token ≈ 4 characters
    print(f"  World context: ~{token_estimate:,} tokens ({char_count:,} chars)")

    if token_estimate > 8_000:
        print(
            f"\n  Warning: large context (~{token_estimate:,} tokens). "
            "The model may lose early details in long conversations. "
            "Consider --no-entities if responses seem inconsistent.\n"
        )

    # ------------------------------------------------------------------
    # Step 6 — Run conversation
    # ------------------------------------------------------------------
    concept_text = run_conversation(
        client=client,
        model=model,
        temperature=args.temp,
        world_name=world_name,
        world_context=world_context,
        mode=mode,
        constraints=constraints,
    )

    if not concept_text:
        sys.exit(0)

    # ------------------------------------------------------------------
    # Step 7 — Confirm story title and save location
    # ------------------------------------------------------------------
    story_title = extract_story_title(concept_text)
    print(f"Story title: '{story_title}'")

    story_dir = WRITING_ROOM / "stories" / story_title

    if story_dir.exists():
        print(f"Warning: stories/{story_title}/ already exists.")
        answer = input("Overwrite? [y/N]: ").strip().lower()
        if answer not in ("y", "yes"):
            new_name = input("Enter a different story name (or Enter to cancel): ").strip()
            if not new_name:
                print("Cancelled — no files written.")
                sys.exit(0)
            story_title = new_name
            story_dir   = WRITING_ROOM / "stories" / story_title

    answer = input(f"Save to stories/{story_title}/? [Y/n]: ").strip().lower()
    if answer not in ("", "y", "yes"):
        print("Cancelled — no files written.")
        sys.exit(0)

    # ------------------------------------------------------------------
    # Steps 8–10 — Write files, update hooks, update world order
    # ------------------------------------------------------------------
    print("\nSaving files ...")
    concept_path, timeline_path = write_story_files(story_dir, story_title, concept_text)
    print(f"  {concept_path.relative_to(WRITING_ROOM)}")
    print(f"  {timeline_path.relative_to(WRITING_ROOM)}")

    hooks_used = extract_hooks_used(concept_text)
    mark_hooks_in_use(world_path, hooks_used)

    next_pos      = get_next_world_order_position(world_path)
    story_format  = extract_story_format(concept_text)
    print(f"\nWorld order — next available position: {next_pos}")
    raw_pos = input(f"Chronological position (Enter for {next_pos}): ").strip()
    position = next_pos
    if raw_pos:
        try:
            position = int(raw_pos)
        except ValueError:
            print(f"  Not a number — defaulting to {next_pos}.")

    update_world_order(world_path, story_title, story_format, position)

    # ------------------------------------------------------------------
    # Step 11 — Summary
    # ------------------------------------------------------------------
    print(f"""
{'='*60}
  Story Ideator — Complete
{'='*60}
  Story : {story_title}
  World : {world_name}
  Mode  : {mode.capitalize()}
  Model : {model}

  Files written:
    stories/{story_title}/CONCEPT.md
    stories/{story_title}/state/Timeline.md

  Hooks marked In Use : {', '.join(hooks_used) if hooks_used else 'None'}
  World Order position: {position}

  Next step:
    Invoke the Outliner in Claude Code with the story name
    to generate a chapter outline.
{'='*60}
""")


if __name__ == "__main__":
    # This guard ensures main() only runs when this file is executed directly,
    # not if another script imports this module. It is the standard Python
    # idiom for making a file usable both as a script and as a library.
    main()
