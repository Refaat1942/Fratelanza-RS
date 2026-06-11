#!/bin/bash
# =============================================================================
# FRATELANZA REAL ESTATE — VPS PRODUCTION DEPLOY (run on server only)
# =============================================================================
#
# VERIFIED WORKING COMMANDS (Hostinger VPS srv1443693):
#
#   cd /opt/fratelanza
#   git fetch origin && git reset --hard origin/main
#   bash DEPLOY-VPS.sh
#
# Do NOT run:  docker compose up -d --build   (DEV compose — port 5432 conflict)
# =============================================================================
set -euo pipefail

APP_DIR="${1:-/opt/fratelanza}"
APP_PORT="${APP_PORT:-9000}"
cd "$APP_DIR"

echo ""
echo ">>> FRATELANZA production deploy (port ${APP_PORT})"
echo ">>> Folder: $APP_DIR"
echo ""

if [ ! -f docker-compose.prod.yml ]; then
  echo "ERROR: docker-compose.prod.yml not found. Are you in /opt/fratelanza?"
  exit 1
fi

echo ">>> [1/5] Git: force sync to GitHub main..."
git fetch origin
git checkout main
git reset --hard origin/main
COMMIT=$(git rev-parse --short HEAD)
echo "    Commit: $COMMIT"
export GIT_COMMIT="$COMMIT"
export APP_PORT

echo ">>> [2/5] Stop wrong DEV stack (if any) — Hub NOT touched..."
docker compose down 2>/dev/null || true

echo ">>> [3/5] Rebuild PRODUCTION nginx + backend (5-10 min)..."
docker compose -p fratelanza -f docker-compose.prod.yml build --no-cache nginx backend

echo ">>> [4/5] Start production stack..."
docker compose -p fratelanza -f docker-compose.prod.yml up -d

echo ">>> [5/5] Wait for health..."
for i in $(seq 1 40); do
  HEALTH=$(curl -fsS "http://127.0.0.1:${APP_PORT}/health" 2>/dev/null || true)
  if [ -n "$HEALTH" ]; then
    echo ""
    echo "HEALTH: $HEALTH"
  if echo "$HEALTH" | grep -q installment_calculator; then
      echo ""
      echo "============================================"
      echo " SUCCESS — new version is live"
      echo " Calculator, portal, trial: deployed"
      echo " Open: https://rs.fratelanza.com/collections"
      echo " Hard refresh: Ctrl+Shift+R"
      echo "============================================"
      exit 0
    fi
    if echo "$HEALTH" | grep -q git_commit; then
      echo ""
      echo "============================================"
      echo " SUCCESS — backend updated (commit $COMMIT)"
      echo " Hard refresh browser: Ctrl+Shift+R"
      echo "============================================"
      exit 0
    fi
    echo ""
    echo "============================================"
    echo " WARNING: Server runs but still OLD build"
    echo " Paste this output when asking for help:"
    echo "   git log -1 --oneline"
    echo "   docker ps | grep fratelanza"
    echo "   curl -s http://127.0.0.1:9000/health"
    echo "============================================"
    exit 1
  fi
  sleep 3
done

echo "ERROR: Health check failed after 2 minutes."
docker compose -p fratelanza -f docker-compose.prod.yml logs --tail=30
exit 1
