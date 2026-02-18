/**
 * ui.js - All DOM manipulation and rendering
 *
 * No business logic or direct localStorage access.
 * Receives data and callbacks from app.js.
 */

const UI = (function () {

  // Cache DOM references
  var els = {};

  function cacheElements() {
    els.dateLabel      = document.getElementById('date-label');
    els.prevDayBtn     = document.getElementById('prev-day-btn');
    els.nextDayBtn     = document.getElementById('next-day-btn');
    els.mealsContainer = document.getElementById('meals-container');
    els.summaryCalories = document.getElementById('summary-calories');
    els.summaryProtein  = document.getElementById('summary-protein');
    els.summaryCarbs    = document.getElementById('summary-carbs');
    els.summaryFat      = document.getElementById('summary-fat');
    els.progressCalories = document.getElementById('progress-calories');
    els.progressProtein  = document.getElementById('progress-protein');
    els.progressCarbs    = document.getElementById('progress-carbs');
    els.progressFat      = document.getElementById('progress-fat');
    els.goalCalories     = document.getElementById('goal-calories');
    els.goalProtein      = document.getElementById('goal-protein');
    els.goalCarbs        = document.getElementById('goal-carbs');
    els.goalFat          = document.getElementById('goal-fat');
    els.remainingCalories = document.getElementById('remaining-calories');
  }

  // ---------- date header ----------

  function renderDateHeader(date) {
    var today = new Date();
    today.setHours(0, 0, 0, 0);
    var target = new Date(date);
    target.setHours(0, 0, 0, 0);

    var label;
    var diff = Math.round((target - today) / 86400000);

    if (diff === 0) {
      label = 'Today';
    } else if (diff === -1) {
      label = 'Yesterday';
    } else if (diff === 1) {
      label = 'Tomorrow';
    } else {
      label = _formatWeekday(date);
    }

    var monthDay = _formatMonthDay(date);
    els.dateLabel.textContent = label + ', ' + monthDay;
  }

  function _formatMonthDay(date) {
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return months[date.getMonth()] + ' ' + date.getDate();
  }

  function _formatWeekday(date) {
    var days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday',
                'Thursday', 'Friday', 'Saturday'];
    return days[date.getDay()];
  }

  // ---------- summary card ----------

  function renderSummary(totals, goals) {
    els.summaryCalories.textContent = Math.round(totals.calories);
    els.summaryProtein.textContent  = Math.round(totals.protein) + 'g';
    els.summaryCarbs.textContent    = Math.round(totals.carbs) + 'g';
    els.summaryFat.textContent      = Math.round(totals.fat) + 'g';

    els.goalCalories.textContent = goals.calories;
    els.goalProtein.textContent  = goals.protein + 'g';
    els.goalCarbs.textContent    = goals.carbs + 'g';
    els.goalFat.textContent      = goals.fat + 'g';

    var remaining = goals.calories - Math.round(totals.calories);
    els.remainingCalories.textContent = remaining;
    if (remaining < 0) {
      els.remainingCalories.classList.add('over');
    } else {
      els.remainingCalories.classList.remove('over');
    }

    _setProgress(els.progressCalories, totals.calories, goals.calories);
    _setProgress(els.progressProtein,  totals.protein,  goals.protein);
    _setProgress(els.progressCarbs,    totals.carbs,    goals.carbs);
    _setProgress(els.progressFat,      totals.fat,      goals.fat);
  }

  function _setProgress(barEl, current, goal) {
    var pct = goal > 0 ? Math.min((current / goal) * 100, 100) : 0;
    barEl.style.width = pct + '%';

    // Color feedback: green under target, amber near, red over
    barEl.classList.remove('bar-ok', 'bar-warn', 'bar-over');
    if (pct >= 100) {
      barEl.classList.add('bar-over');
    } else if (pct >= 85) {
      barEl.classList.add('bar-warn');
    } else {
      barEl.classList.add('bar-ok');
    }
  }

  // ---------- meal sections ----------

  var MEAL_LABELS = {
    breakfast: 'Breakfast',
    lunch: 'Lunch',
    dinner: 'Dinner',
    snacks: 'Snacks',
  };

  var MEAL_ICONS = {
    breakfast: 'sunrise',
    lunch: 'sun',
    dinner: 'moon',
    snacks: 'cookie',
  };

  /**
   * Render all meal sections.
   * @param {object} dayData - { meals: { breakfast: {entries}, ... } }
   * @param {function} onAddClick - callback(mealType) when "+" is clicked
   * @param {function} computeMealTotals - function(entries) => totals
   */
  function renderMeals(dayData, onAddClick, computeMealTotals) {
    els.mealsContainer.innerHTML = '';

    var mealOrder = ['breakfast', 'lunch', 'dinner', 'snacks'];

    for (var i = 0; i < mealOrder.length; i++) {
      var mealType = mealOrder[i];
      var meal = dayData.meals[mealType];
      var totals = computeMealTotals(meal.entries);
      var section = _buildMealSection(mealType, meal.entries, totals, onAddClick);
      els.mealsContainer.appendChild(section);
    }
  }

  function _buildMealSection(mealType, entries, totals, onAddClick) {
    var section = document.createElement('div');
    section.className = 'meal-section';

    // Header row
    var header = document.createElement('div');
    header.className = 'meal-header';

    var headerLeft = document.createElement('div');
    headerLeft.className = 'meal-header-left';

    var title = document.createElement('h2');
    title.className = 'meal-title';
    title.textContent = MEAL_LABELS[mealType];
    headerLeft.appendChild(title);

    var mealMacros = document.createElement('span');
    mealMacros.className = 'meal-macros-summary';
    mealMacros.textContent = Math.round(totals.calories) + ' Cal';
    headerLeft.appendChild(mealMacros);

    header.appendChild(headerLeft);

    var addBtn = document.createElement('button');
    addBtn.className = 'add-food-btn';
    addBtn.textContent = '+';
    addBtn.title = 'Add food to ' + MEAL_LABELS[mealType];
    addBtn.setAttribute('data-meal', mealType);
    addBtn.addEventListener('click', function () {
      onAddClick(mealType);
    });
    header.appendChild(addBtn);

    section.appendChild(header);

    // Macro breakdown row for meal
    if (entries.length > 0) {
      var macroRow = document.createElement('div');
      macroRow.className = 'meal-macro-row';
      macroRow.innerHTML =
        '<span class="macro-chip protein-chip">P ' + Math.round(totals.protein) + 'g</span>' +
        '<span class="macro-chip carbs-chip">C ' + Math.round(totals.carbs) + 'g</span>' +
        '<span class="macro-chip fat-chip">F ' + Math.round(totals.fat) + 'g</span>';
      section.appendChild(macroRow);
    }

    // Food entries
    for (var i = 0; i < entries.length; i++) {
      section.appendChild(_buildFoodEntry(entries[i]));
    }

    // Empty state
    if (entries.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'empty-meal';
      empty.textContent = 'No foods logged yet';
      section.appendChild(empty);
    }

    return section;
  }

  function _buildFoodEntry(entry) {
    var row = document.createElement('div');
    row.className = 'food-entry';
    row.setAttribute('data-entry-id', entry.id);

    var info = document.createElement('div');
    info.className = 'food-info';

    var nameEl = document.createElement('span');
    nameEl.className = 'food-name';
    nameEl.textContent = entry.name;
    info.appendChild(nameEl);

    var portion = document.createElement('span');
    portion.className = 'food-portion';
    var qtyLabel = entry.servingQty > 1
      ? entry.servingQty + ' x ' + entry.servingLabel
      : entry.servingLabel;
    portion.textContent = qtyLabel;
    info.appendChild(portion);

    row.appendChild(info);

    var macros = document.createElement('div');
    macros.className = 'food-macros';
    macros.innerHTML =
      '<span class="food-cal">' + Math.round(entry.calories) + '</span>' +
      '<span class="food-macro-detail">' +
        '<span class="fm-p">' + Math.round(entry.protein) + '</span>' +
        '<span class="fm-c">' + Math.round(entry.carbs) + '</span>' +
        '<span class="fm-f">' + Math.round(entry.fat) + '</span>' +
      '</span>';
    row.appendChild(macros);

    return row;
  }

  // ---------- food detail screen ----------

  function showFoodDetail(mealType, food, unitConversions, onAdd) {
    var mealLabels = { breakfast: 'Breakfast', lunch: 'Lunch', dinner: 'Dinner', snacks: 'Snacks' };
    document.getElementById('fd-meal-label').textContent = mealLabels[mealType];
    document.getElementById('fd-name').textContent = food.name;

    var unitSelect = document.getElementById('fd-unit');
    unitSelect.innerHTML = '';
    for (var i = 0; i < food.units.length; i++) {
      var opt = document.createElement('option');
      opt.value = i;
      opt.textContent = food.units[i].label;
      unitSelect.appendChild(opt);
    }

    var defaultIdx = food.units.findIndex(function (u) { return u.label === food.defaultUnit; });
    if (defaultIdx === -1) defaultIdx = 0;
    unitSelect.value = defaultIdx;

    var qtyInput = document.getElementById('fd-qty');
    qtyInput.value = food.units[defaultIdx].defaultQty;

    _updateFoodDetailMacros(food, parseFloat(qtyInput.value), food.units[defaultIdx], unitConversions);

    qtyInput.oninput = function () {
      var qty = parseFloat(this.value) || 0;
      var unit = food.units[parseInt(unitSelect.value)];
      _updateFoodDetailMacros(food, qty, unit, unitConversions);
    };

    unitSelect.onchange = function () {
      var unit = food.units[parseInt(this.value)];
      qtyInput.value = unit.defaultQty;
      _updateFoodDetailMacros(food, parseFloat(qtyInput.value), unit, unitConversions);
    };

    document.getElementById('fd-add-btn').onclick = function () {
      var qty = parseFloat(qtyInput.value) || 0;
      var unit = food.units[parseInt(unitSelect.value)];
      onAdd(mealType, food, qty, unit);
    };

    document.getElementById('fd-close-btn').onclick = hideFoodDetail;
    document.getElementById('food-detail-screen').classList.remove('hidden');
  }

  function hideFoodDetail() {
    document.getElementById('food-detail-screen').classList.add('hidden');
  }

  function _updateFoodDetailMacros(food, qty, unit, unitConversions) {
    var n = Storage.calcFoodNutrition(food, qty, unit, unitConversions);
    document.getElementById('fd-cal').textContent     = n.calories;
    document.getElementById('fd-protein').textContent = n.protein;
    document.getElementById('fd-carbs').textContent   = n.carbs;
    document.getElementById('fd-fat').textContent     = n.fat;
  }

  // ---------- add food panel ----------

  function showAddFoodPanel(mealType, foods, onSelect) {
    var mealLabels = { breakfast: 'Breakfast', lunch: 'Lunch', dinner: 'Dinner', snacks: 'Snacks' };
    document.getElementById('panel-title').textContent = 'Add to ' + mealLabels[mealType];
    document.getElementById('food-search-input').value = '';
    _renderFoodList(foods, mealType, onSelect);

    document.getElementById('add-food-overlay').classList.remove('hidden');
    document.getElementById('add-food-panel').classList.remove('hidden');
    document.getElementById('food-search-input').focus();

    document.getElementById('food-search-input').oninput = function () {
      var query = this.value.trim().toLowerCase();
      var filtered = query
        ? foods.filter(function (f) { return f.name.toLowerCase().indexOf(query) !== -1; })
        : foods;
      _renderFoodList(filtered, mealType, onSelect);
    };

    document.getElementById('panel-close-btn').onclick = hideAddFoodPanel;
    document.getElementById('add-food-overlay').onclick = hideAddFoodPanel;
  }

  function hideAddFoodPanel() {
    document.getElementById('add-food-overlay').classList.add('hidden');
    document.getElementById('add-food-panel').classList.add('hidden');
  }

  function _renderFoodList(foods, mealType, onSelect) {
    var list = document.getElementById('food-list');
    list.innerHTML = '';

    if (foods.length === 0) {
      var empty = document.createElement('div');
      empty.className = 'food-list-empty';
      empty.textContent = 'No foods found';
      list.appendChild(empty);
      return;
    }

    for (var i = 0; i < foods.length; i++) {
      var food = foods[i];
      var item = document.createElement('div');
      item.className = 'food-list-item';

      var info = document.createElement('div');
      info.className = 'food-list-item-info';

      var name = document.createElement('span');
      name.className = 'food-list-item-name';
      name.textContent = food.name;

      var serving = document.createElement('span');
      serving.className = 'food-list-item-serving';
      serving.textContent = food.displayServing || food.servingLabel || '';

      info.appendChild(name);
      info.appendChild(serving);

      var cal = document.createElement('span');
      cal.className = 'food-list-item-cal';
      cal.textContent = food.displayCalories !== undefined ? food.displayCalories : 0;

      item.appendChild(info);
      item.appendChild(cal);

      item.addEventListener('click', (function (f) {
        return function () { onSelect(mealType, f); };
      })(food));

      list.appendChild(item);
    }
  }

  // ---------- navigation bindings ----------

  function bindNavigation(onPrev, onNext) {
    els.prevDayBtn.addEventListener('click', onPrev);
    els.nextDayBtn.addEventListener('click', onNext);
  }

  // ---------- init ----------

  function init() {
    cacheElements();
  }

  // ---------- expose ----------

  return {
    init: init,
    renderDateHeader: renderDateHeader,
    renderSummary: renderSummary,
    renderMeals: renderMeals,
    bindNavigation: bindNavigation,
    showAddFoodPanel: showAddFoodPanel,
    hideAddFoodPanel: hideAddFoodPanel,
    showFoodDetail: showFoodDetail,
    hideFoodDetail: hideFoodDetail,
  };
})();
