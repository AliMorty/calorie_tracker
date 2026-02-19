# Feature Requests

This file is the in-repo record of every feature request / enhancement for this project.
It is always kept in sync with GitHub Issues (labeled `enhancement`).

---

## Summary Table

| # | Title | Opened | Closed | Status |
|---|-------|--------|--------|--------|
| 1 | Auto-select amount input text on focus | 2026-02-19 | - | open |

---

<!-- Full feature entries go below this line, most recent at the top -->

---

## Feature #1 - Auto-select amount input text on focus
**GitHub Issue:** #1
**Opened:** 2026-02-19
**Closed:** -
**Status:** open

### What is requested
When the quantity input field on the food detail screen (tab 3) receives focus, the entire value (e.g., "100") should be pre-selected with a blue highlight. This way, typing any new character immediately replaces the whole value instead of requiring the user to manually backspace to clear it first.

### Why
Currently the user has to tap into the field, then backspace multiple times to delete the existing number before typing a new one. Auto-selecting is faster and is standard UX behavior (e.g., browser address bars work this way).

### Target platforms
- **Primary:** iPhone Safari
- **Secondary:** Desktop browsers

### Relevant code
- `index.html:114` -- the `fd-qty` input element (`<input type="number" id="fd-qty">`)
- `js/ui.js:276-290` -- `showFoodDetail()` where the input value is set and event handlers are attached

### Implementation notes
- The standard approach is calling `input.select()` on focus.
- iPhone Safari has known quirks with `select()` on `type="number"` inputs -- may need `setSelectionRange(0, 9999)` or a brief `setTimeout` wrapper.
- Needs testing on actual iPhone Safari to confirm the highlight appears correctly.
