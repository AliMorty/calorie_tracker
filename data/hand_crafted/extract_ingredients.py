"""Read agent output files and extract ingredient lists to individual files."""
import os
import glob

TASK_DIR = "/tmp/claude-1000/-home-alimorty-calorie-tracker/e6468d11-4e8c-4cd4-bf63-266b1af47210/tasks"
OUTPUT_DIR = "/home/alimorty/calorie_tracker/data/hand_crafted"

# Map agent IDs to cuisine names
agents = {
    "a6cef34ae21be4b9b": "canadian",
    "a7338e758ddd004ce": "american",
    "a637a6beedf8385a7": "british",
    "a5bafef8b8c06826f": "french",
    "a6ad73e0b3073631b": "italian",
    "a3fdbaeb46e683b8f": "greek",
    "a6c168fef4c521d3c": "mediterranean",
    "ab6a05e12e4760b17": "middle_eastern",
    "a7f341fbd16acf834": "iranian",
    "a28530d64feec467e": "south_asian",
    "a105b20b31a1d4320": "chinese",
    "a24da90c44ab4d0eb": "japanese",
    "a45300cdce4371051": "korean",
    "afac39ded30a3d3f4": "southeast_asian",
    "ac4dff8b73f39bebb": "mexican",
    "a1b09b68f7c9987db": "latin_american",
    "a2c76efd8e0ccdfe5": "caribbean",
    "a51b601f85df25ecf": "african",
    "a0929afb2a6ae8cb6": "eastern_european",
    "a9b9e765bf322e68d": "jewish",
}

for agent_id, cuisine in agents.items():
    output_file = os.path.join(TASK_DIR, f"{agent_id}.output")
    if not os.path.exists(output_file):
        print(f"MISSING: {cuisine} ({agent_id})")
        continue

    with open(output_file, "r") as f:
        content = f.read()

    # The ingredient list is in the last assistant message result
    # Look for the final block of plain ingredient lines
    lines = content.split("\n")

    # Find ingredient lines: lowercase, no special prefixes, contain only food words
    # The agent's final response is a plain list of ingredients
    ingredient_lines = []
    in_result = False
    for line in lines:
        stripped = line.strip()
        # Skip empty lines, headers, tool calls, metadata
        if not stripped:
            continue
        # Ingredient lines are simple: lowercase words, possibly with spaces
        # They don't start with #, *, -, numbers, or contain JSON/code markers
        if (stripped.islower() or stripped[0].islower()) and \
           not stripped.startswith(('#', '*', '-', '{', '[', '<', '>', '|', 'agent', 'tool', 'the ', 'i ', 'both', 'could', 'please', 'since', 'here')) and \
           not any(c in stripped for c in [':', '{', '}', '[', ']', '(', ')', '=', '//', 'http']) and \
           len(stripped) < 80 and \
           len(stripped) > 1:
            ingredient_lines.append(stripped)

    if ingredient_lines:
        target = os.path.join(OUTPUT_DIR, f"ingredients_{cuisine}.txt")
        with open(target, "w") as f:
            f.write("\n".join(ingredient_lines) + "\n")
        print(f"OK: {cuisine} — {len(ingredient_lines)} ingredients")
    else:
        print(f"NO INGREDIENTS FOUND: {cuisine}")
