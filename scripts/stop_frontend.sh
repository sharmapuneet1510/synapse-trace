#!/usr/bin/env bash
# Stop the background frontend server
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/backend/logs/frontend.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "[frontend] No PID file found. Frontend may not be running."
  exit 0
fi

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "[frontend] Stopped (PID $PID)."
else
  echo "[frontend] Process $PID not running."
fi
rm -f "$PID_FILE"
