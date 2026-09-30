import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app

# TestClient without a `with` block doesn't run the lifespan, so create tables.
init_db()

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_recipes():
    r = client.get("/recipes")
    assert r.status_code == 200
    assert len(r.json()) >= 6


def test_recipe_steps_unavailable_without_key():
    # No ANTHROPIC_API_KEY in tests -> graceful "unavailable", not an error.
    r = client.get("/recipes/beef-fajitas/steps")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "unavailable"
    assert body["steps"] == []


def test_recipe_steps_404_for_unknown():
    assert client.get("/recipes/not-a-recipe/steps").status_code == 404


def test_coupons_endpoint():
    r = client.get("/coupons")
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 1
    assert all("deal" in c for c in body)


def test_create_and_fetch_plan():
    r = client.post(
        "/plans",
        json={
            "household_size": 4,
            "meal_types": ["dinner"],
            "budget": 1,
            "anchor_meal_ids": ["beef-fajitas", "chicken-tacos"],
        },
    )
    assert r.status_code == 200, r.text
    plan = r.json()
    assert plan["id"] is not None
    assert sum(m["count"] for m in plan["meals"]) == 2
    assert plan["shopping_list"]
    assert plan["estimated_total"] > 0

    got = client.get(f"/plans/{plan['id']}")
    assert got.status_code == 200
    assert got.json()["id"] == plan["id"]
