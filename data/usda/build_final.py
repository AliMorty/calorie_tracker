#!/usr/bin/env python3
"""
Build the final DB-ready food list:
  - keep only matched records (usda_source != null) from ingredients_macros.json
  - drop unmatched (already preserved in unmatched.json)
Note: milk fat-tier variants (1%/2%/whole/skim) already exist as matched entries;
plain "milk" was the only unmatched milk row and is dropped with the rest.
OUTPUT: ../hand_crafted/ingredients_final.json
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
MACROS = HERE / "../hand_crafted/ingredients_macros.json"
OUT = HERE / "../hand_crafted/ingredients_final.json"

macros = json.loads(MACROS.read_text())
final = [rec for rec in macros if rec["usda_source"]]
final.sort(key=lambda r: r["name"])
OUT.write_text(json.dumps(final, indent=2))
print(f"-> {OUT.name}: {len(final)} records (dropped {len(macros) - len(final)} unmatched)")
