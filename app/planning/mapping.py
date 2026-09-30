"""Translate culinary ingredients into H-E-B search queries + brands.

This is the defensible core of the product: it favors H-E-B private labels
(Mi Tienda for Mexican/Tex-Mex, Central Market / H-E-B Organics for
Mediterranean) and runs entirely on our own data — no scraping. It also builds
the heb.com deep link the user's own browser follows (the v1 "buy" step).
"""
from __future__ import annotations

import urllib.parse

from ..config import settings

# Ingredient (lowercase substring) -> optimal H-E-B search query.
INGREDIENT_LOOKUP: dict[str, str] = {
    # Mexican / Tex-Mex
    "fajita beef": "Mi Tienda Seasoned Beef Fajitas",
    "arrachera": "Mi Tienda Seasoned Beef Fajitas Inside Skirt",
    "skirt steak": "beef skirt steak",
    "flank steak": "beef flank steak",
    "queso fresco": "Mi Tienda Queso Fresco",
    "oaxaca cheese": "Mi Tienda Queso Oaxaca",
    "cotija": "Mi Tienda Cotija Grated Cheese",
    "corn tortillas": "Mi Tienda Ready to Cook Corn Tortillas",
    "flour tortillas": "H-E-B Bakery Fresh Butter Tortillas",
    "chorizo": "Mi Tienda Mexican Pork Chorizo",
    "poblano": "Fresh Poblano Peppers",
    "serrano": "Fresh Serrano Peppers",
    "jalapeno": "Fresh Jalapeno Peppers",
    "mexican oregano": "Mi Tienda Mexican Oregano",
    "cilantro": "Fresh Cilantro Bunch",
    "lime": "Fresh Limes",
    "avocado": "Fresh Hass Avocado",
    "black beans": "H-E-B Seasoned Black Beans with Jalapeno",
    "pinto beans": "H-E-B Charro Beans with Bacon",
    # Mediterranean
    "olive oil": "Central Market Extra Virgin Olive Oil PDO Kalamata",
    "feta": "Central Market Greek Feta Cheese in Brine",
    "greek yogurt": "Central Market Organic Plain Greek Whole Milk Yogurt",
    "pita": "H-E-B Bakery Pita Bread",
    "farro": "Central Market Organic Farro",
    "bulgur": "Central Market Organic Bulgur Wheat",
    "tahini": "Central Market Organic Sesame Tahini",
    "chickpeas": "H-E-B Organics Garbanzo Beans",
    "canned tomatoes": "H-E-B Organics Diced Tomatoes",
    "kalamata olives": "Central Market Pitted Kalamata Olives",
    "capers": "Central Market Non-Pareil Capers in Brine",
    "cucumber": "Fresh Cucumber",
    "lemon": "Fresh Lemons",
    # Shared staples
    "chicken breast": "H-E-B Boneless Skinless Chicken Breasts",
    "ground beef": "H-E-B Ground Beef",
    "rice": "H-E-B Long Grain White Rice",
    "onion": "Fresh Yellow Onion",
    "garlic": "Fresh Garlic",
    # Proteins
    "chicken thighs": "H-E-B Boneless Skinless Chicken Thighs",
    "pork shoulder": "H-E-B Boneless Pork Shoulder Roast",
    "ground turkey": "H-E-B Ground Turkey",
    "ground pork": "H-E-B Ground Pork",
    "italian sausage": "H-E-B Italian Sausage",
    "andouille": "H-E-B Andouille Sausage",
    "salmon": "H-E-B Responsibly Raised Atlantic Salmon Fillet",
    "shrimp": "H-E-B Raw Peeled Shrimp",
    "bacon": "H-E-B Fully Cooked Bacon",
    "eggs": "H-E-B Grade A Large Eggs",
    "paneer": "H-E-B Paneer",
    # Dairy / cheese
    "sour cream": "H-E-B Sour Cream",
    "cheddar": "H-E-B Shredded Sharp Cheddar Cheese",
    "mozzarella": "H-E-B Shredded Mozzarella Cheese",
    "parmesan": "Central Market Parmigiano Reggiano",
    "ricotta": "H-E-B Whole Milk Ricotta Cheese",
    "buttermilk": "H-E-B Buttermilk",
    # Pantry / grains / sauces
    "spaghetti": "H-E-B Spaghetti",
    "lasagna noodles": "H-E-B Lasagna",
    "pasta": "H-E-B Penne Pasta",
    "orzo": "H-E-B Orzo Pasta",
    "couscous": "Central Market Couscous",
    "rice noodles": "H-E-B Rice Noodles",
    "lo mein noodles": "H-E-B Lo Mein Noodles",
    "elbow macaroni": "H-E-B Elbow Macaroni",
    "marinara": "Central Market Marinara Sauce",
    "pesto": "Central Market Basil Pesto",
    "pizza dough": "H-E-B Bakery Fresh Pizza Dough",
    "soy sauce": "H-E-B Soy Sauce",
    "sesame oil": "H-E-B Toasted Sesame Oil",
    "gochujang": "H-E-B Gochujang Sauce",
    "coconut milk": "H-E-B Coconut Milk",
    "curry paste": "H-E-B Red Curry Paste",
    "lentils": "H-E-B Dry Lentils",
    "kidney beans": "H-E-B Dark Red Kidney Beans",
    "hominy": "H-E-B Golden Hominy",
    "salsa verde": "H-E-B Salsa Verde",
    "peanuts": "H-E-B Dry Roasted Peanuts",
    "grits": "H-E-B Stone Ground Grits",
    "bbq sauce": "H-E-B Original BBQ Sauce",
    "burger buns": "H-E-B Bakery Hamburger Buns",
    # Produce
    "bell pepper": "Fresh Bell Pepper",
    "green onion": "Fresh Green Onions",
    "ginger": "Fresh Ginger Root",
    "basil": "Fresh Basil",
    "spinach": "Fresh Baby Spinach",
    "cauliflower": "Fresh Cauliflower",
    "broccoli": "Fresh Broccoli Crowns",
    "zucchini": "Fresh Zucchini",
    "carrot": "Fresh Carrots",
    "cabbage": "Fresh Green Cabbage",
    "tomatillo": "Fresh Tomatillos",
    "tomato": "Fresh Roma Tomatoes",
    "potato": "Fresh Russet Potatoes",
    "mushroom": "Fresh Sliced Mushrooms",
}

# Longest-first so multi-word private labels win over the bare "H-E-B" prefix.
KNOWN_BRANDS = [
    "H-E-B Organics",
    "Hill Country Fare",
    "Central Market",
    "Mi Tienda",
    "H-E-B",
]

_CUISINE_BRAND = {
    "mexican": ("Mi Tienda", "H-E-B"),
    "tex-mex": ("Mi Tienda", "H-E-B"),
    "mediterranean": ("Central Market", "H-E-B Organics"),
}


def query_for(ingredient: str, cuisine: str | None = None) -> str:
    """Best H-E-B search query for an ingredient, favoring private labels."""
    key = ingredient.lower().strip()
    # Longest patterns first so specific names ("green onion", "canned
    # tomatoes") win over generic substrings ("onion", "tomato").
    for pattern in sorted(INGREDIENT_LOOKUP, key=len, reverse=True):
        if pattern in key:
            return INGREDIENT_LOOKUP[pattern]
    if cuisine and cuisine.lower() in _CUISINE_BRAND:
        primary, _ = _CUISINE_BRAND[cuisine.lower()]
        return f"{primary} {ingredient}"
    return f"H-E-B {ingredient}"


def brand_of(query: str) -> str | None:
    """The H-E-B brand a query targets, if any."""
    lower = query.lower()
    for brand in KNOWN_BRANDS:
        if brand.lower() in lower:
            return brand
    return None


def deep_link(query: str) -> str:
    """heb.com search URL the user's browser opens for this query."""
    return settings.heb_search_url.format(query=urllib.parse.quote_plus(query))
