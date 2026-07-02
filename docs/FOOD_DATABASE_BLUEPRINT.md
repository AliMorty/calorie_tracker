# Food Database Blueprint

## Goal
Build a curated ~2000-item food database with accurate macros, optimized for fast search. Barcode lookups handled separately via Open Food Facts API.

---

## Step 1: List Cuisine Categories

Use an LLM to list all major cuisine/food categories relevant to a Canadian user. Examples:

1. Canadian / North American
2. Chinese
3. Indian
4. Iranian / Persian
5. Mexican
6. Greek / Mediterranean
7. Italian
8. Japanese / Korean
9. Middle Eastern / Lebanese
10. Thai / Vietnamese / Southeast Asian
11. European (French, German, etc.)
12. African
13. Caribbean

This list should cover the food cultures commonly eaten in Canada.

---

## Step 2: List 20-50 Common Dishes Per Cuisine

For each cuisine category, use an LLM to generate the top 20-50 dishes people commonly cook or order. Examples:

- **Iranian:** ghormeh sabzi, tahdig, joojeh kabab, zereshk polo, ash reshteh, ...
- **Canadian:** poutine, butter tarts, tourtière, ...
- **Chinese:** kung pao chicken, fried rice, mapo tofu, ...
- **Mexican:** tacos, burritos, enchiladas, pozole, ...

---

## Step 3: Break Each Dish Into Ingredients

For each dish, use an LLM to list the ingredients. Example:

- **Ghormeh sabzi** → herbs (parsley, cilantro, fenugreek), kidney beans, lamb, dried limes, onion, oil, turmeric
- **Poutine** → french fries (potatoes, oil), cheese curds, gravy

---

## Step 4: Collect All Unique Ingredients

Merge all ingredient lists across all dishes. Deduplicate. This produces the master list of ~2000 food items that go into our database. These are ingredients, not dishes.

Examples: chicken breast, basmati rice, kidney beans, feta cheese, tortilla, coconut milk, olive oil, ground beef, cilantro, turmeric, butter, cream cheese, mozzarella, etc.

---

## Step 5: Find Accurate Macros for Each Ingredient

For each ingredient in the list:

1. **Ask an LLM to list 3-5 top reliable brands** for that ingredient (e.g., for "greek yogurt 0%" → Oikos, Chobani, Fage)
2. **Search the USDA Branded Foods dataset** (already downloaded locally — 1.8M products) for those brands + ingredient name
3. **Pick the best match** — a well-known brand with complete nutrition data (calories, protein, carbs, fat)
4. **Record the macros per 100g and per typical serving size**

If no branded match is found, fall back to USDA SR Legacy data or LLM knowledge as a last resort.

---

## Step 6: Build the Final Database

Each entry in the database contains:
- `name` — clean, consumer-friendly name (e.g., "Greek Yogurt (0% fat)")
- `calories` — per 100g
- `protein` — per 100g
- `carbs` — per 100g
- `fat` — per 100g
- `serving_size` — typical serving in grams
- `serving_description` — human-readable (e.g., "3/4 cup", "1 slice", "1 tbsp")
- `barcode` — empty for now (populated later via barcode scans)
- `category` — ingredient category (dairy, grain, meat, vegetable, etc.)

Upload to Supabase `foods` table. Tiny (~2000 rows), fits easily in free tier, fast search.

---

## Step 7: Barcode Lookup (Separate Path)

Barcode scanning does NOT use our database. Instead:
1. User scans barcode
2. App calls Open Food Facts API: `https://world.openfoodfacts.org/api/v2/product/{barcode}.json`
3. Returns exact branded product with nutrition data
4. User confirms and logs it

No storage cost, no database bloat. Already verified working in session 009.

---

## Data Source

- **USDA Branded Foods (April 2026)** — 1.8M products with manufacturer-submitted names and macros. Downloaded to `data/usda_branded/`. Used as ground truth for filling macros in Step 5.
- **Open Food Facts API** — used for real-time barcode lookups only (Step 7).
- **USDA SR Legacy** — fallback for generic whole foods not found in branded data.
