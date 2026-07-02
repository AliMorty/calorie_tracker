#!/usr/bin/env python3
"""Retrieval with plural-stemming + claude matching, tested on 50 curated items
(fat variants + previous plural failures + a generic mix)."""
import csv, json, re, subprocess
from concurrent.futures import ThreadPoolExecutor

CURATED = [
    # fat / percentage variants
    'greek yogurt, 0%', 'greek yogurt, 2%', 'greek yogurt, 5%',
    'milk, 1%', 'milk, 2%', 'milk, skim (0%)', 'milk, whole (3.25%)',
    'cottage cheese, 1%', 'cottage cheese, 2%', 'cottage cheese, 4%',
    'ground beef, extra lean (10% fat)', 'ground beef, lean (17% fat)',
    'ground beef, regular (27% fat)', 'cream cheese, light', 'mayonnaise, light',
    # earlier plural failures
    'apple', 'banana', 'onion', 'tomato', 'potato', 'basil', 'thyme',
    'bell pepper', 'lemon',
    # generic mix
    'egg', 'chicken breast', 'broccoli', 'spinach', 'carrot', 'cucumber',
    'garlic', 'ginger', 'honey', 'butter', 'olive oil', 'peanut butter',
    'strawberries', 'blueberries', 'orange', 'grapes, green', 'walnuts',
    'almond', 'brown rice', 'cheddar cheese', 'soy sauce', 'ketchup',
    'mustard, yellow', 'salmon, atlantic (fresh)', 'shrimp', 'lentils',
]

FOODSET = {f['name'] for f in json.load(open('../hand_crafted/ingredients_set_deduped.json'))}
ITEMS = [c for c in CURATED if c in FOODSET]
ROWS = list(csv.DictReader(open('foods_per_gram.csv')))


def stem(w):
    if len(w) > 3 and w.endswith('ies'):
        return w[:-3] + 'y'
    return w


def toks(s):
    return [stem(t) for t in re.sub(r"[^a-z0-9% ]", " ", s.lower()).split() if t]


def wmatch(a, b):
    """words match if equal or one is a prefix of the other within 2 chars (plurals)."""
    if a == b:
        return True
    lo, hi = sorted((a, b), key=len)
    return hi.startswith(lo) and len(hi) - len(lo) <= 2


def overlap(qt, nt):
    return sum(1 for q in qt if any(wmatch(q, n) for n in nt))


def seg_eq(qt, seg):
    return len(qt) == len(seg) and all(wmatch(a, b) for a, b in zip(qt, seg))


def candidates(q, k=15):
    qt = toks(q)
    core = q.split(',')[0].split('(')[0].strip().lower()
    scored = []
    for idx, r in enumerate(ROWS):
        n = r['name']; nl = n.lower(); nt = toks(n)
        score = 0.0
        score += 10 * overlap(qt, nt)
        if qt and all(any(wmatch(qq, nn) for nn in nt) for qq in qt):
            score += 20
        if qt and seg_eq(qt, toks(n.split(',')[0])):
            score += 1000
        if nt and qt and wmatch(nt[0], qt[0]):
            score += 8
        if nl.startswith(core) or (core and nl.startswith(core[:-1])):
            score += 15
        score -= 0.2 * len(nt)
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
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # salvage the first {...} block if extra text leaked in
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        print(f"[WARN] chunk returned non-JSON ({len(raw)} chars): {raw[:120]!r}")
        return {}


lookup = {q: candidates(q) for q in ITEMS}


def match_chunk(chunk):
    blocks = []
    for q in chunk:
        lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})"
                 for i, c in enumerate(lookup[q])]
        blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if lines else "  (no candidates)"))
    prompt = ("Match grocery ingredients to USDA foods. Pick the candidate that best matches "
              "the ITEM, paying attention to fat level / percentage (e.g. '2%' -> the 2% milkfat "
              "row, '0%' -> nonfat). Prefer plain/raw generic forms. Answer -1 only if no candidate "
              "is the same food.\nReply ONLY JSON mapping each exact item to chosen [index] int or -1. "
              "No prose.\n\n" + "\n\n".join(blocks))
    return claude(prompt)


chunks = [ITEMS[i:i+17] for i in range(0, len(ITEMS), 17)]
picks = {}
with ThreadPoolExecutor(max_workers=len(chunks)) as ex:
    for d in ex.map(match_chunk, chunks):
        picks.update(d)


def p(r, k): return f"{float(r[k])*100:.0f}"
hit = 0
print(f"{'ITEM':28} {'USDA MATCH':46} {'cal':>4} {'pro':>4} {'carb':>4} {'fat':>4}")
for q in ITEMS:
    idx = picks.get(q, -1); cands = lookup[q]
    if not isinstance(idx, int) or idx < 0 or idx >= len(cands):
        print(f"{q:28} {'-- none --':46}"); continue
    hit += 1; r = cands[idx]
    print(f"{q:28} {r['name'][:46]:46} {p(r,'calories'):>4} {p(r,'protein'):>4} {p(r,'carbs'):>4} {p(r,'fat'):>4}")
print(f"\nMATCHED {hit}/{len(ITEMS)}  ({100*hit//max(len(ITEMS),1)}%)")
