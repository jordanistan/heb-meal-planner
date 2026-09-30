# HEB Family Meal Planner — SaaS backend (v1)

A privacy-first meal-planning SaaS for Texas H-E-B families. Families set their
**anchor meals** and dietary lane; the service builds a weekly plan, consolidates
the ingredients, and maps each one to a real H-E-B product — favoring private
labels (Mi Tienda, Central Market, H-E-B Organics). The "buy" step is a
**deep link** the user's own browser follows to heb.com, so no automation or
scraping ever runs on our servers.

See the full product & architecture plan: the "HEB Family Meal Planner — SaaS Plan" doc.

## Architecture (v1)

- **FastAPI** backend (`app/`) — stateless, scales horizontally.
- **PostgreSQL** — households and generated plans.
- **Planning core** (`app/planning/`) — recipe library, brand mapping, and the
  consolidation logic. Deterministic; no LLM required for v1.
- **Catalog worker** (`app/worker/`) — scheduled refresh, decoupled from user traffic.
- Packaged as one Docker image; **Docker Compose** for local dev, **Kubernetes**
  (`k8s/`) for production scaling.

## Run locally (Docker)

```bash
docker compose up -d --build        # API on http://127.0.0.1:8000
curl http://127.0.0.1:8000/health   # {"status":"ok","database":true}
open http://127.0.0.1:8000/docs     # interactive API docs
```

Generate a plan:

```bash
curl -X POST http://127.0.0.1:8000/plans -H 'Content-Type: application/json' -d '{
  "household_size": 4,
  "days": 3,
  "anchor_meal_ids": ["beef-fajitas", "chicken-tacos"],
  "cuisines": ["tex-mex", "mexican"]
}'
```

Run the catalog worker once: `docker compose run --rm catalog`.
Tear down: `docker compose down` (add `-v` to drop the database volume).

## Run without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload     # uses SQLite (dev.db) by default
pytest -q                         # run the test suite
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness + DB check (probes) |
| GET | `/recipes` | Recipe library (pick anchor meals) |
| POST | `/plans` | Generate + store a weekly plan and shopping list |
| GET | `/plans/{id}` | Fetch a stored plan |
| GET | `/docs` | OpenAPI / Swagger UI |

## Deploy to Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/config.yaml -f k8s/postgres.yaml -f k8s/api.yaml -f k8s/catalog-cronjob.yaml
```

The API `Deployment` has an `HorizontalPodAutoscaler` (2–10 replicas on CPU);
the catalog refresh runs as a `CronJob`. Push the image to your registry and set
`image:` in `k8s/api.yaml` first. In production, use a managed database instead
of the in-cluster Postgres, and manage the DB `Secret` with a secrets operator.

## Configuration

All config is via environment variables (see `.env.example`): `DATABASE_URL`
(defaults to SQLite locally; Postgres in Compose/k8s), and the optional
`ANTHROPIC_API_KEY` / `ANTHROPIC_MODEL` to enable Claude-generated plans later.
