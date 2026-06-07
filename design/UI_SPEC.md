# UI Specification

This is the single source of truth for all design decisions: layout principles,
animations, transitions, and navigation structure.

Implementation tasks are tracked separately in `issue_documentations/FEATURES.md`.

---

## Navigation Map

The app currently has one navigation graph rooted at the Main View.
As new top-level sections are added (e.g., a bottom navigation bar with
Explore, Settings, etc.), each would become its own navigation graph.

### Graph 1: Daily Tracker (current)

```
+---------------------+
|    Main View        |
|  (Daily summary +   |
|   meal sections)    |
+---------------------+
   |              |
   | tap "+"      | tap existing
   | on meal      | food entry
   v              v
+---------------------+
|  Add Food Panel     |    (slides up from bottom)
|  (search + browse)  |
+---------------------+
   |
   | pick a food
   v
+---------------------+
|  Food Detail Screen |    (slides in from right)
|  (qty, unit, macros)|
+---------------------+
   |
   | tap "Add food"
   | or "Update"
   v
   Back to Main View
```

**Edit shortcut:** Tapping an existing food entry in a meal goes directly
to the Food Detail Screen (skips the Add Food Panel).

**Day navigation:** Prev/next arrows on the main view shift the date.
No panel transition -- the main view content refreshes in place.

### Future: Bottom Navigation Bar

When additional top-level sections are added (like Instagram's bottom bar),
each tab in the bar gets its own navigation graph above. For example:

```
Bottom Bar:  [ Tracker ]  [ Stats ]  [ Settings ]
                 |            |            |
              Graph 1      Graph 2      Graph 3
```

Not yet implemented. This section will be expanded when those features are designed.

---

## Animations and Transitions

### Principles

- **Snappy, not instant.** Every panel transition should have just enough motion
  that the user feels directional flow, but never slow enough to feel like waiting.
- **Direction communicates hierarchy.** Going deeper into the flow = slide from right.
  Going back = slide to right. Overlays = slide up from bottom.
- **Timing: 150-200ms.** Fast enough to feel responsive, slow enough to register.
  Use `ease-out` for entrances (decelerates into place) and `ease-in` for exits.

### Transition Specifications

| Transition | Direction | Duration | Easing | Notes |
|------------|-----------|----------|--------|-------|
| Main View > Add Food Panel | Slide up from bottom | 200ms | ease-out | Overlay fades in simultaneously |
| Add Food Panel > dismiss | Slide down to bottom | 150ms | ease-in | Overlay fades out simultaneously |
| Add Food Panel > Food Detail | Slide in from right | 200ms | ease-out | Add Food Panel hides behind it |
| Food Detail > dismiss | Slide out to right | 150ms | ease-in | Returns to whatever was behind |
| Main View > Food Detail (edit) | Slide in from right | 200ms | ease-out | Direct entry, no intermediate panel |
| Day prev/next | None (instant refresh) | - | - | Content swaps in place, no slide |

### What NOT to animate

- Day navigation (prev/next) -- content refreshes in place, no slide needed.
- Macro number updates while typing quantity -- instant recalculation, no transition.
- Adding/removing food entries from meal lists -- instant for now (list animations can be added later if desired).

---

## Layout Principles

(To be expanded as design decisions are made.)

- Panels stack with z-index: Main View (0) < Overlay (100) < Add Food Panel (101) < Food Detail (200).
- The Add Food Panel is a bottom sheet, not full screen.
- The Food Detail Screen is full screen.
- The `.hidden` class (`display: none`) controls visibility. Animations will need
  to replace this with opacity/transform transitions before adding `.hidden`.

---

## Input Behavior

- **Quantity input (Food Detail Screen):** On focus, the entire value is auto-selected
  (highlighted blue) so the user can immediately type a replacement without backspacing.
  Implemented via `select()` with a short `setTimeout` for iOS Safari compatibility.
  See Feature #1.

---

## UX Polish Roadmap

These are the main reasons the app feels less smooth than native apps like Carbon,
and what to do about each one. Ordered by impact.

### 1. Optimistic UI (high impact)

**Problem:** Every action (add/delete/edit food) waits for Supabase to respond before
updating the screen. This creates a noticeable delay, especially on mobile networks.

**Fix:** Update the UI immediately on user action (assume success), then sync to
Supabase in the background. If the server call fails, revert the UI and show an error.
This is what native apps do — the screen reacts instantly.

### 2. Screen transition animations (high impact)

**Problem:** Panels appear/disappear with `display: none` toggling — instant and jarring.
Native apps slide, fade, or spring into place, giving spatial context.

**Fix:** Replace `.hidden` toggling with CSS transform transitions (already specced in
the Animations section above, but not yet implemented). Panels should slide in/out with
150-200ms easing.

### 3. Real food database API (high impact)

**Problem:** The static local JSON has ~50 foods. Carbon has hundreds of thousands.
Limited search results make the app feel incomplete.

**Fix:** Integrate USDA FoodData Central or OpenFoodFacts API. Show results as user
types with debounced search (300ms delay). Cache recent searches locally.

### 4. Incremental DOM updates (medium impact)

**Problem:** After any change, the entire day re-renders (`innerHTML = ''`). This causes
a brief flash — all food entries disappear and reappear. Native apps update only the
affected row.

**Fix:** Instead of wiping and rebuilding the meal list, surgically insert/remove/update
only the specific DOM element that changed. Alternatively, adopt a lightweight virtual
DOM approach.

### 5. Haptic and micro-feedback (low impact, native-only)

**Problem:** No tactile confirmation on swipe threshold, no subtle bounce on pull,
no press states that feel physical.

**Fix:** Limited options on web. Can add: subtle scale-down on touch (`:active` transform),
CSS spring-style animations for swipe snap-back, and the Vibration API for Android
(`navigator.vibrate(10)` on swipe threshold). iOS Safari doesn't support vibration.

### 6. Typography and spacing refinement (low impact)

**Problem:** Functional but not premium. Native apps have carefully tuned font weights,
letter-spacing, line-height, and whitespace ratios.

**Fix:** Audit padding/margins for consistent vertical rhythm. Use slightly heavier
font weight for numbers (tabular figures). Add subtle color hierarchy (not everything
the same gray).
