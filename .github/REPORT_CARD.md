# 📋 Project Report Card — HEB Meal Planner

_Generated 2026-09-30 from commit `936a2fa`. Regenerate with `./scripts/gen-sbom-report.sh`._

## Overall: **A−**

A clean, containerized full-stack MVP with a live site, current dependencies,
and no open security alerts. Main gap: no automated CI pipeline or coverage
gate yet.

## Grades

| Area | Grade | Notes |
|------|:-----:|-------|
| 🔐 Security | A | 0 open Dependabot alerts; Next.js on a patched release |
| 🧪 Tests | B+ | 15 passed in 0.78s; unit + API coverage, no e2e/coverage gate yet |
| 📦 Dependencies | A | 9 Python + 3 npm direct deps, pinned; SBOM tracked |
| 🐳 Packaging | A | Docker Compose (api + web + Postgres) and k8s manifests (HPA, CronJob) |
| 📚 Documentation | A | README, CLAUDE.md, GitHub Pages site, this report + SBOM |
| ⚖️ Licensing | A | MIT |
| 🤖 CI/CD | C | No automated pipeline yet (tests/build run locally) |

## Metrics

| Metric | Value |
|--------|-------|
| SBOM components (declared) | 17 |
| Python deps (direct) | 9 |
| npm deps (direct) | 3 |
| Recipes in library | 56 |
| App source lines (py/ts/tsx) | 1852 |
| Open Dependabot alerts | 0 |
| Tests | 15 passed in 0.78s |

## Artifacts

- 📄 SBOM (SPDX 2.3 JSON): [`.github/sbom.spdx.json`](./sbom.spdx.json)
- 🌐 Live site: https://jordanistan.github.io/heb-meal-planner/
- 📦 Repository: https://github.com/jordanistan/heb-meal-planner

## Recommended next steps

1. Add a GitHub Actions workflow to run `pytest` + `docker build` on every PR.
2. Add test coverage reporting and a minimum threshold.
3. Commit a `package-lock.json` so the SBOM captures transitive npm deps.
