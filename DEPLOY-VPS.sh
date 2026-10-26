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

echo ">>> [3b] Database backup (before any change)..."
BACKUP_DIR=/root/fratelanza-backups
mkdir -p "$BACKUP_DIR"
if docker ps -a --format '{{.Names}}' | grep -qx fratelanza_postgres; then
  docker start fratelanza_postgres >/dev/null
  sleep 3
  BK="$BACKUP_DIR/fratelanza_$(date +%F_%H%M%S).sql"
  if docker exec fratelanza_postgres sh -c 'pg_dump -U "${POSTGRES_USER:-fratelanza}" "${POSTGRES_DB:-fratelanza_db}"' > "$BK" && [ -s "$BK" ]; then
    echo "    Saved $BK ($(du -h "$BK" | cut -f1))"
  else
    echo "ERROR: database backup failed — nothing was changed. Fix the database container and retry."
    exit 1
  fi
fi

echo ">>> [3c] Adopt containers created outside the 'fratelanza' compose project..."
NEW_VOL="fratelanza_fratelanza_postgres"
if docker ps -a --format '{{.Names}}' | grep -qx fratelanza_postgres; then
  PROJ=$(docker inspect fratelanza_postgres --format '{{index .Config.Labels "com.docker.compose.project"}}')
  if [ "$PROJ" != "fratelanza" ]; then
    OLD_VOL=$(docker inspect fratelanza_postgres --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}')
    OLD_IMG=$(docker inspect fratelanza_postgres --format '{{.Config.Image}}')
    echo "    fratelanza_postgres belongs to project '$PROJ' (volume '$OLD_VOL', image '$OLD_IMG')"
    if [ -n "$OLD_VOL" ] && [ "$OLD_VOL" != "$NEW_VOL" ]; then
      NEW_HAS_DATA=$(docker run --rm -v "$NEW_VOL":/to alpine sh -c 'ls -A /to | head -1' 2>/dev/null || true)
      case "$OLD_IMG" in postgres:16*) SAME_MAJOR=yes ;; *) SAME_MAJOR=no ;; esac
      if [ -n "$NEW_HAS_DATA" ] || [ "$SAME_MAJOR" != "yes" ]; then
        echo "STOP: data is in volume '$OLD_VOL' but production uses '$NEW_VOL' (already has data: ${NEW_HAS_DATA:+yes}, same Postgres major: $SAME_MAJOR)."
        echo "      Nothing was deleted. Backup: $BK. Ask for help before continuing."
        exit 1
      fi
      echo "    Copying database files $OLD_VOL -> $NEW_VOL (old volume is kept untouched)"
      docker stop fratelanza_postgres >/dev/null
      docker volume create "$NEW_VOL" >/dev/null
      docker run --rm -v "$OLD_VOL":/from:ro -v "$NEW_VOL":/to alpine sh -c 'cp -a /from/. /to/'
    fi
  fi
fi
for c in fratelanza_postgres fratelanza_redis fratelanza_backend fratelanza_nginx fratelanza_frontend; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$c"; then
    PROJ=$(docker inspect "$c" --format '{{index .Config.Labels "com.docker.compose.project"}}')
    if [ "$PROJ" != "fratelanza" ]; then
      echo "    Removing stale container $c (project '$PROJ') — volumes are kept"
      docker rm -f "$c" >/dev/null
    fi
  fi
done

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
