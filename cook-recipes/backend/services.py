import io
import uuid
from dataclasses import dataclass
from pathlib import Path
from fastapi import HTTPException, UploadFile
from PIL import Image

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
@dataclass
class NutritionTotals:
    weight: float = 0.0
    calories: float = 0.0
    proteins: float = 0.0
    fats: float = 0.0
    carbs: float = 0.0
@dataclass

class RecipeCalorieItem:
    id: int
    calories: float

def calculate_from_food(
    proteins_per_100g: float,
    fats_per_100g: float,
    carbs_per_100g: float,
    calories_per_100g: float,
    grams: float,
) -> NutritionTotals:
    factor = grams / 100.0
    return NutritionTotals(
        weight=grams,
        calories=round(calories_per_100g * factor, 2),
        proteins=round(proteins_per_100g * factor, 2),
        fats=round(fats_per_100g * factor, 2),
        carbs=round(carbs_per_100g * factor, 2),
    )

def merge_totals(*items: NutritionTotals) -> NutritionTotals:
    return NutritionTotals(
        weight=round(sum(i.weight for i in items), 2),
        calories=round(sum(i.calories for i in items), 2),
        proteins=round(sum(i.proteins for i in items), 2),
        fats=round(sum(i.fats for i in items), 2),
        carbs=round(sum(i.carbs for i in items), 2),
    )

def calories_per_100g(total_calories: float, total_weight: float) -> float:
    if total_weight <= 0:
        return 0.0
    return round((total_calories / total_weight) * 100.0, 2)

def find_best_meal_combination(
    recipes: list[RecipeCalorieItem],
    target_calories: float,
    max_overshoot: float = 100.0,
) -> list[int]:
    if not recipes or target_calories <= 0:
        return []
    max_allowed = target_calories + max_overshoot
    best_ids: list[int] = []
    best_diff = float("inf")
    def search(index: int, current_ids: list[int], current_cal: float) -> None:
        nonlocal best_ids, best_diff
        if current_cal > max_allowed:
            return
        diff = abs(target_calories - current_cal)
        if current_cal > 0 and diff < best_diff:
            best_diff = diff
            best_ids = current_ids.copy()
        if index >= len(recipes):
            return
        search(index + 1, current_ids, current_cal)
        recipe = recipes[index]
        new_cal = current_cal + recipe.calories
        if new_cal <= max_allowed:
            current_ids.append(recipe.id)
            search(index + 1, current_ids, new_cal)
            current_ids.pop()

    search(0, [], 0.0)
    if best_ids:
        return best_ids
    sorted_recipes = sorted(recipes, key=lambda r: r.calories, reverse=True)
    greedy_ids: list[int] = []
    greedy_cal = 0.0
    for recipe in sorted_recipes:
        if greedy_cal + recipe.calories <= max_allowed:
            greedy_ids.append(recipe.id)
            greedy_cal += recipe.calories
            if abs(target_calories - greedy_cal) <= max_overshoot:
                break

    return greedy_ids

async def save_image(file: UploadFile) -> str:
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="Фото не загружено")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Неверный формат фото. Допустимы: jpg, jpeg, png, webp",
        )

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Фото не загружено")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = UPLOAD_DIR / filename
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        image = Image.open(io.BytesIO(content))
        image.save(filepath)
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Неверные данные: файл не является изображением",
        ) from exc

    return f"uploads/{filename}"