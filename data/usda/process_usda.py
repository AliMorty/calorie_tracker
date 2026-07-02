"""
Process USDA SR Legacy CSVs into a single flat CSV for Supabase import.
All nutrient values are stored PER 1 GRAM (original data is per 100g, so we divide by 100).
"""
import csv
import os

DIR = os.path.join(os.path.dirname(__file__), "FoodData_Central_sr_legacy_food_csv_2018-04")

# Nutrient IDs we care about
NUTRIENT_IDS = {
    "1008": "calories",   # Energy (kcal)
    "1003": "protein",    # Protein (g)
    "1004": "fat",        # Total lipid/fat (g)
    "1005": "carbs",      # Carbohydrate, by difference (g)
}

# Step 1: Load foods (fdc_id -> name)
print("Loading foods...")
foods = {}
with open(os.path.join(DIR, "food.csv"), encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        foods[row["fdc_id"]] = row["description"]

print(f"  Found {len(foods)} foods")

# Step 2: Load nutrient values (fdc_id -> {calories, protein, fat, carbs})
print("Loading nutrients...")
nutrients = {}
with open(os.path.join(DIR, "food_nutrient.csv"), encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        nutrient_id = row["nutrient_id"]
        if nutrient_id in NUTRIENT_IDS:
            fdc_id = row["fdc_id"]
            if fdc_id not in nutrients:
                nutrients[fdc_id] = {}
            field = NUTRIENT_IDS[nutrient_id]
            try:
                # Divide by 100 to get per-gram value
                value = float(row["amount"]) / 100.0
                nutrients[fdc_id][field] = round(value, 4)
            except (ValueError, TypeError):
                pass

# Step 3: Combine and write output
print("Writing output...")
output_path = os.path.join(os.path.dirname(__file__), "foods_per_gram.csv")
count = 0

with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["name", "calories", "protein", "carbs", "fat"])

    for fdc_id, name in foods.items():
        if fdc_id in nutrients:
            n = nutrients[fdc_id]
            # Only include if we have at least calories
            if "calories" in n:
                writer.writerow([
                    name,
                    n.get("calories", 0),
                    n.get("protein", 0),
                    n.get("carbs", 0),
                    n.get("fat", 0),
                ])
                count += 1

print(f"Done! Wrote {count} foods to {output_path}")
