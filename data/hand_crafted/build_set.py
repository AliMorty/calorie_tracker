"""Extract unique ingredients from all cuisine files and write to JSON."""
import json
import glob

def extract_ingredients(filepath):
    ingredients = set()
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            ingredients.add(line.lower())
    return ingredients

def build_set(output_file):
    all_ingredients = set()
    files = sorted(glob.glob("ingredients_*.txt"))
    for f in files:
        items = extract_ingredients(f)
        print(f"  {f}: {len(items)} unique")
        all_ingredients |= items

    sorted_items = sorted(all_ingredients)
    data = [{"name": item, "calories": None, "protein": None, "carbs": None, "fat": None} for item in sorted_items]
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nTotal unique ingredients: {len(sorted_items)}")
    print(f"Written to: {output_file}")
    print(f"\nFirst 30:")
    for item in sorted_items[:30]:
        print(f"  - {item}")

if __name__ == "__main__":
    build_set("ingredients_set.json")
