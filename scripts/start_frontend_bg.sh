#!/usr/bin/env bash
# Start the frontend dev server in the background
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/backend/logs/frontend.pid"
LOG_FILE="$ROOT/backend/logs/frontend.log"

mkdir -p "$ROOT/backend/logs"

if [ -f "$PID_FILE" ]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    echo "[frontend] Already running (PID $PID). Use stop_frontend.sh to stop it."
    exit 1
  fi
  rm -f "$PID_FILE"
fi

echo "[frontend] Starting frontend in background..."
nohup bash "$ROOT/scripts/start_frontend.sh" "${1:-dev}" >> "$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
echo "[frontend] Started (PID $(cat "$PID_FILE")). Logs: $LOG_FILE"
