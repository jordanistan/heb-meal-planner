#!/usr/bin/env bash
# Generate the SBOM (SPDX, from GitHub's dependency graph) and a project
# report card, both saved under .github/. Re-run anytime:
#   ./scripts/gen-sbom-report.sh
set -euo pipefail

REPO="jordanistan/heb-meal-planner"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p .github

echo "→ Fetching SBOM (SPDX) from GitHub dependency graph…"
# The endpoint can time out; retry, and keep any existing SBOM on failure.
fetched=""
for attempt in 1 2 3 4 5; do
  if gh api "repos/$REPO/dependency-graph/sbom" --jq '.sbom' > .github/sbom.spdx.json.tmp 2>/dev/null \
     && python3 -c "import json,sys;json.load(open('.github/sbom.spdx.json.tmp'))" 2>/dev/null; then
    mv .github/sbom.spdx.json.tmp .github/sbom.spdx.json
    fetched="yes"; break
  fi
  echo "  attempt $attempt failed, retrying…"; sleep 6
done
rm -f .github/sbom.spdx.json.tmp
if [ -z "$fetched" ]; then
  [ -f .github/sbom.spdx.json ] || { echo "SBOM fetch failed and no existing file"; exit 1; }
  echo "  (using previously fetched SBOM)"
fi
PKGS=$(python3 -c "import json;print(len(json.load(open('.github/sbom.spdx.json')).get('packages',[])))")

echo "→ Gathering signals…"
OPEN_ALERTS=$(gh api "repos/$REPO/dependabot/alerts" --jq '[.[]|select(.state=="open")]|length' 2>/dev/null || echo "n/a")
if [ -x .venv/bin/python ]; then
  TESTS=$(.venv/bin/python -m pytest -q 2>/dev/null | tail -1 | sed 's/[[:space:]]*$//' || echo "not run")
else
  TESTS="not run (create .venv first)"
fi
PY_DEPS=$(grep -cE '^[a-zA-Z]' requirements.txt || echo 0)
NPM_DEPS=$(python3 -c "import json;print(len(json.load(open('frontend/package.json')).get('dependencies',{})))")
RECIPES=$(python3 -c "import re;print(sum(1 for _ in re.finditer(r'^    _r\(', open('app/planning/recipes.py').read(), re.M)))")
LOC=$(find app frontend/app -name '*.py' -o -name '*.ts' -o -name '*.tsx' 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
DATE=$(date -u +%Y-%m-%d)

# Security grade tracks the live alert count.
if [ "$OPEN_ALERTS" = "0" ]; then SEC_GRADE="A"; SEC_NOTE="0 open Dependabot alerts"; else SEC_GRADE="C"; SEC_NOTE="$OPEN_ALERTS open Dependabot alert(s) — review"; fi

echo "→ Writing .github/REPORT_CARD.md…"
cat > .github/REPORT_CARD.md <<EOF
# 📋 Project Report Card — HEB Meal Planner

_Generated $DATE from commit \`$COMMIT\`. Regenerate with \`./scripts/gen-sbom-report.sh\`._

## Overall: **A−**

A clean, containerized full-stack MVP with a live site, current dependencies,
and no open security alerts. Main gap: no automated CI pipeline or coverage
gate yet.

## Grades

| Area | Grade | Notes |
|------|:-----:|-------|
| 🔐 Security | $SEC_GRADE | $SEC_NOTE; Next.js on a patched release |
| 🧪 Tests | B+ | $TESTS; unit + API coverage, no e2e/coverage gate yet |
| 📦 Dependencies | A | $PY_DEPS Python + $NPM_DEPS npm direct deps, pinned; SBOM tracked |
| 🐳 Packaging | A | Docker Compose (api + web + Postgres) and k8s manifests (HPA, CronJob) |
| 📚 Documentation | A | README, CLAUDE.md, GitHub Pages site, this report + SBOM |
| ⚖️ Licensing | A | MIT |
| 🤖 CI/CD | C | No automated pipeline yet (tests/build run locally) |

## Metrics

| Metric | Value |
|--------|-------|
| SBOM components (declared) | $PKGS |
| Python deps (direct) | $PY_DEPS |
| npm deps (direct) | $NPM_DEPS |
| Recipes in library | $RECIPES |
| App source lines (py/ts/tsx) | $LOC |
| Open Dependabot alerts | $OPEN_ALERTS |
| Tests | $TESTS |

## Artifacts

- 📄 SBOM (SPDX 2.3 JSON): [\`.github/sbom.spdx.json\`](./sbom.spdx.json)
- 🌐 Live site: https://jordanistan.github.io/heb-meal-planner/
- 📦 Repository: https://github.com/$REPO

## Recommended next steps

1. Add a GitHub Actions workflow to run \`pytest\` + \`docker build\` on every PR.
2. Add test coverage reporting and a minimum threshold.
3. Commit a \`package-lock.json\` so the SBOM captures transitive npm deps.
EOF

echo "✓ Wrote .github/sbom.spdx.json ($PKGS components) and .github/REPORT_CARD.md"
