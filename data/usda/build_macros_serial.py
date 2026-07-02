#!/usr/bin/env python3
"""
SERIAL, CHECKPOINTED macro build for all 913 form-tagged ingredients.

- Processes chunks ONE AT A TIME (no parallelism).
- After each chunk, verifies EVERY item in the chunk got a pick. Retries the chunk
  once if any are missing.
- If a chunk still fails, STOPS immediately, saves progress to picks_cache.json, and
  reports which chunk/items failed. Re-running resumes from the saved cache.

INPUT  : ../hand_crafted/ingredients_form.json    (READ ONLY)
CACHE  : ../hand_crafted/picks_cache.json          (resume checkpoint)
OUTPUT : ../hand_crafted/ingredients_macros.json   (name, cal/pro/carb/fat, usda_source)
         ../hand_crafted/unmatched.json            (the "none" items)
         ../hand_crafted/macros_review.txt          (human-readable)
"""
import csv, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "../hand_crafted/ingredients_form.json"
CACHE = HERE / "../hand_crafted/picks_cache.json"
OUT = HERE / "../hand_crafted/ingredients_macros.json"
UNMATCHED = HERE / "../hand_crafted/unmatched.json"
REVIEW = HERE / "../hand_crafted/macros_review.txt"

ITEMS = [f["name"] for f in json.loads(SRC.read_text())]
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


def missing_items(chunk, d):
    """Return chunk items that did NOT get an int pick in dict d."""
    return [q for q in chunk if not isinstance(d.get(q), int)]


# --- resume from checkpoint ---
picks = json.loads(CACHE.read_text()) if CACHE.exists() else {}
remaining = [q for q in ITEMS if q not in picks]
CHUNK = 25
chunks = [remaining[i:i + CHUNK] for i in range(0, len(remaining), CHUNK)]
print(f"{len(ITEMS)} items total | {len(picks)} already cached | "
      f"{len(remaining)} to do in {len(chunks)} chunks (SERIAL)", file=sys.stderr)

for n, chunk in enumerate(chunks, 1):
    print(f"chunk {n}/{len(chunks)} ({len(chunk)} items)...", file=sys.stderr)
    d = match_chunk(chunk)
    miss = missing_items(chunk, d)
    if miss:
        print(f"  chunk {n}: {len(miss)} item(s) missing a pick -> retrying once", file=sys.stderr)
        d2 = match_chunk(chunk)
        d = {**d, **{k: v for k, v in d2.items() if isinstance(v, int)}}
        miss = missing_items(chunk, d)
    if miss:
        # save what we have and STOP
        picks.update({k: v for k, v in d.items() if isinstance(v, int)})
        CACHE.write_text(json.dumps(picks, indent=2))
        print("\n*** STOPPED ***", file=sys.stderr)
        print(f"chunk {n}/{len(chunks)} failed after a retry. {len(miss)} item(s) "
              f"never got a pick:", file=sys.stderr)
        for q in miss:
            print(f"  - {q}", file=sys.stderr)
        print(f"\nProgress saved to {CACHE.name} ({len(picks)} items done). "
              f"Fix the issue and re-run to resume.", file=sys.stderr)
        sys.exit(1)
    picks.update({q: d[q] for q in chunk})
    CACHE.write_text(json.dumps(picks, indent=2))  # checkpoint after every chunk

# --- all chunks done: write outputs ---
def per100(r, key):
    try: return round(float(r[key]) * 100, 1)
    except (TypeError, ValueError): return None


out, review, unmatched = [], [], []
matched = 0
for q in ITEMS:
    idx = picks.get(q, -1); cands = lookup[q]
    rec = {"name": q, "calories": None, "protein": None, "carbs": None,
           "fat": None, "usda_source": None}
    if isinstance(idx, int) and 0 <= idx < len(cands):
        r = cands[idx]
        rec.update(calories=per100(r, "calories"), protein=per100(r, "protein"),
                   carbs=per100(r, "carbs"), fat=per100(r, "fat"),
                   usda_source=r["name"])
        matched += 1
        review.append(f"{q:42} | {rec['calories']:>5} cal | {r['name']}")
    else:
        review.append(f"{q:42} | -- NONE --")
        unmatched.append(q)
    out.append(rec)

OUT.write_text(json.dumps(out, indent=2))
UNMATCHED.write_text(json.dumps(unmatched, indent=2))
REVIEW.write_text("\n".join(review) + "\n")

assert len(out) == len(ITEMS), "reconcile mismatch!"
print(f"\nDONE  matched {matched}/{len(ITEMS)}  none={len(ITEMS)-matched}", file=sys.stderr)
print(f"-> {OUT.name}\n-> {UNMATCHED.name}\n-> {REVIEW.name}", file=sys.stderr)
