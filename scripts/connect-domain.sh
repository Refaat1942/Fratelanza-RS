#!/bin/bash
# Connect your domain to FRATELANZA (port 9000 stays internal)
# Usage: bash scripts/connect-domain.sh erp.yourdomain.com your@email.com
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-admin@${DOMAIN}}}"
APP_PORT="${APP_PORT:-9000}"
VPS_IP="187.124.15.14"

if [ -z "$DOMAIN" ]; then
  echo "Usage: bash scripts/connect-domain.sh YOUR_DOMAIN.COM your@email.com"
  echo "Example: bash scripts/connect-domain.sh erp.fratelanza.com admin@fratelanza.com"
  exit 1
fi

echo "============================================"
echo " Connecting: ${DOMAIN}"
echo " VPS IP:     ${VPS_IP}"
echo " App port:   ${APP_PORT} (internal only)"
echo "============================================"

# Step 1: Update .env CORS
if [ -f /opt/fratelanza/.env ]; then
  cd /opt/fratelanza
  if grep -q "^DOMAIN=" .env; then
    sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" .env
  else
    echo "DOMAIN=${DOMAIN}" >> .env
  fi
  if grep -q "^CORS_ORIGINS=" .env; then
    sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN},http://${VPS_IP}:${APP_PORT}|" .env
  else
    echo "CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN},http://${VPS_IP}:${APP_PORT}" >> .env
  fi
  docker compose -p fratelanza -f docker-compose.prod.yml restart backend 2>/dev/null || true
  echo "✓ Updated CORS settings"
fi

# Step 2: Install nginx + certbot if needed
if ! command -v nginx &>/dev/null; then
  apt-get update && apt-get install -y nginx certbot python3-certbot-nginx
fi

# Step 3: Create isolated nginx config (does NOT touch other projects)
SAFE_NAME=$(echo "$DOMAIN" | tr '.' '-')
cat > "/etc/nginx/sites-available/fratelanza-${SAFE_NAME}" << EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 120s;
    }
}
EOF

ln -sf "/etc/nginx/sites-available/fratelanza-${SAFE_NAME}" "/etc/nginx/sites-enabled/"
nginx -t
systemctl reload nginx
echo "✓ Nginx proxy configured (other projects untouched)"

# Step 4: SSL certificate
echo "Getting SSL certificate..."
certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "${EMAIL}" --redirect || {
  echo ""
  echo "SSL not ready yet. Common reasons:"
  echo "  - DNS not pointing to ${VPS_IP} yet (wait 10-30 min)"
  echo "  - Run again later: certbot --nginx -d ${DOMAIN}"
  echo ""
  echo "HTTP access may work now: http://${DOMAIN}"
}

echo ""
echo "============================================"
echo " DONE!"
echo ""
echo "  Website: https://${DOMAIN}"
echo "  (or http://${DOMAIN} if SSL pending)"
echo ""
echo "  Your other projects are NOT affected."
echo "  FRATELANZA still runs on port ${APP_PORT} internally."
echo "============================================"
