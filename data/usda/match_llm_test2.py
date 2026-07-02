#!/usr/bin/env python3
"""LLM strictly judges USDA candidates for 10 random ingredients; none if no good match."""
import csv, json, subprocess, random

food = json.load(open('../hand_crafted/ingredients_set_deduped.json'))
random.seed()
ITEMS = sorted(random.sample([f['name'] for f in food], 10))

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

blocks, lookup = [], {}
for q in ITEMS:
    cands = candidates(q)
    lookup[q] = cands
    lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})"
             for i, c in enumerate(cands)]
    blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if cands else "  (no candidates)"))

prompt = (
    "You are matching grocery ingredients to USDA foods. For each ITEM, look at "
    "the candidates and pick one ONLY if it is genuinely the same food with "
    "essentially the same macros. Be strict: if the best candidate is only a "
    "loose/approximate substitute (different food, different prep, different "
    "macros), answer -1 (none) instead.\n"
    "Reply ONLY as JSON mapping each exact item string to the chosen [index] "
    "integer, or -1 for none: {\"leek\": 2, ...}. No prose, no fences.\n\n"
    + "\n\n".join(blocks)
)

res = subprocess.run(["claude","--model","sonnet","--dangerously-skip-permissions","-p"],
                     input=prompt, capture_output=True, text=True, timeout=180)
raw = res.stdout.strip()
if raw.startswith("```"):
    raw = raw.split("\n",1)[1].rsplit("```",1)[0].strip()
    if raw.startswith("json"): raw = raw[4:].strip()
picks = json.loads(raw)

def p(r,k): return f"{float(r[k])*100:.1f}"
print(f"{'ITEM':28} {'USDA MATCH':45} {'cal':>5} {'prot':>5} {'carb':>5} {'fat':>5}")
for q in ITEMS:
    idx = picks.get(q, -1)
    cands = lookup[q]
    if not isinstance(idx,int) or idx<0 or idx>=len(cands):
        print(f"{q:28} {'-- none --':45}")
        continue
    r = cands[idx]
    print(f"{q:28} {r['name'][:45]:45} {p(r,'calories'):>5} {p(r,'protein'):>5} {p(r,'carbs'):>5} {p(r,'fat'):>5}")
