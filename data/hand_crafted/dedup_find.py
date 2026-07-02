#!/usr/bin/env python3
"""
Step 1 of dedup pipeline.

Reads ingredients_set.json (READ ONLY - never modified), builds a numbered
list, and asks `claude -p` (sonnet) to identify duplicate ingredients.

The LLM returns ONLY decisions as JSON - it never rewrites the list.
Each decision points a duplicate index at a canonical (survivor) index, and
echoes both names so dedup_apply.py can checksum the index->name pairing and
catch any hallucination.

Output: dedup_decisions.json  (raw decisions from the model)
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "ingredients_set.json"
OUT = HERE / "dedup_decisions.json"

PROMPT_TEMPLATE = """You are cleaning a list of food ingredients for a calorie tracker.

Below is a numbered list of {n} ingredients (format `<index>: <name>`).
Your job: find DUPLICATES - items that are the SAME food and would have the
SAME macros, so only one should survive.

Treat these as duplicates (MERGE them):
- singular/plural: "apple" / "apples"
- spelling variants: "zaatar" / "za'atar", "yoghurt" / "yogurt"
- exact synonyms: "chickpeas" / "garbanzo beans", "cilantro" / "coriander leaves"
- needlessly specific variants of the same food with the same macros:
  "apple fuji" / "apple gala" -> "apple"

Do NOT merge items that are genuinely DIFFERENT foods with DIFFERENT macros:
- "cottage cheese 1%" vs "cottage cheese 4%"  (keep both)
- "white bread" vs "whole wheat bread"  (keep both)
- "chicken breast" vs "chicken thigh"  (keep both)
- "milk 2%" vs "milk skim"  (keep both)
If you are UNSURE whether macros differ, do NOT merge - leave it alone.

For each duplicate, pick the CLEANEST / most generic surviving item as the
canonical, and point the others at it.

Return ONLY a JSON object, no prose, no markdown fences, with this shape:
{{
  "merges": [
    {{"canonical_idx": 12, "canonical_name": "apple",
      "dup_idx": 13, "dup_name": "apples", "reason": "plural"}}
  ],
  "uncertain": [
    {{"idx_a": 50, "name_a": "bell pepper red",
      "idx_b": 51, "name_b": "bell pepper green",
      "note": "macros may differ slightly"}}
  ]
}}

Rules:
- Every index and name MUST be copied exactly from the list below.
- A given dup_idx may appear at most once in "merges".
- "uncertain" is for borderline pairs you did NOT merge but a human should review.

Here is the list:

{listing}
"""


def main():
    items = json.loads(SRC.read_text())
    listing = "\n".join(f"{i}: {it['name']}" for i, it in enumerate(items))
    prompt = PROMPT_TEMPLATE.format(n=len(items), listing=listing)

    print(f"Sending {len(items)} items to claude (sonnet)...", file=sys.stderr)
    result = subprocess.run(
        ["claude", "--model", "sonnet", "-p"],
        input=prompt,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("claude call failed:", result.stderr, file=sys.stderr)
        sys.exit(1)

    raw = result.stdout.strip()
    # strip accidental markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()

    try:
        decisions = json.loads(raw)
    except json.JSONDecodeError as e:
        print("Could not parse model output as JSON:", e, file=sys.stderr)
        (HERE / "dedup_raw_output.txt").write_text(result.stdout)
        print("Raw output saved to dedup_raw_output.txt for inspection.", file=sys.stderr)
        sys.exit(1)

    OUT.write_text(json.dumps(decisions, indent=2))
    merges = decisions.get("merges", [])
    uncertain = decisions.get("uncertain", [])
    print(f"Done. {len(merges)} merges, {len(uncertain)} uncertain pairs -> {OUT.name}")


if __name__ == "__main__":
    main()
