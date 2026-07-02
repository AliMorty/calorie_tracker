import json

with open("ingredients_set.json") as f:
    items = json.load(f)

with open("ingredients_indexed.txt", "w") as f:
    for i, item in enumerate(items):
        f.write(f"{i}: {item['name']}\n")

print(f"Written {len(items)} lines.")
