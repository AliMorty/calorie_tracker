#!/usr/bin/env python3
"""
SMALL SAMPLE TEST: run the macro-matching pipeline on the FIRST 50 items only.
Serial (no parallelism), small chunks. Prints item -> matched USDA source to stdout.
Does NOT overwrite the real ingredients_macros.json.
"""
import csv, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "../hand_crafted/ingredients_form.json"

ITEMS = [f["name"] for f in json.loads(SRC.read_text())][:50]
ROWS = list(csv.DictReader(open(HERE / "foods_per_gram.csv")))


def stem(w):
    if len(w) > 3 and w.endswith('ies'): return w[:-3] + 'y'
    if len(w) > 3 and w.endswith('s') and not w.endswith('ss'): return w[:-1]
    return w


def toks(s):
    return [stem(t) for t in re.sub(r"[^a-z0-9% ]", " ", s.lower()).split() if t]


def wmatch(a, b):
    if a == b: return True
    lo, hi = sorted((a, b), key=len)
    return hi.startswith(lo) and len(hi) - len(lo) <= 2


def candidates(q, k=12):
    qt = toks(q)
    core = q.split(',')[0].split('(')[0].strip().lower()
    want_cooked = 'cooked' in q.lower(); want_raw = 'raw' in q.lower()
    scored = []
    for idx, r in enumerate(ROWS):
        n = r['name']; nl = n.lower(); nt = toks(n)
        score = 0.0
        score += 10 * sum(1 for a in qt if any(wmatch(a, b) for b in nt))
        if qt and all(any(wmatch(a, b) for b in nt) for a in qt): score += 20
        if qt and len(qt) == len(toks(n.split(',')[0])) and \
           all(wmatch(a, b) for a, b in zip(qt, toks(n.split(',')[0]))): score += 1000
        if nt and qt and wmatch(nt[0], qt[0]): score += 8
        if nl.startswith(core[:-1] if core else core): score += 15
        if want_cooked and 'cooked' in nl: score += 15
        if want_raw and 'raw' in nl: score += 15
        if want_cooked and 'raw' in nl: score -= 8
        score -= 0.2 * len(nt)
        if score > 0: scored.append((score, -len(n), idx, r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _, _, _, r in scored[:k]]


def claude(prompt):
    r = subprocess.run(["claude", "--model", "sonnet", "--dangerously-skip-permissions", "-p"],
                       input=prompt, capture_output=True, text=True, timeout=240)
    raw = r.stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        if raw.startswith("json"): raw = raw[4:].strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try: return json.loads(m.group(0))
            except json.JSONDecodeError: pass
        return {}


lookup = {q: candidates(q) for q in ITEMS}


def match_chunk(chunk):
    blocks = []
    for q in chunk:
        lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})"
                 for i, c in enumerate(lookup[q])]
        blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if lines else "  (no candidates)"))
    prompt = ("Match grocery ingredients to USDA foods. Pick the candidate that is the same "
              "food with the right fat level and cooked/raw form. Pick [index], or -1 if none "
              "is genuinely the same food.\nReply ONLY JSON mapping each exact item to int "
              "index or -1. No prose.\n\n" + "\n\n".join(blocks))
    return claude(prompt)


CHUNK = 25
chunks = [ITEMS[i:i + CHUNK] for i in range(0, len(ITEMS), CHUNK)]
print(f"{len(ITEMS)} items in {len(chunks)} chunks (SERIAL)...", file=sys.stderr)

picks = {}
for n, chunk in enumerate(chunks, 1):
    print(f"chunk {n}/{len(chunks)}...", file=sys.stderr)
    d = match_chunk(chunk)
    if not d:
        print(f"  chunk {n} returned NOTHING (failure)", file=sys.stderr)
    picks.update(d)

matched = 0
for q in ITEMS:
    idx = picks.get(q, -1); cands = lookup[q]
    if isinstance(idx, int) and 0 <= idx < len(cands):
        r = cands[idx]
        cal = round(float(r['calories']) * 100)
        print(f"{q:42} | {cal:>5} cal | {r['name']}")
        matched += 1
    else:
        print(f"{q:42} | -- NONE --")

print(f"\nmatched {matched}/{len(ITEMS)}  none={len(ITEMS)-matched}", file=sys.stderr)
