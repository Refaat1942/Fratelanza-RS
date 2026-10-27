#!/bin/bash
# Point Real Estate domains at port 14136 (not Fratelanza Hub).
#
# Fixes by default:
#   rs.fratelanza.com       — company demo + platform
#   rs-control.fratelanza.com — super-admin control panel alias
#
# Usage (on VPS as root):
#   cd /opt/fratelanza && bash scripts/fix-rs-domain.sh
#   cd /opt/fratelanza && bash scripts/fix-rs-domain.sh rs-control.fratelanza.com
set -euo pipefail

EMAIL="${RS_EMAIL:-admin@fratelanza.com}"
APP_PORT="${APP_PORT:-14136}"
APP_DIR="${APP_DIR:-/opt/fratelanza}"
DISABLED_DIR="/etc/nginx/sites-disabled-fratelanza-fix"

fix_one_domain() {
  local DOMAIN="$1"
  local SAFE_NAME
  SAFE_NAME=$(echo "$DOMAIN" | tr '.' '-')
  local TARGET_CONF="/etc/nginx/sites-available/fratelanza-${SAFE_NAME}"

  echo ""
  echo "============================================"
  echo " Fix ${DOMAIN} → Real Estate (port ${APP_PORT})"
  echo "============================================"

  mkdir -p "$DISABLED_DIR"

  echo "Scanning nginx configs for ${DOMAIN}..."
  while IFS= read -r conf; do
    [ -f "$conf" ] || continue
    local base
    base=$(basename "$conf")
    if [ "$conf" = "$TARGET_CONF" ]; then
      echo "  keep  $base (fratelanza target config)"
      continue
    fi
    if grep -q "server_name.*${DOMAIN}" "$conf" 2>/dev/null; then
      local dest="${DISABLED_DIR}/${base}.$(date +%s)"
      echo "  disable $base → $dest"
      mv "$conf" "$dest"
      rm -f "/etc/nginx/sites-enabled/$base"
    fi
  done < <(find /etc/nginx/sites-available /etc/nginx/conf.d -type f \( -name '*.conf' -o ! -name '*~' \) 2>/dev/null | sort -u)

  for link in /etc/nginx/sites-enabled/*; do
    [ -e "$link" ] || continue
    local base target
    base=$(basename "$link")
    target=$(readlink -f "$link" 2>/dev/null || echo "$link")
    if [ "$target" != "$TARGET_CONF" ] && grep -q "server_name.*${DOMAIN}" "$target" 2>/dev/null; then
      echo "  unlink sites-enabled/$base"
      rm -f "$link"
    fi
  done

  if [ -d "$APP_DIR" ]; then
    bash "$APP_DIR/scripts/connect-domain.sh" "$DOMAIN" "$EMAIL"
  else
    bash "$(dirname "$0")/connect-domain.sh" "$DOMAIN" "$EMAIL"
  fi

  local HTTPS_TITLE
  HTTPS_TITLE=$(curl -fsSk "https://${DOMAIN}/login" 2>/dev/null | tr '\n' ' ' | sed -n 's/.*<title>\([^<]*\)<\/title>.*/\1/p' || true)
  if echo "$HTTPS_TITLE" | grep -qi 'hub'; then
    echo "WARNING: https://${DOMAIN} still shows Fratelanza Hub."
    return 1
  fi
  echo "✓ https://${DOMAIN} → ${HTTPS_TITLE:-Real Estate}"
}

# Domains to fix: pass as args, or use defaults
if [ $# -gt 0 ]; then
  DOMAINS=("$@")
else
  DOMAINS=(rs.fratelanza.com rs-control.fratelanza.com)
fi

echo "============================================"
echo " Fratelanza Real Estate — domain fix"
echo " Domains: ${DOMAINS[*]}"
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
  exit 1
fi

if [ -d "$APP_DIR" ]; then
  cd "$APP_DIR"
  git pull origin main 2>/dev/null || true
fi

FAILED=0
for DOMAIN in "${DOMAINS[@]}"; do
  fix_one_domain "$DOMAIN" || FAILED=$((FAILED + 1))
done

echo ""
echo "============================================"
if [ "$FAILED" -eq 0 ]; then
  echo " SUCCESS"
else
  echo " COMPLETED WITH ${FAILED} WARNING(S)"
fi
echo ""
echo " Company demo:  https://rs.fratelanza.com/login"
echo " RS control:    https://rs-control.fratelanza.com/super-admin"
echo "                (or https://rs.fratelanza.com/super-admin)"
echo " Super admin:   admin@fratelanza.com"
echo " Hub (other):   https://hub.fratelanza.com"
echo "============================================"

exit "$FAILED"
