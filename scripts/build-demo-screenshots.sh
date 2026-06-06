#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

export DEMO_URL="${DEMO_URL:-https://rs.fratelanza.com}"
export SCREENSHOTS_DIR="${SCREENSHOTS_DIR:-$(pwd)/docs/demo-screenshots}"

echo "============================================"
echo " FRATELANZA — Bilingual Demo Screenshots"
echo " URL: $DEMO_URL"
echo " Output: $SCREENSHOTS_DIR"
echo "============================================"

if ! npx playwright --version &>/dev/null; then
  echo "Installing Playwright Chromium..."
  npm install -D playwright@1.49.0 --prefix /tmp/pw-install 2>/dev/null || true
  npx playwright install chromium
fi

node scripts/capture-bilingual-demo-screenshots.mjs
node scripts/generate-screenshots-guide.mjs

cd docs
zip -qr fratelanza-demo-screenshots.zip demo-screenshots/*.png demo-screenshots/manifest.json DEMO-SCREENSHOTS-GUIDE.md DEMO-SCREENSHOTS-GUIDE-AR.md
echo "ZIP: docs/fratelanza-demo-screenshots.zip"

echo "Done. Open docs/DEMO-SCREENSHOTS-GUIDE.md"
