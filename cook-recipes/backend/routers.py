import json
from datetime import datetime
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, selectinload
from database import get_db
from models import Food, MealPlan, MealPlanRecipe, Recipe, RecipeFood
from schemas import (
    AutoMealPlanRequest,
    FoodCreate,
    FoodResponse,
    FoodUpdate,
    MealPlanCreate,
    MealPlanRecipeResponse,
    MealPlanResponse,
    RecipeCreate,
    RecipeIngredientResponse,
    RecipeListItem,
    RecipeResponse,
    RecipeUpdate,
)
from services import (
    RecipeCalorieItem,
    calculate_from_food,
    calories_per_100g,
    find_best_meal_combination,
    merge_totals,
    save_image,
)

foods_router = APIRouter(prefix="/api/foods", tags=["foods"])
recipes_router = APIRouter(prefix="/api/recipes", tags=["recipes"])
mealplans_router = APIRouter(prefix="/api/mealplans", tags=["mealplans"])

@foods_router.get("", response_model=list[FoodResponse])
async def list_foods(db: Session = Depends(get_db)) -> list[Food]:
    result = db.execute(select(Food).order_by(Food.created_at.desc()))
    return list(result.scalars().all())

@foods_router.get("/{food_id}", response_model=FoodResponse)
async def get_food(food_id: int, db: Session = Depends(get_db)) -> Food:
    food = db.get(Food, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    return food

@foods_router.post("", response_model=FoodResponse, status_code=201)
async def create_food(
    name: str = Form(...),
    proteins: float = Form(...),
    fats: float = Form(...),
    carbs: float = Form(...),
    calories: float = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Food:
    try:
        data = FoodCreate(
            name=name,
            proteins=proteins,
            fats=fats,
            carbs=carbs,
            calories=calories,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Неверные данные") from exc
    image_path = await save_image(image)
    food = Food(**data.model_dump(), image=image_path)
    db.add(food)
    db.flush()
    db.refresh(food)
    return food

@foods_router.put("/{food_id}", response_model=FoodResponse)
async def update_food(
    food_id: int,
    name: str | None = Form(None),
    proteins: float | None = Form(None),
    fats: float | None = Form(None),
    carbs: float | None = Form(None),
    calories: float | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> Food:
    food = db.get(Food, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    raw = {
        "name": name,
        "proteins": proteins,
        "fats": fats,
        "carbs": carbs,
        "calories": calories,
    }
    filtered = {k: v for k, v in raw.items() if v is not None}
    if filtered:
        try:
            update_data = FoodUpdate(**filtered)
            for field, value in update_data.model_dump(exclude_unset=True).items():
                setattr(food, field, value)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Неверные данные") from exc

    if image and image.filename:
        food.image = await save_image(image)
    db.flush()
    db.refresh(food)
    return food


@foods_router.delete("/{food_id}", status_code=204)
async def delete_food(food_id: int, db: Session = Depends(get_db)) -> None:
    food = db.get(Food, food_id)
    if not food:
        raise HTTPException(status_code=404, detail="Продукт не найден")
    db.delete(food)

def _build_ingredient_response(ingredient: RecipeFood) -> RecipeIngredientResponse:
    food = ingredient.food
    totals = calculate_from_food(
        food.proteins, food.fats, food.carbs, food.calories, ingredient.grams
    )
    return RecipeIngredientResponse(
        id=ingredient.id,
        food_id=ingredient.food_id,
        grams=ingredient.grams,
        food_name=food.name,
        food_image=food.image,
        proteins=totals.proteins,
        fats=totals.fats,
        carbs=totals.carbs,
        calories=totals.calories,
    )

def _build_recipe_response(recipe: Recipe) -> RecipeResponse:
    return RecipeResponse(
        id=recipe.id,
        name=recipe.name,
        image=recipe.image,
        instruction=recipe.instruction,
        calories_per_100g=recipe.calories_per_100g,
        total_weight=recipe.total_weight,
        total_calories=recipe.total_calories,
        total_proteins=recipe.total_proteins,
        total_fats=recipe.total_fats,
        total_carbs=recipe.total_carbs,
        created_at=recipe.created_at,
        ingredients=[_build_ingredient_response(i) for i in recipe.ingredients],
    )

def _apply_ingredients(db: Session, recipe: Recipe, ingredients_data: list) -> None:
    recipe.ingredients.clear()
    totals_list = []

    for item in ingredients_data:
        food = db.get(Food, item.food_id)
        if not food:
            raise HTTPException(
                status_code=400,
                detail=f"Продукт с id={item.food_id} не найден",
            )
        totals = calculate_from_food(
            food.proteins, food.fats, food.carbs, food.calories, item.grams
        )
        totals_list.append(totals)
        recipe.ingredients.append(RecipeFood(food_id=item.food_id, grams=item.grams))

    merged = merge_totals(*totals_list)
    recipe.total_weight = merged.weight
    recipe.total_calories = merged.calories
    recipe.total_proteins = merged.proteins
    recipe.total_fats = merged.fats
    recipe.total_carbs = merged.carbs
    recipe.calories_per_100g = calories_per_100g(merged.calories, merged.weight)

@recipes_router.get("", response_model=list[RecipeListItem])
async def list_recipes(
    search: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    min_calories: float | None = Query(None, ge=0),
    max_calories: float | None = Query(None, ge=0),
    db: Session = Depends(get_db),
) -> list[Recipe]:
    query = select(Recipe).order_by(Recipe.created_at.desc())
    conditions = []
    if search:
        conditions.append(Recipe.name.like(f"%{search}%"))
    if date_from:
        conditions.append(Recipe.created_at >= date_from)
    if date_to:
        conditions.append(Recipe.created_at <= date_to)
    if min_calories is not None:
        conditions.append(Recipe.calories_per_100g >= min_calories)
    if max_calories is not None:
        conditions.append(Recipe.calories_per_100g <= max_calories)

    if conditions:
        query = query.where(and_(*conditions))

    result = db.execute(query)
    return list(result.scalars().all())

@recipes_router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(recipe_id: int, db: Session = Depends(get_db)) -> RecipeResponse:
    result = db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeFood.food))
        .where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    return _build_recipe_response(recipe)

@recipes_router.post("", response_model=RecipeResponse, status_code=201)
async def create_recipe(
    name: str = Form(...),
    instruction: str = Form(...),
    ingredients: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> RecipeResponse:
    try:
        ingredients_list = json.loads(ingredients)
        data = RecipeCreate(
            name=name,
            instruction=instruction,
            ingredients=ingredients_list,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Неверные данные") from exc

    image_path = await save_image(image)
    recipe = Recipe(name=data.name, instruction=data.instruction, image=image_path)
    _apply_ingredients(db, recipe, data.ingredients)
    db.add(recipe)
    db.flush()

    result = db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeFood.food))
        .where(Recipe.id == recipe.id)
    )
    recipe = result.scalar_one()
    return _build_recipe_response(recipe)

@recipes_router.put("/{recipe_id}", response_model=RecipeResponse)
async def update_recipe(
    recipe_id: int,
    name: str | None = Form(None),
    instruction: str | None = Form(None),
    ingredients: str | None = Form(None),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
) -> RecipeResponse:
    result = db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeFood.food))
        .where(Recipe.id == recipe_id)
    )
    recipe = result.scalar_one_or_none()
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")

    try:
        update_fields: dict = {}
        if name is not None:
            update_fields["name"] = name
        if instruction is not None:
            update_fields["instruction"] = instruction
        if ingredients is not None:
            update_fields["ingredients"] = json.loads(ingredients)
        if update_fields:
            update_data = RecipeUpdate(**update_fields)
            if update_data.name is not None:
                recipe.name = update_data.name
            if update_data.instruction is not None:
                recipe.instruction = update_data.instruction
            if update_data.ingredients is not None:
                _apply_ingredients(db, recipe, update_data.ingredients)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Неверные данные") from exc

    if image and image.filename:
        recipe.image = await save_image(image)

    db.flush()
    result = db.execute(
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeFood.food))
        .where(Recipe.id == recipe.id)
    )
    recipe = result.scalar_one()
    return _build_recipe_response(recipe)

@recipes_router.delete("/{recipe_id}", status_code=204)
async def delete_recipe(recipe_id: int, db: Session = Depends(get_db)) -> None:
    recipe = db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Рецепт не найден")
    db.delete(recipe)

def _build_meal_plan_response(meal_plan: MealPlan) -> MealPlanResponse:
    total_cal = 0.0
    total_prot = 0.0
    total_fats = 0.0
    total_carbs = 0.0
    recipe_items: list[MealPlanRecipeResponse] = []

    for link in meal_plan.recipes:
        recipe = link.recipe
        if not recipe:
            continue
        total_cal += recipe.total_calories
        total_prot += recipe.total_proteins
        total_fats += recipe.total_fats
        total_carbs += recipe.total_carbs
        recipe_items.append(
            MealPlanRecipeResponse(
                id=link.id,
                recipe_id=link.recipe_id,
                recipe_name=recipe.name,
                recipe_image=recipe.image,
                calories=recipe.total_calories,
                proteins=recipe.total_proteins,
                fats=recipe.total_fats,
                carbs=recipe.total_carbs,
            )
        )

    return MealPlanResponse(
        id=meal_plan.id,
        name=meal_plan.name,
        target_calories=meal_plan.target_calories,
        created_at=meal_plan.created_at,
        total_calories=round(total_cal, 2),
        total_proteins=round(total_prot, 2),
        total_fats=round(total_fats, 2),
        total_carbs=round(total_carbs, 2),
        calories_exceeded=total_cal > meal_plan.target_calories,
        recipes=recipe_items,
    )

def _load_meal_plan(db: Session, plan_id: int) -> MealPlan | None:
    result = db.execute(
        select(MealPlan)
        .options(selectinload(MealPlan.recipes).selectinload(MealPlanRecipe.recipe))
        .where(MealPlan.id == plan_id)
    )
    return result.scalar_one_or_none()

@mealplans_router.get("", response_model=list[MealPlanResponse])
async def list_meal_plans(db: Session = Depends(get_db)) -> list[MealPlanResponse]:
    result = db.execute(
        select(MealPlan)
        .options(selectinload(MealPlan.recipes).selectinload(MealPlanRecipe.recipe))
        .order_by(MealPlan.created_at.desc())
    )
    plans = result.scalars().all()
    return [_build_meal_plan_response(p) for p in plans]

@mealplans_router.get("/{plan_id}", response_model=MealPlanResponse)
async def get_meal_plan(plan_id: int, db: Session = Depends(get_db)) -> MealPlanResponse:
    plan = _load_meal_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Рацион не найден")
    return _build_meal_plan_response(plan)

@mealplans_router.post("", response_model=MealPlanResponse, status_code=201)
async def create_meal_plan(
    data: MealPlanCreate, db: Session = Depends(get_db)
) -> MealPlanResponse:
    plan = MealPlan(name=data.name, target_calories=data.target_calories)

    for recipe_id in data.recipe_ids:
        recipe = db.get(Recipe, recipe_id)
        if not recipe:
            raise HTTPException(
                status_code=400,
                detail=f"Рецепт с id={recipe_id} не найден",
            )
        plan.recipes.append(MealPlanRecipe(recipe_id=recipe_id))

    db.add(plan)
    db.flush()
    loaded = _load_meal_plan(db, plan.id)
    assert loaded is not None
    return _build_meal_plan_response(loaded)

@mealplans_router.post("/auto", response_model=MealPlanResponse, status_code=201)
async def create_auto_meal_plan(
    data: AutoMealPlanRequest, db: Session = Depends(get_db)
) -> MealPlanResponse:
    result = db.execute(select(Recipe))
    recipes = list(result.scalars().all())

    if not recipes:
        raise HTTPException(
            status_code=400,
            detail="Нет доступных рецептов для составления рациона",
        )

    items = [
        RecipeCalorieItem(id=r.id, calories=r.total_calories)
        for r in recipes
        if r.total_calories > 0
    ]
    selected_ids = find_best_meal_combination(items, data.target_calories)

    if not selected_ids:
        raise HTTPException(
            status_code=400,
            detail="Не удалось подобрать рацион для указанной калорийности",
        )

    plan = MealPlan(name=data.name, target_calories=data.target_calories)
    for recipe_id in selected_ids:
        plan.recipes.append(MealPlanRecipe(recipe_id=recipe_id))

    db.add(plan)
    db.flush()
    loaded = _load_meal_plan(db, plan.id)
    assert loaded is not None
    return _build_meal_plan_response(loaded)

@mealplans_router.delete("/{plan_id}", status_code=204)
async def delete_meal_plan(plan_id: int, db: Session = Depends(get_db)) -> None:
    plan = db.get(MealPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Рацион не найден")
    db.delete(plan)