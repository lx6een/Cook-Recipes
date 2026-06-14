from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select
from database import SessionLocal
from models import Food, MealPlan, Recipe
from routers import foods_router, mealplans_router, recipes_router

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"

app = FastAPI(
    title="Cook Recipes",
    description="Веб-приложение для управления продуктами, рецептами и рационом",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(foods_router)
app.include_router(recipes_router)
app.include_router(mealplans_router)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"detail": "Неверные данные", "errors": exc.errors()},
    )

@app.get("/api/stats")
async def get_stats() -> dict:
    with SessionLocal() as session:
        foods_count = session.scalar(select(func.count()).select_from(Food))
        recipes_count = session.scalar(select(func.count()).select_from(Recipe))
        plans_count = session.scalar(select(func.count()).select_from(MealPlan))
    return {
        "foods": foods_count or 0,
        "recipes": recipes_count or 0,
        "meal_plans": plans_count or 0,
    }

def _serve_page(filename: str) -> FileResponse:
    path = FRONTEND_DIR / filename
    if not path.exists():
        return FileResponse(FRONTEND_DIR / "index.html")
    return FileResponse(path)

@app.get("/")
async def index() -> FileResponse:
    return _serve_page("index.html")

@app.get("/foods")
async def foods_page() -> FileResponse:
    return _serve_page("foods.html")

@app.get("/recipes")
async def recipes_page() -> FileResponse:
    return _serve_page("recipes.html")

@app.get("/recipes/{recipe_id}")
async def recipe_detail_page(recipe_id: int) -> FileResponse:
    return _serve_page("recipe.html")

@app.get("/mealplans")
async def mealplans_page() -> FileResponse:
    return _serve_page("mealplans.html")