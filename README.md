<h1 align="center">🛒 HEB Meal Planner</h1>

<p align="center">
  <em>Plan your family's week in H-E-B's own language — pick the meals you love,
  get one consolidated shopping list mapped to real H-E-B products, on budget.</em>
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white">
  <img alt="FastAPI" src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white">
  <img alt="Next.js" src="https://img.shields.io/badge/Web-Next.js-000000?logo=nextdotjs&logoColor=white">
  <img alt="Docker" src="https://img.shields.io/badge/Run-Docker%20Compose-2496ED?logo=docker&logoColor=white">
  <img alt="Kubernetes" src="https://img.shields.io/badge/Scale-Kubernetes-326CE5?logo=kubernetes&logoColor=white">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

---

## What is this?

Most meal-plan apps hand you recipes and a generic list. **HEB Meal Planner** is
built for Texas families who already shop at H-E-B: it plans the week around your
**anchor meals** and diet, then turns every ingredient into the *right H-E-B
product* — favoring private labels like **Mi Tienda**, **Central Market**, and
**H-E-B Organics** — with a one-tap deep link to buy.

- 🍽️ **56 recipes across 10 cuisines** — Mediterranean, Mexican, Tex-Mex, Italian, Asian, Indian, American, Southern, Cajun, Breakfast.
- 🎯 **Anchor meals + smart auto-fill** — lock in your go-to dinners, we fill the rest of the week.
- 🧾 **Consolidated shopping list** — "2 limes + 3 limes = 5 limes," grouped by store department.
- 🏷️ **H-E-B brand intelligence** — maps `skirt steak` → *Mi Tienda Seasoned Beef Fajitas*, `feta` → *Central Market Greek Feta*.
- 💵 **Budget mode** — "I want to spend $X" and the plan fits.
- 🎟️ **Weekly-ad coupons** — deals on your list, with estimated savings.
- 🥗 **Diet & protein filters** — vegetarian, vegan, gluten-free, pescatarian, or "chicken only."
- 🚚 **Pickup or delivery.**
- 🌙 **Dark mode.**
- 🤖 **Claude-powered cooking steps** (optional, bring your own API key).

> **Privacy by design:** the "buy" step is a deep link your *own* browser follows
> to heb.com. The app never scrapes or automates H-E-B from its servers.

---

## Quick start (Docker)

The whole stack — API, web, and Postgres — comes up with one command.

```bash
git clone https://github.com/jordanistan/heb-meal-planner.git
cd heb-meal-planner
docker compose up -d --build
```

Then open:

| URL | What |
|-----|------|
| **http://localhost:3000** | 🖥️ The app |
| http://localhost:8000/docs | 🔌 API (Swagger) |

Stop it with `docker compose down` (add `-v` to wipe the database).

### Optional: Claude cooking steps

Add an Anthropic API key and restart the API to enable generated recipe steps:

```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
docker compose up -d api
```

### Run without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload      # API on :8000 (SQLite by default)
pytest -q                          # 15 tests

cd frontend && npm install && npm run dev   # web on :3000
```

---

## How it works

```
Your browser ──▶ Next.js web  ──▶ FastAPI API ──▶ Claude API (optional steps)
      │                                  │
      │                                  └──▶ PostgreSQL (plans, households, cache)
      │                                  └──▶ Catalog worker (scheduled)
      └───────────────▶ heb.com   (deep links — your session, never our servers)
```

- **`app/planning/`** — the brains: recipe library, brand mapping, consolidation, pricing, coupons. Pure Python, no web/DB deps.
- **`app/`** — FastAPI service (stateless, scales horizontally).
- **`frontend/`** — Next.js app; proxies to the API server-side.
- **`k8s/`** — production manifests: API `Deployment` + `HorizontalPodAutoscaler`, Postgres, and a catalog `CronJob`.

See [`CLAUDE.md`](./CLAUDE.md) for the full architecture and conventions.

---

## API at a glance

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness + DB check |
| `GET` | `/recipes` | Recipe library (with ingredients) |
| `GET` | `/recipes/{id}/steps` | Claude-generated cooking steps (cached) |
| `GET` | `/coupons` | This week's ad coupons |
| `POST` | `/plans` | Generate a weekly plan + shopping list |
| `GET` | `/plans/{id}` | Fetch a saved plan |

---

## Deploy to Kubernetes

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/config.yaml -f k8s/postgres.yaml -f k8s/api.yaml -f k8s/catalog-cronjob.yaml
```

Push the image to your registry and set `image:` in `k8s/api.yaml` first. Use a
managed database in production instead of the in-cluster Postgres.

---

## Roadmap

- **Pro tier — assisted cart-fill:** your API key + Claude's browser extension log into heb.com *in your browser* and load the cart, stopping before payment.
- Real catalog prices & live weekly-ad coupons via a partner feed (today's are estimates/samples).
- Multi-retailer support.

---

## Status & disclaimer

v1 / MVP. Prices and coupons are **sample/estimated data**, not live H-E-B
pricing. Not affiliated with or endorsed by H-E-B; "H-E-B", "Mi Tienda", and
"Central Market" are trademarks of their respective owner and are referenced
here only to map shopping queries.

## License

[MIT](./LICENSE)
