# Bug History

This file is the in-repo record of every bug found and fixed in this project.
It is always kept in sync with GitHub Issues.
See CLAUDE.md for the full rules on how to use this file.

---

## Summary Table

| # | Title | Opened | Closed | Status |
|---|-------|--------|--------|--------|
| 1 | Add Food panel height is content-driven - header cuts off or panel drifts | 2026-02-18 | 2026-02-18 | fixed |
| 2 | Search results show recent foods above matches - should be reversed | 2026-02-18 | 2026-02-19 | fixed |
| 3 | Supabase food search returns irrelevant results before staple foods | 2026-06-07 | — | workaround |
| 4 | Tapping an added database (USDA) food entry does not reopen it for editing | 2026-07-03 | 2026-07-06 | fixed |
| 5 | Barcode scanner Confirm button/result bar pushed off-screen | 2026-07-08 | 2026-07-08 | fixed |

---

<!-- Full issue entries go below this line, most recent at the top -->

---

## Issue #5 - Barcode scanner Confirm button/result bar pushed off-screen
**Opened:** 2026-07-08
**Closed:** 2026-07-08
**Status:** fixed

### What happened
On the barcode scanner (iPhone Safari), scanning worked (green flash), but no result/number
showed and the Confirm button was not visible — it sat off the bottom of the screen.

### Root cause
`.viewfinder-camera` in `css/styles.css` had both `height: 100%` and `flex: 1`. Inside the
full-viewport flex column (`.barcode-viewfinder`), `height: 100%` forced the camera to the full
viewport height, so the header + camera already filled the screen and the `.barcode-result` bar
(number + Confirm) was pushed below the visible area.

### Final fix
Removed `height: 100%` from `.viewfinder-camera` (kept `flex: 1` + added `min-height: 0`) so the
camera fills only the leftover space and the result bar stays on screen. Also added
`env(safe-area-inset-bottom)` padding to `.barcode-result` so the Confirm button clears the iPhone
home indicator. Confidence: high — clear flexbox sizing conflict; matches the reported symptom.

### Lessons
In a fixed full-height flex column, size children with `flex` alone; a `height: 100%` on a flex
child fights the flex layout and overflows. Watch iOS safe areas for bottom-anchored controls.

---

## Issue #4 - Tapping an added database (USDA) food entry does not reopen it for editing
**Opened:** 2026-07-03
**Closed:** 2026-07-06
**Status:** fixed
(GitHub issue #5)

### What happened
In a meal's list of added foods, tapping an entry that was added from a **handmade** food
(e.g. banana, bread — from `data/foods.json`) reopens the food-detail screen so the grams/serving
can be edited. But tapping an entry that was added from a **database (USDA/Supabase)** food does
nothing — the detail screen never opens, so those entries cannot be edited after adding.

Reported by Ali on 2026-07-03. Not yet reproduced/confirmed on a specific device — noticed during
normal use.

### Root cause (hypothesis, not yet fixed — high confidence)
`handleEditEntry` in `js/app.js:209-218` finds the food to edit by scanning the in-memory
`foodDatabase` array for a matching `id`:

```
for (var i = 0; i < foodDatabase.length; i++) {
  if (foodDatabase[i].id === entry.foodId) { food = foodDatabase[i]; break; }
}
if (!food) return;   // <- silently exits here for database foods
```

`foodDatabase` is only populated with the handmade foods (`data/foods.json`) plus the 100 local
`data/common_foods.json` items (see `_bootApp`, `js/app.js:~147-160`). Foods added via Supabase
search (`searchFoodsFromDB` → `SupabaseAuth.searchFoods`) are **not** added to `foodDatabase`, so
when you later tap that entry, the lookup fails, `food` stays null, and `if (!food) return;`
exits without opening anything. Handmade foods are in the array, so they work.

### Final fix
Applied the reconstruct-from-entry approach (option 1 below) in `js/app.js` `handleEditEntry`.
When the food isn't found in `foodDatabase` and the entry was logged in grams
(`servingUnit === 'g'`), we rebuild a gram-based food object from the entry's own stored macros:
`per100g = storedMacro * 100 / servingQty`, with a single `g` unit. `showFoodDetail` then reopens
normally and `onFoodConfirmed` updates the existing entry. No network/Supabase lookup needed, so it
also works offline and for entries logged in past sessions. Minor rounding drift is possible
(stored macros are rounded), which is acceptable for a calorie tracker.
**Confidence:** high — root cause was confirmed by reading `handleEditEntry` (the silent
`if (!food) return;`), and the reconstruction is the exact inverse of `calcFoodNutrition` for grams.
Still needs a real device tap-test to confirm end-to-end.

### Fix attempts
Single change, described under Final fix.

### Alternative approaches considered (for reference)
Don't rely on `foodDatabase` for editing. Options, roughly in order of preference:
1. Store enough of the food's data on the entry itself when it's added (it already saves
   `foodId` + `name`; also persist the per-gram macros / unit info), then reconstruct a food
   object from the entry in `handleEditEntry` instead of looking it up.
2. Re-fetch the food from Supabase by name/id on tap.
3. Cache every searched/picked food into `foodDatabase` so the later lookup succeeds.
Option 1 is the most robust (works offline, no dependency on the food still existing in search).

### Lessons
`handleEditEntry`'s silent `if (!food) return;` hides the failure — there's no console error, so
the tap just appears dead. When fixing, consider logging or a user-facing message when a food
can't be resolved. Note the two food sources with different shapes: handmade foods have `units`
+ real `id`s; adapted USDA foods use `id: name` and grams-only (see `_adaptFlatFood`).

---

## Issue #3 - Supabase food search returns irrelevant results before staple foods
**Opened:** 2026-06-07
**Closed:** —
**Status:** workaround

### What happened
When searching the Supabase `foods` table (7,793 USDA SR Legacy foods), common staple foods are buried under processed/branded variants:

1. **"brown rice"** → Returns snack bars and baby food ("Snacks, rice cakes, brown rice, sesame seed") instead of plain "Rice, brown, long-grain, cooked". Root cause: USDA names use inverted word order ("Rice, brown") so `ilike '%brown rice%'` doesn't match the staple food at all — only products where "brown rice" appears as a contiguous substring.

2. **"dark chocolate"** → Returns "Candies, SPECIAL DARK Chocolate Bar" before "Chocolate, dark, 70-85% cacao solids". The branded candy has the query words in order and a shorter name, so it scores higher.

### Root cause
Two compounding problems:

**Problem A — Query mismatch:** The initial `ilike '%brown rice%'` query searches for the exact contiguous string. USDA names invert word order with commas ("Rice, brown, long-grain, cooked"), so the staple food doesn't even match the query.

**Problem B — No relevance ranking:** Supabase `ilike` returns results in insertion order with no relevance scoring. The first 30 matches are whatever the database finds first, which is often processed/branded products since USDA has many more of those than staple foods.

**Deeper root cause:** USDA names are scientific/taxonomic ("Chicken, broilers or fryers, breast, skinless, boneless, meat only, cooked, grilled") while users search with everyday language ("chicken breast"). This is a fundamental mismatch that simple string matching cannot fully solve.

### Fix attempts

#### Attempt 1 — Client-side ranking (starts-with + name length)
- **Files changed:** `js/ui.js`
- **What was changed:** Added `_rankSearchResults()` that sorts results: names starting with the query first, then shorter names first
- **Confidence:** Low — wouldn't help since the staple foods weren't even being returned by the query
- **Outcome:** Did not fix the brown rice problem because the real issue was at the query level

#### Attempt 2 — Split query into individual words
- **Files changed:** `js/supabase.js`
- **What was changed:** Split search query into words and apply separate `ilike` filters for each: "brown rice" → `ilike '%brown%' AND ilike '%rice%'`
- **Confidence:** High that it would fix the missing results problem
- **Outcome:** Worked — "Rice, brown, long-grain, cooked" now appears in results. But ranking still imperfect.

#### Attempt 3 — Smarter ranking with word order and scoring
- **Files changed:** `js/ui.js`
- **What was changed:** Replaced simple ranking with a scoring system: exact contiguous match (-100), words in same order (-50), starts with first query word (-25), plus name length as tiebreaker
- **Confidence:** Medium — improves ranking but cannot fully solve the USDA naming mismatch
- **Outcome:** Better but not perfect. "dark chocolate" still shows a branded candy before the plain chocolate entry. Ranking is a workaround, not a real fix.

### Final fix
No final fix — current state is a **workaround**. The search is functional but ranking is imperfect due to the fundamental mismatch between USDA scientific naming and human search patterns.

### Proposed real fix
Use an LLM to generate a `search_tags` column for each food in the Supabase table, containing human-friendly aliases (e.g. "chicken breast" for "Chicken, broilers or fryers, breast, skinless..."). Then search against both `name` and `search_tags`. This would solve the problem properly but requires a one-time batch processing step.

### Lessons
- USDA food names are scientific/inverted, not how humans search. Any food database using USDA data will have this problem.
- Simple `ilike` with a single contiguous string fails when the database uses comma-separated inverted naming.
- Splitting into per-word matching is essential but insufficient — ranking/relevance is a separate problem.
- Client-side ranking hacks have diminishing returns. A proper solution requires either PostgreSQL full-text search with `ts_rank`, or LLM-generated search aliases.
- When building search, test with multi-word queries early — single-word queries ("chicken") hide the word-order problems that multi-word queries ("chicken breast") expose.

---

## Issue #2 - Search results show recent foods above matches - should be reversed
**Opened:** 2026-02-18
**Closed:** 2026-02-19
**Status:** fixed

### What happened
When the user types a search query in the Add Food panel (e.g. "rice"), the panel shows:
1. RECENT section at the top (foods added today, unfiltered)
2. ALL FOODS section below (filtered search results matching the query)

The user wants the opposite behaviour when actively searching: the most relevant search matches should appear at the top, with recent foods either hidden or shown below the results.

### Expected behaviour
When the search bar is empty: show Recent section at top, All Foods below (current behaviour is correct).
When the user is actively typing a query: hide the Recent section entirely and show only the filtered search results, ranked by relevance.

### Root cause
The `oninput` handler in `js/ui.js:370` correctly calls `classList.add('hidden')` on `#recent-section` when a query is typed. However there is no CSS rule for `.hidden` on generic elements. The stylesheet only has specific rules:
- `.food-detail-screen.hidden { display: none }`
- `.overlay.hidden, .add-food-panel.hidden { display: none }`

There is no generic `.hidden { display: none }`. So adding `hidden` to `#recent-section` and `#all-foods-heading` via JS has zero visual effect - those elements stay fully visible.

**Fix:** Add a single generic `.hidden { display: none; }` rule to `css/styles.css`. Safe to do - every use of the `hidden` class in this codebase intends the element to be invisible. The existing specific rules are redundant with it but harmless.

**Confidence: very high.** Confirmed by grepping CSS for all `.hidden` rules - only three specific selectors exist, none covering `#recent-section` or `#all-foods-heading`.

### Fix attempts

#### Attempt 1
- **Files changed:** `css/styles.css`
- **What was changed:** Added `.hidden { display: none; }` as a generic rule at the top of the utility section
- **Reasoning:** Direct fix for the missing CSS rule. Every element that uses the `hidden` class in this project intends to be hidden.
- **Confidence:** Very high.
- **Outcome:** PARTIALLY fixed. The recent section now hides correctly during search (CSS was missing a generic `.hidden { display: none }` rule). However the ORDER was not addressed - recent still appeared above all foods when no query was active. A second fix was needed.

#### Attempt 2
- **Files changed:** `index.html`, `js/ui.js`
- **What was changed:** Swapped `#food-list` and `#recent-section` in the HTML so all foods renders at the top and recent appears at the bottom. Removed `#all-foods-heading` element (no longer needed). Updated `showAddFoodPanel` in ui.js to match the new order and remove all-foods-heading references.
- **Reasoning:** The CSS fix in attempt 1 was correct but only solved half the problem - the hiding. The ordering was wrong from the start. Swapping the DOM order is the simplest fix.
- **Confidence:** High.
- **Outcome:** DID NOT FULLY RESOLVE. The DOM order was swapped correctly but the fix also hides the recent section during search, which Ali did not want. Ali clarified: recent foods should ALWAYS be visible below the food list - even when the user is actively searching. Hiding recents during search was an assumption made without confirming with Ali first.

**Clarified desired behaviour:**
- No search query: all foods at top, recent at bottom - both always visible
- Typing a query: filtered search results at top, recent foods still visible below

#### Attempt 3 (final)
- **Files changed:** `index.html`, `js/ui.js`
- **What was changed:** (1) Wrapped `#food-list` in a new `#all-foods-section` div with an "All Foods" heading, restoring the labeled two-section layout. (2) Removed the JS lines that hid `#recent-section` during search, so both sections stay visible at all times.
- **Reasoning:** Attempt 2 had removed the section headings and merged everything into a flat list, which was never requested. The original request was simply to swap the order of two labeled sections. The HTML already had `#food-list` before `#recent-section` (correct order from attempt 2), so only the missing "All Foods" heading and the unwanted hiding logic needed to be addressed.
- **Confidence:** High. Minimal change, restoring previously working UI pattern.
- **Outcome:** WORKED. Confirmed by Ali on alimorty.github.io/calorie_tracker.

### Final fix
Added an "All Foods" heading above `#food-list` in `index.html` and removed the JS logic in `ui.js` that hid the recent section during search. The DOM order was already correct from attempt 2 (`#food-list` before `#recent-section`), so the only missing pieces were the section label and the unwanted hiding behavior.

### Lessons
- Always confirm intended behaviour before implementing. The ticket said "recent foods either hidden or shown below" - two options were written and the wrong one was chosen without asking.
- Do not make UX decisions unilaterally. When the spec is ambiguous, ask Ali before coding.
- Attempt 1 fixed the wrong thing (CSS hiding) without fixing the order. Attempt 2 fixed the order but introduced unwanted hiding behaviour and removed section labels that were never asked to be removed. Two partial fixes compounded each other.
- **Do not remove UI elements that were not part of the bug report.** The section headings ("RECENT", "ALL FOODS") were working fine. The only request was to swap order. Removing headings and merging into a flat list was scope creep that made the UI worse.
- **Make the smallest possible change.** If the request is "swap the order of two sections", the fix should be swapping two DOM elements - not restructuring the entire panel.

---

## Issue #1 - Add Food panel height is content-driven - header cuts off or panel drifts
**Opened:** 2026-02-18
**Closed:** 2026-02-18
**Status:** fixed - confirmed working on iPhone by Ali

### What happened
On iPhone Safari, the Add Food bottom sheet panel does not have a stable fixed height.
- When many results are shown (e.g. typing "B" returns ~7+ foods), the panel grows very tall and pushes the header (X button + "Add to Breakfast" title) almost completely off the top of the screen
- When few results are shown (e.g. typing "Brea" returns 2 foods), the panel shrinks to a small height and sits low on the screen
- The panel height changes as the user types, causing the whole panel to visually drift up and down

**Reference photos:**
- `issue-001_panel-too-short-few-results_brea-typed.jpg` - panel is small with 2 results
- `issue-001_panel-too-tall-many-results_b-typed.jpg` - panel is huge with many results, header nearly off screen
- `issue-001_panel-header-cutoff-empty-search.jpg` - header completely cut off with full food list

### Root cause
The panel CSS uses `max-height: 90vh` but no fixed `height`. This means the panel grows and shrinks with the content of the food list. When the list is long, the panel hits `max-height` and the header gets pushed off the top. When the list is short, the panel shrinks from the top down, drifting toward the bottom.

The fix is to give the panel a fixed height so it is always the same size regardless of how many results are in the list. The list inside (`.panel-body`) already has `overflow-y: auto` so it will scroll within whatever fixed height the panel has.

**Confidence in root cause: high.** The CSS is clear - there is no `height` set, only `max-height`. The behavior observed in the photos is exactly what you would expect from this.

**File to change:** `css/styles.css` - `.add-food-panel` rule.

### Fix attempts

#### Attempt 1
- **Files changed:** `css/styles.css` - `.add-food-panel`
- **What was changed:** Replace `max-height: 90vh` with `height: 72vh` to give the panel a stable fixed height
- **Reasoning:** 72vh leaves enough room above the panel to see the main screen behind the overlay, matches roughly what the reference design shows, and is tall enough to show ~6-8 food items comfortably on an iPhone screen
- **Confidence:** Fairly confident this will fix the drift. Exact value (72vh) may need tuning based on how it looks on device.
- **Outcome:** DID NOT WORK. Ali tested on iPhone Safari and the issue persisted. The panel still does not behave as a stable fixed-height sheet. Root cause is not yet fully understood - the `height: 72vh` change alone was insufficient.

#### Attempt 2
- **Files changed:** `css/styles.css` - `.add-food-panel`
- **What was changed:** Replace `height: 72vh` with `top: 28%` and `bottom: 0`, removing the `height` property entirely. Both edges are now explicitly pinned so the browser computes the height from two fixed constraints rather than from a `vh` calculation.
- **Reasoning:** iOS Safari has a known bug where `vh` units are calculated against the maximum viewport height (address bar hidden), making the panel taller than the visible area when the address bar is showing. By pinning `top` and `bottom` explicitly, we remove the `vh` calculation entirely and force the browser to derive the height from two absolute positions. There is no JS positioning code - the panel is purely CSS `position: fixed`. Confirmed by reading `ui.js:348` - `showAddFoodPanel` only toggles the `hidden` class, nothing else.
- **Confidence:** Medium. This approach is generally more reliable than `vh` on iOS Safari but cannot be confirmed without testing on device. If this also fails, next step is collaborative `console.log` debugging to inspect actual computed values at runtime.
- **Outcome:** DID NOT WORK on iPhone. However Ali provided Windows browser screenshots which show the panel behaving correctly on desktop - fixed size, stable header, list scrolls. This is a critical finding: **the CSS fix is correct and works on desktop. The problem is iOS Safari specific.**

**Reference photos (Windows - working correctly):**
- `issue-001_windows-working-few-results_brea-typed.png` - panel stable with 2 results and empty space below
- `issue-001_windows-working-many-results-scrollable.png` - panel stable with full list scrollable inside

**New hypothesis:** iOS Safari has a well-known bug where `position: fixed` elements shift when the virtual keyboard opens. When the user taps the search bar, iOS Safari opens the keyboard, shrinks the visual viewport, and tries to scroll the page to show the focused input. This causes `position: fixed` elements to move even though they should be immune to scrolling. As the user types and the keyboard stays open, any further viewport adjustments keep shifting the panel. This is NOT a CSS sizing problem - the CSS is correct. It is an iOS Safari keyboard + `position: fixed` interaction problem.

**Fix approach for attempt 3:** Use the browser's Visual Viewport API (`window.visualViewport`) to detect when the keyboard opens/closes and dynamically adjust the panel's `bottom` value in JavaScript to compensate. When the keyboard is open, `window.innerHeight - window.visualViewport.height` gives the keyboard height. Setting `panel.style.bottom = keyboardHeight + 'px'` keeps the panel sitting just above the keyboard.

**Confidence:** Medium-high. The Visual Viewport API is the standard modern solution for this iOS Safari issue. The risk is that it may not be supported on older iOS versions, but iOS 13+ supports it which covers the vast majority of active iPhones.

#### Attempt 3
- **Files changed:** `js/ui.js` - `showAddFoodPanel` and `hideAddFoodPanel`
- **What was changed:** Added Visual Viewport API listeners inside `showAddFoodPanel`. When the visual viewport resizes (keyboard opens/closes), the panel's `bottom` is adjusted to equal the keyboard height. Listeners are cleaned up when the panel is hidden.
- **Reasoning:** The CSS positioning is correct (confirmed working on desktop). The issue is purely iOS Safari's keyboard interaction with `position: fixed`. The Visual Viewport API is the standard fix for this.
- **Confidence:** Medium-high. Cannot test on device directly.
- **Outcome:** WORKED. Confirmed fixed on iPhone by Ali.

### Final fix
The CSS sizing was never the problem - `top: 28%; bottom: 0` on `.add-food-panel` works correctly on desktop and was the right approach. The actual bug was iOS Safari's handling of `position: fixed` elements when the virtual keyboard opens.

iOS Safari makes a deliberate distinction between the **layout viewport** (used to calculate CSS positions) and the **visual viewport** (what the user actually sees). When the keyboard opens, the visual viewport shrinks but the layout viewport stays the same. `position: fixed` elements anchor to the layout viewport, so they end up physically under the keyboard. iOS then tries to scroll the page to compensate, causing fixed elements to drift.

**Fix applied in `js/ui.js`:**
- Added `_adjustPanelForKeyboard()` which reads `window.visualViewport.height` and computes keyboard height as `window.innerHeight - window.visualViewport.height - window.visualViewport.offsetTop`
- Sets `panel.style.bottom` to the keyboard height so the panel always sits just above the keyboard
- Listeners attached on `showAddFoodPanel`, removed on `hideAddFoodPanel` to avoid memory leaks

### Lessons
- Always test mobile web apps on a real iOS device early. iOS Safari's `position: fixed` + keyboard behavior is fundamentally different from every other browser and cannot be reproduced on desktop.
- When a CSS fix works on desktop but not iOS, the first suspect should always be the iOS Safari visual viewport / keyboard interaction.
- Two failed CSS-only attempts were needed before identifying this as a JS problem. In hindsight, the Windows screenshots provided by Ali were the key evidence - they proved the CSS was correct and pointed directly at iOS-specific behavior.
- The Visual Viewport API (`window.visualViewport`) is the correct modern tool for handling keyboard-aware layouts on iOS Safari. It is supported on iOS 13+.
