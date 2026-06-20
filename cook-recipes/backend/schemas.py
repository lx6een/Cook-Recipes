from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class FoodBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    proteins: float = Field(..., ge=0)
    fats: float = Field(..., ge=0)
    carbs: float = Field(..., ge=0)
    calories: float = Field(..., ge=0)

class FoodCreate(FoodBase):
    pass

class FoodUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    proteins: float | None = Field(None, ge=0)
    fats: float | None = Field(None, ge=0)
    carbs: float | None = Field(None, ge=0)
    calories: float | None = Field(None, ge=0)

class FoodResponse(FoodBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image: str
    created_at: datetime

class RecipeIngredientInput(BaseModel):
    food_id: int = Field(..., gt=0)
    grams: float = Field(..., gt=0)

class RecipeIngredientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    food_id: int
    grams: float
    food_name: str | None = None
    food_image: str | None = None
    proteins: float | None = None
    fats: float | None = None
    carbs: float | None = None
    calories: float | None = None

class RecipeBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    instruction: str = Field(..., min_length=1)

class RecipeCreate(RecipeBase):
    ingredients: list[RecipeIngredientInput] = Field(..., min_length=1)

class RecipeUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    instruction: str | None = Field(None, min_length=1)
    ingredients: list[RecipeIngredientInput] | None = Field(None, min_length=1)

class RecipeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    image: str
    calories_per_100g: float
    created_at: datetime

class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    image: str
    instruction: str
    calories_per_100g: float
    total_weight: float
    total_calories: float
    total_proteins: float
    total_fats: float
    total_carbs: float
    created_at: datetime
    ingredients: list[RecipeIngredientResponse] = []

class MealPlanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target_calories: float = Field(..., gt=0)
    recipe_ids: list[int] = Field(..., min_length=1)

class AutoMealPlanRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target_calories: float = Field(..., gt=0)

class MealPlanRecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    recipe_id: int
    recipe_name: str | None = None
    recipe_image: str | None = None
    calories: float | None = None
    proteins: float | None = None
    fats: float | None = None
    carbs: float | None = None

class MealPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    target_calories: float
    created_at: datetime
    total_calories: float = 0.0
    total_proteins: float = 0.0
    total_fats: float = 0.0
    total_carbs: float = 0.0
    calories_exceeded: bool = False
    recipes: list[MealPlanRecipeResponse] = []