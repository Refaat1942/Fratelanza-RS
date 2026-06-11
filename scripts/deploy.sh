#!/bin/bash
# FRATELANZA Real Estate — deploy on port 9000 (does NOT stop Hub or other projects)
#
# Usage:
#   cd /opt/fratelanza && bash scripts/deploy.sh
#   INSPECT_ONLY=1 bash scripts/deploy.sh    # only show ports + docker, no deploy
#   FIX_DOMAINS=1 bash scripts/deploy.sh     # also run fix-rs-domain.sh (optional)

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/fratelanza}"
APP_PORT="${APP_PORT:-9000}"
COMPOSE_PROJECT="fratelanza"
REPO_URL="${REPO_URL:-https://github.com/Refaat1942/Fratelanza-RS.git}"
BRANCH="${BRANCH:-main}"
FIX_DOMAINS="${FIX_DOMAINS:-0}"
INSPECT_ONLY="${INSPECT_ONLY:-0}"

log() { echo "[deploy] $*"; }
die() { echo "[deploy] ERROR: $*" >&2; exit 1; }

show_vps_status() {
  echo ""
  echo "========== LISTENING PORTS (host) =========="
  if command -v ss &>/dev/null; then
    ss -tlnp | grep -E ':(80|443|3000|5173|8000|9000|5432|6379)\s' || ss -tlnp | head -30
  else
    netstat -tlnp 2>/dev/null | head -30 || true
  fi

  echo ""
  echo "========== DOCKER CONTAINERS (all running) =========="
  docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}' 2>/dev/null || docker ps

  echo ""
  echo "========== WHO USES PORT ${APP_PORT}? =========="
  found=0
  while IFS= read -r name; do
    [ -z "$name" ] && continue
    ports=$(docker port "$name" 2>/dev/null || true)
    if echo "$ports" | grep -q ":${APP_PORT}"; then
      echo "  container: $name"
      echo "  ports:     $ports"
      found=1
    fi
  done < <(docker ps --format '{{.Names}}' 2>/dev/null || true)
  if [ "$found" -eq 0 ]; then
    echo "  (no docker container mapped to host :${APP_PORT})"
  fi
  if ss -tlnp 2>/dev/null | grep -q ":${APP_PORT} "; then
    echo "  host listener on :${APP_PORT}:"
    ss -tlnp | grep ":${APP_PORT} " || true
  fi

  echo ""
  echo "========== HTTP on 127.0.0.1:${APP_PORT} =========="
  if curl -fsS --max-time 3 "http://127.0.0.1:${APP_PORT}/health" 2>/dev/null; then
    echo ""
  else
    echo "  (no /health response on :${APP_PORT})"
  fi
  TITLE=$(curl -fsS --max-time 3 "http://127.0.0.1:${APP_PORT}/login" 2>/dev/null | tr '\n' ' ' | sed -n 's/.*<title>\([^<]*\)<\/title>.*/\1/p' || echo "")
  if [ -n "$TITLE" ]; then
    echo "  /login page title: $TITLE"
  else
    echo "  (no /login page on :${APP_PORT})"
  fi

  echo ""
  echo "========== THIS PROJECT (fratelanza compose) =========="
  if [ -f "${APP_DIR}/docker-compose.prod.yml" ]; then
    docker compose -p "${COMPOSE_PROJECT}" -f "${APP_DIR}/docker-compose.prod.yml" ps 2>/dev/null || echo "  (not running yet)"
  else
    echo "  ${APP_DIR}/docker-compose.prod.yml not found"
  fi
  echo ""
}

echo "============================================"
echo " FRATELANZA Real Estate — deploy"
echo " Port ${APP_PORT} | project ${COMPOSE_PROJECT} only"
echo " Does NOT stop Hub or other VPS projects"
echo "============================================"

show_vps_status

if [ "${INSPECT_ONLY}" = "1" ]; then
  echo "INSPECT_ONLY=1 — no deploy performed."
  exit 0
fi

if ! command -v docker &>/dev/null; then
  die "Docker not installed. Install Docker first."
fi

if [ -d "${APP_DIR}/.git" ]; then
  log "Updating ${APP_DIR}..."
  cd "${APP_DIR}"
  git fetch origin
  git checkout "${BRANCH}" 2>/dev/null || git checkout main
  git pull origin "$(git branch --show-current)"
else
  log "Cloning into ${APP_DIR}..."
  mkdir -p "$(dirname "${APP_DIR}")"
  git clone -b "${BRANCH}" "${REPO_URL}" "${APP_DIR}" || git clone "${REPO_URL}" "${APP_DIR}"
  cd "${APP_DIR}"
  git checkout "${BRANCH}" 2>/dev/null || true
fi

chmod +x scripts/*.sh 2>/dev/null || true

if [ ! -f .env ]; then
  log "Creating .env from .env.production.example"
  cp .env.production.example .env
fi

grep -q "^APP_PORT=" .env 2>/dev/null && sed -i "s|^APP_PORT=.*|APP_PORT=${APP_PORT}|" .env || echo "APP_PORT=${APP_PORT}" >> .env
export APP_PORT

# Warn if another container already owns APP_PORT (we do not stop it)
while IFS= read -r name; do
  [ -z "$name" ] && continue
  [[ "$name" == fratelanza_* ]] && continue
  if docker port "$name" 2>/dev/null | grep -q ":${APP_PORT}"; then
    log "WARNING: port ${APP_PORT} is already used by container: $name"
    log "WARNING: Hub/other projects are NOT stopped. Set APP_PORT=9001 in .env or free the port yourself."
  fi
done < <(docker ps --format '{{.Names}}' 2>/dev/null || true)

log "Restarting ONLY compose project '${COMPOSE_PROJECT}' (docker-compose.prod.yml)..."
docker compose -p "${COMPOSE_PROJECT}" -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -p "${COMPOSE_PROJECT}" -f docker-compose.prod.yml up -d --build

log "Waiting for health on :${APP_PORT}..."
ok=0
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${APP_PORT}/health" >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 2
done

echo ""
echo "========== AFTER DEPLOY =========="
show_vps_status

if [ "$ok" -ne 1 ]; then
  die "Health check failed on :${APP_PORT}. See logs: docker compose -p ${COMPOSE_PROJECT} -f docker-compose.prod.yml logs"
fi

if [ "${FIX_DOMAINS}" = "1" ] && [ -f scripts/fix-rs-domain.sh ]; then
  log "FIX_DOMAINS=1 — running fix-rs-domain.sh (nginx only, does not stop Hub containers)..."
  RS_EMAIL="${RS_EMAIL:-admin@fratelanza.com}" bash scripts/fix-rs-domain.sh ${RS_DOMAINS:-rs.fratelanza.com rs-control.fratelanza.com} || true
fi

VPS_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo "============================================"
echo " Deploy finished (project ${COMPOSE_PROJECT} only)"
echo " Try: http://${VPS_IP:-127.0.0.1}:${APP_PORT}/login"
echo " Inspect only: INSPECT_ONLY=1 bash scripts/deploy.sh"
echo " Logs: docker compose -p ${COMPOSE_PROJECT} -f docker-compose.prod.yml logs -f"
echo "============================================"
