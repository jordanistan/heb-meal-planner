"""Build a weekly plan: choose meals, consolidate ingredients, map to H-E-B.

The plan covers a 7-day week for the chosen meal types (lunch + dinner by
default, breakfast optional) — we don't ask for a raw meal count. An optional
budget caps how many meals are included. Costs are rough estimates (see
pricing.py); the "buy" step is always a heb.com deep link.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

from . import coupons, mapping, pricing
from .recipes import DEFAULT_PANTRY, RECIPES_BY_ID, Recipe, filter_recipes

WEEK_DAYS = 7
MAX_MEALS = 21  # cap so 3 meal types * 7 days stays sane


@dataclass
class PlanRequest:
    household_size: int = 2
    meal_types: list[str] = field(default_factory=lambda: ["lunch", "dinner"])
    cuisines: list[str] | None = None
    diet: str | None = None
    anchor_meal_ids: list[str] | None = None
    pantry_exclude: list[str] | None = None
    budget: float | None = None


def _scale(quantity: float, base_servings: int, household_size: int) -> float:
    factor = household_size / base_servings if base_servings else 1
    scaled = quantity * factor
    return float(math.ceil(scaled)) if quantity == int(quantity) else round(scaled, 1)


def _recipe_cost(recipe: Recipe) -> float:
    """Rough standalone cost of a recipe (sum of its ingredient line prices)."""
    return round(
        sum(
            pricing.estimate(i.name)
            for i in recipe.ingredients
            if not i.pantry and i.name.lower() not in DEFAULT_PANTRY
        ),
        2,
    )


def _target_count(req: PlanRequest) -> int:
    types = [t for t in (req.meal_types or []) if t] or ["dinner"]
    return min(MAX_MEALS, WEEK_DAYS * len(types))


def _choose_meals(req: PlanRequest) -> list[Recipe]:
    """Anchors first, then fill toward the weekly target from matching recipes,
    repeating recipes if needed. A budget stops filling once it's reached."""
    target = _target_count(req)
    budget = req.budget if req.budget and req.budget > 0 else None
    chosen: list[Recipe] = []
    running = 0.0

    # Anchor meals are always honored (even if they exceed the budget).
    for mid in req.anchor_meal_ids or []:
        recipe = RECIPES_BY_ID.get(mid)
        if recipe:
            chosen.append(recipe)
            running += _recipe_cost(recipe)

    pool = filter_recipes(req.cuisines, req.diet)
    if not pool:
        return chosen[:target]

    i = 0
    while len(chosen) < target:
        recipe = pool[i % len(pool)]
        i += 1
        cost = _recipe_cost(recipe)
        if budget is not None and running + cost > budget and chosen:
            break  # next meal would blow the budget
        chosen.append(recipe)
        running += cost
        if i > target * 4:  # safety against a tiny/empty pool
            break

    return chosen[:target]


def generate_plan(req: PlanRequest) -> dict:
    meals = _choose_meals(req)
    pantry = DEFAULT_PANTRY | {p.lower() for p in (req.pantry_exclude or [])}

    # Consolidate: (ingredient, unit) -> summed quantity + metadata.
    agg: dict[tuple[str, str], dict] = {}
    for recipe in meals:
        for ing in recipe.ingredients:
            if ing.pantry or ing.name.lower() in pantry:
                continue
            qty = _scale(ing.quantity, recipe.base_servings, req.household_size)
            key = (ing.name, ing.unit)
            if key in agg:
                agg[key]["quantity"] += qty
            else:
                agg[key] = {
                    "ingredient": ing.name,
                    "quantity": qty,
                    "unit": ing.unit,
                    "department": ing.department,
                    "cuisine": recipe.cuisine,
                }

    shopping_list = []
    matched_coupons: dict[str, dict] = {}
    estimated_total = 0.0
    for item in agg.values():
        query = mapping.query_for(item["ingredient"], item["cuisine"])
        cost = pricing.estimate(item["ingredient"])
        estimated_total += cost
        coupon = coupons.match_for(item["ingredient"], query)
        if coupon:
            matched_coupons[coupon["match"]] = coupon
        shopping_list.append(
            {
                "ingredient": item["ingredient"],
                "quantity": round(item["quantity"], 1),
                "unit": item["unit"],
                "department": item["department"],
                "heb_query": query,
                "brand": mapping.brand_of(query),
                "deep_link": mapping.deep_link(query),
                "est_cost": round(cost, 2),
                "coupon": coupon["deal"] if coupon else None,
            }
        )
    shopping_list.sort(key=lambda x: (x["department"], x["ingredient"]))

    # Aggregate meals with counts (repeats show as "x2").
    meal_counts: dict[str, dict] = {}
    for r in meals:
        if r.id in meal_counts:
            meal_counts[r.id]["count"] += 1
        else:
            meal_counts[r.id] = {"id": r.id, "name": r.name, "cuisine": r.cuisine, "count": 1}

    coupon_list = list(matched_coupons.values())
    savings = round(sum(c["savings"] for c in coupon_list), 2)
    estimated_total = round(estimated_total, 2)
    budget = req.budget if req.budget and req.budget > 0 else None

    now = datetime.now(timezone.utc)
    return {
        "week": now.strftime("%G-W%V"),
        "generated_at": now.isoformat(timespec="seconds"),
        "household_size": req.household_size,
        "meal_types": [t for t in (req.meal_types or []) if t] or ["dinner"],
        "meals": list(meal_counts.values()),
        "shopping_list": shopping_list,
        "estimated_total": estimated_total,
        "budget": budget,
        "under_budget": (estimated_total <= budget) if budget is not None else None,
        "coupons": coupon_list,
        "estimated_savings": savings,
    }
