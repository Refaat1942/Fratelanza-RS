#!/bin/bash
# Update FRATELANZA Real Estate on VPS — pulls main and rebuilds frontend+backend (no cache).
# Safe: only restarts the fratelanza compose project; does NOT stop Hub or other projects.
#
# Usage:
#   cd /opt/fratelanza && bash scripts/vps-update.sh

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/fratelanza}"
APP_PORT="${APP_PORT:-9000}"
COMPOSE_PROJECT="fratelanza"
BRANCH="${BRANCH:-main}"

cd "$APP_DIR"

echo "============================================"
echo " FRATELANZA VPS update"
echo " Directory: $APP_DIR"
echo " Branch:    $BRANCH"
echo "============================================"

if [ ! -d .git ]; then
  echo "ERROR: $APP_DIR is not a git repo. Clone first:"
  echo "  git clone https://github.com/Refaat1942/Fratelanza-RS.git $APP_DIR"
  exit 1
fi

git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"

COMMIT=$(git rev-parse --short HEAD)
echo "Git commit: $COMMIT"
export GIT_COMMIT="$COMMIT"
export APP_PORT

echo ""
echo "Rebuilding containers (this takes several minutes)..."
docker compose -p "$COMPOSE_PROJECT" -f docker-compose.prod.yml build --no-cache nginx backend
docker compose -p "$COMPOSE_PROJECT" -f docker-compose.prod.yml up -d

echo "Waiting for /health..."
ok=0
for _ in $(seq 1 40); do
  if curl -fsS "http://127.0.0.1:${APP_PORT}/health" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 3
done

echo ""
echo "========== HEALTH =========="
curl -fsS "http://127.0.0.1:${APP_PORT}/health" || echo "(health check failed)"
echo ""
echo "========== VERIFY =========="
if curl -fsS "http://127.0.0.1:${APP_PORT}/" | grep -q 'index-'; then
  JS=$(curl -fsS "http://127.0.0.1:${APP_PORT}/" | tr '"' '\n' | grep 'assets/index-.*\.js' | head -1)
  if [ -n "$JS" ]; then
    if curl -fsS "http://127.0.0.1:${APP_PORT}/$JS" | grep -q 'installment_calculator'; then
      echo "OK: New frontend includes installment calculator"
    else
      echo "WARNING: Frontend JS still looks OLD (no installment_calculator). Re-run with --no-cache."
    fi
  fi
fi

if [ "$ok" -eq 1 ]; then
  echo ""
  echo "============================================"
  echo " Update finished. Commit: $COMMIT"
  echo " Open: https://rs.fratelanza.com/collections"
  echo " Hard refresh browser: Ctrl+Shift+R"
  echo "============================================"
else
  echo "ERROR: Health check failed. Logs:"
  echo "  docker compose -p $COMPOSE_PROJECT -f docker-compose.prod.yml logs --tail=50"
  exit 1
fi
