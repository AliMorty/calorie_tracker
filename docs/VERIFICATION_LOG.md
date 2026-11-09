# Verification Log

What has actually been checked, how, and by whom. Use this to tell which features are
trustworthy and which were only written and read. Newest entries at the top.

**Levels used below**
- **Device-tested** – Ali used it on a real phone or PC.
- **Browser-tested (agent)** – an agent clicked through it in real Chrome on Ali's PC (separate
  Chrome profile, local copy at `localhost:8080`), at laptop size unless stated.
- **Layout-only (agent)** – an agent loaded the page in a 390px-wide frame in desktop Chrome.
  This checks layout at iPhone width but NOT touch, swipe, the iOS keyboard or Safari quirks.
- **Checked from outside** – an agent queried the live database/site with the public key only.
- **Code-read only** – written and reviewed, never run.
- **Headless-tested (agent)** – an agent ran an automated script in a hidden Chromium browser
  (Playwright) inside WSL against `localhost:8080`. Same engine as Chrome/Edge; not Safari.
- **Not checked.**

---

## 2026-11-08 / 2026-11-09 – Portfolio prep (session 019)

### Privacy (row-level security)
| What | Level | Evidence |
|---|---|---|
| `food_logs`: users only see/edit their own rows | Checked from outside | Ali ran a read-only diagnostic: RLS on, 4 policies using `auth.uid() = user_id`, 438 rows, 0 without an owner. Signed-out request sees 0 rows. |
| `user_foods`: RLS enabled with 4 own-rows policies | Checked from outside | Ali ran the SQL ("Success"). Signed-out request now sees 0 of 19 rows (was 19 before). |
| `foods`: public read-only | Checked from outside | Only a SELECT policy exists; signed-out request sees all 664 rows. Write attempt NOT tried (would be a DB write). |
| Ali's own saved foods still appear when signed in | **Not checked** | Ask Ali to search for one of their saved foods while signed in. |
| A second real account can't see Ali's data | **Not checked** | Only the signed-out case was tested. |

### Demo mode (branch `feature/demo-mode`)
| What | Level | Evidence |
|---|---|---|
| "Try the demo" opens app with sample week, banner, hints card | Browser-tested (agent) | Today + 6 previous days filled; today's dinner empty. |
| No Supabase writes in demo | Browser-tested (agent) | Only Supabase request seen was a read of `foods`; entries saved under `ct_demo_*` localStorage keys; real `ct_diary` untouched. |
| Add food via search (incl. Supabase results) | Browser-tested (agent) | Searched "goat cheese" (exists only in Supabase), added to Dinner. |
| Edit amount | Browser-tested (agent) | Eggs 2 → 3, totals updated. |
| Delete via × button (mouse) | Browser-tested (agent) | Banana removed, totals updated. |
| Delete via swipe (touch) | Headless-tested (agent), emulated iPhone 13 | Synthetic touch events fired in-page: long swipe deleted the row; short swipe snapped back. A real finger on iPhone Safari is still unchecked. (A first attempt via the browser's touch API delivered no events at all — a test-harness problem, not an app bug.) |
| "Remove from log" button on detail screen | Headless-tested (agent) | Clicked on desktop; entry removed. |
| Day arrows move one day | Browser-tested (agent) | In demo only. |
| Hints tick off (add / edit / delete / day) | Browser-tested (agent) | All four ticked. |
| "Exit demo" returns to landing screen | Layout-only (agent) | Clicked inside the 390px frame. |
| Landing + day view layout at phone width | Layout-only (agent) | "or" divider lines fixed after this check. |
| × delete button hidden on touch devices | Headless-tested (agent), emulated iPhone 13 | Not visible with touch emulation. |
| No sideways scrolling at iPhone width | Headless-tested (agent), emulated iPhone 13 | Page width ≤ screen width. |
| No Supabase writes / no JS errors (desktop + emulated iPhone) | Headless-tested (agent) | Watched all requests: zero non-GET requests to Supabase; zero page errors. |
| Anything on a real iPhone | **Not checked** | Emulation doesn't reproduce Safari's toolbar, keyboard or camera behaviour. |
| Live site (GitHub Pages), commit `5b10b99` | Headless-tested (agent) | 2026-11-09 against `alimorty.github.io/calorie_tracker`: demo seeds 8 entries today, × delete, Supabase search (goat cheese), add food, back arrow = one day, panel above nav, emulated-iPhone swipe delete, no sideways scroll. Zero Supabase writes. Only console error: service worker 404 (pre-existing, below). |

### PC layout fixes
| What | Level | Evidence |
|---|---|---|
| Food detail screen capped to phone width on PC | Browser-tested (agent) | Centered 480px column at 1366px window. |
| Hidden detail screen stays off-screen on wide windows | Browser-tested (agent) | Not visible beside the app after closing. |
| Search panel no longer covered by bottom nav (BUGS #6) | Headless-tested (agent) | 1366×800, demo: element at the bottom of the window is the panel, not the nav. Not checked on a phone. |

### Signed-in double setup (BUGS #7)
| What | Level | Evidence |
|---|---|---|
| Cause: setup ran 2+ times for signed-in users | Confirmed in library code | supabase-js emits `INITIAL_SESSION` on subscribe; `js/supabase.js:62` also calls `getSession()`. |
| Fix: setup runs once per page load | Headless-tested (agent), simulated sign-in | Fake session, Supabase calls stubbed. Before: 2× diary/saved-food loads, Save goals ran 2× per click. After: 1× each. Real signed-in test still needs Ali. |
| Original guess "day arrows jump 2 days" | Disproved | Arrows moved one day even before the fix (browser ignores identical duplicate listeners). |
| Different account signing in from another tab reloads the page | **Code-read only** | Added after independent review. |
| Demo shows an error message if sample data can't load | **Code-read only** | Added after independent review. |

### Independent review
A separate reviewer agent read the full diff on 2026-11-09 (read-only). No high-severity bugs; it
confirmed demo mode can't write to Supabase or touch the real diary, the CSS/z-index ordering, and
that these docs don't overclaim. Its two low-severity findings (silent demo failure; stale diary
after a cross-tab account switch) were fixed afterwards.

### Not app features, but checked
| What | Level | Evidence |
|---|---|---|
| No service key / secrets in tracked files or history | Checked (scan) | Pattern scan of all commits; only the public `sb_publishable_` key. One Google OAuth client secret found in a local-only orphaned git object (never on GitHub `main`); rotation recommended. |
| Service worker never registers on the live site | Confirmed in browser (headless) | 0 registrations; console error "Failed to register a ServiceWorker … /sw.js … 404". Pre-existing; left unfixed on purpose (offline caching adds little for one-time visitors and could serve stale files). |
