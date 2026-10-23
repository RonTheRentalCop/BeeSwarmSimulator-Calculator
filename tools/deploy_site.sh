#!/bin/sh
# Builds the static website with `flet publish` and pushes it to the gh-pages branch (GitHub Pages).
set -e
cd "$(dirname "$0")/.."
find . -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} +
.venv/bin/flet publish main.py -a bss_calc/assets --distpath dist \
  --base-url BeeSwarmSimulator-Calculator --route-url-strategy hash \
  --app-name "BeeSwarmSimulator Calculator" --app-short-name "BSS Calc" \
  --app-description "Bee Swarm Simulator honey calculator" \
  --pwa-background-color "#0B0B0C" --pwa-theme-color "#0B0B0C"
touch dist/.nojekyll
remote=$(git remote get-url origin)
cd dist
rm -rf .git
git init -q -b gh-pages
git add -A
git commit -qm "Deploy website"
git push -qf "$remote" gh-pages
rm -rf .git
echo "Deployed to gh-pages"
