/**
 * demo.js - Demo mode (no sign-in)
 *
 * Seeds a realistic sample week into browser storage and drives the
 * "Try this" hints card. Nothing here talks to Supabase: Storage is put in
 * demo mode first, so every read/write stays in this browser.
 */

const Demo = (function () {
  // One menu per day: [foodId from data/foods.json, qty, unit label].
  // Index 0 is today; dinner is left empty so there is something to add.
  var WEEK = [
    {
      breakfast: [['oats_rolled', 0.5, 'cup'], ['banana', 1, 'medium'], ['milk_whole', 1, 'cup']],
      lunch: [['chicken_breast', 150, 'g'], ['rice_white_cooked', 1, 'cup'], ['broccoli', 1, 'cup']],
      dinner: [],
      snacks: [['greek_yogurt', 0.75, 'cup'], ['almonds', 1, 'oz']],
    },
    {
      breakfast: [['egg_whole', 2, 'large egg'], ['bread_whole_wheat', 2, 'slice'], ['avocado', 1, 'half medium']],
      lunch: [['tuna_canned', 1, 'can (drained)'], ['bread_whole_wheat', 2, 'slice'], ['apple', 1, 'medium']],
      dinner: [['ground_beef_lean', 120, 'g'], ['rice_white_cooked', 1, 'cup'], ['broccoli', 1, 'cup']],
      snacks: [['peanut_butter', 2, 'tbsp'], ['banana', 1, 'medium']],
    },
    {
      breakfast: [['greek_yogurt', 0.75, 'cup'], ['oats_rolled', 3, 'tbsp'], ['banana', 1, 'medium']],
      lunch: [['lentils_cooked', 1, 'cup'], ['bread_whole_wheat', 1, 'slice'], ['cheddar_cheese', 1, 'oz']],
      dinner: [['chicken_breast', 180, 'g'], ['sweet_potato', 1, 'medium'], ['broccoli', 1, 'cup']],
      snacks: [['apple', 1, 'medium'], ['almonds', 1, 'oz']],
    },
    {
      breakfast: [['oats_rolled', 0.5, 'cup'], ['milk_whole', 1, 'cup'], ['banana', 1, 'medium']],
      lunch: [['chicken_breast', 150, 'g'], ['rice_white_cooked', 1, 'cup'], ['avocado', 1, 'half medium']],
      dinner: [['salmon_atlantic', 150, 'g'], ['rice_white_cooked', 1, 'cup'], ['broccoli', 1, 'cup']],
      snacks: [['greek_yogurt', 0.75, 'cup']],
    },
    {
      breakfast: [['egg_whole', 3, 'large egg'], ['bread_whole_wheat', 1, 'slice']],
      lunch: [['ground_beef_lean', 100, 'g'], ['lentils_cooked', 1, 'cup']],
      dinner: [['tuna_canned', 1, 'can (drained)'], ['rice_white_cooked', 1, 'cup'], ['olive_oil', 1, 'tbsp']],
      snacks: [['cheddar_cheese', 1, 'oz'], ['apple', 1, 'medium']],
    },
    {
      breakfast: [['greek_yogurt', 0.75, 'cup'], ['banana', 1, 'medium'], ['almonds', 1, 'oz']],
      lunch: [['chicken_breast', 120, 'g'], ['sweet_potato', 1, 'medium'], ['broccoli', 1, 'cup']],
      dinner: [['salmon_atlantic', 130, 'g'], ['lentils_cooked', 1, 'cup'], ['olive_oil', 1, 'tbsp']],
      snacks: [['peanut_butter', 2, 'tbsp'], ['bread_whole_wheat', 1, 'slice']],
    },
    {
      breakfast: [['egg_whole', 2, 'large egg'], ['avocado', 1, 'half medium'], ['bread_whole_wheat', 2, 'slice']],
      lunch: [['lentils_cooked', 1, 'cup'], ['rice_white_cooked', 1, 'cup']],
      dinner: [['ground_beef_lean', 150, 'g'], ['sweet_potato', 1, 'medium'], ['broccoli', 1, 'cup']],
      snacks: [['banana', 1, 'medium'], ['milk_whole', 1, 'cup']],
    },
  ];

  var MEAL_HOURS = { breakfast: 8, lunch: 13, dinner: 19, snacks: 16 };

  function _dateKey(date) {
    var m = String(date.getMonth() + 1).padStart(2, '0');
    var d = String(date.getDate()).padStart(2, '0');
    return date.getFullYear() + '-' + m + '-' + d;
  }

  /**
   * Build the sample week (today and the 6 days before) from data/foods.json,
   * using the same calcFoodNutrition the app uses, and write it to storage.
   * Returns a Promise.
   */
  function seed() {
    return fetch('data/foods.json')
      .then(function (res) { return res.json(); })
      .then(function (json) {
        var byId = {};
        json.foods.forEach(function (f) { byId[f.id] = f; });

        var diary = {};
        var n = 0;
        WEEK.forEach(function (menu, daysAgo) {
          var date = new Date();
          date.setDate(date.getDate() - daysAgo);
          var day = { meals: {} };
          Object.keys(menu).forEach(function (meal) {
            day.meals[meal] = { entries: menu[meal].map(function (item) {
              var food = byId[item[0]];
              var unit = food.units.find(function (u) { return u.label === item[2]; });
              var nut = Storage.calcFoodNutrition(food, item[1], unit, json.unitConversions);
              var added = new Date(date);
              added.setHours(MEAL_HOURS[meal], 0, 0, 0);
              n++;
              return {
                id: 'demo' + n,
                foodId: food.id,
                name: food.name,
                servingQty: item[1],
                servingUnit: unit.label,
                servingLabel: item[1] + ' ' + unit.label,
                calories: nut.calories,
                protein: nut.protein,
                carbs: nut.carbs,
                fat: nut.fat,
                addedAt: added.toISOString(),
              };
            }) };
          });
          diary[_dateKey(date)] = day;
        });
        Storage.saveDemoDiary(diary);
      });
  }

  // ---------- "Try this" hints card ----------

  function showHints() {
    document.getElementById('demo-banner').classList.remove('hidden');
    document.getElementById('demo-hints').classList.remove('hidden');
    document.getElementById('demo-hints-close').onclick = function () {
      document.getElementById('demo-hints').classList.add('hidden');
    };
  }

  /** Tick off a hint step: 'add', 'edit', 'delete' or 'day'. */
  function markDone(step) {
    var item = document.querySelector('#demo-hints [data-step="' + step + '"]');
    if (item) item.classList.add('done');
  }

  return {
    seed: seed,
    showHints: showHints,
    markDone: markDone,
  };
})();
