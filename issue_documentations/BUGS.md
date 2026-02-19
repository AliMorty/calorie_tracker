# Bug History

This file is the in-repo record of every bug found and fixed in this project.
It is always kept in sync with GitHub Issues.
See CLAUDE.md for the full rules on how to use this file.

---

## Summary Table

| # | Title | Opened | Closed | Status |
|---|-------|--------|--------|--------|
| 1 | Add Food panel height is content-driven - header cuts off or panel drifts | 2026-02-18 | open | open |

---

<!-- Full issue entries go below this line, most recent at the top -->

---

## Issue #1 - Add Food panel height is content-driven - header cuts off or panel drifts
**Opened:** 2026-02-18
**Closed:** open
**Status:** open - fix attempt 1 did not work

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

### Final fix
TBD

### Lessons
TBD
