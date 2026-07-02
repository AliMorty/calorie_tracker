#!/usr/bin/env python3
"""
Improved retrieval + claude-p matching, tested on the 100 most common items.

Steps:
1. ask claude to select the 100 most commonly-used items from the 913
2. for each, build a better candidate shortlist (weighted lexical scorer)
3. claude picks the best candidate (strict) per item, in parallel chunks
4. print table + hit-rate summary
"""
import csv, json, re, subprocess
from concurrent.futures import ThreadPoolExecutor

FOOD = [f['name'] for f in json.load(open('../hand_crafted/ingredients_set_deduped.json'))]
ROWS = list(csv.DictReader(open('foods_per_gram.csv')))


def toks(s):
    return [t for t in re.sub(r"[^a-z0-9% ]", " ", s.lower()).split() if t]


def candidates(q, k=15):
    qt = toks(q)
    qset = set(qt)
    core = q.split(',')[0].split('(')[0].strip().lower()
    scored = []
    for idx, r in enumerate(ROWS):
        n = r['name']
        nl = n.lower()
        nt = toks(n)
        nset = set(nt)
        score = 0.0
        score += 10 * len(qset & nset)                    # whole-word overlap
        if qset and qset <= nset:                          # all query words present
            score += 20
        if qt and toks(n.split(',')[0]) == qt:             # first segment == query
            score += 1000
        if nt and qt and nt[0] == qt[0]:                   # same head word
            score += 8
        if nl.startswith(core):                            # prefix
            score += 15
        score -= 0.2 * len(nt)                             # prefer concise
        score += sum(0.5 for w in qt if w in nl)           # substring fallback
        if score > 0:
            scored.append((score, -len(n), idx, r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _, _, _, r in scored[:k]]


def claude(prompt):
    r = subprocess.run(["claude", "--model", "sonnet", "--dangerously-skip-permissions", "-p"],
                       input=prompt, capture_output=True, text=True, timeout=180)
    raw = r.stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if raw.startswith("json"):
            raw = raw[4:].strip()
    return json.loads(raw)


# step 1: pick 100 common
sel = claude(
    "From this list of grocery ingredients, pick the 100 MOST COMMONLY USED in "
    "everyday cooking. Return ONLY a JSON array of the exact item strings. No prose.\n\n"
    + "\n".join(FOOD))
common = [s for s in sel if s in set(FOOD)][:100]
print(f"selected {len(common)} common items\n")

# step 2: candidates
lookup = {q: candidates(q) for q in common}


# step 3: match in parallel chunks of 20
def match_chunk(chunk):
    blocks = []
    for q in chunk:
        lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})"
                 for i, c in enumerate(lookup[q])]
        blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if lines else "  (no candidates)"))
    prompt = ("Match grocery ingredients to USDA foods. For each ITEM pick a candidate "
              "ONLY if genuinely the same food with essentially the same macros; prefer "
              "plain/raw generic forms; answer -1 if only a loose substitute.\n"
              "Reply ONLY JSON mapping each exact item to chosen [index] int or -1. No prose.\n\n"
              + "\n\n".join(blocks))
    return claude(prompt)


chunks = [common[i:i+20] for i in range(0, len(common), 20)]
picks = {}
with ThreadPoolExecutor(max_workers=len(chunks)) as ex:
    for d in ex.map(match_chunk, chunks):
        picks.update(d)


# step 4: report
def p(r, k): return f"{float(r[k])*100:.0f}"
hit = 0
print(f"{'ITEM':22} {'USDA MATCH':46} {'cal':>4} {'pro':>4} {'carb':>4} {'fat':>4}")
for q in common:
    idx = picks.get(q, -1)
    cands = lookup[q]
    if not isinstance(idx, int) or idx < 0 or idx >= len(cands):
        print(f"{q:22} {'-- none --':46}")
        continue
    hit += 1
    r = cands[idx]
    print(f"{q:22} {r['name'][:46]:46} {p(r,'calories'):>4} {p(r,'protein'):>4} {p(r,'carbs'):>4} {p(r,'fat'):>4}")
print(f"\nMATCHED {hit}/{len(common)}  ({100*hit//max(len(common),1)}%)")
