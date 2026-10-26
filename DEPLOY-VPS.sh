#!/bin/bash
# =============================================================================
# FRATELANZA REAL ESTATE — VPS PRODUCTION DEPLOY (run on server only)
# =============================================================================
#
#   cd /opt/fratelanza
#   git fetch origin && git reset --hard origin/main
#   bash DEPLOY-VPS.sh
#
# Upgrades the live "fratelanza_rs" stack in place (containers fratelanza_rs_*,
# public port 14136 by default). It:
#   * reuses the port and data volumes of the running containers,
#   * backs up the real-estate database to /root/fratelanza-backups/ first,
#   * never touches other projects (fratelanza-chat owns "fratelanza_postgres",
#     plus fratelanza-office/-console/-website, erp, Hub).
# Do NOT run "docker compose up -d --build" (that is the dev compose file).
# =============================================================================
set -euo pipefail

APP_DIR="${1:-/opt/fratelanza}"
PROJECT="fratelanza_rs"
COMPOSE=(docker compose -p "$PROJECT" -f docker-compose.prod.yml)
cd "$APP_DIR"

if [ ! -f docker-compose.prod.yml ]; then
  echo "ERROR: docker-compose.prod.yml not found. Are you in /opt/fratelanza?"
  exit 1
fi

echo ""
echo ">>> [1/6] Git: sync to GitHub main..."
git fetch origin
git checkout main
git reset --hard origin/main
COMMIT=$(git rev-parse --short HEAD)
echo "    Commit: $COMMIT"
export GIT_COMMIT="$COMMIT"

# Volume name mounted at <path> inside <container> (empty if missing / bind mount)
mount_of() {
  docker inspect "$1" --format "{{range .Mounts}}{{if eq .Destination \"$2\"}}{{.Name}}{{end}}{{end}}" 2>/dev/null || true
}
running() { docker ps -a --format '{{.Names}}' | grep -qx "$1"; }

echo ">>> [2/6] Detect the live stack (port + data volumes)..."
if running fratelanza_rs_nginx; then
  LIVE_PORT=$(docker port fratelanza_rs_nginx 9000/tcp 2>/dev/null | head -1 | sed 's/.*://')
fi
ENV_PORT=$(grep -E '^APP_PORT=' .env 2>/dev/null | tail -1 | cut -d= -f2 || true)
export APP_PORT="${APP_PORT:-${LIVE_PORT:-${ENV_PORT:-14136}}}"

detected_pg=$(mount_of fratelanza_rs_postgres /var/lib/postgresql/data)
detected_redis=$(mount_of fratelanza_rs_redis /data)
detected_uploads=$(mount_of fratelanza_rs_backend /app/uploads)
detected_backups=$(mount_of fratelanza_rs_backend /app/backups)
export RS_PG_VOLUME="${detected_pg:-fratelanza_rs_fratelanza_rs_postgres_data}"
export RS_REDIS_VOLUME="${detected_redis:-fratelanza_rs_redis_data}"
export RS_UPLOADS_VOLUME="${detected_uploads:-fratelanza_rs_uploads}"
export RS_BACKUPS_VOLUME="${detected_backups:-fratelanza_rs_backups}"
echo "    Port:     $APP_PORT"
echo "    Database: $RS_PG_VOLUME"
echo "    Uploads:  $RS_UPLOADS_VOLUME"
for v in "$RS_PG_VOLUME" "$RS_REDIS_VOLUME" "$RS_UPLOADS_VOLUME" "$RS_BACKUPS_VOLUME"; do
  docker volume inspect "$v" >/dev/null 2>&1 || { echo "    Creating volume $v"; docker volume create "$v" >/dev/null; }
done

echo ">>> [3/6] Back up the real-estate database..."
BACKUP_DIR=/root/fratelanza-backups
mkdir -p "$BACKUP_DIR"
if running fratelanza_rs_postgres; then
  docker start fratelanza_rs_postgres >/dev/null
  sleep 3
  BK="$BACKUP_DIR/fratelanza_rs_$(date +%F_%H%M%S).sql"
  if docker exec fratelanza_rs_postgres sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$BK" && [ -s "$BK" ]; then
    echo "    Saved $BK ($(du -h "$BK" | cut -f1))"
  else
    echo "ERROR: database backup failed — nothing was changed."
    exit 1
  fi
else
  echo "    No running fratelanza_rs_postgres yet — first install, nothing to back up."
fi

echo ">>> [4/6] Build backend + nginx (5-10 min)..."
"${COMPOSE[@]}" build --no-cache nginx backend

echo ">>> [5/6] Start (database migrations run automatically on backend start)..."
"${COMPOSE[@]}" up -d

echo ">>> [6/6] Wait for health on port ${APP_PORT}..."
for i in $(seq 1 60); do
  HEALTH=$(curl -fsS "http://127.0.0.1:${APP_PORT}/health" 2>/dev/null || true)
  if [ -n "$HEALTH" ] && echo "$HEALTH" | grep -q multi_tenant_rbac; then
    echo ""
    echo "HEALTH: $HEALTH"
    echo "============================================"
    echo " SUCCESS — new version live (commit $COMMIT)"
    echo " Open: http://$(hostname -I | awk '{print $1}'):${APP_PORT}/login"
    echo " Login: superadmin  (password 123456 on first start — change it)"
    echo " Hard refresh browser: Ctrl+Shift+R"
    echo "============================================"
    exit 0
  fi
  sleep 3
done

echo "ERROR: new version did not become healthy within 3 minutes."
echo "Your data is safe; backup: ${BK:-none}"
"${COMPOSE[@]}" ps
"${COMPOSE[@]}" logs --tail=60 backend
exit 1
