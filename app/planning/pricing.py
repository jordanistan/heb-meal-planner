"""Approximate H-E-B prices for budget estimates.

These are rough per-package figures, NOT live prices — real pricing needs a
catalog/partner feed (see the architecture doc). Each shopping-list line is
estimated at a typical package price; the total is a ballpark "cart" cost used
for the budget feature. Everything is clearly labeled "estimated" in the UI.
"""
from __future__ import annotations

DEFAULT_COST = 2.5

# Ingredient (lowercase substring) -> approximate package/shop price in USD.
INGREDIENT_COST: dict[str, float] = {
    # Proteins
    "skirt steak": 12.0, "flank steak": 12.0, "chicken breast": 7.0,
    "chicken thighs": 6.0, "pork shoulder": 10.0, "ground beef": 7.0,
    "ground turkey": 6.0, "ground pork": 5.0, "italian sausage": 6.0,
    "andouille": 6.0, "salmon": 14.0, "shrimp": 11.0, "bacon": 6.0,
    "eggs": 3.0, "paneer": 5.0,
    # Dairy
    "feta": 5.0, "cheddar": 4.0, "mozzarella": 4.0, "parmesan": 7.0,
    "ricotta": 4.0, "sour cream": 2.5, "buttermilk": 2.5, "greek yogurt": 3.5,
    # Pantry / grains / sauces
    "corn tortillas": 2.5, "flour tortillas": 3.0, "pita": 3.0, "rice": 3.0, "spaghetti": 1.5,
    "lasagna noodles": 2.5, "pasta": 1.5, "orzo": 2.0, "couscous": 3.5,
    "rice noodles": 2.5, "lo mein noodles": 2.5, "elbow macaroni": 1.5,
    "marinara": 3.0, "pesto": 4.5, "pizza dough": 3.5, "soy sauce": 3.0,
    "sesame oil": 4.5, "gochujang": 5.0, "coconut milk": 2.0, "curry paste": 4.0,
    "lentils": 2.0, "kidney beans": 1.0, "black beans": 1.0, "pinto beans": 1.0,
    "chickpeas": 1.0, "hominy": 1.5, "canned tomatoes": 1.5, "salsa verde": 3.0,
    "bbq sauce": 3.0, "peanuts": 3.5, "grits": 3.0, "burger buns": 3.5,
    "tahini": 6.0, "farro": 4.0, "bulgur": 3.0, "kalamata olives": 4.0,
    # Produce
    "onion": 1.0, "garlic": 0.6, "lime": 1.0, "lemon": 1.0, "cilantro": 0.8,
    "avocado": 2.0, "poblano": 1.0, "serrano": 0.6, "jalapeno": 0.6,
    "bell pepper": 1.5, "cucumber": 1.0, "tomato": 1.5, "potato": 4.0,
    "spinach": 3.5, "cauliflower": 3.5, "broccoli": 2.5, "zucchini": 1.2,
    "carrot": 2.0, "cabbage": 2.5, "tomatillo": 1.5, "ginger": 1.0,
    "green onion": 1.0, "basil": 2.5, "mushroom": 3.0,
}


def estimate(ingredient: str) -> float:
    """Approximate price for one shopping-list line of this ingredient."""
    key = ingredient.lower().strip()
    for pattern in sorted(INGREDIENT_COST, key=len, reverse=True):
        if pattern in key:
            return INGREDIENT_COST[pattern]
    return DEFAULT_COST
