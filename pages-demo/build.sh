#!/usr/bin/env bash
# Builds the no-server demo into docs/app for GitHub Pages:
#   the real Next.js UI as static files + the real planner code run by Pyodide.
#
#   SRC_ROOT          where to read app/ and frontend/ (default: this repo)
#   OUT_ROOT          where to write docs/app (default: this repo)
#   NODE_MODULES_DIR  reuse an installed node_modules instead of running npm ci
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/.." && pwd)"
src="${SRC_ROOT:-$repo}"
out="${OUT_ROOT:-$repo}/docs/app"
base_path="/heb-meal-planner/app"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Static export can't include the server proxy route, and the demo replaces it.
tar --exclude=node_modules --exclude=.next -C "$src/frontend" -cf - . | tar -C "$tmp" -xf -
rm -rf "$tmp/app/api"
cat > "$tmp/next.config.js" <<EOF
module.exports = {
  output: "export",
  basePath: "$base_path",
  trailingSlash: true,
  images: { unoptimized: true },
};
EOF

if [ -n "${NODE_MODULES_DIR:-}" ]; then
  ln -s "$NODE_MODULES_DIR" "$tmp/node_modules"
else
  (cd "$tmp" && npm ci --no-audit --no-fund)
fi
(cd "$tmp" && NEXT_TELEMETRY_DISABLED=1 npx next build)

rm -rf "$out"
mkdir -p "$out/demo"
cp -r "$tmp/out/." "$out/"
cp "$here/shim.js" "$here/worker.js" "$out/demo/"

python3 - "$src" "$here" "$out" "$base_path" <<'PY'
import pathlib
import sys
import zipfile

src, here, out, base_path = (sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3]), sys.argv[4])
root = pathlib.Path(src)

# Only pure-Python modules that need no server, database or API key.
modules = [
    "app/__init__.py",
    "app/charts.py",
    "app/reports.py",
    "app/planning/__init__.py",
    "app/planning/coupons.py",
    "app/planning/mapping.py",
    "app/planning/nutrition.py",
    "app/planning/planner.py",
    "app/planning/pricing.py",
    "app/planning/recipes.py",
]
with zipfile.ZipFile(out / "demo" / "py.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for name in modules:
        z.write(root / name, name)
    z.write(pathlib.Path(here) / "heb_demo_api.py", "heb_demo_api.py")
    z.writestr(
        "app/config.py",
        "class _Settings:\n"
        '    heb_search_url = "https://www.heb.com/search/?q={query}"\n'
        "settings = _Settings()\n",
    )

index = out / "index.html"
html = index.read_text()
tag = f'<script src="{base_path}/demo/shim.js"></script>'
assert html.count("<head>") == 1
index.write_text(html.replace("<head>", "<head>" + tag, 1))
PY

echo "Demo built in $out"
