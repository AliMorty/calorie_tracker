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
    dayData = Storage.getDummyDayData();

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
    UI.renderMeals(dayData, handleAddFood, Storage.computeMealTotals);
  }

  function goToPrevDay() {
    currentDate.setDate(currentDate.getDate() - 1);
    renderDay();
  }

  function goToNextDay() {
    currentDate.setDate(currentDate.getDate() + 1);
    renderDay();
  }

  function handleAddFood(mealType) {
    UI.showAddFoodPanel(mealType, foodDatabase, onFoodPicked);
  }

  function onFoodPicked(mealType, food) {
    UI.hideAddFoodPanel();
    UI.showFoodDetail(mealType, food, unitConversions, onFoodConfirmed);
  }

  function onFoodConfirmed(mealType, food, qty, unit) {
    var nutrition = Storage.calcFoodNutrition(food, qty, unit, unitConversions);
    var entry = {
      id: Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
      foodId: food.id,
      name: food.name,
      servingQty: qty,
      servingLabel: qty + ' ' + unit.label,
      calories: nutrition.calories,
      protein: nutrition.protein,
      carbs: nutrition.carbs,
      fat: nutrition.fat,
      addedAt: new Date().toISOString(),
    };
    dayData.meals[mealType].entries.push(entry);
    UI.hideFoodDetail();
    renderDay();
  }

  // ---------- expose ----------

  return {
    init: init,
  };
})();

// Boot the app when DOM is ready
document.addEventListener('DOMContentLoaded', App.init);
