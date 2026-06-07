#!/bin/bash
# FRATELANZA — one-command fix + deploy (password mismatch, missing plans, restart)
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/fratelanza}"
COMPOSE="docker compose -p fratelanza -f docker-compose.prod.yml"

cd "$APP_DIR"

echo "============================================"
echo " FRATELANZA — Fix & Deploy"
echo "============================================"

# --- Fix broken .env (CHANGE_ME placeholders) ---
fix_env_if_needed() {
  if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.production.example .env
  fi

  if grep -q 'CHANGE_ME' .env 2>/dev/null; then
    echo "⚠️  .env has placeholder passwords — auto-fixing..."
    cp .env ".env.bak.$(date +%Y%m%d_%H%M%S)" 2>/dev/null || true

    DB_PASS="${FRATELANZA_DB_PASS:-FratelanzaDb$(openssl rand -hex 6)}"
    SECRET1="$(openssl rand -hex 32)"
    SECRET2="$(openssl rand -hex 32)"
    ADMIN_PASS="${FRATELANZA_ADMIN_PASS:-Fratelanza@$(openssl rand -hex 4)}"
    if [ -f LOGIN_PASSWORD.txt ] && [ -z "${FRATELANZA_ADMIN_PASS:-}" ]; then
      ADMIN_PASS="$(cat LOGIN_PASSWORD.txt | tr -d '\n')"
    fi

    APP_PORT_VAL="$(grep '^APP_PORT=' .env 2>/dev/null | cut -d= -f2 || echo 9000)"
    DOMAIN_VAL="$(grep '^DOMAIN=' .env 2>/dev/null | cut -d= -f2 | sed 's/erp.yourdomain.com/187.124.15.14/' || echo 187.124.15.14)"
    CORS_VAL="$(grep '^CORS_ORIGINS=' .env 2>/dev/null | cut -d= -f2- || echo "http://187.124.15.14:9000,https://rs.fratelanza.com,https://rs-control.fratelanza.com")"

    cat > .env << EOF
APP_NAME=FRATELANZA REAL ESTATE PLATFORM
APP_ENV=production
DEBUG=false
APP_PORT=${APP_PORT_VAL}
DOMAIN=${DOMAIN_VAL}
SECRET_KEY=${SECRET1}
JWT_SECRET_KEY=${SECRET2}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
POSTGRES_USER=fratelanza
POSTGRES_PASSWORD=${DB_PASS}
POSTGRES_DB=fratelanza_db
DATABASE_URL=postgresql+asyncpg://fratelanza:${DB_PASS}@postgres:5432/fratelanza_db
DATABASE_URL_SYNC=postgresql://fratelanza:${DB_PASS}@postgres:5432/fratelanza_db
REDIS_URL=redis://redis:6379/0
VITE_API_URL=
CORS_ORIGINS=${CORS_VAL}
SUPER_ADMIN_EMAIL=admin@fratelanza.com
SUPER_ADMIN_PASSWORD=${ADMIN_PASS}
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=./uploads
EOF
    echo "${ADMIN_PASS}" > LOGIN_PASSWORD.txt
    chmod 600 LOGIN_PASSWORD.txt .env
    echo "✅ .env fixed. Admin password saved to LOGIN_PASSWORD.txt"
  else
    echo "✅ .env looks OK"
  fi
}

sync_postgres_password() {
  local pass
  pass="$(grep '^POSTGRES_PASSWORD=' .env | cut -d= -f2-)"
  if [ -z "$pass" ]; then
    echo "❌ POSTGRES_PASSWORD missing in .env"
    exit 1
  fi
  echo "Syncing PostgreSQL password..."
  $COMPOSE up -d postgres
  sleep 5
  $COMPOSE exec -T postgres psql -U fratelanza -d postgres \
    -c "ALTER USER fratelanza WITH PASSWORD '${pass}';" \
    || $COMPOSE exec -T postgres psql -U postgres -d postgres \
    -c "ALTER USER fratelanza WITH PASSWORD '${pass}';" \
    || true
}

deploy_stack() {
  echo "Building and starting services..."
  export APP_PORT="${APP_PORT:-9000}"
  $COMPOSE up -d --build
  echo "Waiting for backend..."
  sleep 20
}

restore_plans() {
  echo "Restoring subscription plans if missing..."
  $COMPOSE exec -T backend python3 << 'PYEOF' || true
import asyncio
from app.core.database import AsyncSessionLocal
from app.utils.seed import ensure_default_subscription_plans

async def main():
    async with AsyncSessionLocal() as db:
        n = await ensure_default_subscription_plans(db)
        await db.commit()
        print(f"Subscription plans added: {n}")

asyncio.run(main())
PYEOF
}

fix_logins() {
  echo "Fixing all logins (super admin + demo company)..."
  if [ -f scripts/fix-all-logins.sh ]; then
    bash scripts/fix-all-logins.sh
  else
    local pass
    pass="$(grep '^SUPER_ADMIN_PASSWORD=' .env | cut -d= -f2-)"
    [ -f scripts/reset-admin-password.sh ] && bash scripts/reset-admin-password.sh "$pass" 2>/dev/null || true
  fi
}

health_check() {
  local port
  port="$(grep '^APP_PORT=' .env | cut -d= -f2 || echo 9000)"
  if curl -sf "http://localhost:${port}/health" > /dev/null; then
    echo ""
    echo "============================================"
    echo " ✅ FRATELANZA is running!"
    echo ""
    echo " URL:      http://$(hostname -I | awk '{print $1}'):${port}"
    echo " Login:    admin@fratelanza.com"
    echo " Password: $(cat LOGIN_PASSWORD.txt 2>/dev/null || grep '^SUPER_ADMIN_PASSWORD=' .env | cut -d= -f2-)"
    echo "============================================"
    return 0
  fi
  echo "❌ Health check failed. Logs:"
  $COMPOSE logs --tail=40 backend
  return 1
}

fix_env_if_needed
sync_postgres_password
deploy_stack
restore_plans
fix_logins
health_check
