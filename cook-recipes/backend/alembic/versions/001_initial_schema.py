from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "foods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("image", sa.String(length=512), nullable=False),
        sa.Column("proteins", sa.Float(), nullable=False),
        sa.Column("fats", sa.Float(), nullable=False),
        sa.Column("carbs", sa.Float(), nullable=False),
        sa.Column("calories", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recipes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("image", sa.String(length=512), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("calories_per_100g", sa.Float(), nullable=False),
        sa.Column("total_weight", sa.Float(), nullable=False),
        sa.Column("total_calories", sa.Float(), nullable=False),
        sa.Column("total_proteins", sa.Float(), nullable=False),
        sa.Column("total_fats", sa.Float(), nullable=False),
        sa.Column("total_carbs", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "meal_plans",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("target_calories", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "recipe_foods",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.Column("food_id", sa.Integer(), nullable=False),
        sa.Column("grams", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["food_id"], ["foods.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "meal_plan_recipes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("meal_plan_id", sa.Integer(), nullable=False),
        sa.Column("recipe_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["meal_plan_id"], ["meal_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("meal_plan_recipes")
    op.drop_table("recipe_foods")
    op.drop_table("meal_plans")
    op.drop_table("recipes")
    op.drop_table("foods")
