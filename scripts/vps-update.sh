#!/bin/bash
# Wrapper — use DEPLOY-VPS.sh at repo root
exec bash "$(dirname "$0")/../DEPLOY-VPS.sh" "${APP_DIR:-/opt/fratelanza}"
