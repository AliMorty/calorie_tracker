#!/usr/bin/env python3
"""
Test CANDIDATE RECALL on 30 tricky items (percentages, fat variants, cooked/raw,
synonyms). For each item we print the top-8 candidates so we can eyeball whether
the CORRECT USDA row is present, then show the LLM's pick.

Recall is the thing that matters: the scorer only has to put the right row in the
shortlist; the LLM does the final smart choice.
"""
import csv, json, re, subprocess
from concurrent.futures import ThreadPoolExecutor

TRICKY = [
    'milk, 1%', 'milk, 2%', 'milk, skim (0%)', 'milk, whole (3.25%)',
    'greek yogurt, 0%', 'greek yogurt, 2%', 'greek yogurt, 5%',
    'cottage cheese, 1%', 'cottage cheese, 2%', 'cottage cheese, 4%',
    'ground beef, extra lean (10% fat)', 'ground beef, lean (17% fat)',
    'ground beef, regular (27% fat)',
    'lentils, cooked', 'chicken breast, cooked', 'white rice, cooked',
    'spaghetti, cooked', 'black beans, cooked', 'broccoli, cooked',
    'apple, raw', 'banana', 'spinach, raw', 'carrot, raw', 'tomato',
    'cheddar cheese', 'mozzarella cheese', 'cream cheese, light',
    'mayonnaise, light', 'butter, unsalted', 'olive oil',
]

ROWS = list(csv.DictReader(open('foods_per_gram.csv')))


def stem(w):
    if len(w) > 3 and w.endswith('ies'): return w[:-3] + 'y'
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'): return w[:-1]
    return w


def toks(s):
    return [stem(t) for t in re.sub(r"[^a-z0-9% ]", " ", s.lower()).split() if t]


def pcts(s):
    return set(re.findall(r"\d+(?:\.\d+)?%", s.lower()))


def wmatch(a, b):
    if a == b: return True
    lo, hi = sorted((a, b), key=len)
    return hi.startswith(lo) and len(hi) - len(lo) <= 2


def candidates(q, k=8):
    qt = toks(q)  # "milk, 2%" -> ["milk", "2%"]; % stays part of the token
    core = q.split(',')[0].split('(')[0].strip().lower()
    want_cooked = 'cooked' in q.lower(); want_raw = 'raw' in q.lower()
    scored = []
    for idx, r in enumerate(ROWS):
        n = r['name']; nl = n.lower(); nt = toks(n)
        score = 0.0
        # normal word-overlap scoring; "2%" is just another word worth +10
        score += 10 * sum(1 for a in qt if any(wmatch(a, b) for b in nt))
        if qt and all(any(wmatch(a, b) for b in nt) for a in qt): score += 20
        if qt and len(qt) == len(toks(n.split(',')[0])) and \
           all(wmatch(a, b) for a, b in zip(qt, toks(n.split(',')[0]))): score += 1000
        if nt and qt and wmatch(nt[0], qt[0]): score += 8
        if nl.startswith(core[:-1] if core else core): score += 15
        # form awareness (mild, never overrides food-word overlap)
        if want_cooked and 'cooked' in nl: score += 15
        if want_raw and 'raw' in nl: score += 15
        if want_cooked and 'raw' in nl: score -= 8
        score -= 0.2 * len(nt)
        if score > 0: scored.append((score, -len(n), idx, r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _, _, _, r in scored[:k]]


def claude(prompt):
    r = subprocess.run(["claude", "--model", "sonnet", "--dangerously-skip-permissions", "-p"],
                       input=prompt, capture_output=True, text=True, timeout=180)
    raw = r.stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if raw.startswith("json"): raw = raw[4:].strip()
    try: return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0)) if m else {}


lookup = {q: candidates(q) for q in TRICKY}


def match_chunk(chunk):
    blocks = []
    for q in chunk:
        lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})"
                 for i, c in enumerate(lookup[q])]
        blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if lines else "  (none)"))
    prompt = ("Match grocery ingredients to USDA foods. Match fat %/level and cooked/raw "
              "form precisely. Pick the best candidate [index], or -1 if none is the same food.\n"
              "Reply ONLY JSON mapping each exact item to int index or -1. No prose.\n\n"
              + "\n\n".join(blocks))
    return claude(prompt)


chunks = [TRICKY[i:i+15] for i in range(0, len(TRICKY), 15)]
picks = {}
with ThreadPoolExecutor(max_workers=len(chunks)) as ex:
    for d in ex.map(match_chunk, chunks):
        picks.update(d)

# report: show candidates + which the LLM picked (marked *)
for q in TRICKY:
    idx = picks.get(q, -1); cands = lookup[q]
    print(f"\n=== {q}  (LLM pick: {idx}) ===")
    for i, c in enumerate(cands):
        mark = " *" if i == idx else "  "
        print(f"{mark}[{i}] {c['name'][:60]:60} cal={float(c['calories'])*100:.0f}")
    if not cands: print("   (no candidates)")
