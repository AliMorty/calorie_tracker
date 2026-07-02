"""
apply_cooked_tags.py

Appends " cooked" to a hardcoded explicit list of ingredient names in
ingredients_set_deduped.json, writing the result to ingredients_set_cooked.json.

Rules applied:
- Only everyday staples where Ali weighs food AFTER cooking and raw vs cooked
  macros differ materially: grains, legumes, pasta, fresh meats/poultry/fish.
- Format: append " cooked" (space, no comma) to the END of the name.
- Leaves the original file untouched.
- Validates: 913 items preserved, no duplicate names, every tag-list name found.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
INPUT_FILE  = HERE / "ingredients_set_deduped.json"
OUTPUT_FILE = HERE / "ingredients_set_cooked.json"
REVIEW_FILE = HERE / "cooked_tagging_review.txt"

# ---------------------------------------------------------------------------
# EXPLICIT HARDCODED TAG LIST
# Every name here must exactly match an entry in the input file.
# ---------------------------------------------------------------------------

TO_TAG: set[str] = {
    # ----- RICE (eaten as a cooked grain) -----------------------------------
    "brown rice",
    "basmati rice",
    "jasmine rice",
    "white rice",
    "sushi rice",
    "short grain rice",
    "wild rice",
    "broken rice",
    "glutinous rice",       # the plain grain form (not flour)

    # ----- PASTA ------------------------------------------------------------
    "pasta",
    "angel hair pasta",
    "orzo pasta",
    "tubular pasta",
    "fresh pasta (refrigerated)",
    "fettuccine",
    "fusilli",
    "lasagna noodles",
    "linguine",
    "macaroni",
    "penne",
    "rigatoni",
    "spaghetti",

    # ----- LEGUMES (dried or raw — cooked before eating) --------------------
    "lentils",
    "lentils, green (dried)",
    "lentils, red (dried)",
    "chickpeas",
    "dried chickpeas",
    "dried white beans",
    "fava beans",
    "kidney beans",
    "navy beans",
    "pinto beans",
    "white beans",
    "mung beans",
    "split peas, green (dried)",
    "split peas, yellow (dried)",
    "urad dal",
    "giant lima beans",
    "barley, pearl",
    "black-eyed peas, canned",   # borderline — see review

    # ----- GRAINS (cooked whole grains) -------------------------------------
    "bulgur wheat",
    "fine bulgur wheat",
    "farro",
    "freekeh",
    "quinoa",
    "wheat berries",
    "couscous",
    "oats, steel cut",           # typically cooked (porridge)
    "oats, rolled / old fashioned",  # typically cooked (porridge)
    "oats, quick",               # typically cooked (porridge)

    # ----- FRESH MEATS / POULTRY --------------------------------------------
    "chicken breast",
    "chicken thigh, bone-in skin-on",
    "chicken thigh, boneless skinless",
    "chicken thighs",
    "chicken drumstick",
    "chicken wings",
    "chicken",                   # generic

    "beef",
    "beef brisket",
    "beef chuck",
    "beef ribeye",
    "beef roast",
    "beef roast, sirloin tip",
    "beef shank",
    "beef short ribs",
    "beef sirloin",
    "beef steak, flank",
    "beef steak, strip loin",
    "beef steak, tenderloin (filet mignon)",
    "beef back ribs",
    "beef cutlets",
    "stewing beef",

    "ground beef",
    "ground beef, extra lean (10% fat)",
    "ground beef, lean (17% fat)",
    "ground beef, regular (27% fat)",
    "ground chicken",
    "ground lamb",
    "ground pork",
    "ground turkey",

    "pork",
    "pork belly",
    "pork chop",
    "pork chops, bone-in",
    "pork chops, boneless",
    "pork cutlet",
    "pork hocks",
    "pork loin",
    "pork ribs",
    "pork ribs, back",
    "pork roast",
    "pork shoulder",
    "pork tenderloin",

    "lamb",
    "lamb chops",
    "lamb leg",
    "lamb loin",
    "lamb ribs",
    "lamb shoulder",

    "veal cutlets",

    "turkey",
    "turkey breast",

    # ----- FRESH FISH / SEAFOOD ---------------------------------------------
    "salmon",
    "salmon, atlantic (fresh)",
    "salmon, sockeye (fresh)",
    "shrimp",
    "cod",
    "haddock fillet",
    "halibut fillet",
    "catfish fillet",
    "mahi mahi fillet",
    "sea bream",
    "sole fillet",
    "tilapia fillet",
    "trout fillet",
    "tuna, fresh / frozen steak",
    "yellowtail",
    "whole fish",
    "whole white fish",
    "octopus",
    "squid",
    "scallops",
    "mussels",
    "lobster",
    "lobster meat",
    "crab",
}

# ---------------------------------------------------------------------------
# BORDERLINE ITEMS (flagged for human review — NOT tagged)
# ---------------------------------------------------------------------------
BORDERLINE: list[tuple[str, str]] = [
    ("black-eyed peas, canned",
     "Listed in TO_TAG because canned black-eyed peas are a pre-cooked convenience "
     "product and macros are per cooked weight. However 'canned' usually means "
     "leave unchanged per the rules. NEEDS REVIEW — removed from TO_TAG for safety."),
    ("whole chicken",
     "Could be roasted whole or broken down raw. Similar to 'rotisserie chicken' "
     "(which is excluded). If Ali buys whole raw chicken to cook himself, tag; "
     "if he buys it pre-roasted, don't. BORDERLINE — not tagged."),
    ("whole duck",
     "Same ambiguity as whole chicken. BORDERLINE — not tagged."),
    ("beef tripe",
     "Organ/specialty item. Tripe is cooked but macros don't change drastically. "
     "Rules say 'use judgment, when in doubt leave unchanged'. NOT tagged."),
    ("beef cheeks",
     "Organ/specialty item. BORDERLINE — not tagged."),
    ("beef bones",
     "Used for stock/broth, not eaten directly as a portion. NOT tagged."),
    ("pork bones",
     "Used for stock/broth, not eaten as a portion. NOT tagged."),
    ("lamb intestines",
     "Organ/specialty item. BORDERLINE — not tagged."),
    ("lamb offal",
     "Organ/specialty item. BORDERLINE — not tagged."),
    ("chicken skin",
     "Specialty item. Rules say leave unchanged. NOT tagged."),
    ("ham hock",
     "Often sold smoked/cured (preservation state). BORDERLINE — not tagged."),
    ("oats, steel cut",
     "Included in TO_TAG (cooked porridge). If Ali eats them raw/overnight-oats, "
     "this tag would be wrong. BORDERLINE — tagged, but flagged."),
    ("oats, rolled / old fashioned",
     "Included in TO_TAG (cooked porridge). Same caveat as steel cut. BORDERLINE."),
    ("oats, quick",
     "Included in TO_TAG (cooked porridge). Same caveat. BORDERLINE."),
    ("couscous",
     "Technically reconstituted with boiling water, macro change is moderate. "
     "Tagged as a cooked grain — BORDERLINE."),
    ("barley, pearl",
     "Tagged as a cooked grain. BORDERLINE — verify Ali cooks it."),
    ("giant lima beans",
     "Fresh or dried? If canned, should be left unchanged. Listed without 'canned' "
     "or 'dried' qualifier — assuming dried/fresh and cooked. BORDERLINE — tagged."),
    ("urad dal",
     "Dal is always cooked; tagged. BORDERLINE only because it doesn't have 'dried' "
     "qualifier, but dal == dried lentil in practice."),
    ("fava beans",
     "Can be eaten fresh (raw/blanched) or dried-and-cooked. BORDERLINE — tagged."),
    ("mung beans",
     "Can be sprouted (raw) or cooked. BORDERLINE — tagged under assumption of cooked."),
    ("grilled pork",
     "Already encodes a cooking method ('grilled'). NOT tagged — left unchanged."),
    ("pork carnitas",
     "Already a cooked preparation. NOT tagged."),
    ("clams",
     "Seafood — typically cooked. Could argue for tagging. BORDERLINE — not tagged "
     "(no explicit mention in rules; left unchanged to be safe)."),
    ("lobster",
     "Included in TO_TAG. BORDERLINE — could be purchased pre-cooked (e.g. lobster "
     "tail from store). Flagged."),
    ("lobster meat",
     "Included in TO_TAG. Often sold pre-cooked. BORDERLINE — flagged."),
    ("egg noodles",
     "Pasta-like but often sold pre-cooked/dry. BORDERLINE — not tagged "
     "(not in the explicit pasta list above)."),
    ("reshteh noodles",
     "Persian noodle, cooked in soups. BORDERLINE — not tagged (specialty item, "
     "not in the staple pasta list)."),
    ("soba noodles",
     "Japanese buckwheat noodle, cooked. BORDERLINE — not tagged (not in the "
     "explicit pasta list; specialty item)."),
    ("udon noodles",
     "Japanese wheat noodle, cooked. BORDERLINE — not tagged (specialty noodle)."),
    ("lo mein noodles",
     "Chinese wheat noodle, cooked. BORDERLINE — not tagged (specialty noodle)."),
    ("wheat noodles",
     "Generic term. BORDERLINE — not tagged."),
    ("vermicelli",
     "Could be wheat or rice vermicelli. BORDERLINE — not tagged (rice vermicelli "
     "is excluded per rules; wheat vermicelli is specialty)."),
]

# Remove black-eyed peas, canned from TO_TAG (it's in borderline)
TO_TAG.discard("black-eyed peas, canned")


def main() -> None:
    # Load input
    with INPUT_FILE.open(encoding="utf-8") as f:
        data: list[dict] = json.load(f)

    input_count = len(data)
    print(f"Loaded {input_count} items from {INPUT_FILE.name}")

    # Build name -> index map for quick lookup
    input_names: set[str] = {item["name"] for item in data}

    # Validate: every name in TO_TAG exists in input
    missing = TO_TAG - input_names
    if missing:
        print("\nERROR: The following tag-list names were NOT found in the input file:")
        for m in sorted(missing):
            print(f"  - {m!r}")
        sys.exit(1)
    else:
        print(f"All {len(TO_TAG)} tag-list names verified present in input. OK.")

    # Apply tags
    tagged_pairs: list[tuple[str, str]] = []
    output: list[dict] = []
    for item in data:
        new_item = dict(item)
        if item["name"] in TO_TAG:
            old_name = item["name"]
            new_name = old_name + " cooked"
            new_item["name"] = new_name
            tagged_pairs.append((old_name, new_name))
        output.append(new_item)

    # Validate: output count
    if len(output) != 913:
        print(f"\nERROR: Output has {len(output)} items, expected 913.")
        sys.exit(1)

    # Validate: no duplicate names
    output_names = [item["name"] for item in output]
    if len(output_names) != len(set(output_names)):
        from collections import Counter
        dupes = [n for n, c in Counter(output_names).items() if c > 1]
        print(f"\nERROR: Duplicate names after tagging: {dupes}")
        sys.exit(1)

    # Write output file
    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"Written {len(output)} items to {OUTPUT_FILE.name}")

    # Write review file
    tagged_pairs.sort(key=lambda p: p[0])
    with REVIEW_FILE.open("w", encoding="utf-8") as f:
        f.write("COOKED TAGGING REVIEW\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"Total items in file : {input_count}\n")
        f.write(f"Items tagged        : {len(tagged_pairs)}\n")
        f.write(f"Items unchanged     : {input_count - len(tagged_pairs)}\n\n")

        f.write("=" * 70 + "\n")
        f.write("TAGGED ITEMS (old name -> new name)\n")
        f.write("=" * 70 + "\n")
        for old, new in tagged_pairs:
            f.write(f"  {old!r:55s} -> {new!r}\n")

        f.write("\n" + "=" * 70 + "\n")
        f.write("BORDERLINE / NEEDS HUMAN REVIEW\n")
        f.write("=" * 70 + "\n")
        for name, reason in BORDERLINE:
            f.write(f"\n  Item : {name!r}\n")
            f.write(f"  Note : {reason}\n")

    print(f"Review written to {REVIEW_FILE.name}")
    print(f"\nSUMMARY: {len(tagged_pairs)} items tagged, {input_count} total (unchanged: {input_count - len(tagged_pairs)})")
    print("Original file ingredients_set_deduped.json is UNTOUCHED.")


if __name__ == "__main__":
    main()
