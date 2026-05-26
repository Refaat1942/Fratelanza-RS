#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${FRATELANZA_APP_DIR:-/opt/fratelanza}"
PORT="${FRATELANZA_API_PORT:-1058}"
ADMIN_KEY="${FRATELANZA_ADMIN_KEY:-}"
DATA_ROOT="${FRATELANZA_VPS_DATA_ROOT:-/opt/fratelanza/data}"
REPO_URL="${FRATELANZA_REPO_URL:-https://github.com/Refaat1942/Fratelanza-LMP.git}"
BRANCH="${FRATELANZA_BRANCH:-cursor/fratelanza-business-suite-becb}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run this script as root on the VPS."
  exit 1
fi

if [ -z "$ADMIN_KEY" ]; then
  ADMIN_KEY="$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(32))
PY
)"
fi

echo "==> Installing OS packages"
apt update
apt install -y git python3 python3-venv python3-pip nginx ufw curl

echo "==> Preparing application directory"
if [ ! -d "$APP_DIR/.git" ]; then
  rm -rf "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi
cd "$APP_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

echo "==> Installing Python backend dependencies"
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --upgrade pip
"$APP_DIR/.venv/bin/pip" install -e ".[backend]"

echo "==> Writing VPS environment"
mkdir -p "$DATA_ROOT"
cat > "$APP_DIR/.env.vps" <<EOF
FRATELANZA_ADMIN_KEY=$ADMIN_KEY
FRATELANZA_VPS_DATA_ROOT=$DATA_ROOT
EOF
chmod 600 "$APP_DIR/.env.vps"

echo "==> Stopping anything using port $PORT"
if command -v fuser >/dev/null 2>&1; then
  fuser -k "${PORT}/tcp" || true
fi

echo "==> Creating systemd service"
cat > /etc/systemd/system/fratelanza-api.service <<EOF
[Unit]
Description=Fratelanza VPS Admin API
After=network.target

[Service]
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env.vps
ExecStart=$APP_DIR/.venv/bin/uvicorn backend.vps_admin.main:app --host 127.0.0.1 --port $PORT
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable fratelanza-api
systemctl restart fratelanza-api

echo "==> Configuring Nginx reverse proxy"
cat > /etc/nginx/sites-available/fratelanza <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
ln -sf /etc/nginx/sites-available/fratelanza /etc/nginx/sites-enabled/fratelanza
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "==> Opening local firewall if enabled"
ufw allow 22/tcp || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
ufw allow "$PORT/tcp" || true
ufw reload || true

echo "==> Health checks"
sleep 2
curl -fsS "http://127.0.0.1:$PORT/health"
echo
curl -fsS "http://127.0.0.1/health"
echo

PUBLIC_IP="$(curl -fsS https://api.ipify.org || true)"
echo
echo "Fratelanza VPS API is deployed."
echo "Local API: http://127.0.0.1:$PORT/health"
if [ -n "$PUBLIC_IP" ]; then
  echo "Public API: http://$PUBLIC_IP/health"
  echo "Admin EXE URL: http://$PUBLIC_IP"
fi
echo "Admin key: $ADMIN_KEY"
echo
echo "Put these in dist\\FratelanzaAdminConsole\\.env on your laptop:"
echo "FRATELANZA_ADMIN_API_BASE_URL=http://${PUBLIC_IP:-YOUR_VPS_IP}"
echo "FRATELANZA_ADMIN_KEY=$ADMIN_KEY"
