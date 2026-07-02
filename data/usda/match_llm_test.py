#!/usr/bin/env python3
"""Prototype: retrieve USDA candidates with a script, let the LLM pick by index."""
import csv, json, subprocess

ITEMS = ['beef gravy','leek','paprika, smoked','pearl onions',
         'pineapple, canned chunks','puff pastry (frozen)','salt beef',
         'special k','sugar, raw / turbinado','zucchini']

rows = list(csv.DictReader(open('foods_per_gram.csv')))

def candidates(q, k=10):
    ql = q.lower().replace(',', ' ').replace('(', ' ').replace(')', ' ').replace('/', ' ')
    words = [w for w in ql.split() if len(w) > 2]
    scored = []
    for idx, r in enumerate(rows):
        nl = r['name'].lower()
        s = sum(1 for w in words if w in nl)
        if s:
            scored.append((s, -len(r['name']), idx, r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _,_,_,r in scored[:k]]

# build prompt; LLM answers with the candidate INDEX (or -1 for none)
blocks, lookup = [], {}
for q in ITEMS:
    cands = candidates(q)
    lookup[q] = cands
    lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})"
             for i, c in enumerate(cands)]
    blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if cands else "  (no candidates)"))

prompt = (
    "For each ITEM, choose the candidate that best matches it as a generic "
    "ingredient. Reply with the candidate's [index] number, or -1 if none fits.\n"
    "Return ONLY JSON mapping each exact item string to an integer index: "
    "{\"beef gravy\": 0, ...}. No prose, no fences.\n\n" + "\n\n".join(blocks)
)

res = subprocess.run(["claude","--model","sonnet","--dangerously-skip-permissions","-p"],
                     input=prompt, capture_output=True, text=True, timeout=180)
raw = res.stdout.strip()
if raw.startswith("```"):
    raw = raw.split("\n",1)[1].rsplit("```",1)[0].strip()
    if raw.startswith("json"): raw = raw[4:].strip()
picks = json.loads(raw)

def per100(r, key): return f"{float(r[key])*100:.1f}"

print(f"{'ITEM':28} {'USDA MATCH':45} {'cal':>5} {'prot':>5} {'carb':>5} {'fat':>5}")
for q in ITEMS:
    idx = picks.get(q, -1)
    cands = lookup[q]
    if not isinstance(idx, int) or idx < 0 or idx >= len(cands):
        print(f"{q:28} {'-- none (fill another way) --':45}")
        continue
    r = cands[idx]
    print(f"{q:28} {r['name'][:45]:45} "
          f"{per100(r,'calories'):>5} {per100(r,'protein'):>5} "
          f"{per100(r,'carbs'):>5} {per100(r,'fat'):>5}")
