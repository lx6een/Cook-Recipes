import sys
from pathlib import Path
from PIL import Image, ImageDraw
from sqlalchemy import select
sys.path.insert(0, str(Path(__file__).parent))
from database import SessionLocal
from models import Food, MealPlan, MealPlanRecipe, Recipe, RecipeFood
from services import UPLOAD_DIR, calculate_from_food, calories_per_100g, merge_totals

COLORS = [
    (231, 76, 60),
    (46, 204, 113),
    (52, 152, 219),
    (155, 89, 182),
    (241, 196, 15),
    (230, 126, 34),
]
def _create_placeholder_image(name: str, color_index: int) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    color = COLORS[color_index % len(COLORS)]
    img = Image.new("RGB", (400, 300), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 380, 280], outline=(255, 255, 255), width=3)
    draw.text((40, 130), name[:20], fill=(255, 255, 255))

    filename = f"seed_{name.lower().replace(' ', '_')}.png"
    filepath = UPLOAD_DIR / filename
    img.save(filepath, format="PNG")
    return f"uploads/{filename}"
def seed() -> None:
    with SessionLocal() as session:
        existing = session.scalar(select(Food).limit(1))
        if existing:
            print("База уже содержит данные — пропуск seed.")
            return

        foods_data = [
            ("Куриная грудка", 23.1, 1.2, 0.0, 110),
            ("Рис белый", 2.7, 0.3, 28.0, 130),
            ("Брокколи", 2.8, 0.4, 7.0, 34),
            ("Яйцо куриное", 12.7, 11.5, 0.7, 157),
            ("Овсянка", 12.3, 6.1, 59.5, 342),
            ("Творог 5%", 17.2, 5.0, 1.8, 121),
            ("Банан", 1.5, 0.2, 21.8, 89),
            ("Лосось", 20.0, 13.0, 0.0, 208),
        ]
        foods: list[Food] = []
        for i, (name, p, f, c, kcal) in enumerate(foods_data):
            food = Food(
                name=name,
                image=_create_placeholder_image(name, i),
                proteins=p,
                fats=f,
                carbs=c,
                calories=kcal,
            )
            session.add(food)
            foods.append(food)
        session.flush()
        recipes_spec = [
            (
                "Омлет с брокколи",
                "Взбейте яйца, добавьте нарезанную брокколи. Жарьте на сковороде 5 минут.",
                [(foods[3], 120), (foods[2], 80)],
            ),
            (
                "Куриный боул с рисом",
                "Отварите рис. Обжарьте куриную грудку. Подавайте вместе.",
                [(foods[0], 150), (foods[1], 200)],
            ),
            (
                "Овсянка с бананом",
                "Залейте овсянку кипятком, добавьте нарезанный банан.",
                [(foods[4], 50), (foods[6], 100)],
            ),
            (
                "Творожный салат",
                "Смешайте творог с брокколи и курицей.",
                [(foods[5], 150), (foods[2], 60), (foods[0], 100)],
            ),
            (
                "Лосось с рисом",
                "Запеките лосось 20 минут при 180°C. Подавайте с отварным рисом.",
                [(foods[7], 180), (foods[1], 150)],
            ),
        ]
        for i, (name, instruction, ingredients) in enumerate(recipes_spec):
            totals_list = []
            recipe = Recipe(
                name=name,
                image=_create_placeholder_image(name, i + 3),
                instruction=instruction,
            )
            for food, grams in ingredients:
                totals_list.append(
                    calculate_from_food(
                        food.proteins, food.fats, food.carbs, food.calories, grams
                    )
                )
                recipe.ingredients.append(RecipeFood(food_id=food.id, grams=grams))
            merged = merge_totals(*totals_list)
            recipe.total_weight = merged.weight
            recipe.total_calories = merged.calories
            recipe.total_proteins = merged.proteins
            recipe.total_fats = merged.fats
            recipe.total_carbs = merged.carbs
            recipe.calories_per_100g = calories_per_100g(merged.calories, merged.weight)
            session.add(recipe)

        session.flush()
        result = session.execute(select(Recipe))
        all_recipes = list(result.scalars().all())
        manual_plan = MealPlan(name="Рацион на 1800 ккал", target_calories=1800)
        for recipe in all_recipes[:3]:
            manual_plan.recipes.append(MealPlanRecipe(recipe_id=recipe.id))
        session.add(manual_plan)
        session.commit()
        print(f"Добавлено: {len(foods)} продуктов, {len(recipes_spec)} рецептов, 1 рацион.")

if __name__ == "__main__":
    seed()