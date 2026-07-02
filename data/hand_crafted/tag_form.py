#!/usr/bin/env python3
"""
Tag each of the 913 ingredients with the form people normally LOG it in:
  cooked / raw / none(=not applicable, e.g. spices, oils, condiments, dairy)

The LLM only returns a tag per item (decisions, not a rewrite). A Python script
applies the rename and reconciles counts so no item can disappear.

Rule given to the LLM:
  - cooked  -> foods normally eaten cooked: meat, poultry, fish, grains, rice,
              pasta, legumes/lentils/beans, potatoes, eggs (when cooked)
  - raw     -> foods normally eaten raw: most vegetables eaten raw, fruit, salad
  - none    -> form is meaningless: spices, herbs(dried), oils, vinegars, sauces,
              condiments, dairy, sugar, flour, drinks, nuts, canned/processed items

Outputs:
  - form_tags.json        {name: tag}
  - ingredients_form.json  renamed list (cooked/raw appended), macros still null
  - form_review.txt        OLD -> NEW side by side for eyeballing
INPUT ingredients_set_deduped.json is READ ONLY.
"""
import json, re, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "ingredients_set_deduped.json"
ITEMS = [f["name"] for f in json.loads(SRC.read_text())]

PROMPT = (
    "For each food ITEM below, output how people normally LOG/eat it:\n"
    "  \"cooked\" = normally eaten cooked (meat, poultry, fish, grains, rice, pasta,\n"
    "             lentils, beans, potatoes, eggs when cooked)\n"
    "  \"raw\"    = normally eaten raw (most salad vegetables, fruit)\n"
    "  \"none\"   = form is meaningless: spices, dried herbs, oils, vinegars, sauces,\n"
    "             condiments, dairy, cheese, sugar, flour, drinks, nuts, seeds,\n"
    "             already-processed/canned/frozen-prepared items, breads\n"
    "Default to \"cooked\" if a cookable whole food and unsure.\n"
    "Return ONLY JSON mapping each exact item string to one of cooked/raw/none. "
    "No prose, no fences.\n\nITEMS:\n{listing}"
)


def claude(prompt):
    r = subprocess.run(["claude", "--model", "sonnet", "--dangerously-skip-permissions", "-p"],
                       input=prompt, capture_output=True, text=True, timeout=180)
    raw = r.stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        print(f"[WARN] non-JSON chunk: {raw[:120]!r}")
        return {}


def tag_chunk(chunk):
    listing = "\n".join(chunk)
    return claude(PROMPT.format(listing=listing))


CHUNK = 60
chunks = [ITEMS[i:i + CHUNK] for i in range(0, len(ITEMS), CHUNK)]
tags = {}
with ThreadPoolExecutor(max_workers=len(chunks)) as ex:
    for d in ex.map(tag_chunk, chunks):
        tags.update(d)

# apply
def rename(name, tag):
    if tag not in ("cooked", "raw"):
        return name
    # don't double-tag if the name already says it
    if "cooked" in name.lower() or "raw" in name.lower():
        return name
    return f"{name}, {tag}"

renamed, review, missing = [], [], []
for n in ITEMS:
    t = tags.get(n)
    if t is None:
        missing.append(n)
        t = "none"
    new = rename(n, t)
    renamed.append({"name": new, "calories": None, "protein": None,
                    "carbs": None, "fat": None})
    flag = "  <-- CHANGED" if new != n else ""
    review.append(f"{n:40} | {t:7} -> {new}{flag}")

(HERE / "form_tags.json").write_text(json.dumps(tags, indent=2))
(HERE / "ingredients_form.json").write_text(json.dumps(renamed, indent=2))
(HERE / "form_review.txt").write_text("\n".join(review) + "\n")

assert len(renamed) == len(ITEMS), "reconcile mismatch!"
changed = sum(1 for r in review if "CHANGED" in r)
print(f"items: {len(ITEMS)}  tagged: {len(tags)}  missing(->none): {len(missing)}")
print(f"renamed: {changed}")
from collections import Counter
print("tag counts:", dict(Counter(tags.values())))
print("review -> form_review.txt   list -> ingredients_form.json")
