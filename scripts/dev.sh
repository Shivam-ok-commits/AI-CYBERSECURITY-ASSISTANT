#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT/frontend"
ELECTRON_DIR="$ROOT/electron"
FRONTEND_URL="http://localhost:5173"

echo "=== Sentinel Desktop Development ==="
echo ""

echo "[frontend] Starting Vite dev server..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

# Wait for frontend to be ready
echo "[frontend] Waiting for server..."
for i in $(seq 1 30); do
  if curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
    echo "[frontend] Ready at $FRONTEND_URL"
    break
  fi
  sleep 1
done

# Build Electron TypeScript
echo "[electron] Building TypeScript..."
cd "$ELECTRON_DIR"
npm run build
echo "[electron] Build complete"

# Launch Electron
echo "[electron] Launching..."
cd "$ELECTRON_DIR"
npx electron . &
ELECTRON_PID=$!

echo ""
echo "=== All services running ==="
echo "  Frontend: $FRONTEND_URL"
echo "  Press Ctrl+C to stop all"

trap "echo ''; echo 'Shutting down...'; kill $FRONTEND_PID $ELECTRON_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
