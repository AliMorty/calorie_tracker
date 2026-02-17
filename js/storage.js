/**
 * storage.js - Data persistence layer
 *
 * All localStorage read/write logic lives here. No DOM access.
 * Exposes a clean interface so the backing store can be swapped
 * to a remote API later without touching the rest of the app.
 */

const Storage = (function () {
  const KEYS = {
    diary: 'ct_diary',       // diary entries keyed by date
    goals: 'ct_goals',       // daily macro goals
    profile: 'ct_profile',   // user profile (future)
    customFoods: 'ct_custom_foods', // user-created foods (future)
  };

  // ---------- low-level helpers ----------

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

  // Canonical date string used as diary key: "YYYY-MM-DD"
  function _dateKey(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return y + '-' + m + '-' + d;
  }

  // ---------- diary ----------

  /**
   * Returns the full diary object (all dates).
   * Structure:
   * {
   *   "2026-02-16": {
   *     meals: {
   *       breakfast: { entries: [ { id, foodId, name, servingQty, servingLabel, calories, protein, carbs, fat, addedAt } ] },
   *       lunch:     { entries: [...] },
   *       dinner:    { entries: [...] },
   *       snacks:    { entries: [...] }
   *     }
   *   }
   * }
   */
  function _getDiary() {
    return _read(KEYS.diary) || {};
  }

  function _saveDiary(diary) {
    _write(KEYS.diary, diary);
  }

  // Empty day template
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
   * @param {Date} date
   * @returns {{ meals: { breakfast: {entries:[]}, lunch: {entries:[]}, dinner: {entries:[]}, snacks: {entries:[]} } }}
   */
  function getMealsForDate(date) {
    const diary = _getDiary();
    const key = _dateKey(date);
    return diary[key] || _emptyDay();
  }

  /**
   * Add a food entry to a meal on a given date.
   * @param {Date} date
   * @param {string} mealType - "breakfast" | "lunch" | "dinner" | "snacks"
   * @param {object} entry - { foodId, name, servingQty, servingLabel, calories, protein, carbs, fat }
   * @returns {object} the created entry (with generated id and timestamp)
   */
  function addFoodEntry(date, mealType, entry) {
    const diary = _getDiary();
    const key = _dateKey(date);

    if (!diary[key]) {
      diary[key] = _emptyDay();
    }

    const newEntry = Object.assign({}, entry, {
      id: _generateId(),
      addedAt: new Date().toISOString(),
    });

    diary[key].meals[mealType].entries.push(newEntry);
    _saveDiary(diary);
    return newEntry;
  }

  /**
   * Remove a food entry by id from a meal on a given date.
   */
  function removeFoodEntry(date, mealType, entryId) {
    const diary = _getDiary();
    const key = _dateKey(date);

    if (!diary[key]) return false;

    const meal = diary[key].meals[mealType];
    const idx = meal.entries.findIndex(function (e) { return e.id === entryId; });
    if (idx === -1) return false;

    meal.entries.splice(idx, 1);
    _saveDiary(diary);
    return true;
  }

  /**
   * Update an existing food entry (e.g. change serving quantity).
   */
  function updateFoodEntry(date, mealType, entryId, updates) {
    const diary = _getDiary();
    const key = _dateKey(date);

    if (!diary[key]) return null;

    const meal = diary[key].meals[mealType];
    const entry = meal.entries.find(function (e) { return e.id === entryId; });
    if (!entry) return null;

    Object.assign(entry, updates);
    _saveDiary(diary);
    return entry;
  }

  // ---------- goals ----------

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

  // ---------- utility ----------

  function _generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  }

  /**
   * Compute totals for a day's meals object.
   * @param {{ meals: object }} dayData - as returned by getMealsForDate
   * @returns {{ calories: number, protein: number, carbs: number, fat: number }}
   */
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

  /**
   * Compute totals for a single meal.
   */
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

  // ---------- expose public interface ----------

  return {
    getMealsForDate: getMealsForDate,
    addFoodEntry: addFoodEntry,
    removeFoodEntry: removeFoodEntry,
    updateFoodEntry: updateFoodEntry,
    getGoals: getGoals,
    saveGoals: saveGoals,
    computeDayTotals: computeDayTotals,
    computeMealTotals: computeMealTotals,
    getDummyDayData: getDummyDayData,
  };
})();
