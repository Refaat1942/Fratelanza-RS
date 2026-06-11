#!/bin/bash
set -euo pipefail

# FRATELANZA — Deploy to Hostinger VPS on Port 9000
# Usage: ./scripts/deploy-hostinger.sh
# Server: ssh root@187.124.15.14

APP_DIR="${APP_DIR:-/opt/fratelanza}"
APP_PORT="${APP_PORT:-9000}"
REPO_URL="${REPO_URL:-https://github.com/Refaat1942/Fratelanza-RS.git}"
BRANCH="${BRANCH:-main}"

echo "============================================"
echo " FRATELANZA — Hostinger Deployment"
echo " Port: ${APP_PORT}"
echo " Directory: ${APP_DIR}"
echo "============================================"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Clone or update
if [ -d "$APP_DIR/.git" ]; then
    echo "Updating repository..."
    cd "$APP_DIR"
    git fetch origin
    git checkout "$BRANCH" 2>/dev/null || git checkout main
    git pull origin "$(git branch --show-current)"
else
    echo "Cloning repository..."
    mkdir -p "$(dirname "$APP_DIR")"
    git clone -b "$BRANCH" "$REPO_URL" "$APP_DIR" 2>/dev/null || \
        git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
    git checkout "$BRANCH" 2>/dev/null || true
fi

# Environment
if [ ! -f .env ]; then
    cp .env.production.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env with strong passwords before continuing!"
    echo "    nano ${APP_DIR}/.env"
    echo ""
    read -p "Press Enter after editing .env..."
fi

# Open firewall port (if ufw active)
if command -v ufw &> /dev/null && ufw status | grep -q "active"; then
    ufw allow "${APP_PORT}/tcp" comment "FRATELANZA Platform"
    echo "✅ Firewall port ${APP_PORT} opened"
fi

# Build and start
export APP_PORT
export GIT_COMMIT="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
docker compose -p fratelanza -f docker-compose.prod.yml down 2>/dev/null || true
docker compose -p fratelanza -f docker-compose.prod.yml build --no-cache nginx backend
docker compose -p fratelanza -f docker-compose.prod.yml up -d

echo "Waiting for services..."
sleep 15

# Health check
if curl -sf "http://localhost:${APP_PORT}/health" > /dev/null; then
    echo ""
    echo "============================================"
    echo " ✅ FRATELANZA deployed successfully!"
    echo ""
    echo " Access: http://$(hostname -I | awk '{print $1}'):${APP_PORT}"
    echo " API Docs: http://$(hostname -I | awk '{print $1}'):${APP_PORT}/docs"
    echo ""
    echo " Super Admin: admin@fratelanza.com"
    echo " (password from .env SUPER_ADMIN_PASSWORD)"
    echo "============================================"
else
    echo "❌ Health check failed. Check logs:"
    echo "   docker compose -f docker-compose.prod.yml logs"
    exit 1
fi
