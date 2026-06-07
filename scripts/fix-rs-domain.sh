#!/bin/bash
# Point rs.fratelanza.com at the Real Estate platform (port 9000), not Fratelanza Hub.
#
# Problem: rs.fratelanza.com may serve "Fratelanza Hub" while Fratelanza-RS runs on :9000.
# Fix: ensure only the fratelanza nginx site proxies rs.fratelanza.com → 127.0.0.1:9000
#
# Usage (on VPS as root):
#   cd /opt/fratelanza && bash scripts/fix-rs-domain.sh
#   cd /opt/fratelanza && bash scripts/fix-rs-domain.sh rs.fratelanza.com admin@fratelanza.com
set -euo pipefail

DOMAIN="${1:-rs.fratelanza.com}"
EMAIL="${2:-admin@fratelanza.com}"
APP_PORT="${APP_PORT:-9000}"
APP_DIR="${APP_DIR:-/opt/fratelanza}"
SAFE_NAME=$(echo "$DOMAIN" | tr '.' '-')
TARGET_CONF="/etc/nginx/sites-available/fratelanza-${SAFE_NAME}"
DISABLED_DIR="/etc/nginx/sites-disabled-fratelanza-fix"

echo "============================================"
echo " Fix ${DOMAIN} → Real Estate (port ${APP_PORT})"
echo "============================================"

if ! curl -fsS "http://127.0.0.1:${APP_PORT}/health" >/dev/null 2>&1; then
  echo "ERROR: Nothing healthy on 127.0.0.1:${APP_PORT}"
  echo "Start Fratelanza-RS first:"
  echo "  cd ${APP_DIR} && docker compose -p fratelanza -f docker-compose.prod.yml up -d --build"
  exit 1
fi

TITLE=$(curl -fsS "http://127.0.0.1:${APP_PORT}/login" | tr '\n' ' ' | sed -n 's/.*<title>\([^<]*\)<\/title>.*/\1/p')
echo "Port ${APP_PORT} serves: ${TITLE:-unknown}"
if echo "$TITLE" | grep -qi 'hub'; then
  echo "ERROR: Port ${APP_PORT} is Fratelanza Hub, not Real Estate."
  echo "Deploy Fratelanza-RS to ${APP_PORT} before running this script."
  exit 1
fi

mkdir -p "$DISABLED_DIR"

echo ""
echo "Scanning nginx configs for ${DOMAIN}..."
while IFS= read -r conf; do
  [ -f "$conf" ] || continue
  base=$(basename "$conf")
  if [ "$conf" = "$TARGET_CONF" ]; then
    echo "  keep  $base (fratelanza target config)"
    continue
  fi
  if grep -q "server_name.*${DOMAIN}" "$conf" 2>/dev/null; then
    dest="${DISABLED_DIR}/${base}.$(date +%s)"
    echo "  disable $base → $dest"
    mkdir -p "$(dirname "$dest")"
    mv "$conf" "$dest"
    rm -f "/etc/nginx/sites-enabled/$base"
  fi
done < <(find /etc/nginx/sites-available /etc/nginx/conf.d -type f \( -name '*.conf' -o ! -name '*~' \) 2>/dev/null | sort -u)

# Also remove enabled symlinks that still reference the domain via includes
for link in /etc/nginx/sites-enabled/*; do
  [ -e "$link" ] || continue
  base=$(basename "$link")
  target=$(readlink -f "$link" 2>/dev/null || echo "$link")
  if [ "$target" != "$TARGET_CONF" ] && grep -q "server_name.*${DOMAIN}" "$target" 2>/dev/null; then
    echo "  unlink sites-enabled/$base"
    rm -f "$link"
  fi
done

if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR"
  git pull origin main 2>/dev/null || true
  bash scripts/connect-domain.sh "$DOMAIN" "$EMAIL"
else
  echo "WARN: ${APP_DIR} not found — writing nginx config only"
  bash "$(dirname "$0")/connect-domain.sh" "$DOMAIN" "$EMAIL"
fi

echo ""
echo "Verifying..."
HTTPS_TITLE=$(curl -fsSk "https://${DOMAIN}/login" 2>/dev/null | tr '\n' ' ' | sed -n 's/.*<title>\([^<]*\)<\/title>.*/\1/p' || true)
if echo "$HTTPS_TITLE" | grep -qi 'hub'; then
  echo "WARNING: https://${DOMAIN} still shows Fratelanza Hub."
  echo "Check for other nginx configs or CDN/DNS overrides."
  echo "Direct Real Estate URL (always works): http://187.124.15.14:${APP_PORT}/login"
  exit 1
fi

echo ""
echo "============================================"
echo " SUCCESS"
echo " Real Estate demo: https://${DOMAIN}/login"
echo " Hub (separate app): https://hub.fratelanza.com"
echo "============================================"
