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

  function init() {
    UI.init();
    UI.bindNavigation(goToPrevDay, goToNextDay);
    dayData = Storage.getDummyDayData();

    fetch('data/foods.json')
      .then(function (res) { return res.json(); })
      .then(function (json) { foodDatabase = json.foods; })
      .catch(function () { foodDatabase = []; });

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
    UI.showAddFoodPanel(mealType, foodDatabase, onFoodSelected);
  }

  function onFoodSelected(mealType, food) {
    var entry = {
      id: Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
      foodId: food.id,
      name: food.name,
      servingQty: 1,
      servingLabel: food.servingLabel,
      calories: food.calories,
      protein: food.protein,
      carbs: food.carbs,
      fat: food.fat,
      addedAt: new Date().toISOString(),
    };
    dayData.meals[mealType].entries.push(entry);
    UI.hideAddFoodPanel();
    renderDay();
  }

  // ---------- expose ----------

  return {
    init: init,
  };
})();

// Boot the app when DOM is ready
document.addEventListener('DOMContentLoaded', App.init);
