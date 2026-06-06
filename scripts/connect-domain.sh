#!/bin/bash
# Connect domain to FRATELANZA ONLY — never touches pharmapos or other projects
# Usage: bash scripts/connect-domain.sh rs.fratelanza.com your@email.com
set -euo pipefail

DOMAIN="${1:-}"
EMAIL="${2:-admin@fratelanza.com}"
APP_PORT="${APP_PORT:-9000}"
VPS_IP="187.124.15.14"
SAFE_NAME=$(echo "${DOMAIN:-unknown}" | tr '.' '-')
NGINX_CONF="/etc/nginx/sites-available/fratelanza-${SAFE_NAME}"
CERTBOT_WEBROOT="/var/www/fratelanza-certbot-only"

if [ -z "$DOMAIN" ]; then
  echo "Usage: bash scripts/connect-domain.sh rs.fratelanza.com your@email.com"
  exit 1
fi

echo "============================================"
echo " FRATELANZA domain setup (ISOLATED)"
echo " Domain:  ${DOMAIN}"
echo " Will NOT modify pharmapos or other sites"
echo "============================================"

# Update .env CORS only
if [ -f /opt/fratelanza/.env ]; then
  cd /opt/fratelanza
  grep -q "^DOMAIN=" .env && sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" .env || echo "DOMAIN=${DOMAIN}" >> .env
  grep -q "^CORS_ORIGINS=" .env && sed -i "s|^CORS_ORIGINS=.*|CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN},http://${VPS_IP}:${APP_PORT}|" .env || \
    echo "CORS_ORIGINS=https://${DOMAIN},http://${DOMAIN},http://${VPS_IP}:${APP_PORT}" >> .env
  docker compose -p fratelanza -f docker-compose.prod.yml restart backend 2>/dev/null || true
fi

# Install nginx/certbot if missing (does not change existing configs)
command -v nginx &>/dev/null || apt-get update && apt-get install -y nginx
command -v certbot &>/dev/null || apt-get install -y certbot

mkdir -p "$CERTBOT_WEBROOT"

# STEP 1: HTTP-only config for FRATELANZA only (separate file)
cat > "$NGINX_CONF" << EOF
# FRATELANZA ONLY — do not edit other project configs
server {
    listen 80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root ${CERTBOT_WEBROOT};
    }

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

ln -sf "$NGINX_CONF" "/etc/nginx/sites-enabled/fratelanza-${SAFE_NAME}"
nginx -t
systemctl reload nginx
echo "✓ FRATELANZA nginx config created (pharmapos untouched)"

# STEP 2: SSL certificate — webroot method (does NOT run certbot --nginx)
echo "Getting SSL certificate (isolated method)..."
certbot certonly --webroot \
  -w "$CERTBOT_WEBROOT" \
  -d "$DOMAIN" \
  --non-interactive \
  --agree-tos \
  -m "$EMAIL" \
  --cert-name "fratelanza-${SAFE_NAME}" || {
    echo ""
    echo "SSL pending — DNS may need more time. HTTP should work:"
    echo "  http://${DOMAIN}"
    echo "Retry SSL later with:"
    echo "  bash /opt/fratelanza/scripts/connect-domain.sh ${DOMAIN} ${EMAIL}"
    exit 0
}

# STEP 3: Add SSL to FRATELANZA config ONLY
cat > "$NGINX_CONF" << EOF
# FRATELANZA ONLY — SSL for ${DOMAIN}
server {
    listen 80;
    server_name ${DOMAIN};
    location /.well-known/acme-challenge/ { root ${CERTBOT_WEBROOT}; }
    location / { return 301 https://\$host\$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name ${DOMAIN};

    ssl_certificate /etc/letsencrypt/live/fratelanza-${SAFE_NAME}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fratelanza-${SAFE_NAME}/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

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

# Certbot may store under domain name folder — fix path if needed
CERT_DIR="/etc/letsencrypt/live/fratelanza-${SAFE_NAME}"
if [ ! -d "$CERT_DIR" ]; then
  CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"
  sed -i "s|fratelanza-${SAFE_NAME}|${DOMAIN}|g" "$NGINX_CONF"
fi

nginx -t
systemctl reload nginx

echo ""
echo "============================================"
echo " SUCCESS — FRATELANZA domain ready"
echo " https://${DOMAIN}"
echo ""
echo " pharmapos and other projects: UNTOUCHED"
echo " Only file added: ${NGINX_CONF}"
echo "============================================"
