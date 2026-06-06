#!/bin/bash
# ============================================================
# FRATELANZA — EASY INSTALL (copy this entire file to VPS)
# Run on server after: ssh root@187.124.15.14
# ============================================================
set -e

echo ""
echo "=========================================="
echo "  FRATELANZA - Easy Install"
echo "=========================================="
echo ""

# 1. Install Docker if missing
if ! command -v docker &>/dev/null; then
  echo "[1/6] Installing Docker..."
  curl -fsSL https://get.docker.com | sh
else
  echo "[1/6] Docker already installed."
fi

# 2. Download project
echo "[2/6] Downloading project..."
mkdir -p /opt
if [ -d /opt/fratelanza/.git ]; then
  cd /opt/fratelanza
  git fetch origin
  git checkout cursor/hostinger-deploy-all-phases-8cb9 2>/dev/null || git checkout main
  git pull
else
  rm -rf /opt/fratelanza
  git clone -b cursor/hostinger-deploy-all-phases-8cb9 https://github.com/Refaat1942/Fratelanza-RS.git /opt/fratelanza || \
    git clone https://github.com/Refaat1942/Fratelanza-RS.git /opt/fratelanza
  cd /opt/fratelanza
  git checkout cursor/hostinger-deploy-all-phases-8cb9 2>/dev/null || true
fi

# 3. Create .env with auto-generated passwords
echo "[3/6] Creating settings..."
if [ ! -f .env ]; then
  DB_PASS=$(openssl rand -hex 16)
  SECRET1=$(openssl rand -hex 32)
  SECRET2=$(openssl rand -hex 32)
  ADMIN_PASS="Fratelanza@$(openssl rand -hex 4)"

  cat > .env << EOF
APP_NAME=FRATELANZA REAL ESTATE PLATFORM
APP_ENV=production
DEBUG=false
APP_PORT=9000
DOMAIN=187.124.15.14
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
CORS_ORIGINS=http://187.124.15.14:9000,http://localhost:9000
SUPER_ADMIN_EMAIL=admin@fratelanza.com
SUPER_ADMIN_PASSWORD=${ADMIN_PASS}
STORAGE_TYPE=local
STORAGE_LOCAL_PATH=./uploads
EOF

  echo ""
  echo "=========================================="
  echo "  SAVE THESE LOGIN DETAILS!"
  echo "=========================================="
  echo "  Website:  http://187.124.15.14:9000"
  echo "  Email:    admin@fratelanza.com"
  echo "  Password: ${ADMIN_PASS}"
  echo "=========================================="
  echo ""
  echo "${ADMIN_PASS}" > /opt/fratelanza/LOGIN_PASSWORD.txt
  echo "Password also saved to: /opt/fratelanza/LOGIN_PASSWORD.txt"
  echo ""
fi

# 4. Open firewall port
echo "[4/6] Opening port 9000..."
if command -v ufw &>/dev/null; then
  ufw allow 9000/tcp 2>/dev/null || true
fi

# 5. Build and start
echo "[5/6] Building and starting (this takes 3-5 minutes)..."
export APP_PORT=9000
docker compose -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# 6. Wait and test
echo "[6/6] Waiting for app to start..."
sleep 20
for i in 1 2 3 4 5; do
  if curl -sf http://localhost:9000/health >/dev/null; then
    echo ""
    echo "=========================================="
    echo "  SUCCESS! FRATELANZA IS RUNNING"
    echo "=========================================="
    echo "  Open in browser:"
    echo "  http://187.124.15.14:9000"
    echo ""
    echo "  Login email: admin@fratelanza.com"
    echo "  Password:    cat /opt/fratelanza/LOGIN_PASSWORD.txt"
    echo "=========================================="
    exit 0
  fi
  echo "  Still starting... ($i/5)"
  sleep 10
done

echo "Install finished but health check pending."
echo "Check logs: cd /opt/fratelanza && docker compose -f docker-compose.prod.yml logs"
exit 0
