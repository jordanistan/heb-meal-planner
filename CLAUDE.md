# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**HEB Family Meal Planner** — a FastAPI SaaS backend (v1) that turns a family's
anchor meals + dietary lane into a weekly plan and a consolidated H-E-B shopping
list. The product's defensible core is **cuisine + H-E-B private-label
intelligence**, which runs entirely on our own data.

**Hard rule:** we never automate or scrape heb.com from our servers. It's behind
Akamai bot protection (a datacenter request gets a 401 — verified), and doing it
commercially violates H-E-B's ToS. The "buy" step is a **deep link** the user's
own browser follows (`app/planning/mapping.deep_link`); a later browser extension
does cart-fill in the user's own session. Keep all H-E-B interaction client-side.

## Commands

```bash
# Docker (the intended workflow; mirrors production)
docker compose up -d --build        # API on 127.0.0.1:8000, Postgres alongside
docker compose run --rm catalog     # run the catalog worker once
docker compose down                 # (-v also drops the DB volume)

# Without Docker (SQLite fallback)
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest -q                           # run all tests
pytest tests/test_planner.py -q     # one file
```

## Architecture

Request flow: `app/main.py` (FastAPI + lifespan that calls `init_db`) →
`app/api/routes.py` → `app/planning/planner.py` → persist via `app/models.py`.

- **`app/planning/`** is the domain core and has no web/DB dependencies, so it's
  unit-testable in isolation:
  - `mapping.py` — ingredient → H-E-B query (private-label-aware),
    `brand_of()` (longest-first match so "H-E-B Organics" beats "H-E-B"), and
    `deep_link()` (the heb.com search URL the user's browser opens).
  - `recipes.py` — the seed recipe library (dataclasses) + `DEFAULT_PANTRY`.
    Editing recipes here changes what plans can contain; `base_servings` drives scaling.
  - `planner.py` — `generate_plan()`: picks anchor meals then auto-fills to
    `days`, scales quantities to household size, **consolidates duplicate
    `(ingredient, unit)` pairs**, drops pantry items, and maps each line to
    query + brand + deep link.
- **`app/db.py`** — one SQLAlchemy engine/session. `DATABASE_URL` selects the
  backend: SQLite locally (with `check_same_thread`), Postgres in
  Compose/k8s. `init_db()` runs `create_all` (v1 has no migrations yet — add
  Alembic before schema churn).
- **`app/worker/catalog.py`** — the scheduled catalog job (Compose service under
  the `worker` profile; k8s `CronJob`). Decoupled from request traffic. It does
  **not** scrape heb.com.
- **`app/config.py`** — all settings via env (`pydantic-settings`); `ANTHROPIC_API_KEY`
  is optional and gates future Claude-generated plans (v1 is fully deterministic).

## Deployment

- One image (`Dockerfile`, `python:3.12-slim`) serves both the API (default CMD:
  uvicorn) and the worker (CMD override).
- `k8s/` holds namespace, config/secret, in-cluster Postgres (demo — use a
  managed DB in prod), the API Deployment + Service + HPA (2–10 on CPU), and the
  catalog CronJob. Set `image:` in `k8s/api.yaml` to your registry before applying.

## Conventions & gotchas

- Adding a `jobs`-style column or model means editing `models.py`; there are no
  migrations yet, so `init_db`'s `create_all` won't alter existing tables —
  introduce Alembic when the schema is no longer additive on a fresh DB.
- Tests default to SQLite; `tests/test_api.py` calls `init_db()` explicitly
  because `TestClient` without a `with` block doesn't trigger the lifespan.
- The `POST /plans` endpoint returns 422 when no recipe matches the requested
  cuisines/diet — widen filters rather than expecting an empty plan.
- Legacy MCP-scraper specs are archived under `docs/legacy/` for reference only;
  that approach was abandoned (see the Hard rule above).
