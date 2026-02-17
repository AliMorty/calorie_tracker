# Feature Roadmap

This is the master list of all planned features. Each feature has a priority tier and current status. Update this document as features are completed or new ones are identified.

Status legend: `planned` | `in-progress` | `done` | `cut`

---

## Tier 1 - Core (must have for daily use)

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 1.1 | Diary view with date navigation | done | Step 1 complete. Hardcoded data. |
| 1.2 | localStorage persistence | planned | Wire up real read/write so entries survive refresh |
| 1.3 | Add food to a meal | planned | The "+" button flow (see UI_SPEC.md for details) |
| 1.4 | Quick Add | planned | Manually type food name + macros without searching a database |
| 1.5 | Remove food entry | planned | Swipe or tap to delete an entry from a meal |
| 1.6 | Edit food entry | planned | Change serving quantity on an existing entry |
| 1.7 | Daily macro goals | planned | Set calorie/protein/carbs/fat targets, persist in localStorage |
| 1.8 | Food search with autocomplete | planned | Type-ahead search against the local food database |
| 1.9 | Basic food database | planned | Expand foods.json to a larger curated Canadian food list |

## Tier 2 - Scanner and Camera Features

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 2.1 | Barcode scanner | planned | Use phone camera to scan food barcode (UPC/EAN), look up nutrition info |
| 2.2 | Barcode-to-food database | planned | Map barcodes to nutrition data. Start with Open Food Facts API (has Canadian products). Cache results locally. |
| 2.3 | OCR nutrition table scanner | planned | Point camera at a nutrition facts label, extract calories/protein/carbs/fat automatically |
| 2.4 | OCR result editing | planned | After OCR extraction, show editable form so user can correct any misreads before saving |

## Tier 3 - Food Database and Data

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 3.1 | Canadian food database | planned | Curate a substantial database of Canadian brand foods and common items |
| 3.2 | User-created custom foods | planned | User can create and save their own foods with full macro info |
| 3.3 | Recently used foods | planned | Show recently logged foods for quick re-adding |
| 3.4 | Favorite foods | planned | Star/pin frequently used foods for even faster access |
| 3.5 | Food database sync | planned | When we add a backend, user-added foods contribute to a shared database |

## Tier 4 - User Accounts and Sync

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 4.1 | User registration and login | planned | Email/password or OAuth |
| 4.2 | Cloud sync | planned | Sync diary data across devices via backend API |
| 4.3 | User profile | planned | Name, age, weight, height (for TDEE calculations later) |
| 4.4 | Data export | planned | Export diary as CSV or JSON |

## Tier 5 - Analytics and Insights

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 5.1 | Weekly summary view | planned | Bar chart or table of daily totals for the past 7 days |
| 5.2 | Monthly trends | planned | Macro trends over time |
| 5.3 | Streak tracking | planned | How many consecutive days the user has logged |

## Tier 6 - Polish and Platform

| # | Feature | Status | Notes |
|---|---------|--------|-------|
| 6.1 | PWA support | planned | Service worker, offline mode, add-to-homescreen on iOS/Android |
| 6.2 | Dark mode | planned | Toggle between light and dark themes |
| 6.3 | Meal timestamps | planned | Record what time each food was logged |
| 6.4 | Copy previous day | planned | One-tap to duplicate yesterday's meals into today |
| 6.5 | Multi-language support | planned | English/French at minimum for Canada |

---

## Notes

- Tier 1 is the priority. The app should be usable for daily calorie tracking before moving to Tier 2+.
- Barcode scanning (2.1) and OCR (2.3) require HTTPS or localhost to access the camera API. We will need to either serve via a local HTTPS server or deploy somewhere.
- The Canadian food database (3.1) could start from Open Food Facts (open source, has Canadian products) and be enriched over time by user contributions.
- **End goal: the app must visually match the reference design.** Reference screenshots of the desired app are stored in `docs/samples/`. Before considering any UI feature complete, compare it against the reference screenshots and make sure they match.
