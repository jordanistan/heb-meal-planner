from app.planning import mapping
from app.planning.planner import PlanRequest, generate_plan


def test_mapping_prefers_private_labels():
    assert mapping.query_for("skirt steak", "tex-mex") == "beef skirt steak"
    assert mapping.query_for("feta", "mediterranean").startswith("Central Market")
    assert mapping.brand_of("H-E-B Organics Garbanzo Beans") == "H-E-B Organics"
    assert mapping.brand_of("Mi Tienda Queso Fresco") == "Mi Tienda"
    # Longest-first: "green onion" must not match the generic "onion".
    assert mapping.query_for("green onion") == "Fresh Green Onions"


def test_deep_link_encodes_query():
    assert mapping.deep_link("Mi Tienda Queso Fresco") == (
        "https://www.heb.com/search/?q=Mi+Tienda+Queso+Fresco"
    )


def _meal_count(plan):
    return sum(m["count"] for m in plan["meals"])


def test_consolidation_and_costs():
    # A tiny budget keeps just the two anchors (no autofill), so the
    # consolidation is deterministic.
    plan = generate_plan(
        PlanRequest(
            household_size=4,
            meal_types=["dinner"],
            budget=1.0,
            anchor_meal_ids=["beef-fajitas", "chicken-tacos"],
        )
    )
    assert _meal_count(plan) == 2
    lines = {i["ingredient"]: i for i in plan["shopping_list"]}
    cilantro = [i for i in plan["shopping_list"] if i["ingredient"] == "cilantro"]
    assert len(cilantro) == 1  # consolidated across both meals
    assert lines["lime"]["quantity"] == 5  # 2 + 3
    assert all(i["est_cost"] > 0 for i in plan["shopping_list"])
    assert plan["estimated_total"] > 0


def test_meal_types_scale_to_the_week():
    # One meal type => 7 days => 7 meals; mediterranean pool has enough.
    plan = generate_plan(
        PlanRequest(household_size=2, meal_types=["dinner"], cuisines=["mediterranean"])
    )
    assert _meal_count(plan) == 7
    assert all(m["cuisine"] == "mediterranean" for m in plan["meals"])


def test_budget_limits_meal_count():
    small = generate_plan(PlanRequest(household_size=2, meal_types=["dinner"], budget=25.0))
    full = generate_plan(PlanRequest(household_size=2, meal_types=["dinner"]))
    assert _meal_count(small) < _meal_count(full)
    assert small["estimated_total"] <= 25.0
    assert small["under_budget"] is True


def test_coupons_attached_to_matching_items():
    plan = generate_plan(
        PlanRequest(household_size=2, meal_types=["dinner"], anchor_meal_ids=["chicken-tacos"], budget=1.0)
    )
    # chicken tacos -> chicken breast + avocado, both have sample coupons.
    assert plan["coupons"], "expected at least one matched coupon"
    assert plan["estimated_savings"] > 0


def test_chicken_protein_filter():
    from app.planning.recipes import filter_recipes

    med_chicken = filter_recipes(["mediterranean"], "chicken")
    assert len(med_chicken) >= 5
    assert all(
        any("chicken" in i.name for i in r.ingredients) for r in med_chicken
    )
    # A vegan filter excludes all of them.
    assert all(
        any("chicken" in i.name for i in r.ingredients) is False
        for r in filter_recipes(["mediterranean"], "vegan")
    )


def test_pantry_exclusion_drops_items():
    plan = generate_plan(
        PlanRequest(
            household_size=2,
            meal_types=["dinner"],
            budget=1.0,
            anchor_meal_ids=["chickpea-stew"],
            pantry_exclude=["garlic"],
        )
    )
    names = {i["ingredient"] for i in plan["shopping_list"]}
    assert "garlic" not in names
    assert "chickpeas" in names
