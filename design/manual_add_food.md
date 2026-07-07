# Feature Spec — Manually Add a Food (Issue #9)

**Status:** planned — TOP PRIORITY (to be built before finishing the barcode scanner #4)
**GitHub issue:** #9 "user added foods"
**Related:** #6 (completing the shared database — different: that's about the global USDA list, this is user-entered foods)

## Goal

Let the user add a food on the spot, by hand, when it isn't in the database — enter its name and
macros, specify the serving size those macros are for, then log however much they actually ate
(rescaled). Optionally save the food to a personal list so it can be reused later.

## User-facing requirements (from Ali)

1. In the add-food panel there is an **"Enter manually"** option.
2. The manual form collects:
   - **Name** of the food
   - **Macros**: calories, protein, carbs, fat
   - **Serving size the macros are given for** — e.g. "per 250 g". Ali's example: the label says
     values per 250 g; he enters those, then logs whatever amount he consumed and it **rescales**.
3. A **checkbox: "Add this to my list of foods?"**
   - **No** → one-time only: the food is added to *today's log* for this meal, but not saved for reuse.
   - **Yes** → in addition to logging it, the food is **saved to the user's personal food list**, so
     it shows up in future searches/recent and can be re-logged.
4. After entering, Ali sets **how much he actually ate** and the macros rescale from the reference
   serving to the consumed amount.

## How it fits the existing code (design notes)

- **Normalize to per-gram.** Everything in the app stores macros **per gram** (see
  `data/common_foods.json`, the Supabase `foods` table, and `_adaptFlatFood` in `js/app.js`, which
  multiplies by 100). So a manual entry of "X kcal per N grams" should be stored as
  `perGram = X / N` (and same for each macro). This makes it identical in shape to every other food.
- **Reuse the food-detail screen for rescaling.** `UI.showFoodDetail` already has a grams input with
  live macro recomputation (`calcFoodNutrition`). Build the manual food object with a `per100g`
  block (`perGram * 100`) and a single `g` unit, then open the detail screen prefilled — the user
  types the consumed grams and confirms. No new rescaling math needed; it reuses what edit-food (#5)
  already does.
- **One-time vs saved:**
  - *One-time*: construct the food object in memory, go straight to the detail screen → confirm →
    it's saved as a normal `food_logs` entry (the entry already stores its own macros, so it survives
    with no reference food — same mechanism the #5 fix relies on).
  - *Saved*: additionally persist the food to a **per-user food list** so it appears in search/recent.

## Open decision — where do saved user-foods live?

The one thing to settle before building. Options:

1. **Supabase per-user table `user_foods`** (recommended long-term): columns
   `id, user_id, name, calories, protein, carbs, fat` (per-gram), scoped by `user_id`. Syncs across
   devices; searchable alongside the shared `foods` table. Requires creating the table (a bit of SQL
   Ali runs) — and RLS if privacy mattered (Ali has said it doesn't, for now, see #11).
2. **localStorage only** (fastest to ship): store user-foods in the browser like daily goals
   currently are. No backend change, but they don't sync across devices and are lost if the browser
   data is cleared.

**Recommendation:** Supabase `user_foods` table, because the whole point of "save to my list" is
reuse over time and across sessions/devices. But if Ali wants it usable *today* with zero setup,
start with localStorage and migrate later. **Confirm with Ali when building.**

## Suggested build order

1. Add "Enter manually" entry point + the manual form UI in the add-food panel.
2. Wire the form → normalize to per-gram → open the food-detail screen prefilled for rescaling → log.
   (This alone delivers the one-time path and the rescale requirement — usable immediately.)
3. Add the "save to my foods" checkbox + persistence (per the storage decision above) + surface saved
   foods in search/recent.

Steps 1–2 give Ali the "add a food by hand and log the right amount" capability while the barcode
work is paused; step 3 adds reuse.
