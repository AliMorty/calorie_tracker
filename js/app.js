/**
 * app.js - Application orchestrator
 *
 * Wires Storage and UI together.
 * Manages current state (selected date) and user interactions.
 */

const App = (function () {

  var currentDate = new Date();

  function init() {
    UI.init();
    UI.bindNavigation(goToPrevDay, goToNextDay);
    renderDay();
  }

  function renderDay() {
    // For step 1, use hardcoded dummy data regardless of date.
    // In step 2 this will switch to: Storage.getMealsForDate(currentDate)
    var dayData = Storage.getDummyDayData();
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
    // Placeholder for step 2 - will open an add-food modal/panel
    console.log('Add food clicked for:', mealType);
  }

  // ---------- expose ----------

  return {
    init: init,
  };
})();

// Boot the app when DOM is ready
document.addEventListener('DOMContentLoaded', App.init);
