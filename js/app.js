/**
 * app.js - Application orchestrator
 *
 * Wires Storage and UI together.
 * Manages current state (selected date) and user interactions.
 */

const App = (function () {

  var currentDate = new Date();
  var dayData = null;
  var foodDatabase = [];
  var unitConversions = {};

  function init() {
    UI.init();
    UI.bindNavigation(goToPrevDay, goToNextDay);
    dayData = Storage.getMealsForDate(currentDate);

    fetch('data/foods.json')
      .then(function (res) { return res.json(); })
      .then(function (json) {
        unitConversions = json.unitConversions;
        foodDatabase = json.foods.map(function (food) {
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
        foodDatabase = [];
      });

    renderDay();
  }

  function renderDay() {
    var goals = Storage.getGoals();
    var totals = Storage.computeDayTotals(dayData);

    UI.renderDateHeader(currentDate);
    UI.renderSummary(totals, goals);
    UI.renderMeals(dayData, handleAddFood, handleEditEntry, Storage.computeMealTotals);
  }

  function goToPrevDay() {
    currentDate.setDate(currentDate.getDate() - 1);
    dayData = Storage.getMealsForDate(currentDate);
    renderDay();
  }

  function goToNextDay() {
    currentDate.setDate(currentDate.getDate() + 1);
    dayData = Storage.getMealsForDate(currentDate);
    renderDay();
  }

  function handleAddFood(mealType) {
    var recentFoods = _getRecentFoods(5);
    UI.showAddFoodPanel(mealType, foodDatabase, recentFoods, onFoodPicked);
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
    UI.hideAddFoodPanel();
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

    if (existingEntry) {
      Storage.updateFoodEntry(currentDate, mealType, existingEntry.id, entryData);
    } else {
      Storage.addFoodEntry(currentDate, mealType, Object.assign({
        foodId: food.id,
        name: food.name,
      }, entryData));
    }

    dayData = Storage.getMealsForDate(currentDate);
    UI.hideFoodDetail();
    renderDay();
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
