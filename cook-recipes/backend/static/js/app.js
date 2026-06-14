const API = {
  base: "",
  async request(url, options = {}) {
    const response = await fetch(`${this.base}${url}`, options);
    if (!response.ok) {
      let message = "Ошибка запроса";
      try {
        const data = await response.json();
        message = data.detail || message;
        if (typeof message === "object") message = JSON.stringify(message);
      } catch (_) {
        message = response.statusText;
      }
      throw new Error(message);
    }
    if (response.status === 204) return null;
    return response.json();
  },

  getStats() {
    return this.request("/api/stats");
  },

  getFoods() {
    return this.request("/api/foods");
  },
  getFood(id) {
    return this.request(`/api/foods/${id}`);
  },
  createFood(formData) {
    return this.request("/api/foods", { method: "POST", body: formData });
  },
  updateFood(id, formData) {
    return this.request(`/api/foods/${id}`, { method: "PUT", body: formData });
  },
  deleteFood(id) {
    return this.request(`/api/foods/${id}`, { method: "DELETE" });
  },

  getRecipes(params = {}) {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== "") qs.append(k, v);
    });
    const query = qs.toString();
    return this.request(`/api/recipes${query ? "?" + query : ""}`);
  },
  getRecipe(id) {
    return this.request(`/api/recipes/${id}`);
  },
  createRecipe(formData) {
    return this.request("/api/recipes", { method: "POST", body: formData });
  },
  deleteRecipe(id) {
    return this.request(`/api/recipes/${id}`, { method: "DELETE" });
  },

  getMealPlans() {
    return this.request("/api/mealplans");
  },
  getMealPlan(id) {
    return this.request(`/api/mealplans/${id}`);
  },
  createMealPlan(data) {
    return this.request("/api/mealplans", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  createAutoMealPlan(data) {
    return this.request("/api/mealplans/auto", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
  },
  deleteMealPlan(id) {
    return this.request(`/api/mealplans/${id}`, { method: "DELETE" });
  },
};

function showAlert(container, message, type = "success") {
  const el = document.createElement("div");
  el.className = `alert alert-${type}`;
  el.textContent = message;
  container.prepend(el);
  setTimeout(() => el.remove(), 4000);
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function imageUrl(path) {
  return path ? `/${path}` : "/static/images/placeholder.svg";
}

async function initIndexPage() {
  const statsEl = document.getElementById("stats");
  if (!statsEl) return;
  try {
    const stats = await API.getStats();
    document.getElementById("stat-foods").textContent = stats.foods;
    document.getElementById("stat-recipes").textContent = stats.recipes;
    document.getElementById("stat-plans").textContent = stats.meal_plans;
  } catch (e) {
    statsEl.innerHTML =
      '<div class="alert alert-error">Не удалось загрузить статистику. Убедитесь, что сервер запущен.</div>';
  }
}

async function initFoodsPage() {
  const alertsEl = document.getElementById("alerts");
  const foodsList = document.getElementById("foods-list");
  const foodForm = document.getElementById("food-form");
  if (!foodsList) return;

  async function loadFoods() {
    try {
      const foods = await API.getFoods();
      if (!foods.length) {
        foodsList.innerHTML = '<div class="empty-state">Пока нет продуктов. Добавьте первый!</div>';
        return;
      }
      foodsList.innerHTML = foods
        .map(
          (f) => `
      <div class="card" data-id="${f.id}">
        <img class="card-image" src="${imageUrl(f.image)}" alt="${f.name}">
        <div class="card-body">
          <div class="card-title">${f.name}</div>
          <div class="card-meta">${formatDate(f.created_at)}</div>
          <div class="card-tags">
            <span class="tag">Б: ${f.proteins}г</span>
            <span class="tag">Ж: ${f.fats}г</span>
            <span class="tag">У: ${f.carbs}г</span>
            <span class="tag">${f.calories} ккал</span>
          </div>
          <button class="btn btn-danger btn-sm" style="margin-top:12px" onclick="deleteFood(${f.id})">Удалить</button>
        </div>
      </div>`
        )
        .join("");
    } catch (e) {
      foodsList.innerHTML = `<div class="alert alert-error">${e.message}</div>`;
    }
  }

  window.deleteFood = async (id) => {
    if (!confirm("Удалить продукт?")) return;
    try {
      await API.deleteFood(id);
      showAlert(alertsEl, "Продукт удалён");
      loadFoods();
    } catch (e) {
      showAlert(alertsEl, e.message, "error");
    }
  };

  foodForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(foodForm);
    try {
      await API.createFood(formData);
      showAlert(alertsEl, "Продукт добавлен!");
      foodForm.reset();
      loadFoods();
    } catch (err) {
      showAlert(alertsEl, err.message, "error");
    }
  });

  loadFoods();
}

async function initRecipesPage() {
  const alertsEl = document.getElementById("alerts");
  const recipesList = document.getElementById("recipes-list");
  const ingredientsContainer = document.getElementById("ingredients-container");
  if (!recipesList) return;

  let allFoods = [];

  function createIngredientRow() {
    const row = document.createElement("div");
    row.className = "ingredient-row";
    const options = allFoods
      .map((f) => `<option value="${f.id}">${f.name}</option>`)
      .join("");
    row.innerHTML = `
    <select class="ing-food" required>
      <option value="">Выберите продукт</option>${options}
    </select>
    <input type="number" class="ing-grams" placeholder="Граммы" min="1" step="1" required>
    <button type="button" class="btn btn-danger btn-sm" onclick="this.parentElement.remove()">✕</button>
  `;
    ingredientsContainer.appendChild(row);
  }

  async function loadFoods() {
    allFoods = await API.getFoods();
    createIngredientRow();
  }

  async function loadRecipes() {
    const params = {
      search: document.getElementById("filter-search").value,
      date_from: document.getElementById("filter-date-from").value
        ? document.getElementById("filter-date-from").value + "T00:00:00"
        : "",
      date_to: document.getElementById("filter-date-to").value
        ? document.getElementById("filter-date-to").value + "T23:59:59"
        : "",
      min_calories: document.getElementById("filter-min-cal").value,
      max_calories: document.getElementById("filter-max-cal").value,
    };

    try {
      const recipes = await API.getRecipes(params);
      if (!recipes.length) {
        recipesList.innerHTML = '<div class="empty-state">Рецепты не найдены</div>';
        return;
      }
      recipesList.innerHTML = recipes
        .map(
          (r) => `
      <div class="card">
        <img class="card-image" src="${imageUrl(r.image)}" alt="${r.name}">
        <div class="card-body">
          <div class="card-title">${r.name}</div>
          <div class="card-meta">${formatDate(r.created_at)}</div>
          <div class="card-tags">
            <span class="tag">${r.calories_per_100g} ккал / 100г</span>
          </div>
          <a href="/recipes/${r.id}" class="btn btn-primary btn-sm" style="margin-top:12px; display:inline-flex">Открыть</a>
          <button class="btn btn-danger btn-sm" style="margin-top:12px" onclick="deleteRecipe(${r.id})">Удалить</button>
        </div>
      </div>`
        )
        .join("");
    } catch (e) {
      recipesList.innerHTML = `<div class="alert alert-error">${e.message}</div>`;
    }
  }

  window.deleteRecipe = async (id) => {
    if (!confirm("Удалить рецепт?")) return;
    try {
      await API.deleteRecipe(id);
      showAlert(alertsEl, "Рецепт удалён");
      loadRecipes();
    } catch (e) {
      showAlert(alertsEl, e.message, "error");
    }
  };

  document.getElementById("recipe-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const rows = ingredientsContainer.querySelectorAll(".ingredient-row");
    const ingredients = [];
    rows.forEach((row) => {
      const foodId = row.querySelector(".ing-food").value;
      const grams = row.querySelector(".ing-grams").value;
      if (foodId && grams) ingredients.push({ food_id: parseInt(foodId), grams: parseFloat(grams) });
    });

    if (!ingredients.length) {
      showAlert(alertsEl, "Добавьте хотя бы один ингредиент", "error");
      return;
    }

    const formData = new FormData();
    formData.append("name", document.getElementById("recipe-name").value);
    formData.append("instruction", document.getElementById("recipe-instruction").value);
    formData.append("ingredients", JSON.stringify(ingredients));
    formData.append("image", document.getElementById("recipe-image").files[0]);

    try {
      await API.createRecipe(formData);
      showAlert(alertsEl, "Рецепт создан!");
      e.target.reset();
      ingredientsContainer.innerHTML = "";
      createIngredientRow();
      loadRecipes();
    } catch (err) {
      showAlert(alertsEl, err.message, "error");
    }
  });

  document.getElementById("add-ingredient").addEventListener("click", createIngredientRow);
  document.getElementById("apply-filters").addEventListener("click", loadRecipes);
  document.getElementById("reset-filters").addEventListener("click", () => {
    document.getElementById("filter-search").value = "";
    document.getElementById("filter-date-from").value = "";
    document.getElementById("filter-date-to").value = "";
    document.getElementById("filter-min-cal").value = "";
    document.getElementById("filter-max-cal").value = "";
    loadRecipes();
  });

  loadFoods().then(loadRecipes).catch((e) => {
    showAlert(alertsEl, e.message, "error");
  });
}

async function initRecipeDetailPage() {
  const container = document.getElementById("recipe-content");
  if (!container) return;

  const recipeId = window.location.pathname.split("/").pop();

  try {
    const r = await API.getRecipe(recipeId);
    document.title = `${r.name} — Cook Recipes`;

    const ingredientsHtml = r.ingredients
      .map(
        (i) => `
      <li>
        <span>${i.food_name} — ${i.grams} г</span>
        <span>${i.calories} ккал</span>
      </li>`
      )
      .join("");

    container.innerHTML = `
      <div class="page-header">
        <h1>${r.name}</h1>
        <a href="/recipes" class="btn btn-secondary">← Назад</a>
      </div>
      <div class="recipe-detail">
        <div>
          <img src="${imageUrl(r.image)}" alt="${r.name}">
          <p style="color: var(--text-secondary); margin-top: 12px;">Добавлен: ${formatDate(r.created_at)}</p>
        </div>
        <div>
          <h2 style="margin-bottom: 12px;">Пищевая ценность</h2>
          <div class="nutrition-grid">
            <div class="nutrition-item"><div class="val">${r.total_calories}</div><div class="lbl">ккал</div></div>
            <div class="nutrition-item"><div class="val">${r.total_proteins}г</div><div class="lbl">белки</div></div>
            <div class="nutrition-item"><div class="val">${r.total_fats}г</div><div class="lbl">жиры</div></div>
            <div class="nutrition-item"><div class="val">${r.total_carbs}г</div><div class="lbl">углеводы</div></div>
          </div>
          <p style="color: var(--text-secondary);">Калорийность: <strong>${r.calories_per_100g} ккал / 100 г</strong> (всего ${r.total_weight} г)</p>

          <h3 style="margin-top: 24px;">Ингредиенты</h3>
          <ul class="ingredients-list">${ingredientsHtml}</ul>
        </div>
      </div>
      <div class="instruction-block">
        <h3 style="margin-bottom: 12px; color: var(--accent-light);">Инструкция приготовления</h3>
        ${r.instruction}
      </div>`;
  } catch (e) {
    container.innerHTML = `<div class="alert alert-error">${e.message}</div>`;
  }
}

async function initMealPlansPage() {
  const alertsEl = document.getElementById("alerts");
  const plansList = document.getElementById("plans-list");
  const recipeCheckboxes = document.getElementById("recipe-checkboxes");
  const manualPreview = document.getElementById("manual-preview");
  if (!plansList) return;

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById(`tab-${tab.dataset.tab}`).classList.add("active");
    });
  });

  function renderPlanCard(plan) {
    const exceeded = plan.calories_exceeded
      ? '<div class="alert alert-warning" style="margin-top:12px">⚠ Превышена норма калорий!</div>'
      : "";
    const recipesHtml = plan.recipes
      .map((r) => `<span class="tag">${r.recipe_name} (${r.calories} ккал)</span>`)
      .join(" ");

    return `
    <div class="meal-plan-card ${plan.calories_exceeded ? "exceeded" : ""}">
      <div style="display:flex; justify-content:space-between; align-items:start;">
        <div>
          <h3>${plan.name}</h3>
          <p style="color:var(--text-secondary)">${formatDate(plan.created_at)} · Цель: ${plan.target_calories} ккал</p>
        </div>
        <button class="btn btn-danger btn-sm" onclick="deletePlan(${plan.id})">Удалить</button>
      </div>
      <div class="nutrition-grid" style="margin-top:16px">
        <div class="nutrition-item"><div class="val">${plan.total_calories}</div><div class="lbl">ккал</div></div>
        <div class="nutrition-item"><div class="val">${plan.total_proteins}г</div><div class="lbl">белки</div></div>
        <div class="nutrition-item"><div class="val">${plan.total_fats}г</div><div class="lbl">жиры</div></div>
        <div class="nutrition-item"><div class="val">${plan.total_carbs}г</div><div class="lbl">углеводы</div></div>
      </div>
      <div class="card-tags" style="margin-top:12px">${recipesHtml}</div>
      ${exceeded}
    </div>`;
  }

  async function loadPlans() {
    try {
      const plans = await API.getMealPlans();
      if (!plans.length) {
        plansList.innerHTML = '<div class="empty-state">Нет сохранённых рационов</div>';
        return;
      }
      plansList.innerHTML = plans.map(renderPlanCard).join("");
    } catch (e) {
      plansList.innerHTML = `<div class="alert alert-error">${e.message}</div>`;
    }
  }

  async function loadRecipesForSelect() {
    try {
      const allRecipes = await API.getRecipes();
      if (!allRecipes.length) {
        recipeCheckboxes.innerHTML = '<p class="empty-state">Сначала создайте рецепты</p>';
        return;
      }
      recipeCheckboxes.innerHTML = allRecipes
        .map(
          (r) => `
      <label style="display:flex; align-items:center; gap:8px; margin-bottom:8px; cursor:pointer;">
        <input type="checkbox" class="recipe-check" value="${r.id}" data-calories="${r.calories_per_100g}">
        ${r.name}
      </label>`
        )
        .join("");

      recipeCheckboxes.addEventListener("change", updateManualPreview);
    } catch (e) {
      recipeCheckboxes.innerHTML = `<div class="alert alert-error">${e.message}</div>`;
    }
  }

  async function updateManualPreview() {
    const checked = [...document.querySelectorAll(".recipe-check:checked")].map(
      (el) => parseInt(el.value)
    );
    if (!checked.length) {
      manualPreview.innerHTML = "";
      return;
    }

    let totalCal = 0, totalP = 0, totalF = 0, totalC = 0;
    for (const id of checked) {
      const r = await API.getRecipe(id);
      totalCal += r.total_calories;
      totalP += r.total_proteins;
      totalF += r.total_fats;
      totalC += r.total_carbs;
    }

    const target = parseFloat(document.getElementById("plan-target").value) || 0;
    const warning =
      target && totalCal > target
        ? '<div class="alert alert-warning">⚠ Превышена норма калорий!</div>'
        : "";

    manualPreview.innerHTML = `
    <div class="nutrition-grid">
      <div class="nutrition-item"><div class="val">${totalCal.toFixed(1)}</div><div class="lbl">ккал</div></div>
      <div class="nutrition-item"><div class="val">${totalP.toFixed(1)}г</div><div class="lbl">белки</div></div>
      <div class="nutrition-item"><div class="val">${totalF.toFixed(1)}г</div><div class="lbl">жиры</div></div>
      <div class="nutrition-item"><div class="val">${totalC.toFixed(1)}г</div><div class="lbl">углеводы</div></div>
    </div>${warning}`;
  }

  document.getElementById("plan-target").addEventListener("input", updateManualPreview);

  document.getElementById("manual-plan-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const recipeIds = [...document.querySelectorAll(".recipe-check:checked")].map(
      (el) => parseInt(el.value)
    );
    if (!recipeIds.length) {
      showAlert(alertsEl, "Выберите хотя бы одно блюдо", "error");
      return;
    }
    try {
      await API.createMealPlan({
        name: document.getElementById("plan-name").value,
        target_calories: parseFloat(document.getElementById("plan-target").value),
        recipe_ids: recipeIds,
      });
      showAlert(alertsEl, "Рацион сохранён!");
      e.target.reset();
      manualPreview.innerHTML = "";
      loadPlans();
    } catch (err) {
      showAlert(alertsEl, err.message, "error");
    }
  });

  document.getElementById("auto-plan-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await API.createAutoMealPlan({
        name: document.getElementById("auto-plan-name").value,
        target_calories: parseFloat(document.getElementById("auto-plan-target").value),
      });
      showAlert(alertsEl, "Рацион сгенерирован!");
      e.target.reset();
      loadPlans();
    } catch (err) {
      showAlert(alertsEl, err.message, "error");
    }
  });

  window.deletePlan = async (id) => {
    if (!confirm("Удалить рацион?")) return;
    try {
      await API.deleteMealPlan(id);
      showAlert(alertsEl, "Рацион удалён");
      loadPlans();
    } catch (e) {
      showAlert(alertsEl, e.message, "error");
    }
  };

  loadRecipesForSelect();
  loadPlans();
}

initIndexPage();
initFoodsPage();
initRecipesPage();
initRecipeDetailPage();
initMealPlansPage();