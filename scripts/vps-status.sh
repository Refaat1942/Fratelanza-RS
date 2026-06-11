#!/bin/bash
# Show ports + docker on VPS (no deploy, no stops)
APP_DIR="${APP_DIR:-/opt/fratelanza}"
export INSPECT_ONLY=1
exec "$(dirname "$0")/deploy.sh"
