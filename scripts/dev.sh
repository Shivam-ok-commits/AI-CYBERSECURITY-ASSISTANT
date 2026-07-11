#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT/frontend"
ELECTRON_DIR="$ROOT/electron"
VITE_URL="http://localhost:5173"

echo "=== Sentinel Desktop - Development ==="
echo ""

# Kill stale processes
echo "[setup] Cleaning stale processes..."
pkill -f "uvicorn src.api:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "electron ." 2>/dev/null || true
sleep 1

# 1. Backend with reload
echo "[backend] Starting FastAPI with hot reload..."
cd "$ROOT"
.venv/bin/python -m uvicorn src.api:app --host 127.0.0.1 --port 8000 --reload --log-level info &
BACKEND_PID=$!

echo "[backend] Waiting..."
for i in $(seq 1 30); do
  if curl -s "http://127.0.0.1:8000/api/v1/health" > /dev/null 2>&1; then
    echo "[backend] Ready!"
    break
  fi
  echo -n "."
  sleep 1
done

# 2. Frontend with Vite HMR
echo -e "\n[frontend] Starting Vite dev server..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

echo "[frontend] Waiting..."
for i in $(seq 1 30); do
  if curl -s "$VITE_URL" > /dev/null 2>&1; then
    echo "[frontend] Ready!"
    break
  fi
  echo -n "."
  sleep 1
done

# 3. Electron TypeScript watch
echo -e "\n[electron] Starting TypeScript watcher..."
cd "$ELECTRON_DIR"
npx tsc --watch --preserveWatchOutput &
TSC_PID=$!

sleep 3

# 4. Launch Electron
echo "[electron] Launching..."
cd "$ELECTRON_DIR"
npx electron . &
ELECTRON_PID=$!
echo "[electron] PID: $ELECTRON_PID"

# Watch for changes and restart
echo "[electron] Watching for changes..."
(
  while true; do
    inotifywait -r -e modify "$ELECTRON_DIR/dist/" 2>/dev/null || fswatch -r "$ELECTRON_DIR/dist/" 2>/dev/null || sleep 5
    sleep 1
    echo "[electron] Change detected, restarting..."
    kill $ELECTRON_PID 2>/dev/null || true
    sleep 1
    cd "$ELECTRON_DIR"
    npx electron . &
    ELECTRON_PID=$!
    echo "[electron] Restarted, PID: $ELECTRON_PID"
  done
) &
WATCHER_PID=$!

echo ""
echo "=== All Services Running ==="
echo "  Frontend : $VITE_URL"
echo "  Backend  : http://127.0.0.1:8000"
echo "  API Docs : http://127.0.0.1:8000/docs"
echo ""
echo "  Hot Reload:"
echo "    React   : Instant HMR (save .tsx/.ts)"
echo "    Python  : Auto-restart (save .py)"
echo "    Electron: Auto-restart (save electron/src/*.ts)"
echo ""
echo "  Press Ctrl+C to stop all"

trap "echo ''; echo 'Shutting down...'; kill $BACKEND_PID $FRONTEND_PID $TSC_PID $ELECTRON_PID $WATCHER_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
