#!/usr/bin/env python3
"""
Applies a hand-curated dedup map to ingredients_set.json.

ingredients_set.json is READ ONLY - never modified.

MERGES is a list of (dup_idx, canonical_idx): the dup folds into the canonical
(survivor). Decisions were made by reading the full list and using common sense:
- merge plurals, spelling variants, exact synonyms, and same-macro variants
- keep foods whose macros genuinely differ (fat %, cut, dry vs canned, type)

Outputs:
- dedup_review.txt          human-readable list of every removal
- ingredients_set_deduped.json   survivors only, original order, macros still null

Safety: the script validates every index, refuses if a canonical is itself
removed, and reconciles counts (original == survivors + removed).
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "ingredients_set.json"
REVIEW = HERE / "dedup_review.txt"
OUT = HERE / "ingredients_set_deduped.json"

# (dup_idx -> canonical_idx)
MERGES = [
    (7, 6),                                              # allspice berries -> allspice
    (12, 8), (13, 8), (14, 8), (15, 8),                  # almond variants -> almond
    (23, 20), (24, 20), (25, 20), (26, 20), (27, 20), (28, 20),  # apple variants -> apple
    (43, 42),                                            # baguette/french bread -> baguette
    (52, 50),                                            # bananas -> banana
    (66, 65),                                            # beef broth/stock -> beef broth
    (69, 68), (74, 68),                                  # beef chuck roast/roast chuck -> beef chuck
    (80, 72),                                            # beef steak ribeye -> beef ribeye
    (81, 78),                                            # beef steak sirloin -> beef sirloin
    (400, 79),                                           # flank steak -> beef steak, flank
    (87, 86),                                            # beets -> beet
    (89, 88), (90, 88), (91, 88), (92, 88), (93, 88),    # bell pepper colors -> bell pepper
    (496, 88), (497, 88), (506, 88), (852, 88),          # green/red bell pepper -> bell pepper
    (99, 98),                                            # black pepper ground -> black pepper
    (113, 787),                                          # bread, pita -> pita bread
    (114, 890),                                          # bread, rye -> rye bread
    (116, 1077),                                         # bread, white sandwich -> white bread
    (111, 118), (120, 118),                              # bread crumbs/plain -> breadcrumbs
    (119, 735),                                          # breadcrumbs panko -> panko breadcrumbs
    (968, 110), (1013, 110),                             # stale bread / toast -> bread
    (128, 127),                                          # brown rice long grain -> brown rice
    (134, 133), (135, 133),                              # butter salted/unsalted -> butter
    (139, 138), (140, 138), (141, 138),                  # cabbage colors/napa -> cabbage
    (498, 138), (687, 138), (929, 138),                  # green/napa/shredded cabbage -> cabbage
    (147, 251),                                          # canned coconut milk -> coconut milk
    (274, 272),                                          # corn kernels -> corn
    (171, 169),                                          # carrots -> carrot
    (184, 182), (185, 182),                              # cheddar marble/old -> cheddar cheese
    (1025, 190), (1026, 190),                            # tomato cherry/grape -> cherry tomatoes
    (195, 194),                                          # chicken breast bnls sknls -> chicken breast
    (197, 196),                                          # chicken broth/stock -> chicken broth
    (206, 205),                                          # chickpeas canned -> chickpeas
    (214, 208),                                          # chilies -> chili
    (304, 209), (338, 209), (853, 209), (859, 209),      # red pepper/chili flakes -> chili flakes
    (217, 216),                                          # chipotles in adobo -> chipotle peppers in adobo
    (355, 339),                                          # dried red chilies -> dried chili peppers
    (323, 322),                                          # dark chocolate bar -> dark chocolate
    (414, 235),                                          # fresh cilantro -> cilantro
    (240, 238),                                          # cinnamon ground -> cinnamon
    (244, 243),                                          # cloves ground -> cloves
    (246, 245),                                          # cocoa unsweetened -> cocoa powder
    (328, 250),                                          # desiccated coconut -> coconut flakes
    (256, 255),                                          # cod fillet -> cod
    (278, 277),                                          # corn tortillas -> corn tortilla
    (158, 305),                                          # canned crushed tomatoes -> crushed tomatoes
    (307, 306), (308, 306),                              # cucumber english/persian -> cucumber
    (682, 329),                                          # mustard dijon -> dijon mustard
    (415, 330),                                          # fresh dill -> dill
    (343, 332),                                          # dried dill -> dill, dried
    (776, 331),                                          # pickles dill -> dill pickles
    (774, 768),                                          # pickles -> pickle
    (418, 657),                                          # fresh mint -> mint
    (728, 351),                                          # oregano dried -> dried oregano
    (421, 886),                                          # fresh rosemary -> rosemary
    (887, 357),                                          # rosemary dried -> dried rosemary
    (423, 1010),                                         # fresh thyme -> thyme
    (1011, 360),                                         # thyme dried -> dried thyme
    (353, 839), (354, 839), (840, 839),                  # dried plums variants -> prunes
    (372, 364), (373, 364),                              # eggs/large -> egg
    (369, 368),                                          # egg yolks -> egg yolk
    (371, 370),                                          # eggplant/aubergine -> eggplant
    (374, 631), (375, 631), (632, 631),                  # elbow/macaroni pasta -> macaroni
    (402, 5), (406, 5), (1068, 5),                       # flour/AP/wheat flour -> all-purpose flour
    (1090, 409),                                         # whole wheat flour -> flour, whole wheat
    (404, 403), (405, 403),                              # flour tortillas sizes -> flour tortillas
    (437, 411), (425, 411),                              # frozen fries/fried strips -> french fries
    (412, 55),                                           # fresh basil -> basil
    (413, 224),                                          # fresh chives -> chives
    (416, 386),                                          # fresh fenugreek -> fenugreek leaves
    (419, 741),                                          # fresh parsley -> parsley
    (436, 398),                                          # frozen fish sticks -> fish sticks (frozen)
    (471, 470),                                          # ginger root -> ginger
    (478, 477),                                          # gochujang (korean) -> gochujang
    (489, 488),                                          # grapes red -> grapes green
    (504, 503), (505, 503),                              # green onion scallion/plural -> green onion
    (517, 516),                                          # guacamole store-bought -> guacamole
    (522, 521),                                          # habanero pepper -> habanero chile
    (528, 527),                                          # ham sliced deli -> ham
    (529, 132),                                          # hamburger buns -> burger buns
    (536, 535),                                          # heavy cream 35% -> heavy cream
    (1074, 1073),                                        # whipping cream 33% -> whipping cream
    (568, 567), (569, 567),                              # jalapenos/jalapeño -> jalapeno pepper
    (715, 502),                                          # olives green jarred -> green olives
    (605, 604),                                          # leeks -> leek
    (883, 621), (884, 621),                              # romaine lettuce/leaves -> lettuce, romaine
    (932, 617),                                          # shredded lettuce -> lettuce
    (417, 640),                                          # fresh mango -> mango
    (1089, 656),                                         # whole milk -> milk, whole (3.25%)
    (660, 659),                                          # mirin (rice wine) -> mirin
    (926, 675),                                          # shiitake mushrooms -> mushroom, shiitake
    (1103, 684),                                         # yellow mustard -> mustard, yellow
    (694, 693), (695, 693), (696, 693),                  # nori powder/seaweed/sheets -> nori
    (698, 697),                                          # nutmeg ground -> nutmeg
    (882, 703),                                          # rolled oats -> oats, rolled
    (707, 1055),                                         # oil -> vegetable oil
    (711, 710), (712, 710),                              # olive oil evoo/light -> olive oil
    (718, 716), (719, 716), (720, 716), (857, 716), (1079, 716),  # onion colors -> onion
    (724, 723),                                          # orange juice pulp-free -> orange juice
    (725, 726),                                          # orange peel -> orange zest
    (739, 737),                                          # paprika sweet -> paprika
    (940, 738),                                          # smoked paprika -> paprika, smoked
    (744, 743),                                          # parsnips -> parsnip
    (879, 756),                                          # roasted peanuts -> peanuts, roasted
    (758, 54),                                           # pearl barley -> barley, pearl
    (785, 784), (786, 784),                              # pistachio slivers/plural -> pistachio
    (794, 793),                                          # poblano peppers -> poblano pepper
    (795, 280),                                          # polenta/cornmeal -> cornmeal
    (821, 819), (822, 819), (823, 819), (824, 819), (825, 819),  # potato variants -> potato
    (974, 977),                                          # sugar -> sugar, granulated (white)
    (560, 978), (827, 978),                              # icing/powdered sugar -> sugar, icing/powdered
    (975, 129), (976, 129),                              # brown sugar dark/light -> brown sugar
    (828, 934), (936, 934), (937, 934),                  # prawns/shrimp cooked/raw -> shrimp
    (846, 845),                                          # radishes -> radish
    (856, 616),                                          # red lentils -> lentils, red (dried)
    (501, 615),                                          # green lentils -> lentils, green (dried)
    (881, 880),                                          # roasted red peppers jarred -> roasted red peppers
    (898, 897), (900, 897),                              # salmon fillet/frozen -> salmon
    (905, 903), (906, 903), (907, 903),                  # salsa hot/medium/mild -> salsa
    (910, 908), (911, 908), (912, 908),                  # salt kosher/sea/table -> salt
    (923, 994),                                          # sesame paste -> tahini
    (959, 958),                                          # spinach baby -> spinach
    (1104, 961),                                         # yellow split peas -> split peas, yellow
    (965, 964),                                          # squid/calamari -> squid
    (987, 985),                                          # sweet potatoes -> sweet potato
    (988, 264),                                          # sweetened condensed milk -> condensed milk
    (1000, 100),                                         # tea, black -> black tea
    (1029, 1019), (1027, 1019), (1028, 1019),            # tomatoes/vine/roma -> tomato
    (1024, 1022),                                        # tomato sauce plain -> tomato sauce
    (1036, 1037),                                        # tuna -> tuna, fresh/frozen steak
    (1057, 1056),                                        # vermicelli noodles -> vermicelli
    (262, 1064), (548, 1064), (558, 1064), (1062, 1064), (550, 1064),  # water variants/ice -> water
    (1082, 1081), (868, 1081),                           # white rice long grain / rice -> white rice
    (1113, 1112),                                        # zaatar -> za'atar
]


def main():
    items = json.loads(SRC.read_text())
    n = len(items)
    names = [it["name"] for it in items]

    dup_to_canon = {}
    errors = []
    for dup, canon in MERGES:
        if not (0 <= dup < n) or not (0 <= canon < n):
            errors.append(f"index out of range: {dup}->{canon}")
            continue
        if dup in dup_to_canon:
            errors.append(f"dup {dup} ({names[dup]}) listed twice")
        dup_to_canon[dup] = canon

    removed = set(dup_to_canon)
    # a canonical must NOT itself be removed (no broken chains)
    for dup, canon in dup_to_canon.items():
        if canon in removed:
            errors.append(f"canonical {canon} ({names[canon]}) is itself removed "
                          f"(dup {dup} {names[dup]} would have no survivor)")

    if errors:
        print("VALIDATION FAILED - nothing written:")
        for e in errors:
            print("  -", e)
        sys.exit(1)

    # review file
    lines = []
    for dup in sorted(dup_to_canon):
        canon = dup_to_canon[dup]
        lines.append(f"REMOVE {dup}: {names[dup]:<45} -> KEEP {canon}: {names[canon]}")
    REVIEW.write_text("\n".join(lines) + "\n")

    # survivors, original order, macros untouched (still null)
    survivors = [it for i, it in enumerate(items) if i not in removed]
    OUT.write_text(json.dumps(survivors, indent=2))

    # reconcile
    assert len(survivors) + len(removed) == n, "reconciliation mismatch!"
    print(f"original:  {n}")
    print(f"removed:   {len(removed)}")
    print(f"survivors: {len(survivors)}")
    print(f"reconcile: {len(survivors)} + {len(removed)} = {len(survivors)+len(removed)} == {n}  OK")
    print(f"\nreview -> {REVIEW.name}")
    print(f"output -> {OUT.name}  (original ingredients_set.json untouched)")


if __name__ == "__main__":
    main()
