#!/bin/bash
set -euo pipefail

# Setup domain proxy on Hostinger VPS
# Routes external domain (port 80/443) → FRATELANZA on port 9000
# Keeps FRATELANZA isolated from other projects

DOMAIN="${1:-erp.yourdomain.com}"
APP_PORT="${APP_PORT:-9000}"

if [ "$DOMAIN" = "erp.yourdomain.com" ]; then
    echo "Usage: ./scripts/setup-domain-proxy.sh your-domain.com"
    exit 1
fi

echo "Setting up domain proxy: ${DOMAIN} → localhost:${APP_PORT}"

# Install certbot if needed
if ! command -v certbot &> /dev/null; then
    apt-get update && apt-get install -y certbot python3-certbot-nginx nginx
fi

# Create isolated nginx site config
cat > "/etc/nginx/sites-available/fratelanza-${DOMAIN}" << EOF
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
    }
}
EOF

ln -sf "/etc/nginx/sites-available/fratelanza-${DOMAIN}" "/etc/nginx/sites-enabled/"
nginx -t && systemctl reload nginx

echo "Getting SSL certificate..."
certbot --nginx -d "${DOMAIN}" --non-interactive --agree-tos -m "admin@${DOMAIN}" || \
    echo "SSL setup failed — configure manually with: certbot --nginx -d ${DOMAIN}"

echo ""
echo "============================================"
echo " Domain configured!"
echo ""
echo " 1. DNS: Point A record ${DOMAIN} → your VPS IP"
echo " 2. Access: https://${DOMAIN}"
echo " 3. FRATELANZA runs isolated on port ${APP_PORT}"
echo "============================================"
