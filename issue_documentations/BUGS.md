# Bug History

This file is the in-repo record of every bug found and fixed in this project.
It is always kept in sync with GitHub Issues.
See CLAUDE.md for the full rules on how to use this file.

---

## Summary Table

| # | Title | Opened | Closed | Status |
|---|-------|--------|--------|--------|
| 1 | Add Food panel height is content-driven - header cuts off or panel drifts | 2026-02-18 | 2026-02-18 | fixed |
| 2 | Search results show recent foods above matches - should be reversed | 2026-02-18 | open | open |

---

<!-- Full issue entries go below this line, most recent at the top -->

---

## Issue #2 - Search results show recent foods above matches - should be reversed
**Opened:** 2026-02-18
**Closed:** open
**Status:** open

### What happened
When the user types a search query in the Add Food panel (e.g. "rice"), the panel shows:
1. RECENT section at the top (foods added today, unfiltered)
2. ALL FOODS section below (filtered search results matching the query)

The user wants the opposite behaviour when actively searching: the most relevant search matches should appear at the top, with recent foods either hidden or shown below the results.

### Expected behaviour
When the search bar is empty: show Recent section at top, All Foods below (current behaviour is correct).
When the user is actively typing a query: hide the Recent section entirely and show only the filtered search results, ranked by relevance.

### Root cause
Not yet investigated. The relevant code is likely in `js/ui.js` in the `showAddFoodPanel` `oninput` handler and `_renderRecentSection`.

### Fix attempts
None yet.

### Final fix
TBD

### Lessons
TBD

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
