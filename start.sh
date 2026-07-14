#!/usr/bin/env bash
# Start/restart all services under PM2.
set -euo pipefail

PROJ_DIR="${PROJ_DIR:-/opt/zy}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
GATEWAY_PORT="${GATEWAY_PORT:-8080}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:${BACKEND_PORT}}"
PUBLIC_HOST="${PUBLIC_HOST:-125.208.17.114}"

BACKEND_NAME="zy-backend"
GATEWAY_NAME="zy-gateway"

section() {
  echo ""
  echo "======================================"
  echo "  $1"
  echo "======================================"
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing command: $1"
    exit 1
  fi
}

need_cmd git
need_cmd python3
need_cmd node
need_cmd pm2

section "Pull latest code"
cd "$PROJ_DIR"
git pull

section "Stop old/manual processes"
pm2 delete "$BACKEND_NAME" >/dev/null 2>&1 || true
pm2 delete "$GATEWAY_NAME" >/dev/null 2>&1 || true
pkill -f "uvicorn app.main:app" >/dev/null 2>&1 || true
pkill -f "node gateway.js" >/dev/null 2>&1 || true

section "Start backend with PM2 (port ${BACKEND_PORT})"
cd "$PROJ_DIR/backend"
pm2 start python3 \
  --name "$BACKEND_NAME" \
  --cwd "$PROJ_DIR/backend" \
  -- -m uvicorn app.main:app --host 0.0.0.0 --port "$BACKEND_PORT"

section "Start gateway with PM2 (port ${GATEWAY_PORT})"
cd "$PROJ_DIR/live-gateway"
if [ ! -d node_modules ]; then
  echo "node_modules not found, running npm install..."
  npm install
fi
BACKEND_URL="$BACKEND_URL" pm2 start gateway.js \
  --name "$GATEWAY_NAME" \
  --cwd "$PROJ_DIR/live-gateway" \
  --update-env

section "Save PM2 process list"
pm2 save

if command -v systemctl >/dev/null 2>&1 && [ "$(id -u)" = "0" ]; then
  section "Ensure PM2 starts on boot"
  pm2 startup systemd -u root --hp /root >/tmp/zy-pm2-startup.log 2>&1 || true
  pm2 save
fi

section "Service status"
pm2 list

section "Health check"
if command -v curl >/dev/null 2>&1; then
  curl -fsS "http://127.0.0.1:${BACKEND_PORT}/health" || true
  echo ""
  curl -fsS "http://127.0.0.1:${GATEWAY_PORT}/health" || true
  echo ""
else
  python3 - <<PY
import urllib.request
for url in ("http://127.0.0.1:${BACKEND_PORT}/health", "http://127.0.0.1:${GATEWAY_PORT}/health"):
    try:
        print(url, urllib.request.urlopen(url, timeout=5).read().decode())
    except Exception as exc:
        print(url, "FAILED", exc)
PY
fi

section "Access URLs"
echo "Backend API: http://${PUBLIC_HOST}:${BACKEND_PORT}"
echo "Admin:       http://${PUBLIC_HOST}:${GATEWAY_PORT}/"
echo "Viewer:      http://${PUBLIC_HOST}:${GATEWAY_PORT}/viewer/"
echo ""
echo "Logs:"
echo "  pm2 logs ${BACKEND_NAME}"
echo "  pm2 logs ${GATEWAY_NAME}"
