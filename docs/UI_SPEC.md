# UI/UX Specification

This document describes every screen, modal, and interaction flow in the app. When building a feature, follow this spec exactly. If something is unclear or needs changing, update this document first, then build.

Convention: `[Button Label]` means a tappable element. `-->` means "navigates to" or "triggers". Indentation shows nesting/hierarchy.

---

## 1. Main Screen (Diary View)

This is what the user sees when they open the app.

```
+------------------------------------------+
|  [<]      Today, Feb 16        [>]       |  <-- date header, sticky top
+------------------------------------------+
|                                          |
|     1,610          390         2,000     |
|     eaten       remaining       goal     |
|  [============================----]      |  <-- calorie progress bar
|                                          |
|  Protein    115g / 150g                  |
|  [========================------]        |
|  Carbs      158g / 250g                  |
|  [================--------------]        |
|  Fat         60g / 65g                   |
|  [==============================]        |
|                                          |
+------------------------------------------+
|  Breakfast                 408 Cal  [+]  |
|  P 15g  C 66g  F 11g                    |
|  ----------------------------------------|
|  Oats, rolled, dry                       |
|  1/2 cup                     154 cal     |
|  ----------------------------------------|
|  Banana                                  |
|  1 medium                    105 cal     |
|  ----------------------------------------|
|  Milk, whole                             |
|  1 cup                       149 cal     |
+------------------------------------------+
|  Lunch                     508 Cal  [+]  |
|  ...                                     |
+------------------------------------------+
|  Dinner                    430 Cal  [+]  |
|  ...                                     |
+------------------------------------------+
|  Snacks                    264 Cal  [+]  |
|  ...                                     |
+------------------------------------------+
```

### Interactions on Main Screen

| Element | Action | Result |
|---------|--------|--------|
| `[<]` arrow | Tap | Navigate to previous day |
| `[>]` arrow | Tap | Navigate to next day |
| Date label | (future) Tap | Open date picker calendar |
| `[+]` on any meal | Tap | Open **Add Food Sheet** for that meal (see section 2) |
| Food entry row | Tap | Open **Food Detail View** for that entry (see section 3) |
| Food entry row | Swipe left | Reveal delete button (see section 3) |
| Summary card | (future) Tap | Open **Goals Settings** (see section 5) |

---

## 2. Add Food Sheet

Opens when user taps `[+]` on a meal section. This is a **bottom sheet** that slides up from the bottom of the screen, covering ~90% of the viewport.

```
+------------------------------------------+
|  [X Close]     Add to Breakfast          |  <-- header with meal name
+------------------------------------------+
|  [  Search foods...              ] [Scan]|  <-- search bar + scan button
+------------------------------------------+
|                                          |
|  RECENT                                  |  <-- section header
|  ----------------------------------------|
|  Chicken Breast, grilled                 |
|  100g  |  165 cal                        |
|  ----------------------------------------|
|  Rice, white, cooked                     |
|  1 cup  |  206 cal                       |
|  ----------------------------------------|
|  Banana                                  |
|  1 medium  |  105 cal                    |
|  ----------------------------------------|
|  ... more recent items ...               |
|                                          |
|  [+ Quick Add]                           |  <-- button at bottom
|                                          |
+------------------------------------------+
```

### States of the Add Food Sheet

**Default state (just opened):**
- Search bar is empty and focused (keyboard may appear on mobile)
- Below search bar: list of recently used foods (most recent first)
- At the bottom: a "Quick Add" button

**Searching state (user is typing):**
- Search results replace the recent foods list
- Results filter in real-time as user types (autocomplete)
- Results come from: local food database, user-created custom foods, and (future) API search
- Each result shows: food name, default serving, calories

**Empty results:**
- Message: "No foods found"
- Prominent "Quick Add" and "Create Custom Food" buttons

### Interactions on Add Food Sheet

| Element | Action | Result |
|---------|--------|--------|
| `[X Close]` | Tap | Close the sheet, return to diary |
| Search bar | Type | Filter foods in real-time (autocomplete) |
| `[Scan]` button | Tap | Open **Scanner View** (see section 4) |
| Food result row | Tap | Open **Serving Size Picker** (see section 2.1) |
| `[+ Quick Add]` | Tap | Open **Quick Add Form** (see section 2.2) |

---

### 2.1 Serving Size Picker

Opens after tapping a food from search results. This is a smaller modal or inline expansion.

```
+------------------------------------------+
|  [< Back]     Chicken Breast, grilled    |
+------------------------------------------+
|                                          |
|  Serving size:                           |
|  [  1  ] x [  100g          v ]          |  <-- quantity input + unit dropdown
|                                          |
|  Nutrition for this serving:             |
|  Calories:  165                          |
|  Protein:   31g                          |
|  Carbs:     0g                           |
|  Fat:       3.6g                         |
|                                          |
|  [ Add to Breakfast ]                    |  <-- primary action button
|                                          |
+------------------------------------------+
```

- Quantity is a number input (supports decimals like 1.5)
- Unit dropdown shows available serving units for this food (g, cup, oz, "1 large", etc.)
- Nutrition values update live as quantity changes
- "Add to Breakfast" button saves the entry and closes back to the diary

---

### 2.2 Quick Add Form

For when the food is not in the database. User manually enters everything.

```
+------------------------------------------+
|  [< Back]          Quick Add             |
+------------------------------------------+
|                                          |
|  Food name:                              |
|  [  e.g. Homemade soup            ]     |
|                                          |
|  Calories:    [       ]                  |
|  Protein (g): [       ]                  |
|  Carbs (g):   [       ]                  |
|  Fat (g):     [       ]                  |
|                                          |
|  [ ] Save to my custom foods             |  <-- checkbox
|                                          |
|  [ Add to Breakfast ]                    |
|                                          |
+------------------------------------------+
```

- All fields are required except "Save to my custom foods"
- If checkbox is checked, the food is saved to the custom foods database for future reuse
- Tapping "Add to Breakfast" saves the entry and returns to diary

---

## 3. Food Detail View / Edit / Delete

When user taps an existing food entry in the diary.

**Option A - Inline swipe (preferred for mobile):**
- Swipe left on a food entry reveals a red `[Delete]` button
- Tapping the entry itself opens an edit view (same as Serving Size Picker, pre-filled with current values, with "Update" instead of "Add")

**Option B - Tap to open detail:**
- Tapping a food entry opens a detail view with:
  - Full nutrition info
  - Editable serving quantity
  - `[Update]` button to save changes
  - `[Delete]` button (with confirmation) to remove the entry

We will decide on Option A vs B during implementation based on what feels better.

---

## 4. Scanner View

Accessed from the `[Scan]` button in the Add Food Sheet. Opens a full-screen camera view.

```
+------------------------------------------+
|  [X Close]                               |
|                                          |
|                                          |
|         +--------------------+           |
|         |                    |           |
|         |   Camera viewfinder|           |
|         |                    |           |
|         +--------------------+           |
|                                          |
|  [Barcode]           [Nutrition Label]   |  <-- toggle between scan modes
|                                          |
+------------------------------------------+
```

### Scanner Modes

**Barcode mode (default):**
- Camera scans for UPC/EAN barcodes
- On successful scan: look up barcode in food database
  - If found: go directly to Serving Size Picker with the food pre-loaded
  - If not found: show "Food not found for this barcode" with option to Quick Add and associate the barcode for future scans

**Nutrition Label mode (OCR):**
- Camera captures an image of a nutrition facts table
- OCR extracts: calories, protein, carbs, fat (and serving size if possible)
- Shows extracted values in an editable Quick Add form so user can verify/correct
- User names the food and saves

### Technical Notes
- Camera access requires HTTPS or localhost (browser security policy)
- Barcode scanning: use a JS library (e.g., QuaggaJS or ZXing-js)
- OCR: use Tesseract.js (runs in-browser) or a cloud OCR API
- Barcode lookup: Open Food Facts API (free, has Canadian products)

---

## 5. Goals Settings

Accessed by tapping the summary card on the main screen (future).

```
+------------------------------------------+
|  [< Back]          Daily Goals           |
+------------------------------------------+
|                                          |
|  Calories:    [ 2000 ]                   |
|  Protein (g): [  150 ]                   |
|  Carbs (g):   [  250 ]                   |
|  Fat (g):     [   65 ]                   |
|                                          |
|  [ Save ]                                |
|                                          |
+------------------------------------------+
```

- Simple form, numeric inputs
- Save persists to localStorage (and later to backend)
- Values reflect in the progress bars on the main screen immediately

---

## 6. Navigation Model

The app uses a **single-screen model with overlays**. There is no page-based routing.

```
Main Screen (Diary)
  |
  +--> [+] --> Add Food Sheet (bottom sheet overlay)
  |              |
  |              +--> Food result --> Serving Size Picker (sub-view within sheet)
  |              +--> [Scan] --> Scanner View (full-screen overlay)
  |              +--> [Quick Add] --> Quick Add Form (sub-view within sheet)
  |
  +--> Tap food entry --> Food Detail / Edit (modal or inline)
  |
  +--> Tap summary card --> Goals Settings (modal or new view)
  |
  +--> [<] [>] --> Same screen, different date
```

All overlays have a close/back button that returns to the previous state. The browser back button should also close overlays (using history.pushState).

---

## 7. Design Principles

1. **Mobile-first.** Every element must be comfortably tappable with a thumb on a phone.
2. **Minimal taps to log food.** The most common flow (add a recent food) should be: tap [+], tap food, tap [Add]. Three taps.
3. **No dead ends.** Every screen has a clear way back.
4. **Show macros everywhere.** Any time a food appears (search results, diary entries, recent list), show at minimum its calories. Show full macros where space allows.
5. **Fast.** No loading spinners for local operations. Autocomplete should feel instant.

---

## Updating This Document

This is a living document. Before building any UI feature:
1. Check this spec for how it should look and behave
2. If the spec is missing details, add them here first
3. Then build to match the spec

If during implementation something feels wrong or a better approach emerges, update this document to reflect the change so it stays the source of truth.
