"""In-browser stand-in for app/api/routes.py, used only by the GitHub Pages demo.

Runs under Pyodide and calls the real planner, nutrition and report code. Data
lives in this module's memory, so nothing is stored or sent, and a page reload
starts over. Keep responses in step with app/api/routes.py.
"""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from urllib.parse import parse_qs

from app import reports
from app.planning import coupons, nutrition
from app.planning.planner import PlanRequest, generate_plan
from app.planning.recipes import (
    CORE_IDS,
    DIET_TAGS,
    NUTRITION_FILTERS,
    PROTEIN_KEYWORDS,
    RECIPES,
    RECIPES_BY_ID,
    matches_diet,
    proteins_in,
)

FILTERS = (*sorted(DIET_TAGS), *PROTEIN_KEYWORDS, "pescatarian", *NUTRITION_FILTERS, "no-added-sugar")
MAX_LOG_DAYS = 366
MEAL_ORDER = {"breakfast": 0, "lunch": 1, "dinner": 2, "snack": 3}

_plans: dict[int, dict] = {}
_log: list[dict] = []
_next_id = {"plan": 1, "log": 1}
_catalog: list[dict] | None = None


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail


def _new_id(kind: str) -> int:
    value = _next_id[kind]
    _next_id[kind] += 1
    return value


def _recipes() -> list[dict]:
    global _catalog
    if _catalog is None:
        _catalog = [
            {
                "id": r.id,
                "name": r.name,
                "cuisine": r.cuisine,
                "diets": list(r.diets),
                "core": r.id in CORE_IDS,
                "servings": r.base_servings,
                "ingredients": [
                    {"name": i.name, "quantity": i.quantity, "unit": i.unit, "department": i.department}
                    for i in r.ingredients
                ],
                "steps": list(r.steps),
                "equipment": list(r.equipment),
                "alternatives": [
                    {"replaces": k, "use": sub, "instructions": note} for k, sub, note in r.alternatives
                ],
                "nutrition": nutrition.per_serving(r),
                "filters": [f for f in FILTERS if f not in PROTEIN_KEYWORDS and matches_diet(r, f)],
                "proteins": sorted(proteins_in(r)),
            }
            for r in RECIPES
        ]
    return _catalog


def _kitchen(equipment: list[str] | None, stove: str | None) -> list[str] | None:
    if equipment is None:
        return None
    have = set(equipment)
    if stove == "none":
        have.discard("stovetop")
    return sorted(have)


def _create_plan(body: dict) -> dict:
    week_start = date.fromisoformat(body["week_start"]) if body.get("week_start") else None
    plan = generate_plan(
        PlanRequest(
            household_size=body.get("household_size", 2),
            meal_types=body.get("meal_types") or ["lunch", "dinner"],
            cuisines=body.get("cuisines"),
            diet=[*(body.get("diets") or []), *([body["diet"]] if body.get("diet") else [])],
            anchor_meal_ids=body.get("anchor_meal_ids"),
            pantry_exclude=body.get("pantry_exclude"),
            budget=body.get("budget"),
            fulfillment=body.get("fulfillment", "pickup"),
            kitchen=_kitchen(body.get("kitchen"), body.get("stove")),
            stove=body.get("stove"),
            week_start=week_start,
        )
    )
    if not plan["meals"]:
        raise ApiError(422, "No meals matched the requested cuisines/diet/kitchen. Widen the filters.")
    # The server stores plans as JSON, and the report code expects that shape.
    stored = json.loads(json.dumps(plan, default=_encode))
    plan_id = _new_id("plan")
    _plans[plan_id] = stored
    return {"id": plan_id, **stored}


def _get_plan(plan_id: int) -> dict:
    if plan_id not in _plans:
        raise ApiError(404, "Plan not found")
    return _plans[plan_id]


def _add_log(body: dict, today: date) -> dict:
    servings = float(body.get("servings", 1.0))
    recipe_id = body.get("recipe_id")
    if recipe_id:
        recipe = RECIPES_BY_ID.get(recipe_id)
        if not recipe:
            raise ApiError(404, "Recipe not found")
        name = recipe.name
        facts = nutrition.per_serving(recipe, servings)
    else:
        name = (body.get("name") or "").strip()
        if not name:
            raise ApiError(422, "Provide a recipe_id or a name for a custom food.")
        per = {**nutrition.zero(), **(body.get("nutrition") or {})}
        facts = nutrition.rounded({k: v * servings for k, v in per.items()})
    # JSON numbers can arrive as ints; the CSV export must print them as floats.
    facts = {k: float(v) for k, v in facts.items()}
    entry = {
        "id": _new_id("log"),
        "eaten_on": date.fromisoformat(body["eaten_on"]) if body.get("eaten_on") else today,
        "meal_type": body.get("meal_type", "dinner"),
        "recipe_id": recipe_id,
        "name": name,
        "servings": servings,
        "nutrition": facts,
        "notes": body.get("notes"),
    }
    _log.append(entry)
    return entry


def _range(query: dict, today: date) -> tuple[date, date]:
    end = date.fromisoformat(query["end"][0]) if query.get("end") else today
    start = date.fromisoformat(query["start"][0]) if query.get("start") else end - timedelta(days=6)
    if start > end:
        raise ApiError(422, "start must be on or before end")
    if (end - start).days >= MAX_LOG_DAYS:
        raise ApiError(422, f"Range is limited to {MAX_LOG_DAYS} days")
    return start, end


def _load_log(start: date, end: date) -> dict:
    days = []
    current = start
    while current <= end:
        entries = sorted(
            (e for e in _log if e["eaten_on"] == current),
            key=lambda e: MEAL_ORDER.get(e["meal_type"], 9),
        )
        totals = nutrition.zero()
        for e in entries:
            totals = nutrition.add(totals, e["nutrition"])
        days.append({"date": current, "totals": nutrition.rounded(totals), "entries": entries})
        current += timedelta(days=1)

    logged = [d for d in days if d["entries"]]
    average = nutrition.zero()
    for d in logged:
        average = nutrition.add(average, d["totals"])
    count = len(logged) or 1
    return {
        "start": start,
        "end": end,
        "days": days,
        "daily_average": nutrition.rounded({k: v / count for k, v in average.items()}),
    }


def _encode(value):
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Cannot encode {type(value)}")


def _json(data, status: int = 200) -> dict:
    return {"status": status, "type": "application/json", "body": json.dumps(data, default=_encode)}


def _file(body: str, media_type: str, filename: str) -> dict:
    return {"status": 200, "type": media_type, "body": body, "filename": filename}


def _is_true(query: dict, key: str) -> bool:
    return (query.get(key) or [""])[0].lower() in {"1", "true", "yes", "on"}


def _route(method: str, path: str, query: dict, body: dict, today: date) -> dict:
    if method == "GET" and path == "/recipes":
        return _json(_recipes())

    match = re.fullmatch(r"/recipes/([^/]+)/steps", path)
    if method == "GET" and match:
        recipe = RECIPES_BY_ID.get(match[1])
        if not recipe:
            raise ApiError(404, "Recipe not found")
        if recipe.steps:
            return _json({"steps": list(recipe.steps), "source": "library"})
        return _json({"steps": [], "source": "unavailable"})

    if method == "GET" and path == "/coupons":
        return _json(coupons.current())

    if method == "POST" and path == "/plans":
        return _json(_create_plan(body))

    match = re.fullmatch(r"/plans/(\d+)", path)
    if method == "GET" and match:
        plan_id = int(match[1])
        return _json({"id": plan_id, **_get_plan(plan_id)})

    match = re.fullmatch(r"/plans/(\d+)/report", path)
    if method == "GET" and match:
        plan = _get_plan(int(match[1]))
        return _file(reports.plan_report(plan), "text/html", f"meal-plan-{plan['week']}.html")

    if method == "POST" and path == "/log":
        return _json(_add_log(body, today))

    match = re.fullmatch(r"/log/(\d+)", path)
    if method == "DELETE" and match:
        entry_id = int(match[1])
        if not any(e["id"] == entry_id for e in _log):
            raise ApiError(404, "Log entry not found")
        _log[:] = [e for e in _log if e["id"] != entry_id]
        return {"status": 204, "type": "application/json", "body": ""}

    if method == "GET" and path == "/log":
        return _json(_load_log(*_range(query, today)))

    if method == "GET" and path == "/log/report":
        start, end = _range(query, today)
        log = _load_log(start, end)
        stem = f"food-log-{start.isoformat()}-to-{end.isoformat()}"
        if (query.get("format") or ["html"])[0] == "csv":
            return _file(reports.log_csv(log["days"]), "text/csv", f"{stem}.csv")
        goal = float(query["calorie_goal"][0]) if query.get("calorie_goal") else None
        name = query["name"][0] if query.get("name") else None
        html = reports.log_report(log["days"], start, end, goal, name, query.get("kitchen"))
        return _file(html, "text/html", f"{stem}.html")

    raise ApiError(404, "Not found")


def handle(method: str, path: str, query_string: str, body: str, today: str) -> str:
    """Answer one request and return the response as a JSON string."""
    try:
        response = _route(
            method.upper(),
            path,
            parse_qs(query_string),
            json.loads(body) if body else {},
            date.fromisoformat(today),
        )
    except ApiError as e:
        response = _json({"detail": e.detail}, e.status)
    return json.dumps(response)


def init(today: str) -> None:
    """Fill the food log with six made-up days so the history and reports have content."""
    if _log:
        return
    now = date.fromisoformat(today)
    oatmeal = {"calories": 310, "protein_g": 9, "carbs_g": 58, "fat_g": 5, "sodium_mg": 120}
    week = [
        ["breakfast-tacos", "turkey-chili", "beef-fajitas"],
        ["breakfast-tacos", "greek-bowls", "teriyaki-salmon"],
        [None, "chicken-tacos", "baked-chicken-veg"],
        ["breakfast-tacos", "spaghetti-marinara", "turkey-chili"],
        [None, "greek-bowls", "classic-burgers"],
        ["breakfast-tacos", "chicken-fried-rice", "chicken-tacos"],
    ]
    for offset, meals in zip(range(6, 0, -1), week):
        day = (now - timedelta(days=offset)).isoformat()
        for meal_type, recipe_id in zip(("breakfast", "lunch", "dinner"), meals):
            if recipe_id:
                _add_log({"recipe_id": recipe_id, "eaten_on": day, "meal_type": meal_type}, now)
            else:
                _add_log(
                    {"name": "Oatmeal with banana", "nutrition": oatmeal, "eaten_on": day, "meal_type": meal_type},
                    now,
                )
