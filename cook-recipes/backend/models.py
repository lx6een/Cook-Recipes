from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Food(Base):
    __tablename__ = "foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[str] = mapped_column(String(512), nullable=False)
    proteins: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    fats: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    carbs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    calories: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    recipe_foods: Mapped[list["RecipeFood"]] = relationship(
        "RecipeFood", back_populates="food", cascade="all, delete-orphan"
    )

class Recipe(Base):
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[str] = mapped_column(String(512), nullable=False)
    instruction: Mapped[str] = mapped_column(Text, nullable=False, default="")
    calories_per_100g: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_calories: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_proteins: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_fats: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_carbs: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    ingredients: Mapped[list["RecipeFood"]] = relationship(
        "RecipeFood",
        back_populates="recipe",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    meal_plan_recipes: Mapped[list["MealPlanRecipe"]] = relationship(
        "MealPlanRecipe", back_populates="recipe", cascade="all, delete-orphan"
    )

class RecipeFood(Base):
    __tablename__ = "recipe_foods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    food_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("foods.id", ondelete="CASCADE"), nullable=False
    )
    grams: Mapped[float] = mapped_column(Float, nullable=False)

    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="ingredients")
    food: Mapped["Food"] = relationship("Food", back_populates="recipe_foods")

class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_calories: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    recipes: Mapped[list["MealPlanRecipe"]] = relationship(
        "MealPlanRecipe",
        back_populates="meal_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

class MealPlanRecipe(Base):
    __tablename__ = "meal_plan_recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    meal_plan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False
    )
    recipe_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False
    )
    meal_plan: Mapped["MealPlan"] = relationship("MealPlan", back_populates="recipes")
    recipe: Mapped["Recipe"] = relationship("Recipe", back_populates="meal_plan_recipes")