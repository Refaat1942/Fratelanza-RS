#!/bin/bash
# FRATELANZA Real Estate — ONE command deploy (Hostinger VPS)
# Stops old Hub containers, deploys ERP on port 9000, fixes rs.fratelanza.com routing.
#
# Usage (on VPS as root):
#   curl -fsSL https://raw.githubusercontent.com/Refaat1942/Fratelanza-RS/main/scripts/deploy.sh | bash
#
# Or if repo already cloned:
#   cd /opt/fratelanza && bash scripts/deploy.sh

set -euo pipefail

APP_DIR="${APP_DIR:-/opt/fratelanza}"
APP_PORT="${APP_PORT:-9000}"
COMPOSE_PROJECT="fratelanza"
REPO_URL="${REPO_URL:-https://github.com/Refaat1942/Fratelanza-RS.git}"
BRANCH="${BRANCH:-main}"
RS_DOMAINS="${RS_DOMAINS:-rs.fratelanza.com rs-control.fratelanza.com}"
FIX_DOMAINS="${FIX_DOMAINS:-1}"

log() { echo "[deploy] $*"; }
die() { echo "[deploy] ERROR: $*" >&2; exit 1; }

echo "============================================"
echo " FRATELANZA Real Estate — one-command deploy"
echo " Port ${APP_PORT} | dir ${APP_DIR}"
echo "============================================"

if ! command -v docker &>/dev/null; then
  log "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
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
  log "Creating .env from .env.production.example — edit passwords after deploy!"
  cp .env.production.example .env
fi

# Ensure APP_PORT in .env
grep -q "^APP_PORT=" .env 2>/dev/null && sed -i "s|^APP_PORT=.*|APP_PORT=${APP_PORT}|" .env || echo "APP_PORT=${APP_PORT}" >> .env
export APP_PORT

if command -v ufw &>/dev/null && ufw status 2>/dev/null | grep -q "active"; then
  ufw allow "${APP_PORT}/tcp" comment "Fratelanza Real Estate" 2>/dev/null || true
fi

log "Stopping legacy Hub containers (wrong app on this VPS)..."
LEGACY=(
  fratelanza-app-1
  fratelanza-admin-app-1
  fratelanza-db-1
  fratelanza-admin-db-1
)
for c in "${LEGACY[@]}"; do
  docker rm -f "$c" 2>/dev/null && log "  removed $c" || true
done

# Stop any other container publishing host port 9000 except our target nginx
while IFS= read -r line; do
  name="${line%% *}"
  [ -z "$name" ] || [ "$name" = "fratelanza_nginx" ] && continue
  if docker port "$name" 2>/dev/null | grep -q ":${APP_PORT}"; then
    log "  stopping $name (was using port ${APP_PORT})"
    docker rm -f "$name" 2>/dev/null || true
  fi
done < <(docker ps --format '{{.Names}}' 2>/dev/null || true)

log "Stopping previous Real Estate stack..."
docker compose -p "${COMPOSE_PROJECT}" -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

log "Building and starting Real Estate (docker-compose.prod.yml)..."
docker compose -p "${COMPOSE_PROJECT}" -f docker-compose.prod.yml up -d --build --remove-orphans

log "Waiting for health..."
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${APP_PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

curl -fsS "http://127.0.0.1:${APP_PORT}/health" >/dev/null 2>&1 || die "Health check failed on port ${APP_PORT}. Logs: docker compose -p ${COMPOSE_PROJECT} -f docker-compose.prod.yml logs"

TITLE=$(curl -fsS "http://127.0.0.1:${APP_PORT}/login" 2>/dev/null | tr '\n' ' ' | sed -n 's/.*<title>\([^<]*\)<\/title>.*/\1/p' || echo "")
if echo "$TITLE" | grep -qi 'hub'; then
  die "Port ${APP_PORT} still serves Fratelanza Hub — wrong image. Check docker ps and remove Hub containers."
fi

log "Port ${APP_PORT} OK — ${TITLE:-Real Estate}"

if [ "${FIX_DOMAINS}" = "1" ] && [ -f scripts/fix-rs-domain.sh ]; then
  log "Fixing domain nginx (rs.fratelanza.com → port ${APP_PORT})..."
  RS_EMAIL="${RS_EMAIL:-admin@fratelanza.com}" bash scripts/fix-rs-domain.sh ${RS_DOMAINS} || log "Domain fix skipped or partial (app still on :${APP_PORT})"
fi

VPS_IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "============================================"
echo " DONE — Real Estate ERP is live"
echo ""
echo " Direct:  http://${VPS_IP:-YOUR_IP}:${APP_PORT}/login"
echo " Domain:  https://rs.fratelanza.com/login"
echo " Control: https://rs-control.fratelanza.com/super-admin"
echo ""
echo " Demo:    admin@demo.fratelanza.com / Demo123456"
echo " Super:   admin@fratelanza.com (see .env SUPER_ADMIN_PASSWORD)"
echo ""
echo " Logs:    cd ${APP_DIR} && docker compose -p ${COMPOSE_PROJECT} -f docker-compose.prod.yml logs -f"
echo " Redeploy: cd ${APP_DIR} && bash scripts/deploy.sh"
echo "============================================"
