/**
 * app.js - Application orchestrator
 *
 * Wires Storage and UI together.
 * Manages current state (selected date) and user interactions.
 * Handles auth flow (login screen vs app).
 */

const App = (function () {

  var currentDate = new Date();
  var dayData = null;
  var foodDatabase = [];
  var unitConversions = {};

  function init() {
    // Initialize auth and wait for session check
    SupabaseAuth.init(onAuthChange);
  }

  function onAuthChange(user) {
    if (user) {
      _showApp(user);
    } else {
      _showLogin();
    }
  }

  function _showLogin() {
    document.getElementById('login-screen').classList.remove('hidden');
    document.getElementById('app').classList.add('hidden');
  }

  function _showApp(user) {
    document.getElementById('login-screen').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');

    // Update user display
    var nameEl = document.getElementById('user-display-name');
    if (nameEl && user.user_metadata) {
      nameEl.textContent = user.user_metadata.full_name || user.email || '';
    }

    _bootApp();
  }

  /**
   * Convert a flat food object (per-gram values) into the format
   * expected by showFoodDetail and calcFoodNutrition.
   */
  function _adaptFlatFood(flat) {
    return {
      id: flat.name, // use name as ID for Supabase foods
      name: flat.name,
      per100g: {
        calories: Math.round(flat.calories * 100),
        protein: Math.round(flat.protein * 100 * 10) / 10,
        carbs: Math.round(flat.carbs * 100 * 10) / 10,
        fat: Math.round(flat.fat * 100 * 10) / 10,
      },
      units: [
        { label: 'g', type: 'weight', grams: 1, defaultQty: 100 },
      ],
      defaultUnit: 'g',
      displayCalories: Math.round(flat.calories * 100),
      displayServing: '100 g',
    };
  }

  function _bootApp() {
    UI.init();
    UI.bindNavigation(goToPrevDay, goToNextDay);

    // Bind sign out button
    var signOutBtn = document.getElementById('sign-out-btn');
    if (signOutBtn) {
      signOutBtn.addEventListener('click', function () {
        SupabaseAuth.signOut();
      });
    }

    // Load both: handmade foods (with units) + USDA common foods (grams only)
    var handmadePromise = fetch('data/foods.json')
      .then(function (res) { return res.json(); })
      .then(function (json) {
        unitConversions = json.unitConversions;
        return json.foods.map(function (food) {
          var defaultUnitData = food.units.find(function (u) { return u.label === food.defaultUnit; }) || food.units[0];
          var n = Storage.calcFoodNutrition(food, defaultUnitData.defaultQty, defaultUnitData, json.unitConversions);
          return Object.assign({}, food, {
            displayCalories: n.calories,
            displayServing: defaultUnitData.defaultQty + ' ' + defaultUnitData.label,
          });
        });
      })
      .catch(function () {
        unitConversions = {};
        return [];
      });

    var usdaPromise = fetch('data/common_foods.json')
      .then(function (res) { return res.json(); })
      .then(function (foods) {
        return foods.map(_adaptFlatFood);
      })
      .catch(function () {
        return [];
      });

    Promise.all([handmadePromise, usdaPromise]).then(function (results) {
      // Handmade foods first, then USDA foods
      foodDatabase = results[0].concat(results[1]);
    });

    _loadAndRenderDay();
  }

  function _loadAndRenderDay() {
    Promise.resolve(Storage.getMealsForDate(currentDate)).then(function (data) {
      dayData = data;
      renderDay();
    });
  }

  function renderDay() {
    var goals = Storage.getGoals();
    var totals = Storage.computeDayTotals(dayData);

    UI.renderDateHeader(currentDate);
    UI.renderSummary(totals, goals);
    UI.renderMeals(dayData, handleAddFood, handleEditEntry, handleDeleteEntry, Storage.computeMealTotals);
  }

  function goToPrevDay() {
    currentDate.setDate(currentDate.getDate() - 1);
    _loadAndRenderDay();
  }

  function goToNextDay() {
    currentDate.setDate(currentDate.getDate() + 1);
    _loadAndRenderDay();
  }

  function handleAddFood(mealType) {
    var recentFoods = _getRecentFoods(5);
    UI.showAddFoodPanel(mealType, foodDatabase, recentFoods, onFoodPicked, searchFoodsFromDB);
  }

  function searchFoodsFromDB(query) {
    return SupabaseAuth.searchFoods(query).then(function (results) {
      return results.map(_adaptFlatFood);
    });
  }

  function handleDeleteEntry(mealType, entry) {
    Promise.resolve(Storage.removeFoodEntry(currentDate, mealType, entry.id)).then(function () {
      _loadAndRenderDay();
    });
  }

  function handleEditEntry(mealType, entry) {
    var food = null;
    for (var i = 0; i < foodDatabase.length; i++) {
      if (foodDatabase[i].id === entry.foodId) {
        food = foodDatabase[i];
        break;
      }
    }
    if (!food) return;
    UI.showFoodDetail(mealType, food, unitConversions, onFoodConfirmed, entry);
  }

  function onFoodPicked(mealType, food) {
    UI.showFoodDetail(mealType, food, unitConversions, onFoodConfirmed, null);
  }

  function onFoodConfirmed(mealType, food, qty, unit, existingEntry) {
    var nutrition = Storage.calcFoodNutrition(food, qty, unit, unitConversions);
    var entryData = {
      servingQty: qty,
      servingUnit: unit.label,
      servingLabel: qty + ' ' + unit.label,
      calories: nutrition.calories,
      protein: nutrition.protein,
      carbs: nutrition.carbs,
      fat: nutrition.fat,
    };

    var promise;
    if (existingEntry) {
      promise = Storage.updateFoodEntry(currentDate, mealType, existingEntry.id, entryData);
    } else {
      promise = Storage.addFoodEntry(currentDate, mealType, Object.assign({
        foodId: food.id,
        name: food.name,
      }, entryData));
    }

    Promise.resolve(promise).then(function () {
      UI.hideFoodDetail();
      _loadAndRenderDay();
    });
  }

  function _getRecentFoods(limit) {
    var seen = {};
    var result = [];
    var allEntries = [];
    var mealTypes = ['breakfast', 'lunch', 'dinner', 'snacks'];

    for (var i = 0; i < mealTypes.length; i++) {
      var entries = dayData.meals[mealTypes[i]].entries;
      for (var j = 0; j < entries.length; j++) {
        allEntries.push(entries[j]);
      }
    }

    allEntries.sort(function (a, b) {
      return new Date(b.addedAt || 0) - new Date(a.addedAt || 0);
    });

    for (var k = 0; k < allEntries.length; k++) {
      var entry = allEntries[k];
      if (!seen[entry.foodId]) {
        seen[entry.foodId] = true;
        var food = null;
        for (var m = 0; m < foodDatabase.length; m++) {
          if (foodDatabase[m].id === entry.foodId) {
            food = foodDatabase[m];
            break;
          }
        }
        if (food) result.push(food);
        if (result.length >= limit) break;
      }
    }

    return result;
  }

  // ---------- expose ----------

  return {
    init: init,
  };
})();

// Boot the app when DOM is ready
document.addEventListener('DOMContentLoaded', App.init);
