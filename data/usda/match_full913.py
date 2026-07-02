#!/usr/bin/env python3
"""Full 913-item USDA macro-matching pipeline.
Reuses candidates()/scorer and claude() from match_test50.py verbatim.
Adds: capped parallelism (max 8), tolerant retry pass, status tracking."""
import csv, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

SOURCE = '../hand_crafted/ingredients_set_cooked.json'
REFCSV = 'foods_per_gram.csv'
OUT_JSON = 'ingredients_macros.json'
OUT_REPORT = 'match_full913_report.txt'

ITEMS = [f['name'] for f in json.load(open(SOURCE))]
ROWS = list(csv.DictReader(open(REFCSV)))

# ── scorer (copied verbatim from match_test50.py, with one extra boost for
#    "cooked" so cooked items prefer boiled/cooked USDA rows) ──────────────

def stem(w):
    if len(w) > 3 and w.endswith('ies'):
        return w[:-3] + 'y'
    return w


def toks(s):
    return [stem(t) for t in re.sub(r"[^a-z0-9% ]", " ", s.lower()).split() if t]


def wmatch(a, b):
    """words match if equal or one is a prefix of the other within 2 chars."""
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
    item_has_cooked = 'cooked' in qt
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
        # Boost: if item is "X cooked" and USDA row also mentions cooked/boiled
        if item_has_cooked:
            cooked_words = {'cooked', 'boiled', 'baked', 'roasted', 'stewed',
                            'braised', 'broiled', 'grilled', 'fried', 'steamed'}
            if any(w in cooked_words for w in nt):
                score += 12
        score -= 0.2 * len(nt)
        if score > 0:
            scored.append((score, -len(n), idx, r))
    scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
    return [r for _, _, _, r in scored[:k]]


def claude(prompt):
    r = subprocess.run(
        ["claude", "--model", "sonnet", "--dangerously-skip-permissions", "-p"],
        input=prompt, capture_output=True, text=True, timeout=240)
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
        print(f"[WARN] chunk returned non-JSON ({len(raw)} chars): {raw[:120]!r}",
              flush=True)
        return {}


# ── pre-compute candidates for all items ─────────────────────────────────
print(f"Computing candidates for {len(ITEMS)} items …", flush=True)
lookup = {q: candidates(q) for q in ITEMS}
print("Done.", flush=True)


# ── prompt builder ────────────────────────────────────────────────────────
def match_chunk(chunk):
    blocks = []
    for q in chunk:
        lines = [f"  [{i}] {c['name']} (cal/100g={float(c['calories'])*100:.0f})"
                 for i, c in enumerate(lookup[q])]
        blocks.append(f"ITEM: {q}\n" + ("\n".join(lines) if lines else "  (no candidates)"))
    prompt = (
        "Match grocery ingredients to USDA foods. Pick the candidate that best matches "
        "the ITEM, paying attention to fat level / percentage (e.g. '2%' -> the 2% milkfat "
        "row, '0%' -> nonfat). For items ending in 'cooked', strongly prefer a cooked/boiled "
        "USDA row over a raw one when available. Prefer plain/raw generic forms for uncooked items. "
        "Answer -1 only if no candidate is the same food.\n"
        "Reply ONLY JSON mapping each exact item to chosen [index] int or -1. "
        "No prose.\n\n" + "\n\n".join(blocks)
    )
    return claude(prompt)


# ── parallel matching pass ────────────────────────────────────────────────
CHUNK_SIZE = 17
MAX_WORKERS = 8

def run_pass(items, label="pass-1"):
    chunks = [items[i:i+CHUNK_SIZE] for i in range(0, len(items), CHUNK_SIZE)]
    print(f"[{label}] {len(items)} items → {len(chunks)} chunks "
          f"(max_workers={MAX_WORKERS})", flush=True)
    picks = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        for i, d in enumerate(ex.map(match_chunk, chunks), 1):
            picks.update(d)
            print(f"  chunk {i}/{len(chunks)} done ({len(picks)} picks so far)",
                  flush=True)
    return picks

picks = run_pass(ITEMS, "pass-1")

# ── retry: items that got no valid pick ──────────────────────────────────
def valid_pick(q, d):
    idx = d.get(q)
    return isinstance(idx, int) and (idx == -1 or 0 <= idx < len(lookup[q]))

missing = [q for q in ITEMS if not valid_pick(q, picks)]
if missing:
    print(f"\nRetrying {len(missing)} items in smaller chunks …", flush=True)
    retry_picks = run_pass(missing, "pass-2")
    picks.update(retry_picks)

still_missing = [q for q in ITEMS if not valid_pick(q, picks)]
if still_missing:
    print(f"[WARN] {len(still_missing)} items still unmatched after retry → marked 'skipped'",
          flush=True)

# ── build output ──────────────────────────────────────────────────────────
def p100(r, k):
    return round(float(r[k]) * 100, 1)

results = []
n_matched = n_none = n_skipped = 0
sample_matches = []
none_items = []

for q in ITEMS:
    idx = picks.get(q)
    if not isinstance(idx, int) or not (idx == -1 or 0 <= idx < len(lookup[q])):
        # skipped
        n_skipped += 1
        results.append({"name": q, "calories": None, "protein": None,
                        "carbs": None, "fat": None, "status": "skipped",
                        "usda_match": None})
        continue
    if idx == -1:
        n_none += 1
        none_items.append(q)
        results.append({"name": q, "calories": None, "protein": None,
                        "carbs": None, "fat": None, "status": "none",
                        "usda_match": None})
        continue
    r = lookup[q][idx]
    cal  = p100(r, 'calories')
    pro  = p100(r, 'protein')
    carb = p100(r, 'carbs')
    fat  = p100(r, 'fat')
    n_matched += 1
    results.append({"name": q, "calories": cal, "protein": pro,
                    "carbs": carb, "fat": fat, "status": "matched",
                    "usda_match": r['name']})
    sample_matches.append((q, r['name'], cal, pro, carb, fat))

with open(OUT_JSON, 'w') as f:
    json.dump(results, f, indent=2)

total = len(ITEMS)
rate = 100 * n_matched // max(total, 1)

# ── report ────────────────────────────────────────────────────────────────
lines = [
    "=" * 70,
    "USDA MACRO-MATCHING REPORT  —  full 913-item run",
    "=" * 70,
    f"Total items  : {total}",
    f"Matched      : {n_matched}  ({rate}%)",
    f"None (-1)    : {n_none}",
    f"Skipped      : {n_skipped}",
    f"Match rate   : {rate}%",
    "",
    "─" * 70,
    "SAMPLE MATCHES (up to 30)",
    "─" * 70,
]
for (q, usda, cal, pro, carb, fat) in sample_matches[:30]:
    lines.append(f"  {q[:35]:<35} -> {usda[:40]:<40}  "
                 f"cal={cal:.0f} pro={pro:.1f} carb={carb:.1f} fat={fat:.1f}")

lines += [
    "",
    "─" * 70,
    f"NONE items ({n_none})",
    "─" * 70,
]
for name in none_items:
    lines.append(f"  {name}")

lines += [
    "",
    "─" * 70,
    f"SKIPPED items ({n_skipped})",
    "─" * 70,
]
for q in still_missing:
    lines.append(f"  {q}")
if not still_missing:
    lines.append("  (none)")

report_text = "\n".join(lines) + "\n"
with open(OUT_REPORT, 'w') as f:
    f.write(report_text)

print("\n" + report_text)
print(f"Wrote {OUT_JSON} and {OUT_REPORT}.")
