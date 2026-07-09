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
    if (nameEl) {
      nameEl.textContent = (user.user_metadata && user.user_metadata.full_name) || user.email || '';
    }
    var emailEl = document.getElementById('user-email');
    if (emailEl) {
      emailEl.textContent = user.email || '';
    }

    _bootApp();
  }

  /**
   * Convert a flat food object (per-UNIT values) into the format expected by
   * showFoodDetail and calcFoodNutrition. `flat.unit` defaults to 'g' (grams);
   * manually-saved foods may use any label (e.g. 'cup') with no conversion.
   */
  function _adaptFlatFood(flat) {
    var unit = flat.unit || 'g';
    // Grams default to a 100 g reference serving; other units default to 1.
    var defQty = unit === 'g' ? 100 : 1;
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
        { label: unit, type: 'weight', grams: 1, defaultQty: defQty },
      ],
      defaultUnit: unit,
      displayCalories: Math.round(flat.calories * defQty),
      displayServing: defQty + ' ' + unit,
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

    // Bottom-nav tab switching (Tracker <-> Profile)
    var trackerView = document.getElementById('tracker-view');
    var profileView = document.getElementById('profile-view');
    var tabTracker = document.getElementById('tab-tracker');
    var tabProfile = document.getElementById('tab-profile');

    function _fillProfileInputs() {
      var goals = Storage.getGoals();
      document.getElementById('profile-calories').value = goals.calories;
      document.getElementById('profile-protein').value = goals.protein;
      document.getElementById('profile-carbs').value = goals.carbs;
      document.getElementById('profile-fat').value = goals.fat;
    }

    function showTab(tab) {
      var toProfile = tab === 'profile';
      trackerView.classList.toggle('hidden', toProfile);
      profileView.classList.toggle('hidden', !toProfile);
      tabTracker.classList.toggle('active', !toProfile);
      tabProfile.classList.toggle('active', toProfile);
      if (toProfile) _fillProfileInputs();
    }

    if (tabTracker) {
      tabTracker.addEventListener('click', function () { showTab('tracker'); });
    }
    if (tabProfile) {
      tabProfile.addEventListener('click', function () { showTab('profile'); });
    }

    var profileSaveBtn = document.getElementById('profile-save-btn');
    if (profileSaveBtn) {
      profileSaveBtn.addEventListener('click', function () {
        Storage.saveGoals({
          calories: parseInt(document.getElementById('profile-calories').value) || 0,
          protein:  parseInt(document.getElementById('profile-protein').value)  || 0,
          carbs:    parseInt(document.getElementById('profile-carbs').value)    || 0,
          fat:      parseInt(document.getElementById('profile-fat').value)      || 0,
        });
        renderDay();
        showTab('tracker');
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

    // The user's own manually-saved foods (per-gram), adapted like USDA foods.
    var userFoodsPromise = Promise.resolve(Storage.getUserFoods())
      .then(function (foods) {
        return foods.map(_adaptFlatFood);
      })
      .catch(function () {
        return [];
      });

    Promise.all([handmadePromise, usdaPromise, userFoodsPromise]).then(function (results) {
      // Handmade foods first, then USDA foods, then the user's saved foods
      foodDatabase = results[0].concat(results[1]).concat(results[2]);
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
    UI.showAddFoodPanel(mealType, foodDatabase, recentFoods, onFoodPicked, searchFoodsFromDB, onManualFood, lookupBarcode);
  }

  // Look up a scanned barcode against the free Open Food Facts database.
  // Resolves to a food object ready for showFoodDetail, or null if not found.
  function lookupBarcode(code) {
    var url = 'https://world.openfoodfacts.org/api/v2/product/' +
      encodeURIComponent(code) + '.json?fields=product_name,nutriments';
    return fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data || data.status !== 1 || !data.product) return null;
        var n = data.product.nutriments || {};
        var kcal = n['energy-kcal_100g'];
        if (kcal === undefined || kcal === null) return null; // no usable macros
        // Open Food Facts gives per-100g values; store per-gram like everything else.
        var perGram = {
          name: (data.product.product_name || '').trim() || ('Barcode ' + code),
          calories: Number(kcal) / 100,
          protein: Number(n['proteins_100g'] || 0) / 100,
          carbs: Number(n['carbohydrates_100g'] || 0) / 100,
          fat: Number(n['fat_100g'] || 0) / 100,
        };
        return _adaptFlatFood(perGram);
      })
      .catch(function () { return null; });
  }

  // Handle a manually-entered food. `raw` has the macros for `refGrams` grams;
  // normalize to per-gram, optionally save it to the user's reusable list, then
  // open the detail screen so the amount actually eaten can be set and rescaled.
  function onManualFood(mealType, raw) {
    var amt = raw.refAmount > 0 ? raw.refAmount : 1;
    var unit = raw.unit || 'g';
    // Macros PER ONE UNIT (the unit is just a label — no conversion is done).
    var perUnit = {
      name: raw.name,
      unit: unit,
      calories: raw.calories / amt,
      protein: raw.protein / amt,
      carbs: raw.carbs / amt,
      fat: raw.fat / amt,
    };

    if (raw.save) {
      Storage.saveUserFood(perUnit);
      // Make it reusable immediately this session (search/browse/edit).
      foodDatabase.push(_adaptFlatFood(perUnit));
    }

    var food = {
      id: raw.name,
      name: raw.name,
      per100g: {
        calories: perUnit.calories * 100,
        protein: perUnit.protein * 100,
        carbs: perUnit.carbs * 100,
        fat: perUnit.fat * 100,
      },
      // grams:1 with the chosen label means "qty is measured in <unit>", scaled
      // linearly with no conversion. Prefill the reference amount; the user then
      // changes it to however much they actually ate and the macros rescale.
      units: [{ label: unit, type: 'weight', grams: 1, defaultQty: amt }],
      defaultUnit: unit,
    };

    UI.hideManualFoodForm();
    UI.showFoodDetail(mealType, food, unitConversions, onFoodConfirmed, null);
  }

  function searchFoodsFromDB(query) {
    return SupabaseAuth.searchFoods(query, 100).then(function (results) {
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
    // Database (USDA) foods aren't kept in foodDatabase, so reconstruct a
    // gram-based food object from the entry's own stored macros. This lets
    // logged database foods be reopened and re-portioned (Issue #5), and
    // works offline since it needs no lookup. Database foods are always
    // logged in grams, so per-100g = stored macro * 100 / grams.
    if (!food && entry.servingUnit === 'g' && entry.servingQty) {
      var per = 100 / entry.servingQty;
      food = {
        id: entry.foodId,
        name: entry.name,
        per100g: {
          calories: entry.calories * per,
          protein: entry.protein * per,
          carbs: entry.carbs * per,
          fat: entry.fat * per,
        },
        units: [{ label: 'g', type: 'weight', grams: 1, defaultQty: 100 }],
        defaultUnit: 'g',
      };
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
