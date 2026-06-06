#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
node scripts/generate-subscription-plans-pdf.mjs
ls -lh /opt/cursor/artifacts/fratelanza-subscription-plans.pdf 2>/dev/null || ls -lh docs/marketing/fratelanza-subscription-plans.pdf
