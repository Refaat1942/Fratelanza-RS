#!/bin/bash
# Legacy entrypoint — runs the one-command deploy.
exec "$(dirname "$0")/deploy.sh" "$@"
