"""
Extract ~200 common everyday foods from the USDA SR Legacy dataset.
Pick the shortest/simplest name per keyword to get generic staples, not branded items.
"""
import csv
import json
import os
import re

INPUT = os.path.join(os.path.dirname(__file__), "foods_per_gram.csv")
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "common_foods.json")

# Each entry: (keyword to search, max results to keep per keyword)
# We pick the shortest matching names to get the most generic version
COMMON_KEYWORDS = [
    # Proteins
    "chicken breast", "chicken thigh", "chicken wing", "chicken drumstick",
    "ground beef", "beef, ground",
    "salmon, atlantic", "tuna,", "shrimp,", "tilapia", "cod, atlantic",
    "egg, whole, raw", "egg, whole, cooked", "egg white, raw",
    "turkey breast", "turkey, ground",
    "pork chop", "pork, loin", "bacon, cooked",
    "tofu, raw", "lentils, mature", "chickpeas,",
    # Dairy
    "milk, whole, 3.25%", "milk, reduced fat, 2%", "milk, lowfat, 1%",
    "cheese, cheddar", "cheese, mozzarella", "cheese, cream",
    "cheese, cottage", "cheese, parmesan",
    "yogurt, plain, whole", "yogurt, plain, low",
    "yogurt, greek, plain",
    "butter, salted", "butter, without salt",
    "cream, heavy", "cream, sour",
    # Grains
    "rice, white, long-grain, regular, cooked",
    "rice, white, short-grain, cooked",
    "rice, brown, long-grain, cooked",
    "bread, white, commercially prepared",
    "bread, whole-wheat, commercially prepared",
    "pasta, cooked, enriched",
    "oats, regular",
    "tortillas, ready-to-bake",
    "bagels, plain",
    "flour, white, all-purpose",
    # Fruits
    "bananas, raw", "apples, raw", "oranges, raw",
    "strawberries, raw", "blueberries, raw",
    "grapes, red", "watermelon, raw", "mangos, raw",
    "pineapple, raw", "peaches, raw", "pears, raw",
    "avocados, raw", "kiwifruit", "raspberries, raw",
    "cherries, sweet, raw", "lemon, raw",
    # Vegetables
    "broccoli, raw", "broccoli, cooked",
    "spinach, raw", "spinach, cooked",
    "carrots, raw", "carrots, cooked",
    "tomatoes, red, ripe, raw",
    "potatoes, russet, flesh and skin, baked",
    "potatoes, boiled, cooked",
    "sweet potato, cooked, baked",
    "onions, raw", "lettuce, iceberg", "lettuce, cos",
    "cucumber, with peel, raw",
    "peppers, sweet, red, raw", "peppers, sweet, green, raw",
    "corn, sweet, yellow, cooked",
    "beans, snap, green, raw",
    "peas, green, raw", "peas, green, cooked",
    "cauliflower, raw", "cabbage, raw",
    "celery, raw", "mushrooms, white, raw",
    "zucchini, includes skin, raw", "garlic, raw",
    "kale, raw", "asparagus, raw", "eggplant, raw",
    # Nuts & seeds
    "almonds", "peanuts, dry-roasted", "walnuts, english",
    "cashew nuts", "peanut butter, smooth",
    "sunflower seed kernels",
    # Oils
    "oil, olive, salad or cooking",
    "oil, coconut",
    "oil, canola",
    # Beans/legumes
    "beans, black, mature", "beans, kidney",
    "beans, pinto", "hummus, commercial",
    # Sweeteners & condiments
    "honey", "sugar, granulated",
    "ketchup", "mustard, prepared, yellow",
    "mayonnaise,", "salsa, ready to serve",
    "soy sauce",
    # Common prepared/other
    "pizza, cheese", "soup, chicken noodle",
    "ice cream, vanilla",
]

# Load all foods
foods = []
with open(INPUT, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        foods.append(row)

print(f"Total foods in dataset: {len(foods)}")

# For each keyword, find the best (shortest name) match
selected = {}
for keyword in COMMON_KEYWORDS:
    matches = []
    kw_lower = keyword.lower()
    for food in foods:
        if kw_lower in food["name"].lower():
            matches.append(food)

    if not matches:
        print(f"  WARNING: No match for '{keyword}'")
        continue

    # Sort by name length (shorter = more generic) and take the first
    matches.sort(key=lambda x: len(x["name"]))
    best = matches[0]

    if best["name"] not in selected:
        selected[best["name"]] = {
            "name": best["name"],
            "calories": float(best["calories"]),
            "protein": float(best["protein"]),
            "carbs": float(best["carbs"]),
            "fat": float(best["fat"]),
        }

# Sort alphabetically
result = sorted(selected.values(), key=lambda x: x["name"])

print(f"\nSelected {len(result)} common foods")

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print(f"Written to {OUTPUT}")
for item in result[:10]:
    print(f"  {item['name']}: {item['calories']:.2f} kcal/g, P:{item['protein']:.3f} C:{item['carbs']:.3f} F:{item['fat']:.3f}")
