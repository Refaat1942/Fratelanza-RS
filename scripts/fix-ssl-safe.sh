#!/bin/bash
# Safe SSL fix for rs.fratelanza.com — does NOT touch pharmapos
# Run on VPS: bash /opt/fratelanza/scripts/fix-ssl-safe.sh
set -e

DOMAIN="${1:-rs.fratelanza.com}"
EMAIL="${2:-admin@fratelanza.com}"

echo "Checking pharmapos is still intact..."
if [ -f /etc/nginx/sites-enabled/00-pharmapos ]; then
  echo "✓ pharmapos config exists — will NOT be modified"
else
  echo "Note: pharmapos config not found at expected path"
fi

echo ""
echo "Running isolated FRATELANZA domain setup only..."
bash /opt/fratelanza/scripts/connect-domain.sh "$DOMAIN" "$EMAIL"

echo ""
echo "Verify pharmapos still works — check your pharmapos URL in browser."
echo "FRATELANZA: https://${DOMAIN}"
