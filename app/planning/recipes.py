"""Seed recipe library for v1 (deterministic, no LLM required).

Each recipe lists ingredients with a base quantity per `base_servings`. The
planner scales these to the household size and consolidates across meals. A
later version can generate recipes with Claude; this library keeps v1 working
offline and gives the LLM concrete examples to imitate.

Ingredients are written compactly as (name, quantity, unit, department) tuples
via the `_r` builder.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Pantry staples excluded from shopping lists by default.
DEFAULT_PANTRY = {"salt", "black pepper", "water", "olive oil spray"}

# Store departments used for grouping the shopping list.
PRODUCE = "Produce"
MEAT = "Meat/Seafood"
DAIRY = "Deli/Dairy"
PANTRY = "Pantry/Grains"
BAKERY = "Bakery"
FROZEN = "Frozen"


@dataclass(frozen=True)
class Ingredient:
    name: str
    quantity: float
    unit: str
    department: str
    pantry: bool = False


@dataclass(frozen=True)
class Recipe:
    id: str
    name: str
    cuisine: str
    diets: tuple[str, ...] = ()
    base_servings: int = 4
    ingredients: tuple[Ingredient, ...] = field(default_factory=tuple)


def _r(rid, name, cuisine, diets, *ings) -> Recipe:
    return Recipe(
        id=rid,
        name=name,
        cuisine=cuisine,
        diets=tuple(diets),
        ingredients=tuple(Ingredient(*i) for i in ings),
    )


RECIPES: tuple[Recipe, ...] = (
    # --- Tex-Mex / Mexican (original ids preserved) ---
    _r("beef-fajitas", "Skirt Steak Fajitas", "tex-mex", ("gluten-free",),
       ("skirt steak", 1.5, "lb", MEAT), ("poblano", 2, "each", PRODUCE),
       ("onion", 1, "each", PRODUCE), ("lime", 2, "each", PRODUCE),
       ("corn tortillas", 12, "each", PANTRY), ("cilantro", 1, "bunch", PRODUCE)),
    _r("chicken-tacos", "Cilantro-Lime Chicken Tacos", "mexican", ("gluten-free",),
       ("chicken breast", 1.5, "lb", MEAT), ("lime", 3, "each", PRODUCE),
       ("cilantro", 1, "bunch", PRODUCE), ("corn tortillas", 12, "each", PANTRY),
       ("avocado", 2, "each", PRODUCE), ("serrano", 2, "each", PRODUCE)),
    _r("charro-beans-bowl", "Charro Beans & Rice Bowl", "tex-mex", ("vegetarian",),
       ("pinto beans", 2, "can", PANTRY), ("rice", 2, "cup", PANTRY),
       ("onion", 1, "each", PRODUCE), ("jalapeno", 2, "each", PRODUCE),
       ("cilantro", 1, "bunch", PRODUCE)),
    _r("carnitas-tacos", "Pork Carnitas Tacos", "mexican", ("gluten-free",),
       ("pork shoulder", 2, "lb", MEAT), ("corn tortillas", 12, "each", PANTRY),
       ("onion", 1, "each", PRODUCE), ("cilantro", 1, "bunch", PRODUCE),
       ("lime", 3, "each", PRODUCE)),
    _r("enchiladas-verdes", "Chicken Enchiladas Verdes", "mexican", (),
       ("chicken breast", 1.5, "lb", MEAT), ("salsa verde", 1, "jar", PANTRY),
       ("corn tortillas", 12, "each", PANTRY), ("cheddar", 8, "oz", DAIRY),
       ("sour cream", 8, "oz", DAIRY)),
    _r("shrimp-tacos", "Baja Shrimp Tacos", "mexican", ("gluten-free",),
       ("shrimp", 1.5, "lb", MEAT), ("cabbage", 0.5, "head", PRODUCE),
       ("lime", 3, "each", PRODUCE), ("corn tortillas", 12, "each", PANTRY),
       ("cilantro", 1, "bunch", PRODUCE)),
    _r("beef-picadillo", "Beef Picadillo", "tex-mex", ("gluten-free",),
       ("ground beef", 1.5, "lb", MEAT), ("potato", 2, "each", PRODUCE),
       ("tomato", 3, "each", PRODUCE), ("onion", 1, "each", PRODUCE),
       ("rice", 2, "cup", PANTRY)),
    _r("chicken-enchiladas", "Tex-Mex Chicken Enchiladas", "tex-mex", (),
       ("chicken breast", 1.5, "lb", MEAT), ("corn tortillas", 12, "each", PANTRY),
       ("cheddar", 8, "oz", DAIRY), ("onion", 1, "each", PRODUCE),
       ("canned tomatoes", 1, "can", PANTRY)),
    _r("queso-chicken-bowl", "Queso Chicken Rice Bowl", "tex-mex", ("gluten-free",),
       ("chicken breast", 1.5, "lb", MEAT), ("rice", 2, "cup", PANTRY),
       ("black beans", 1, "can", PANTRY), ("cheddar", 6, "oz", DAIRY),
       ("jalapeno", 2, "each", PRODUCE)),
    _r("huevos-rancheros", "Huevos Rancheros", "mexican", ("vegetarian", "gluten-free"),
       ("eggs", 8, "each", DAIRY), ("corn tortillas", 8, "each", PANTRY),
       ("black beans", 1, "can", PANTRY), ("salsa verde", 1, "jar", PANTRY),
       ("avocado", 2, "each", PRODUCE)),
    _r("pozole-rojo", "Pozole Rojo", "mexican", ("gluten-free",),
       ("pork shoulder", 2, "lb", MEAT), ("hominy", 2, "can", PANTRY),
       ("onion", 1, "each", PRODUCE), ("cilantro", 1, "bunch", PRODUCE),
       ("cabbage", 0.5, "head", PRODUCE)),

    # --- Mediterranean (original ids preserved) ---
    _r("greek-bowls", "Greek Chicken & Farro Bowls", "mediterranean", (),
       ("chicken breast", 1.5, "lb", MEAT), ("farro", 1.5, "cup", PANTRY),
       ("feta", 6, "oz", DAIRY), ("cucumber", 1, "each", PRODUCE),
       ("kalamata olives", 1, "cup", PANTRY), ("lemon", 2, "each", PRODUCE)),
    _r("chickpea-stew", "Mediterranean Chickpea Stew", "mediterranean",
       ("vegetarian", "vegan"),
       ("chickpeas", 2, "can", PANTRY), ("canned tomatoes", 1, "can", PANTRY),
       ("onion", 1, "each", PRODUCE), ("garlic", 4, "clove", PRODUCE),
       ("bulgur", 1, "cup", PANTRY)),
    _r("tahini-bowls", "Roasted Veg & Tahini Bowls", "mediterranean",
       ("vegetarian", "vegan", "gluten-free"),
       ("chickpeas", 1, "can", PANTRY), ("tahini", 0.5, "cup", PANTRY),
       ("lemon", 1, "each", PRODUCE), ("cucumber", 1, "each", PRODUCE),
       ("garlic", 2, "clove", PRODUCE)),
    _r("shakshuka", "Shakshuka", "mediterranean", ("vegetarian", "gluten-free"),
       ("eggs", 6, "each", DAIRY), ("canned tomatoes", 1, "can", PANTRY),
       ("bell pepper", 1, "each", PRODUCE), ("onion", 1, "each", PRODUCE),
       ("feta", 4, "oz", DAIRY)),
    _r("lemon-chicken-orzo", "Lemon Chicken Orzo", "mediterranean", (),
       ("chicken thighs", 1.5, "lb", MEAT), ("orzo", 2, "cup", PANTRY),
       ("lemon", 2, "each", PRODUCE), ("spinach", 5, "oz", PRODUCE),
       ("garlic", 3, "clove", PRODUCE)),
    _r("falafel-bowls", "Falafel Bowls", "mediterranean", ("vegetarian", "vegan"),
       ("chickpeas", 2, "can", PANTRY), ("tahini", 0.5, "cup", PANTRY),
       ("cucumber", 1, "each", PRODUCE), ("tomato", 2, "each", PRODUCE),
       ("bulgur", 1, "cup", PANTRY)),
    _r("salmon-couscous", "Herbed Salmon & Couscous", "mediterranean", (),
       ("salmon", 1.5, "lb", MEAT), ("couscous", 1.5, "cup", PANTRY),
       ("lemon", 2, "each", PRODUCE), ("zucchini", 2, "each", PRODUCE)),
    _r("stuffed-peppers", "Mediterranean Stuffed Peppers", "mediterranean",
       ("vegetarian", "gluten-free"),
       ("bell pepper", 4, "each", PRODUCE), ("rice", 1.5, "cup", PANTRY),
       ("feta", 4, "oz", DAIRY), ("canned tomatoes", 1, "can", PANTRY),
       ("onion", 1, "each", PRODUCE)),
    _r("chicken-shawarma-bowls", "Chicken Shawarma Bowls", "mediterranean",
       ("gluten-free",),
       ("chicken thighs", 1.5, "lb", MEAT), ("garlic", 4, "clove", PRODUCE),
       ("lemon", 2, "each", PRODUCE), ("cucumber", 1, "each", PRODUCE),
       ("greek yogurt", 1, "cup", DAIRY), ("bulgur", 1, "cup", PANTRY)),
    _r("chicken-souvlaki", "Chicken Souvlaki", "mediterranean", ("gluten-free",),
       ("chicken breast", 1.5, "lb", MEAT), ("lemon", 2, "each", PRODUCE),
       ("garlic", 3, "clove", PRODUCE), ("bell pepper", 2, "each", PRODUCE),
       ("onion", 1, "each", PRODUCE), ("greek yogurt", 1, "cup", DAIRY)),
    _r("avgolemono-soup", "Greek Lemon Chicken Soup", "mediterranean", (),
       ("chicken breast", 1, "lb", MEAT), ("lemon", 3, "each", PRODUCE),
       ("orzo", 1, "cup", PANTRY), ("eggs", 3, "each", DAIRY),
       ("spinach", 5, "oz", PRODUCE)),
    _r("zaatar-chicken-farro", "Za'atar Chicken & Farro", "mediterranean", (),
       ("chicken thighs", 1.5, "lb", MEAT), ("farro", 1.5, "cup", PANTRY),
       ("lemon", 2, "each", PRODUCE), ("spinach", 5, "oz", PRODUCE),
       ("feta", 4, "oz", DAIRY)),
    _r("mediterranean-chicken-sheet-pan", "Mediterranean Chicken Sheet-Pan",
       "mediterranean", ("gluten-free",),
       ("chicken thighs", 2, "lb", MEAT), ("bell pepper", 2, "each", PRODUCE),
       ("zucchini", 2, "each", PRODUCE), ("tomato", 3, "each", PRODUCE),
       ("feta", 4, "oz", DAIRY)),
    _r("chicken-gyro-bowls", "Chicken Gyro Bowls", "mediterranean", (),
       ("chicken breast", 1.5, "lb", MEAT), ("cucumber", 1, "each", PRODUCE),
       ("tomato", 2, "each", PRODUCE), ("feta", 4, "oz", DAIRY),
       ("greek yogurt", 1, "cup", DAIRY), ("bulgur", 1, "cup", PANTRY)),

    # --- Italian ---
    _r("spaghetti-marinara", "Spaghetti Marinara", "italian", ("vegetarian",),
       ("spaghetti", 1, "lb", PANTRY), ("marinara", 1, "jar", PANTRY),
       ("garlic", 3, "clove", PRODUCE), ("basil", 1, "bunch", PRODUCE)),
    _r("chicken-parmesan", "Chicken Parmesan", "italian", (),
       ("chicken breast", 1.5, "lb", MEAT), ("marinara", 1, "jar", PANTRY),
       ("mozzarella", 8, "oz", DAIRY), ("parmesan", 4, "oz", DAIRY),
       ("spaghetti", 1, "lb", PANTRY)),
    _r("pesto-pasta", "Pesto Pasta", "italian", ("vegetarian",),
       ("pasta", 1, "lb", PANTRY), ("pesto", 1, "jar", PANTRY),
       ("parmesan", 4, "oz", DAIRY), ("tomato", 2, "each", PRODUCE)),
    _r("lasagna", "Classic Lasagna", "italian", (),
       ("ground beef", 1.5, "lb", MEAT), ("lasagna noodles", 1, "box", PANTRY),
       ("marinara", 2, "jar", PANTRY), ("ricotta", 15, "oz", DAIRY),
       ("mozzarella", 8, "oz", DAIRY)),
    _r("margherita-flatbread", "Margherita Flatbread", "italian", ("vegetarian",),
       ("pizza dough", 1, "each", BAKERY), ("mozzarella", 8, "oz", DAIRY),
       ("tomato", 3, "each", PRODUCE), ("basil", 1, "bunch", PRODUCE)),
    _r("sausage-peppers", "Italian Sausage & Peppers", "italian", ("gluten-free",),
       ("italian sausage", 1.5, "lb", MEAT), ("bell pepper", 3, "each", PRODUCE),
       ("onion", 2, "each", PRODUCE), ("garlic", 3, "clove", PRODUCE)),
    _r("minestrone", "Minestrone Soup", "italian", ("vegetarian", "vegan"),
       ("canned tomatoes", 1, "can", PANTRY), ("kidney beans", 1, "can", PANTRY),
       ("pasta", 0.5, "lb", PANTRY), ("carrot", 3, "each", PRODUCE),
       ("zucchini", 1, "each", PRODUCE)),

    # --- Asian ---
    _r("chicken-fried-rice", "Chicken Fried Rice", "asian", ("gluten-free",),
       ("chicken breast", 1, "lb", MEAT), ("rice", 3, "cup", PANTRY),
       ("eggs", 3, "each", DAIRY), ("green onion", 1, "bunch", PRODUCE),
       ("soy sauce", 1, "bottle", PANTRY)),
    _r("beef-stir-fry", "Beef & Broccoli Stir-Fry", "asian", (),
       ("flank steak", 1.5, "lb", MEAT), ("broccoli", 2, "head", PRODUCE),
       ("soy sauce", 1, "bottle", PANTRY), ("ginger", 1, "each", PRODUCE),
       ("rice", 2, "cup", PANTRY)),
    _r("teriyaki-salmon", "Teriyaki Salmon", "asian", ("gluten-free",),
       ("salmon", 1.5, "lb", MEAT), ("rice", 2, "cup", PANTRY),
       ("broccoli", 1, "head", PRODUCE), ("green onion", 1, "bunch", PRODUCE)),
    _r("pad-thai", "Chicken Pad Thai", "asian", ("gluten-free",),
       ("chicken breast", 1, "lb", MEAT), ("rice noodles", 8, "oz", PANTRY),
       ("peanuts", 4, "oz", PANTRY), ("eggs", 2, "each", DAIRY),
       ("green onion", 1, "bunch", PRODUCE)),
    _r("sesame-noodles", "Sesame Noodles", "asian", ("vegetarian", "vegan"),
       ("lo mein noodles", 12, "oz", PANTRY), ("sesame oil", 1, "bottle", PANTRY),
       ("soy sauce", 1, "bottle", PANTRY), ("green onion", 1, "bunch", PRODUCE)),
    _r("veggie-lo-mein", "Vegetable Lo Mein", "asian", ("vegetarian", "vegan"),
       ("lo mein noodles", 12, "oz", PANTRY), ("carrot", 2, "each", PRODUCE),
       ("cabbage", 0.5, "head", PRODUCE), ("soy sauce", 1, "bottle", PANTRY),
       ("mushroom", 8, "oz", PRODUCE)),
    _r("korean-beef-bowl", "Korean Beef Bowl", "asian", ("gluten-free",),
       ("ground beef", 1.5, "lb", MEAT), ("rice", 2, "cup", PANTRY),
       ("gochujang", 1, "jar", PANTRY), ("green onion", 1, "bunch", PRODUCE),
       ("garlic", 3, "clove", PRODUCE)),

    # --- Indian ---
    _r("chicken-tikka-masala", "Chicken Tikka Masala", "indian", ("gluten-free",),
       ("chicken thighs", 1.5, "lb", MEAT), ("canned tomatoes", 1, "can", PANTRY),
       ("coconut milk", 1, "can", PANTRY), ("rice", 2, "cup", PANTRY),
       ("ginger", 1, "each", PRODUCE)),
    _r("chana-masala", "Chana Masala", "indian", ("vegetarian", "vegan", "gluten-free"),
       ("chickpeas", 2, "can", PANTRY), ("canned tomatoes", 1, "can", PANTRY),
       ("onion", 1, "each", PRODUCE), ("ginger", 1, "each", PRODUCE),
       ("rice", 2, "cup", PANTRY)),
    _r("palak-paneer", "Palak Paneer", "indian", ("vegetarian", "gluten-free"),
       ("paneer", 12, "oz", DAIRY), ("spinach", 10, "oz", PRODUCE),
       ("onion", 1, "each", PRODUCE), ("garlic", 4, "clove", PRODUCE),
       ("rice", 2, "cup", PANTRY)),
    _r("dal-rice", "Dal & Rice", "indian", ("vegetarian", "vegan", "gluten-free"),
       ("lentils", 2, "cup", PANTRY), ("rice", 2, "cup", PANTRY),
       ("onion", 1, "each", PRODUCE), ("ginger", 1, "each", PRODUCE)),
    _r("veg-curry", "Coconut Vegetable Curry", "indian",
       ("vegetarian", "vegan", "gluten-free"),
       ("cauliflower", 1, "head", PRODUCE), ("coconut milk", 1, "can", PANTRY),
       ("curry paste", 1, "jar", PANTRY), ("potato", 2, "each", PRODUCE),
       ("rice", 2, "cup", PANTRY)),

    # --- American ---
    _r("classic-burgers", "Classic Cheeseburgers", "american", (),
       ("ground beef", 2, "lb", MEAT), ("burger buns", 8, "each", BAKERY),
       ("cheddar", 8, "oz", DAIRY), ("onion", 1, "each", PRODUCE),
       ("tomato", 2, "each", PRODUCE)),
    _r("baked-chicken-veg", "Baked Chicken & Vegetables", "american", ("gluten-free",),
       ("chicken thighs", 2, "lb", MEAT), ("potato", 4, "each", PRODUCE),
       ("carrot", 4, "each", PRODUCE), ("broccoli", 1, "head", PRODUCE)),
    _r("turkey-chili", "Turkey Chili", "american", ("gluten-free",),
       ("ground turkey", 1.5, "lb", MEAT), ("kidney beans", 2, "can", PANTRY),
       ("canned tomatoes", 1, "can", PANTRY), ("onion", 1, "each", PRODUCE),
       ("bell pepper", 1, "each", PRODUCE)),
    _r("mac-and-cheese", "Baked Mac & Cheese", "american", ("vegetarian",),
       ("elbow macaroni", 1, "lb", PANTRY), ("cheddar", 12, "oz", DAIRY),
       ("mozzarella", 4, "oz", DAIRY)),
    _r("sheet-pan-sausage", "Sheet-Pan Sausage & Potatoes", "american", ("gluten-free",),
       ("italian sausage", 1.5, "lb", MEAT), ("potato", 4, "each", PRODUCE),
       ("bell pepper", 2, "each", PRODUCE), ("onion", 1, "each", PRODUCE)),
    _r("bbq-chicken", "BBQ Chicken & Slaw", "american", ("gluten-free",),
       ("chicken thighs", 2, "lb", MEAT), ("bbq sauce", 1, "bottle", PANTRY),
       ("cabbage", 0.5, "head", PRODUCE), ("carrot", 2, "each", PRODUCE)),

    # --- Southern ---
    _r("shrimp-grits", "Shrimp & Grits", "southern", ("gluten-free",),
       ("shrimp", 1.5, "lb", MEAT), ("grits", 1.5, "cup", PANTRY),
       ("cheddar", 4, "oz", DAIRY), ("bacon", 6, "oz", MEAT),
       ("green onion", 1, "bunch", PRODUCE)),
    _r("fried-chicken-sandwich", "Buttermilk Fried Chicken Sandwich", "southern", (),
       ("chicken thighs", 1.5, "lb", MEAT), ("buttermilk", 1, "qt", DAIRY),
       ("burger buns", 6, "each", BAKERY), ("cabbage", 0.5, "head", PRODUCE)),
    _r("chicken-fried-steak", "Chicken-Fried Steak", "southern", (),
       ("skirt steak", 1.5, "lb", MEAT), ("buttermilk", 1, "qt", DAIRY),
       ("potato", 4, "each", PRODUCE)),

    # --- Cajun ---
    _r("jambalaya", "Chicken & Sausage Jambalaya", "cajun", ("gluten-free",),
       ("chicken thighs", 1, "lb", MEAT), ("andouille", 1, "lb", MEAT),
       ("rice", 2, "cup", PANTRY), ("bell pepper", 2, "each", PRODUCE),
       ("onion", 1, "each", PRODUCE)),
    _r("red-beans-rice", "Red Beans & Rice", "cajun", (),
       ("kidney beans", 2, "can", PANTRY), ("andouille", 1, "lb", MEAT),
       ("rice", 2, "cup", PANTRY), ("bell pepper", 1, "each", PRODUCE),
       ("onion", 1, "each", PRODUCE)),

    # --- Breakfast ---
    _r("breakfast-tacos", "Texas Breakfast Tacos", "breakfast", ("vegetarian",),
       ("eggs", 8, "each", DAIRY), ("flour tortillas", 8, "each", BAKERY),
       ("cheddar", 6, "oz", DAIRY), ("potato", 2, "each", PRODUCE)),
)

RECIPES_BY_ID = {r.id: r for r in RECIPES}

# Crowd-pleasers shown by default when no cuisine is selected.
CORE_IDS = {
    "classic-burgers",
    "spaghetti-marinara",
    "chicken-tacos",
    "beef-fajitas",
    "chicken-fried-rice",
    "baked-chicken-veg",
    "mac-and-cheese",
    "chicken-parmesan",
    "teriyaki-salmon",
    "greek-bowls",
    "turkey-chili",
    "breakfast-tacos",
}


# Real dietary lanes (matched against a recipe's `diets` tags).
DIET_TAGS = {"vegetarian", "vegan", "gluten-free"}

# Protein filters (matched against a recipe's ingredients). The dropdown lets a
# family say e.g. "chicken only".
PROTEIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "chicken": ("chicken",),
    "beef": ("beef", "skirt steak", "flank steak"),
    "pork": ("pork", "chorizo", "bacon", "andouille", "sausage"),
    "seafood": ("salmon", "shrimp"),
    "turkey": ("turkey",),
}

# Any ingredient keyword that means "land/poultry meat" (for pescatarian).
_MEAT_KEYWORDS = (
    "chicken", "beef", "pork", "turkey", "steak", "sausage",
    "chorizo", "bacon", "andouille",
)


def _has_ingredient(recipe: Recipe, keywords: tuple[str, ...]) -> bool:
    return any(
        any(k in i.name.lower() for k in keywords) for i in recipe.ingredients
    )


def matches_diet(recipe: Recipe, diet: str | None) -> bool:
    if not diet:
        return True
    d = diet.lower().strip()
    if d in DIET_TAGS:
        return d in recipe.diets
    if d in PROTEIN_KEYWORDS:
        return _has_ingredient(recipe, PROTEIN_KEYWORDS[d])
    if d == "pescatarian":
        return not _has_ingredient(recipe, _MEAT_KEYWORDS)
    # Unknown filter: fall back to tag match so nothing breaks.
    return d in recipe.diets


def filter_recipes(cuisines: list[str] | None, diet: str | None) -> list[Recipe]:
    """Recipes matching the requested cuisines and diet/protein filter."""
    out = []
    for r in RECIPES:
        if cuisines and r.cuisine not in cuisines:
            continue
        if not matches_diet(r, diet):
            continue
        out.append(r)
    return out
