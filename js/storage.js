/**
 * storage.js - Data persistence layer
 *
 * When logged in: reads/writes from Supabase (food_logs table).
 * When not logged in: falls back to localStorage.
 *
 * Exposes the same public API regardless of backing store.
 */

const Storage = (function () {
  const KEYS = {
    diary: 'ct_diary',       // diary entries keyed by date
    goals: 'ct_goals',       // daily macro goals
    profile: 'ct_profile',   // user profile (future)
    customFoods: 'ct_custom_foods', // user-created foods (future)
  };

  // ---------- low-level localStorage helpers ----------

  function _read(key) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      console.error('Storage read error for key ' + key, e);
      return null;
    }
  }

  function _write(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (e) {
      console.error('Storage write error for key ' + key, e);
    }
  }

  // ---------- date helpers ----------

  function _dateKey(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + d;
  }

  // ---------- Supabase helpers ----------

  function _isOnline() {
    return typeof SupabaseAuth !== 'undefined' && SupabaseAuth.isLoggedIn();
  }

  function _db() {
    return SupabaseAuth.getClient();
  }

  function _userId() {
    var user = SupabaseAuth.getUser();
    return user ? user.id : null;
  }

  // Convert a Supabase row to our entry format
  function _rowToEntry(row) {
    return {
      id: row.id,
      foodId: row.food_id,
      name: row.name,
      servingQty: Number(row.serving_qty),
      servingUnit: row.serving_unit,
      servingLabel: row.serving_label,
      calories: Number(row.calories),
      protein: Number(row.protein),
      carbs: Number(row.carbs),
      fat: Number(row.fat),
      addedAt: row.added_at,
    };
  }

  // ---------- diary (localStorage fallback) ----------

  function _getDiary() {
    return _read(KEYS.diary) || {};
  }

  function _saveDiary(diary) {
    _write(KEYS.diary, diary);
  }

  function _emptyDay() {
    return {
      meals: {
        breakfast: { entries: [] },
        lunch:     { entries: [] },
        dinner:    { entries: [] },
        snacks:    { entries: [] },
      },
    };
  }

  // ---------- public API ----------

  /**
   * Get meals for a specific date.
   * Returns a Promise when online, or plain object when offline.
   * Callers should always use Promise.resolve() wrapper.
   */
  function getMealsForDate(date) {
    if (!_isOnline()) {
      var diary = _getDiary();
      var key = _dateKey(date);
      return Promise.resolve(diary[key] || _emptyDay());
    }

    var dateStr = _dateKey(date);
    return _db()
      .from('food_logs')
      .select('*')
      .eq('user_id', _userId())
      .eq('date', dateStr)
      .then(function (result) {
        if (result.error) {
          console.error('Supabase read error:', result.error);
          // Fallback to localStorage
          var diary = _getDiary();
          return diary[dateStr] || _emptyDay();
        }

        var dayData = _emptyDay();
        var rows = result.data || [];
        for (var i = 0; i < rows.length; i++) {
          var row = rows[i];
          var meal = row.meal;
          if (dayData.meals[meal]) {
            dayData.meals[meal].entries.push(_rowToEntry(row));
          }
        }
        return dayData;
      });
  }

  /**
   * Add a food entry to a meal on a given date.
   * Returns a Promise.
   */
  function addFoodEntry(date, mealType, entry) {
    if (!_isOnline()) {
      var diary = _getDiary();
      var key = _dateKey(date);
      if (!diary[key]) diary[key] = _emptyDay();
      var newEntry = Object.assign({}, entry, {
        id: _generateId(),
        addedAt: new Date().toISOString(),
      });
      diary[key].meals[mealType].entries.push(newEntry);
      _saveDiary(diary);
      return Promise.resolve(newEntry);
    }

    var row = {
      user_id: _userId(),
      date: _dateKey(date),
      meal: mealType,
      food_id: entry.foodId || null,
      name: entry.name,
      serving_qty: entry.servingQty,
      serving_unit: entry.servingUnit || '',
      serving_label: entry.servingLabel || '',
      calories: entry.calories,
      protein: entry.protein,
      carbs: entry.carbs,
      fat: entry.fat,
    };

    return _db()
      .from('food_logs')
      .insert(row)
      .select()
      .then(function (result) {
        if (result.error) {
          console.error('Supabase insert error:', result.error);
          return null;
        }
        return _rowToEntry(result.data[0]);
      });
  }

  /**
   * Remove a food entry by id.
   */
  function removeFoodEntry(date, mealType, entryId) {
    if (!_isOnline()) {
      var diary = _getDiary();
      var key = _dateKey(date);
      if (!diary[key]) return Promise.resolve(false);
      var meal = diary[key].meals[mealType];
      var idx = meal.entries.findIndex(function (e) { return e.id === entryId; });
      if (idx === -1) return Promise.resolve(false);
      meal.entries.splice(idx, 1);
      _saveDiary(diary);
      return Promise.resolve(true);
    }

    return _db()
      .from('food_logs')
      .delete()
      .eq('id', entryId)
      .eq('user_id', _userId())
      .then(function (result) {
        if (result.error) {
          console.error('Supabase delete error:', result.error);
          return false;
        }
        return true;
      });
  }

  /**
   * Update an existing food entry.
   */
  function updateFoodEntry(date, mealType, entryId, updates) {
    if (!_isOnline()) {
      var diary = _getDiary();
      var key = _dateKey(date);
      if (!diary[key]) return Promise.resolve(null);
      var meal = diary[key].meals[mealType];
      var entry = meal.entries.find(function (e) { return e.id === entryId; });
      if (!entry) return Promise.resolve(null);
      Object.assign(entry, updates);
      _saveDiary(diary);
      return Promise.resolve(entry);
    }

    // Map our entry field names to DB column names
    var dbUpdates = {};
    if (updates.name !== undefined) dbUpdates.name = updates.name;
    if (updates.servingQty !== undefined) dbUpdates.serving_qty = updates.servingQty;
    if (updates.servingUnit !== undefined) dbUpdates.serving_unit = updates.servingUnit;
    if (updates.servingLabel !== undefined) dbUpdates.serving_label = updates.servingLabel;
    if (updates.calories !== undefined) dbUpdates.calories = updates.calories;
    if (updates.protein !== undefined) dbUpdates.protein = updates.protein;
    if (updates.carbs !== undefined) dbUpdates.carbs = updates.carbs;
    if (updates.fat !== undefined) dbUpdates.fat = updates.fat;
    if (updates.foodId !== undefined) dbUpdates.food_id = updates.foodId;

    return _db()
      .from('food_logs')
      .update(dbUpdates)
      .eq('id', entryId)
      .eq('user_id', _userId())
      .select()
      .then(function (result) {
        if (result.error) {
          console.error('Supabase update error:', result.error);
          return null;
        }
        return result.data[0] ? _rowToEntry(result.data[0]) : null;
      });
  }

  // ---------- goals (always localStorage for now) ----------

  function getGoals() {
    return _read(KEYS.goals) || {
      calories: 2000,
      protein: 150,
      carbs: 250,
      fat: 65,
    };
  }

  function saveGoals(goals) {
    _write(KEYS.goals, goals);
  }

  // ---------- user-created foods ----------
  // Per-user list of manually-added foods (macros stored PER GRAM, same as the
  // shared foods table). Falls back to localStorage when signed out.

  function getUserFoods() {
    if (!_isOnline()) {
      return Promise.resolve(_read(KEYS.customFoods) || []);
    }
    return _db()
      .from('user_foods')
      .select('name, calories, protein, carbs, fat')
      .eq('user_id', _userId())
      .then(function (result) {
        if (result.error) {
          console.error('Supabase user_foods select error:', result.error);
          return [];
        }
        return (result.data || []).map(function (r) {
          return {
            name: r.name,
            calories: Number(r.calories),
            protein: Number(r.protein),
            carbs: Number(r.carbs),
            fat: Number(r.fat),
          };
        });
      });
  }

  function saveUserFood(food) {
    // food: { name, calories, protein, carbs, fat } — all PER GRAM
    if (!_isOnline()) {
      var list = _read(KEYS.customFoods) || [];
      list.push(food);
      _write(KEYS.customFoods, list);
      return Promise.resolve(food);
    }
    return _db()
      .from('user_foods')
      .insert({
        user_id: _userId(),
        name: food.name,
        calories: food.calories,
        protein: food.protein,
        carbs: food.carbs,
        fat: food.fat,
      })
      .select()
      .then(function (result) {
        if (result.error) {
          console.error('Supabase user_foods insert error:', result.error);
          return null;
        }
        return food;
      });
  }

  // ---------- utility ----------

  function _generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  }

  function computeDayTotals(dayData) {
    var totals = { calories: 0, protein: 0, carbs: 0, fat: 0 };
    var mealTypes = Object.keys(dayData.meals);
    for (var i = 0; i < mealTypes.length; i++) {
      var entries = dayData.meals[mealTypes[i]].entries;
      for (var j = 0; j < entries.length; j++) {
        totals.calories += entries[j].calories || 0;
        totals.protein  += entries[j].protein  || 0;
        totals.carbs    += entries[j].carbs    || 0;
        totals.fat      += entries[j].fat      || 0;
      }
    }
    return totals;
  }

  function computeMealTotals(entries) {
    var totals = { calories: 0, protein: 0, carbs: 0, fat: 0 };
    for (var i = 0; i < entries.length; i++) {
      totals.calories += entries[i].calories || 0;
      totals.protein  += entries[i].protein  || 0;
      totals.carbs    += entries[i].carbs    || 0;
      totals.fat      += entries[i].fat      || 0;
    }
    return totals;
  }

  // ---------- hardcoded dummy data for step 1 ----------

  function getDummyDayData() {
    return {
      meals: {
        breakfast: {
          entries: [
            { id: 'demo1', foodId: 'oats_rolled', name: 'Oats, rolled, dry', servingQty: 1, servingLabel: '1/2 cup', calories: 154, protein: 5.3, carbs: 27.4, fat: 2.6 },
            { id: 'demo2', foodId: 'banana', name: 'Banana', servingQty: 1, servingLabel: '1 medium', calories: 105, protein: 1.3, carbs: 27, fat: 0.4 },
            { id: 'demo3', foodId: 'milk_whole', name: 'Milk, whole', servingQty: 1, servingLabel: '1 cup', calories: 149, protein: 8, carbs: 12, fat: 8 },
          ],
        },
        lunch: {
          entries: [
            { id: 'demo4', foodId: 'chicken_breast', name: 'Chicken Breast, grilled', servingQty: 1.5, servingLabel: '150g', calories: 248, protein: 46.5, carbs: 0, fat: 5.4 },
            { id: 'demo5', foodId: 'rice_white_cooked', name: 'Rice, white, cooked', servingQty: 1, servingLabel: '1 cup', calories: 206, protein: 4.3, carbs: 44.5, fat: 0.4 },
            { id: 'demo6', foodId: 'broccoli', name: 'Broccoli, steamed', servingQty: 2, servingLabel: '1 cup', calories: 54, protein: 3.8, carbs: 11.2, fat: 0.6 },
          ],
        },
        dinner: {
          entries: [
            { id: 'demo7', foodId: 'salmon_atlantic', name: 'Salmon, Atlantic, cooked', servingQty: 1, servingLabel: '100g', calories: 208, protein: 20, carbs: 0, fat: 13 },
            { id: 'demo8', foodId: 'sweet_potato', name: 'Sweet Potato, baked', servingQty: 1, servingLabel: '1 medium', calories: 103, protein: 2.3, carbs: 24, fat: 0.1 },
            { id: 'demo9', foodId: 'olive_oil', name: 'Olive Oil', servingQty: 1, servingLabel: '1 tbsp', calories: 119, protein: 0, carbs: 0, fat: 13.5 },
          ],
        },
        snacks: {
          entries: [
            { id: 'demo10', foodId: 'greek_yogurt', name: 'Greek Yogurt, plain, 2%', servingQty: 1, servingLabel: '3/4 cup', calories: 100, protein: 17, carbs: 6, fat: 1.8 },
            { id: 'demo11', foodId: 'almonds', name: 'Almonds', servingQty: 1, servingLabel: '1 oz', calories: 164, protein: 6, carbs: 6, fat: 14 },
          ],
        },
      },
    };
  }

  // ---------- food nutrition calculator ----------

  function calcFoodNutrition(food, qty, unit, unitConversions) {
    var multiplier = 0;
    var base;

    if (unit.type === 'weight') {
      var gramsPerUnit = unit.grams !== undefined
        ? unit.grams
        : (unitConversions.weight ? unitConversions.weight[unit.label] : 0);
      multiplier = qty * gramsPerUnit / 100;
      base = food.per100g;
    } else if (unit.type === 'volume') {
      var mlPerUnit = unit.ml !== undefined
        ? unit.ml
        : (unitConversions.volume ? unitConversions.volume[unit.label] : 0);
      multiplier = qty * mlPerUnit / 100;
      base = food.per100ml;
    }

    if (!base || multiplier === 0) {
      return { calories: 0, protein: 0, carbs: 0, fat: 0 };
    }

    return {
      calories: Math.round(base.calories * multiplier),
      protein:  Math.round(base.protein  * multiplier * 10) / 10,
      carbs:    Math.round(base.carbs    * multiplier * 10) / 10,
      fat:      Math.round(base.fat      * multiplier * 10) / 10,
    };
  }

  // ---------- expose public interface ----------

  return {
    getMealsForDate: getMealsForDate,
    addFoodEntry: addFoodEntry,
    removeFoodEntry: removeFoodEntry,
    updateFoodEntry: updateFoodEntry,
    getGoals: getGoals,
    saveGoals: saveGoals,
    getUserFoods: getUserFoods,
    saveUserFood: saveUserFood,
    computeDayTotals: computeDayTotals,
    computeMealTotals: computeMealTotals,
    getDummyDayData: getDummyDayData,
    calcFoodNutrition: calcFoodNutrition,
  };
})();
