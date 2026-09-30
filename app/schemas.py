"""Request/response schemas for the API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class PlanRequestIn(BaseModel):
    household_size: int = Field(2, ge=1, le=12)
    meal_types: list[str] = Field(
        default_factory=lambda: ["lunch", "dinner"],
        description="Which daily meals to plan: breakfast, lunch, dinner",
    )
    cuisines: list[str] | None = None
    diet: str | None = Field(None, description="e.g. vegetarian, vegan, gluten-free")
    anchor_meal_ids: list[str] | None = Field(
        None, description="Recipe ids the family always wants this week"
    )
    pantry_exclude: list[str] | None = None
    budget: float | None = Field(None, ge=0, description="Target weekly spend, USD")
    fulfillment: str = Field("pickup", description="pickup | delivery")
    household_id: int | None = None


class ShoppingItem(BaseModel):
    ingredient: str
    quantity: float
    unit: str
    department: str
    heb_query: str
    brand: str | None
    deep_link: str
    est_cost: float
    coupon: str | None = None


class Meal(BaseModel):
    id: str
    name: str
    cuisine: str
    count: int = 1


class Coupon(BaseModel):
    match: str
    title: str
    deal: str
    savings: float


class PlanOut(BaseModel):
    id: int | None = None
    week: str
    generated_at: str
    household_size: int
    meal_types: list[str]
    fulfillment: str
    meals: list[Meal]
    shopping_list: list[ShoppingItem]
    estimated_total: float
    budget: float | None = None
    under_budget: bool | None = None
    coupons: list[Coupon] = []
    estimated_savings: float = 0.0


class IngredientOut(BaseModel):
    name: str
    quantity: float
    unit: str
    department: str


class RecipeOut(BaseModel):
    id: str
    name: str
    cuisine: str
    diets: list[str]
    core: bool = False
    ingredients: list[IngredientOut] = []


class StepsOut(BaseModel):
    steps: list[str]
    # "cached" | "claude" | "unavailable" | "error"
    source: str
    detail: str | None = None
