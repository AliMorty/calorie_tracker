#!/usr/bin/env python3
"""Strict LLM matching for 20 basic staple ingredients."""
import csv, json, subprocess

BASIC = ['egg','milk','white rice','chicken breast','potato','banana','apple',
         'carrot','onion','garlic','butter','olive oil','sugar','salt',
         'all-purpose flour','tomato','broccoli','cheddar cheese','ground beef',
         'spaghetti']

food = {f['name'] for f in json.load(open('../hand_crafted/ingredients_set_deduped.json'))}
ITEMS = [b for b in BASIC if b in food]  # keep only ones present
rows = list(csv.DictReader(open('foods_per_gram.csv')))

def candidates(q, k=10):
    ql = q.lower().replace(',', ' ').replace('(', ' ').replace(')', ' ').replace('/', ' ')
    words = [w for w in ql.split() if len(w) > 2]
    scored = []
    for idx, r in enumerate(rows):
        s = sum(1 for w in words if w in r['name'].lower())
        if s: scored.append((s, -len(r['name']), idx, r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _,_,_,r in scored[:k]]

blocks, lookup = [], {}
for q in ITEMS:
    cands = candidates(q); lookup[q] = cands
    lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})" for i,c in enumerate(cands)]
    blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if cands else "  (no candidates)"))

prompt = ("Match grocery ingredients to USDA foods. For each ITEM pick a candidate "
    "ONLY if genuinely the same food with essentially the same macros; if only a "
    "loose substitute, answer -1. Prefer plain/raw generic forms.\n"
    "Reply ONLY JSON mapping each exact item to chosen [index] int or -1. No prose.\n\n"
    + "\n\n".join(blocks))

res = subprocess.run(["claude","--model","sonnet","--dangerously-skip-permissions","-p"],
                     input=prompt, capture_output=True, text=True, timeout=180)
raw = res.stdout.strip()
if raw.startswith("```"):
    raw = raw.split("\n",1)[1].rsplit("```",1)[0].strip()
    if raw.startswith("json"): raw = raw[4:].strip()
picks = json.loads(raw)

def p(r,k): return f"{float(r[k])*100:.1f}"
print(f"{'ITEM':20} {'USDA MATCH':48} {'cal':>5} {'prot':>5} {'carb':>5} {'fat':>5}")
for q in ITEMS:
    idx = picks.get(q,-1); cands = lookup[q]
    if not isinstance(idx,int) or idx<0 or idx>=len(cands):
        print(f"{q:20} {'-- none --':48}"); continue
    r = cands[idx]
    print(f"{q:20} {r['name'][:48]:48} {p(r,'calories'):>5} {p(r,'protein'):>5} {p(r,'carbs'):>5} {p(r,'fat'):>5}")
